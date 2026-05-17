"""
会话管理器 / Session Manager

管理会话的生命周期 / Manages session lifecycle
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from alonechat.session.storage import SessionStorage, Session


class SessionManager:
    """会话管理器 / Session Manager"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage = SessionStorage(storage_dir)
        self.current_session: Optional[Session] = None
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """创建新会话 / Create new session"""
        session = Session.create(session_id)
        session.metadata["cwd"] = str(Path.cwd())
        self.storage.save(session)
        self.current_session = session
        return session
    
    def continue_session(self) -> Optional[Session]:
        """继续最近的会话 / Continue latest session"""
        cwd = str(Path.cwd())
        
        session = self.storage.get_session_by_cwd(cwd)
        if session:
            self.current_session = session
            return session
        
        session = self.storage.get_latest_session()
        if session:
            self.current_session = session
            return session
        
        return None
    
    def resume_session(self, session_id: str) -> Optional[Session]:
        """恢复指定会话 / Resume specific session"""
        session = self.storage.load(session_id)
        if session:
            self.current_session = session
            return session
        return None
    
    def save_current_session(self) -> None:
        """保存当前会话 / Save current session"""
        if self.current_session:
            self.storage.save(self.current_session)
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到当前会话 / Add message to current session"""
        if self.current_session is None:
            self.create_session()
        
        self.current_session.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_current_session()
    
    def get_messages(self) -> list[dict]:
        """获取当前会话的消息 / Get messages from current session"""
        if self.current_session:
            return self.current_session.messages.copy()
        return []
    
    def clear_messages(self) -> None:
        """清除当前会话的消息 / Clear messages from current session"""
        if self.current_session:
            self.current_session.messages = []
            self.save_current_session()
    
    def list_sessions(self, limit: int = 20) -> list[Session]:
        """列出所有会话 / List all sessions"""
        return self.storage.list_sessions(limit)
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话 / Delete session"""
        return self.storage.delete(session_id)
    
    def get_session_info(self) -> dict:
        """获取当前会话信息 / Get current session info"""
        if self.current_session is None:
            return {
                "has_session": False,
                "id": None,
                "message_count": 0,
                "created_at": None,
                "updated_at": None
            }
        
        return {
            "has_session": True,
            "id": self.current_session.id,
            "message_count": len(self.current_session.messages),
            "created_at": self.current_session.created_at,
            "updated_at": self.current_session.updated_at,
            "cwd": self.current_session.metadata.get("cwd")
        }
    
    def read_pipe_input(self) -> Optional[str]:
        """读取管道输入 / Read piped input"""
        if not sys.stdin.isatty():
            return sys.stdin.read()
        return None
