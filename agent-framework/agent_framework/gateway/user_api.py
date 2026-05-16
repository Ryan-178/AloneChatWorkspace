"""
用户端API - User Client API
包含认证、会话管理等用户端功能
"""
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from .auth import (
    user_manager,
    UserCreate,
    UserLogin,
    UserResponse,
    AuthResponse,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from .session import SessionManager
from .types import SessionState


security = HTTPBearer(auto_error=False)


class SessionCreate(BaseModel):
    """会话创建请求"""
    mode: str = Field(default="MTC", description="Agent模式: MTC 或 CODE")


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    user_id: str
    mode: str
    state: str
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse]
    total: int


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """获取当前用户（依赖注入）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")
    
    return payload


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """获取当前用户（可选）"""
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials)
    return payload


def create_user_api(app: FastAPI, session_manager: SessionManager):
    """创建用户端API路由"""
    
    @app.post("/api/auth/register", response_model=AuthResponse)
    async def register(request: UserCreate):
        """用户注册"""
        try:
            user = user_manager.create_user(
                username=request.username,
                email=request.email,
                password=request.password
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        user_manager.store_refresh_token(user.id, refresh_token)
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                created_at=user.created_at.isoformat(),
            )
        )
    
    @app.post("/api/auth/login", response_model=AuthResponse)
    async def login(request: UserLogin):
        """用户登录"""
        user = user_manager.authenticate(request.username, request.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        user_manager.store_refresh_token(user.id, refresh_token)
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                created_at=user.created_at.isoformat(),
            )
        )
    
    @app.get("/api/auth/me", response_model=UserResponse)
    async def get_me(user: dict = Depends(get_current_user)):
        """获取当前用户信息"""
        user_obj = user_manager.get_user(user["user_id"])
        
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            id=user_obj.id,
            username=user_obj.username,
            email=user_obj.email,
            avatar_url=user_obj.avatar_url,
            created_at=user_obj.created_at.isoformat(),
        )
    
    @app.post("/api/auth/logout")
    async def logout(user: dict = Depends(get_current_user)):
        """用户登出"""
        return {"success": True, "message": "已成功登出"}
    
    @app.post("/api/auth/refresh")
    async def refresh_token(
        authorization: Optional[str] = Header(None)
    ):
        """刷新访问令牌"""
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="未提供刷新令牌")
        
        refresh_token_value = authorization.replace("Bearer ", "")
        user_id = user_manager.validate_refresh_token(refresh_token_value)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的刷新令牌")
        
        user = user_manager.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        new_access_token = create_access_token(user)
        
        return {"access_token": new_access_token}
    
    @app.get("/api/sessions", response_model=SessionListResponse)
    async def list_sessions(
        user: dict = Depends(get_current_user),
        limit: int = Query(20, ge=1, le=100),
    ):
        """获取用户的会话列表"""
        sessions = session_manager.get_user_sessions(user["user_id"])
        
        return SessionListResponse(
            sessions=[
                SessionResponse(
                    session_id=s.session_id,
                    user_id=s.user_id,
                    mode=s.agent_config.get("mode", "MTC"),
                    state=s.state.value,
                    created_at=s.created_at.isoformat(),
                    updated_at=s.updated_at.isoformat(),
                )
                for s in sessions[:limit]
            ],
            total=len(sessions),
        )
    
    @app.post("/api/sessions", response_model=SessionResponse)
    async def create_session(
        request: SessionCreate,
        user: dict = Depends(get_current_user),
    ):
        """创建新会话"""
        session = session_manager.create_session(
            user_id=user["user_id"],
            channel="chat_app",
            agent_config={"mode": request.mode}
        )
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            mode=request.mode,
            state=session.state.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
    
    @app.get("/api/sessions/{session_id}", response_model=SessionResponse)
    async def get_session(
        session_id: str,
        user: dict = Depends(get_current_user),
    ):
        """获取会话详情"""
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        if session.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            mode=session.agent_config.get("mode", "MTC"),
            state=session.state.value,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
    
    @app.delete("/api/sessions/{session_id}")
    async def delete_session(
        session_id: str,
        user: dict = Depends(get_current_user),
    ):
        """删除会话"""
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        
        if session.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="无权删除此会话")
        
        success = session_manager.delete_session(session_id)
        
        return {"success": success, "message": f"会话已删除: {session_id}"}
    
    @app.get("/api/users/stats")
    async def get_user_stats():
        """获取用户统计信息"""
        return user_manager.get_stats()
