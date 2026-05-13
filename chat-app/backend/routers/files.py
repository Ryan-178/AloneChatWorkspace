import os
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from auth import get_current_user
from models import User, FileRecord
from schemas import (
    FileRecordResponse,
    FileRecordListResponse,
    PaginatedResponse,
)
from services.office_converter import OfficeConverter

router = APIRouter(prefix="/api/files", tags=["files"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _guess_file_type(filename: str) -> str:
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext in ("docx", "doc"):
        return "document"
    elif ext in ("xlsx", "xls"):
        return "spreadsheet"
    elif ext in ("pptx", "ppt"):
        return "presentation"
    return "other"


def _generate_stored_path(original_name: str) -> str:
    date_dir = datetime.utcnow().strftime("%Y-%m-%d")
    target_dir = os.path.join(UPLOAD_DIR, date_dir)
    os.makedirs(target_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    return os.path.join(target_dir, unique_name)


@router.post("/upload", response_model=FileRecordResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stored_path = _generate_stored_path(file.filename or "unnamed")
    content = await file.read()
    file_size = len(content)
    with open(stored_path, "wb") as f:
        f.write(content)

    file_type = _guess_file_type(file.filename or "")
    preview_data = None
    if file_type in ("document", "spreadsheet", "presentation"):
        try:
            json_data = OfficeConverter.convert_to_json(stored_path, file_type)
            preview_data = json_data
        except Exception:
            preview_data = None

    record = FileRecord(
        filename=file.filename or "unnamed",
        stored_path=stored_path,
        file_size=file_size,
        file_type=file_type,
        uploader_id=current_user.id,
        preview_data=preview_data,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("", response_model=PaginatedResponse)
async def list_files(
    file_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(FileRecord).where(FileRecord.uploader_id == current_user.id)
    if file_type:
        query = query.where(FileRecord.file_type == file_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        query.order_by(FileRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{file_id}", response_model=FileRecordResponse)
async def get_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploader_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found", "details": {}},
        )
    return record


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploader_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found", "details": {}},
        )
    if not os.path.exists(record.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found on disk", "details": {}},
        )
    return FileResponse(
        path=record.stored_path,
        filename=record.filename,
        media_type="application/octet-stream",
    )


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploader_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found", "details": {}},
        )
    return {"preview_data": record.preview_data}


@router.post("/{file_id}/convert")
async def convert_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploader_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found", "details": {}},
        )
    if not os.path.exists(record.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found on disk", "details": {}},
        )
    try:
        json_data = OfficeConverter.convert_to_json(record.stored_path, record.file_type)
        record.preview_data = json_data
        await db.commit()
        return {"content": json_data}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "ConversionError", "message": str(exc), "details": {}},
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FileRecord).where(
            FileRecord.id == file_id,
            FileRecord.uploader_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "File not found", "details": {}},
        )
    if os.path.exists(record.stored_path):
        os.remove(record.stored_path)
    await db.delete(record)
    await db.commit()
    return None
