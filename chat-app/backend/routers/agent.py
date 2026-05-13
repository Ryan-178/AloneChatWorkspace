from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from database import get_db
from auth import get_current_user
from models import User, AgentSession, AgentMessage
from schemas import (
    AgentSessionCreate,
    AgentSessionResponse,
    AgentMessageResponse,
    AgentRunRequest,
    AgentRunResponse,
    AgentSessionsListResponse,
)
from agent_service import (
    get_or_create_agent_session,
    run_agent_task,
    get_session_messages,
)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/sessions", response_model=AgentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_session(
    data: AgentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await get_or_create_agent_session(
        db=db,
        user_id=current_user.id,
        conversation_id=data.conversation_id,
        title=data.title,
    )
    return AgentSessionResponse(
        id=session.id,
        user_id=session.user_id,
        conversation_id=session.conversation_id,
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[],
    )


@router.get("/sessions", response_model=AgentSessionsListResponse)
async def list_agent_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentSession)
        .where(AgentSession.user_id == current_user.id)
        .order_by(desc(AgentSession.updated_at))
    )
    sessions = result.scalars().all()
    items = []
    for session in sessions:
        items.append(AgentSessionResponse(
            id=session.id,
            user_id=session.user_id,
            conversation_id=session.conversation_id,
            title=session.title,
            status=session.status,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[],
        ))
    return AgentSessionsListResponse(items=items)


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
async def get_agent_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentSession).where(
            AgentSession.id == session_id,
            AgentSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await get_session_messages(db, session_id, limit=100)
    message_responses = [
        AgentMessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
            tool_results=msg.tool_results,
            metadata=msg.metadata,
            created_at=msg.created_at,
        )
        for msg in messages
    ]

    return AgentSessionResponse(
        id=session.id,
        user_id=session.user_id,
        conversation_id=session.conversation_id,
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=message_responses,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentSession).where(
            AgentSession.id == session_id,
            AgentSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return None


@router.post("/sessions/{session_id}/run", response_model=AgentRunResponse)
async def run_agent(
    session_id: str,
    data: AgentRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentSession).where(
            AgentSession.id == session_id,
            AgentSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answer = await run_agent_task(db, session_id, data.message)
    return AgentRunResponse(answer=answer)
