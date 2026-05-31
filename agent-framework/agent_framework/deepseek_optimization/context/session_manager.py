"""
Session Manager
会话管理器 - 支持跨会话上下文持久化和恢复
"""
import json
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class SessionMetadata:
    session_id: str
    created_at: datetime
    last_active_at: datetime
    message_count: int = 0
    total_tokens: int = 0
    title: str = ""
    tags: List[str] = field(default_factory=list)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "title": self.title,
            "tags": self.tags,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active_at=datetime.fromisoformat(data["last_active_at"]),
            message_count=data.get("message_count", 0),
            total_tokens=data.get("total_tokens", 0),
            title=data.get("title", ""),
            tags=data.get("tags", []),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionSummary:
    session_id: str
    title: str
    message_count: int
    last_active_at: datetime
    preview: str


class SessionManager:
    """
    会话管理器
    管理会话的创建、保存、加载、删除和搜索
    """
    
    def __init__(
        self,
        storage_root: Path,
        auto_save: bool = True,
        max_sessions: int = 1000,
    ):
        self.storage_root = storage_root
        self.auto_save = auto_save
        self.max_sessions = max_sessions
        
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        self._active_sessions: Dict[str, SessionMetadata] = {}
        self._session_index: Dict[str, Path] = {}
        
        self._load_index()
    
    def _load_index(self):
        index_file = self.storage_root / "session_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for session_id, path_str in data.items():
                        self._session_index[session_id] = Path(path_str)
            except Exception:
                pass
    
    def _save_index(self):
        index_file = self.storage_root / "session_index.json"
        data = {sid: str(path) for sid, path in self._session_index.items()}
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create_session(
        self,
        title: str = "",
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionMetadata:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = SessionMetadata(
            session_id=session_id,
            created_at=now,
            last_active_at=now,
            title=title or f"Session {now.strftime('%Y-%m-%d %H:%M')}",
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        self._session_index[session_id] = session_dir
        self._active_sessions[session_id] = session
        
        self._save_session_metadata(session)
        self._save_index()
        
        return session
    
    def _sanitize_session_id(self, session_id: str) -> str:
        sanitized = re.sub(r'[^\w\-]', '', session_id)
        sanitized = sanitized.strip('.')
        return sanitized or "invalid"

    def _get_session_dir(self, session_id: str) -> Path:
        safe_id = self._sanitize_session_id(session_id)
        return self.storage_root / "sessions" / safe_id[:2] / safe_id
    
    def _save_session_metadata(self, session: SessionMetadata):
        session_dir = self._get_session_dir(session.session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        meta_file = session_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str) -> Optional[SessionMetadata]:
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        session_dir = self._session_index.get(session_id)
        if session_dir is None:
            session_dir = self._get_session_dir(session_id)
        
        meta_file = session_dir / "metadata.json"
        if not meta_file.exists():
            return None
        
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                session = SessionMetadata.from_dict(data)
                self._active_sessions[session_id] = session
                return session
        except Exception:
            return None
    
    def update_session(
        self,
        session_id: str,
        message_count: Optional[int] = None,
        total_tokens: Optional[int] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SessionMetadata]:
        session = self.load_session(session_id)
        if session is None:
            return None
        
        session.last_active_at = datetime.now()
        
        if message_count is not None:
            session.message_count = message_count
        if total_tokens is not None:
            session.total_tokens = total_tokens
        if title is not None:
            session.title = title
        if tags is not None:
            session.tags = tags
        if metadata is not None:
            session.metadata.update(metadata)
        
        self._save_session_metadata(session)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        session_dir = self._session_index.get(session_id)
        if session_dir is None:
            session_dir = self._get_session_dir(session_id)
        
        if not session_dir.exists():
            return False
        
        import shutil
        shutil.rmtree(session_dir)
        
        if session_id in self._session_index:
            del self._session_index[session_id]
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        self._save_index()
        return True
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionSummary]:
        sessions = []
        
        for session_id, session_dir in self._session_index.items():
            meta_file = session_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session = SessionMetadata.from_dict(data)
                    
                    if user_id and session.user_id != user_id:
                        continue
                    if tags and not all(t in session.tags for t in tags):
                        continue
                    
                    preview = self._get_session_preview(session_id)
                    
                    sessions.append(SessionSummary(
                        session_id=session.session_id,
                        title=session.title,
                        message_count=session.message_count,
                        last_active_at=session.last_active_at,
                        preview=preview,
                    ))
            except Exception:
                continue
        
        sessions.sort(key=lambda s: s.last_active_at, reverse=True)
        
        return sessions[offset:offset + limit]
    
    def _get_session_preview(self, session_id: str) -> str:
        session_dir = self._session_index.get(session_id)
        if session_dir is None:
            return ""
        
        messages_file = session_dir / "messages.jsonl"
        if not messages_file.exists():
            return ""
        
        try:
            with open(messages_file, "r", encoding="utf-8") as f:
                first_line = f.readline()
                if first_line:
                    msg = json.loads(first_line)
                    content = msg.get("content", "")
                    return content[:100] + "..." if len(content) > 100 else content
        except Exception:
            pass
        
        return ""
    
    def search_sessions(
        self,
        query: str,
        limit: int = 20,
    ) -> List[SessionSummary]:
        results = []
        query_lower = query.lower()
        
        for summary in self.list_sessions(limit=1000):
            if query_lower in summary.title.lower() or query_lower in summary.preview.lower():
                results.append(summary)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_session_path(self, session_id: str) -> Optional[Path]:
        return self._session_index.get(session_id) or self._get_session_dir(session_id)
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        cutoff = datetime.now()
        cleaned = 0
        
        for session_id, session_dir in list(self._session_index.items()):
            meta_file = session_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_active = datetime.fromisoformat(data["last_active_at"])
                    
                    days_inactive = (cutoff - last_active).days
                    if days_inactive > days:
                        if self.delete_session(session_id):
                            cleaned += 1
            except Exception:
                continue
        
        return cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        total_sessions = len(self._session_index)
        active_sessions = len(self._active_sessions)
        
        total_messages = 0
        total_tokens = 0
        
        for session_id in self._session_index:
            session = self.load_session(session_id)
            if session:
                total_messages += session.message_count
                total_tokens += session.total_tokens
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
        }
