from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import json

from config import get_settings
from database import get_db, engine, Base
from models import User, Conversation, ConversationParticipant, Message, Group, GroupMember, FileRecord
from schemas import (
    UserCreate, UserResponse, UserUpdate, UserLogin, Token,
    MessageCreate, MessageResponse,
    ConversationCreate, ConversationResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupMemberResponse,
    ErrorResponse, PaginatedResponse,
    FileRecordResponse,
)
from auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_user_optional
from websocket_manager import manager
from routers import agent, workspaces, files

settings = get_settings()

app = FastAPI(title="ChatApp API", version="1.0.0")

app.include_router(agent.router)
app.include_router(workspaces.router)
app.include_router(files.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await manager.connect_redis()


@app.on_event("shutdown")
async def shutdown():
    await manager.disconnect_redis()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {
        "error": "InternalServerError",
        "message": str(exc),
        "details": {}
    }


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Conflict", "message": "Email already registered", "details": {}}
        )

    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        display_name=user_data.display_name,
        avatar_url=user_data.avatar_url
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "message": "Incorrect email or password", "details": {}}
        )

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.patch("/api/users/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_data.display_name is not None:
        current_user.display_name = user_data.display_name
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user


@app.get("/api/users", response_model=List[UserResponse])
async def search_users(
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(User).where(User.id != current_user.id)
    if q:
        query = query.where(
            or_(
                User.display_name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%")
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "User not found", "details": {}})
    return user


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = Conversation(type=data.type, name=data.name)
    db.add(conversation)
    await db.flush()

    all_participants = list(set(data.participant_ids + [current_user.id]))
    for pid in all_participants:
        cp = ConversationParticipant(conversation_id=conversation.id, user_id=pid)
        db.add(cp)

    await db.commit()
    await db.refresh(conversation)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation.id)
        .options(selectinload(Conversation.participants).selectinload(ConversationParticipant.user))
    )
    return result.scalar_one()


@app.get("/api/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id == current_user.id)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender)
        )
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    response = []
    for conv in conversations:
        conv_dict = {
            "id": conv.id,
            "type": conv.type,
            "name": conv.name,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "participants": [
                {
                    "id": cp.user.id,
                    "email": cp.user.email,
                    "display_name": cp.user.display_name,
                    "avatar_url": cp.user.avatar_url,
                    "is_online": cp.user.is_online,
                    "last_seen_at": cp.user.last_seen_at,
                    "created_at": cp.user.created_at
                }
                for cp in conv.participants
            ],
            "last_message": None
        }
        if conv.messages:
            last_msg = max(conv.messages, key=lambda m: m.created_at)
            conv_dict["last_message"] = {
                "id": last_msg.id,
                "conversation_id": last_msg.conversation_id,
                "sender_id": last_msg.sender_id,
                "content": last_msg.content,
                "message_type": last_msg.message_type,
                "created_at": last_msg.created_at,
                "sender": {
                    "id": last_msg.sender.id,
                    "email": last_msg.sender.email,
                    "display_name": last_msg.sender.display_name,
                    "avatar_url": last_msg.sender.avatar_url,
                    "is_online": last_msg.sender.is_online,
                    "last_seen_at": last_msg.sender.last_seen_at,
                    "created_at": last_msg.sender.created_at
                } if last_msg.sender else None
            }
        response.append(conv_dict)
    return response


