"""
会话管理模块 - Session Manager
实现会话车道隔离，避免任务冲突
"""
import time
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from collections import defaultdict
from .types import Session, SessionState


class SessionManager:
    """会话管理器"""
    
    def __init__(self, timeout_seconds: int = 3600):
        self.timeout_seconds = timeout_seconds
        self.sessions: Dict[str, Session] = {}  # session_id -> Session
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)  # user_id -> [session_id]
        self.session_lanes: Dict[str, List[str]] = defaultdict(list)  # 用户级车道
        self.last_activity: Dict[str, float] = {}  # session_id -> last_activity_ts
    
    def create_session(self, user_id: str, channel: str = "chat_app", agent_config: Optional[Dict] = None) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            state=SessionState.IDLE,
            agent_config=agent_config or {},
        )
        self.sessions[session_id] = session
        self.user_sessions[user_id].append(session_id)
        self.last_activity[session_id] = time.time()
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            self.last_activity[session_id] = time.time()
        return session
    
    def get_or_create_session(self, session_key: str, user_id: str, channel: str = "chat_app") -> Session:
        """获取或创建会话（通过session_key）"""
        # 尝试用session_key作为session_id查找
        session = self.get_session(session_key)
        if session:
            return session
        # 找不到则创建新会话
        return self.create_session(user_id, channel)
    
    def update_session_state(self, session_id: str, state: SessionState) -> bool:
        """更新会话状态"""
        session = self.sessions.get(session_id)
        if session:
            session.state = state
            session.touch()
            self.last_activity[session_id] = time.time()
            return True
        return False
    
    def update_session_config(self, session_id: str, agent_config: Dict) -> bool:
        """更新会话Agent配置"""
        session = self.sessions.get(session_id)
        if session:
            session.agent_config.update(agent_config)
            session.touch()
            self.last_activity[session_id] = time.time()
            return True
        return False
    
    def update_memory_context(self, session_id: str, memory_context: Dict) -> bool:
        """更新记忆上下文"""
        session = self.sessions.get(session_id)
        if session:
            session.memory_context.update(memory_context)
            session.touch()
            self.last_activity[session_id] = time.time()
            return True
        return False
    
    def acquire_session_lane(self, session_id: str) -> bool:
        """获取会话车道（避免并发冲突）"""
        # 简单实现：检查会话是否正在运行
        session = self.sessions.get(session_id)
        if session and session.state == SessionState.RUNNING:
            return False
        if session:
            session.state = SessionState.RUNNING
            session.touch()
            self.last_activity[session_id] = time.time()
            return True
        return False
    
    def release_session_lane(self, session_id: str):
        """释放会话车道"""
        session = self.sessions.get(session_id)
        if session and session.state == SessionState.RUNNING:
            session.state = SessionState.IDLE
            session.touch()
    
    def list_active_sessions(self) -> List[Session]:
        """列出活跃会话"""
        now = time.time()
        active = []
        for session_id, ts in self.last_activity.items():
            if now - ts < self.timeout_seconds:
                session = self.sessions.get(session_id)
                if session:
                    active.append(session)
        return active
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        now = time.time()
        expired_ids = []
        for session_id, ts in self.last_activity.items():
            if now - ts > self.timeout_seconds:
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            session = self.sessions.pop(session_id, None)
            if session:
                # 从user_sessions中移除
                user_sessions = self.user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
                self.last_activity.pop(session_id, None)
        
        return len(expired_ids)
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        session = self.sessions.pop(session_id, None)
        if session:
            user_sessions = self.user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            self.last_activity.pop(session_id, None)
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户的所有会话"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(self.list_active_sessions()),
            "total_users": len(self.user_sessions),
        }
