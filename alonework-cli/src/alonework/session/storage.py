"""
会话存储 / Session Storage

提供会话的持久化存储功能 / Provides persistent storage for sessions

增强功能 / Enhanced Features:
- 会话显示名称 / Session display name
- 会话分叉 / Session fork/branch
- 父会话引用 / Parent session reference
- 压缩状态追踪 / Compression state tracking
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class Session:
    """
    会话数据类 / Session Data Class

    增强字段 / Enhanced Fields:
    - display_name: 会话显示名称 / Session display name
    - parent_id: 父会话ID（用于分叉）/ Parent session ID (for fork)
    - branch_point: 分叉点消息索引 / Branch point message index
    - compressed: 是否已压缩 / Whether compressed
    - compression_summary: 压缩摘要 / Compression summary
    """
    id: str
    created_at: str
    updated_at: str
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    display_name: Optional[str] = None
    parent_id: Optional[str] = None
    branch_point: int = 0
    compressed: bool = False
    compression_summary: Optional[str] = None
    agent_config: dict = field(default_factory=dict)

    @classmethod
    def create(cls, session_id: Optional[str] = None, display_name: Optional[str] = None) -> "Session":
        """创建新会话 / Create new session"""
        now = datetime.now().isoformat()
        return cls(
            id=session_id or str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            messages=[],
            metadata={},
            display_name=display_name,
        )

    def fork(self, branch_point: Optional[int] = None) -> "Session":
        """
        分叉会话 / Fork session

        创建一个新会话，保留原会话的部分历史 / Create a new session preserving partial history
        """
        now = datetime.now().isoformat()
        fork_point = branch_point if branch_point is not None else len(self.messages)

        return cls(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            messages=self.messages[:fork_point].copy(),
            metadata=self.metadata.copy(),
            display_name=f"{self.display_name or self.id[:8]} (分支)",
            parent_id=self.id,
            branch_point=fork_point,
        )

    def get_name(self) -> str:
        """获取会话显示名称 / Get session display name"""
        return self.display_name or self.id[:8]

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
            metadata=data.get("metadata", {}),
            display_name=data.get("display_name"),
            parent_id=data.get("parent_id"),
            branch_point=data.get("branch_point", 0),
            compressed=data.get("compressed", False),
            compression_summary=data.get("compression_summary"),
            agent_config=data.get("agent_config", {}),
        )


class SessionStorage:
    """会话存储器 / Session Storage"""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path.home() / ".alonework" / "sessions"
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