@app.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.participants).selectinload(ConversationParticipant.user))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Conversation not found", "details": {}})
    return conversation


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count_result = await db.execute(
        select(func.count()).where(Message.conversation_id == conversation_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()

    pages = (total + page_size - 1) // page_size
    return {
        "items": messages,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@app.post("/api/groups", response_model=GroupResponse)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = Group(
        name=data.name,
        description=data.description,
        avatar_url=data.avatar_url,
        owner_id=current_user.id
    )
    db.add(group)
    await db.flush()

    owner_member = GroupMember(group_id=group.id, user_id=current_user.id, role="owner")
    db.add(owner_member)

    for mid in (data.member_ids or []):
        if mid != current_user.id:
            member = GroupMember(group_id=group.id, user_id=mid, role="member")
            db.add(member)

    await db.commit()
    await db.refresh(group)

    result = await db.execute(
        select(Group)
        .where(Group.id == group.id)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
    )
    return result.scalar_one()


@app.get("/api/groups", response_model=List[GroupResponse])
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Group)
        .join(GroupMember)
        .where(GroupMember.user_id == current_user.id)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
        .order_by(Group.created_at.desc())
    )
    return result.scalars().all()


@app.get("/api/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Group)
        .where(Group.id == group_id)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Group not found", "details": {}})
    return group


@app.patch("/api/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Group not found", "details": {}})
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "Forbidden", "message": "Only owner can update group", "details": {}})

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    if data.avatar_url is not None:
        group.avatar_url = data.avatar_url

    await db.commit()
    await db.refresh(group)
    return group


@app.post("/api/groups/{group_id}/members", response_model=GroupMemberResponse)
async def add_group_member(
    group_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Group not found", "details": {}})
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "Forbidden", "message": "Only owner can add members", "details": {}})

    existing = await db.execute(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"error": "Conflict", "message": "User already in group", "details": {}})

    member = GroupMember(group_id=group_id, user_id=user_id, role="member")
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@app.delete("/api/groups/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Group not found", "details": {}})
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"error": "Forbidden", "message": "Only owner can remove members", "details": {}})

    result = await db.execute(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail={"error": "NotFound", "message": "Member not found", "details": {}})

    await db.delete(member)
    await db.commit()
    return {"message": "Member removed"}


@app.get("/api/groups/{group_id}/messages")
async def get_group_messages(
    group_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member_check = await db.execute(
        select(GroupMember).where(
            and_(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id)
        )
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail={"error": "Forbidden", "message": "Not a group member", "details": {}})

    count_result = await db.execute(
        select(func.count()).where(Message.conversation_id == group_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == group_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()

    pages = (total + page_size - 1) // page_size
    return {
        "items": messages,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "message":
                recipient_id = payload.get("recipient_id")
                group_id = payload.get("group_id")
                content = payload.get("content", "")

                if group_id:
                    await manager.broadcast_to_group({
                        "type": "message",
                        "payload": {
                            "group_id": group_id,
                            "sender_id": user_id,
                            "content": content
                        }
                    }, group_id)
                elif recipient_id:
                    await manager.send_message({
                        "type": "message",
                        "payload": {
                            "sender_id": user_id,
                            "recipient_id": recipient_id,
                            "content": content
                        }
                    }, recipient_id)
            elif msg_type == "join_group":
                group_id = payload.get("group_id")
                if group_id:
                    manager.join_group(user_id, group_id)
            elif msg_type == "leave_group":
                group_id = payload.get("group_id")
                if group_id:
                    manager.leave_group(user_id, group_id)
            elif msg_type == "agent":
                content = payload.get("content", "")
                session_id = payload.get("session_id", "")
                stream = payload.get("stream", False)
                if content and session_id:
                    if stream:
                        asyncio.create_task(manager.handle_agent_stream(user_id, content, session_id))
                    else:
                        asyncio.create_task(manager.handle_agent_message(user_id, content, session_id))
            elif msg_type == "message":
                content = payload.get("content", "")
                if content.startswith("/agent "):
                    agent_content = content[7:]
                    session_id = payload.get("session_id", "")
                    if agent_content and session_id:
                        asyncio.create_task(manager.handle_agent_message(user_id, agent_content, session_id))
                elif content.startswith("/multi-agent "):
                    from multi_agent_service import run_multi_agent_team
                    agent_content = content[13:]
                    session_id = payload.get("session_id", "")
                    if agent_content and session_id:
                        asyncio.create_task(run_multi_agent_team(user_id, session_id, agent_content, manager))
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception:
        await manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
