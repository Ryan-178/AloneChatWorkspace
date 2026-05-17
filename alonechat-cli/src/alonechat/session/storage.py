"""
会话存储 / Session Storage

提供会话的持久化存储功能 / Provides persistent storage for sessions
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Session:
    """会话数据类 / Session Data Class"""
    id: str
    created_at: str
    updated_at: str
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def create(cls, session_id: Optional[str] = None) -> "Session":
        """创建新会话 / Create new session"""
        now = datetime.now().isoformat()
        return cls(
            id=session_id or str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            messages=[],
            metadata={}
        )
    
    def to_dict(self) -> dict:
        """转换为字典 / Convert to dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """从字典创建 / Create from dict"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {})
        )


class SessionStorage:
    """会话存储器 / Session Storage"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path.home() / ".alonechat" / "sessions"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        """获取会话文件路径 / Get session file path"""
        return self.storage_dir / f"{session_id}.json"
    
    def save(self, session: Session) -> None:
        """保存会话 / Save session"""
        session.updated_at = datetime.now().isoformat()
        path = self._get_session_path(session.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load(self, session_id: str) -> Optional[Session]:
        """加载会话 / Load session"""
        path = self._get_session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception:
            return None
    
    def delete(self, session_id: str) -> bool:
        """删除会话 / Delete session"""
        path = self._get_session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_sessions(self, limit: int = 20) -> list[Session]:
        """列出所有会话 / List all sessions"""
        sessions = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except Exception:
                continue
        
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]
    
    def get_latest_session(self) -> Optional[Session]:
        """获取最近的会话 / Get latest session"""
        sessions = self.list_sessions(limit=1)
        return sessions[0] if sessions else None
    
    def get_session_by_cwd(self, cwd: str) -> Optional[Session]:
        """根据工作目录获取会话 / Get session by working directory"""
        for session in self.list_sessions(limit=100):
            if session.metadata.get("cwd") == cwd:
                return session
        return None
