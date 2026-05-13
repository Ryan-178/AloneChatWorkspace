from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from database import get_db
from auth import get_current_user
from models import User, Workspace, WorkspaceMember, Conversation, Group
from schemas import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
    WorkspaceMemberResponse,
    WorkspaceInviteRequest,
    WorkspaceListResponse,
)

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


def check_workspace_permission(workspace: Workspace, user: User, required_roles: List[str]) -> bool:
    if workspace.owner_id == user.id and "owner" in required_roles:
        return True
    for member in workspace.members:
        if member.user_id == user.id and member.role in required_roles:
            return True
    return False


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = Workspace(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
    )
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=[WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            invited_by=None,
            created_at=member.created_at,
        )],
    )


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    workspaces = result.scalars().all()
    items = []
    for ws in workspaces:
        members = []
        for m in ws.members:
            members.append(WorkspaceMemberResponse(
                id=m.id,
                workspace_id=m.workspace_id,
                user_id=m.user_id,
                role=m.role,
                invited_by=m.invited_by,
                created_at=m.created_at,
            ))
        items.append(WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            description=ws.description,
            owner_id=ws.owner_id,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
            members=members,
        ))
    return WorkspaceListResponse(items=items)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin", "member"]):
        raise HTTPException(status_code=403, detail="No permission")

    members = []
    for m in workspace.members:
        members.append(WorkspaceMemberResponse(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            role=m.role,
            invited_by=m.invited_by,
            created_at=m.created_at,
        ))

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=members,
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin"]):
        raise HTTPException(status_code=403, detail="No permission")

    if data.name is not None:
        workspace.name = data.name
    if data.description is not None:
        workspace.description = data.description

    await db.commit()
    await db.refresh(workspace)

    members = []
    for m in workspace.members:
        members.append(WorkspaceMemberResponse(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            role=m.role,
            invited_by=m.invited_by,
            created_at=m.created_at,
        ))

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=members,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")

    await db.delete(workspace)
    await db.commit()
    return None


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def invite_member(
    workspace_id: str,
    data: WorkspaceInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin"]):
        raise HTTPException(status_code=403, detail="No permission")

    user_result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in workspace")

    role = data.role if data.role in ["admin", "member"] else "member"

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
        invited_by=current_user.id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        role=member.role,
        invited_by=member.invited_by,
        created_at=member.created_at,
    )


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin"]):
        raise HTTPException(status_code=403, detail="No permission")

    member_result = await db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove owner")

    if current_user.id != workspace.owner_id and member.role == "admin":
        raise HTTPException(status_code=403, detail="Only owner can remove admin")

    await db.delete(member)
    await db.commit()
    return None


@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: str,
    user_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin"]):
        raise HTTPException(status_code=403, detail="No permission")

    member_result = await db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    new_role = data.get("role", "member")
    if new_role not in ["admin", "member"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner role")

    if current_user.id != workspace.owner_id and new_role == "admin":
        raise HTTPException(status_code=403, detail="Only owner can promote to admin")

    member.role = new_role
    await db.commit()
    await db.refresh(member)

    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        role=member.role,
        invited_by=member.invited_by,
        created_at=member.created_at,
    )


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not check_workspace_permission(workspace, current_user, ["owner", "admin", "member"]):
        raise HTTPException(status_code=403, detail="No permission")

    members = []
    for m in workspace.members:
        members.append(WorkspaceMemberResponse(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            role=m.role,
            invited_by=m.invited_by,
            created_at=m.created_at,
        ))
    return members
