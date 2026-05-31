"""
会话存储基类 - Base Session Storage

定义会话存储的抽象接口
Defines abstract interface for session storage
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class SessionData:
    """
    会话数据类 - Session Data Class
    
    表示一个会话的完整数据
    Represents complete data of a session
    """
    
    def __init__(
        self,
        id: str,
        display_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        parent_id: Optional[str] = None,
        branch_point: Optional[int] = None,
        mode: str = "agent",
        interaction_mode: str = "agent",
        metadata: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.display_name = display_name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.parent_id = parent_id
        self.branch_point = branch_point
        self.mode = mode
        self.interaction_mode = interaction_mode
        self.metadata = metadata or {}
        self.agent_config = agent_config or {}
        self.messages: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "parent_id": self.parent_id,
            "branch_point": self.branch_point,
            "mode": self.mode,
            "interaction_mode": self.interaction_mode,
            "metadata": self.metadata,
            "agent_config": self.agent_config,
            "messages": self.messages,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """从字典创建 / Create from dictionary"""
        session = cls(
            id=data["id"],
            display_name=data.get("display_name"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            parent_id=data.get("parent_id"),
            branch_point=data.get("branch_point"),
            mode=data.get("mode", "agent"),
            interaction_mode=data.get("interaction_mode", "agent"),
            metadata=data.get("metadata"),
            agent_config=data.get("agent_config"),
        )
        session.messages = data.get("messages", [])
        return session


class BaseSessionStorage(ABC):
    """
    会话存储基类 - Base Session Storage
    
    定义会话存储的抽象接口，支持多种存储后端
    Defines abstract interface for session storage, supports multiple backends
    
    子类需要实现 / Subclasses need to implement:
    - save(): 保存会话 / Save session
    - load(): 加载会话 / Load session
    - delete(): 删除会话 / Delete session
    - list(): 列出会话 / List sessions
    - search(): 搜索会话 / Search sessions
    """
    
    @abstractmethod
    async def save(self, session: SessionData) -> None:
        """
        保存会话 / Save session
        
        Args:
            session: 会话数据 / Session data
        """
        pass
    
    @abstractmethod
    async def load(self, session_id: str) -> Optional[SessionData]:
        """
        加载会话 / Load session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            会话数据，不存在返回None / Session data, None if not exists
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """
        删除会话 / Delete session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            是否成功 / Whether successful
        """
        pass
    
    @abstractmethod
    async def list(self, limit: int = 50, offset: int = 0) -> List[SessionData]:
        """
        列出会话 / List sessions
        
        Args:
            limit: 最大数量 / Maximum count
            offset: 偏移量 / Offset
        
        Returns:
            会话列表 / Session list
        """
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[SessionData]:
        """
        搜索会话 / Search sessions
        
        Args:
            query: 搜索关键词 / Search keyword
            limit: 最大数量 / Maximum count
        
        Returns:
            匹配的会话列表 / Matched session list
        """
        pass
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加消息到会话 / Add message to session
        
        Args:
            session_id: 会话ID / Session ID
            role: 角色 / Role
            content: 内容 / Content
            metadata: 元数据 / Metadata
        
        Returns:
            消息索引 / Message index
        """
        session = await self.load(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        session.messages.append(message)
        session.updated_at = datetime.utcnow()
        await self.save(session)
        
        return len(session.messages) - 1
    
    async def get_messages(
        self,
        session_id: str,
        start: int = 0,
        end: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取会话消息 / Get session messages
        
        Args:
            session_id: 会话ID / Session ID
            start: 起始索引 / Start index
            end: 结束索引 / End index
        
        Returns:
            消息列表 / Message list
        """
        session = await self.load(session_id)
        if not session:
            return []
        
        return session.messages[start:end]
    
    async def update_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        更新会话元数据 / Update session metadata
        
        Args:
            session_id: 会话ID / Session ID
            metadata: 新元数据 / New metadata
        
        Returns:
            是否成功 / Whether successful
        """
        session = await self.load(session_id)
        if not session:
            return False
        
        session.metadata.update(metadata)
        session.updated_at = datetime.utcnow()
        await self.save(session)
        return True
    
    async def archive(self, session_id: str) -> bool:
        """
        归档会话 / Archive session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            是否成功 / Whether successful
        """
        return await self.update_metadata(session_id, {"archived": True})
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计 / Get storage statistics
        
        Returns:
            统计信息 / Statistics
        """
        sessions = await self.list(limit=1000)
        return {
            "total_sessions": len(sessions),
            "total_messages": sum(len(s.messages) for s in sessions),
            "archived": sum(1 for s in sessions if s.metadata.get("archived")),
        }
