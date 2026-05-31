"""
会话管理器 - Session Manager

管理会话的生命周期，使用SQLite存储
Manage session lifecycle with SQLite storage
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from alonechat.storage import SQLiteSessionStorage, SessionData
from alonechat.core.types import InteractionMode


console = Console()


class SessionManager:
    """
    会话管理器 - Session Manager
    
    管理会话的创建、加载、保存、删除等操作
    Manage session creation, loading, saving, deletion
    
    特性 / Features:
    - SQLite存储 / SQLite storage
    - 会话搜索 / Session search
    - 会话分叉 / Session fork
    - 会话归档 / Session archive
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        初始化会话管理器 / Initialize session manager
        
        Args:
            db_path: 数据库路径 / Database path
            verbose: 是否显示详细信息 / Whether to show verbose info
        """
        if db_path is None:
            db_path = str(Path.home() / ".alonechat" / "data" / "sessions.db")
        
        self.storage = SQLiteSessionStorage(db_path)
        self.verbose = verbose
        self._current_session: Optional[SessionData] = None
    
    @property
    def current_session(self) -> Optional[SessionData]:
        """获取当前会话 / Get current session"""
        return self._current_session
    
    async def create_session(
        self,
        display_name: Optional[str] = None,
        mode: str = "agent",
        interaction_mode: str = "agent",
        parent_id: Optional[str] = None,
        branch_point: Optional[int] = None,
    ) -> SessionData:
        """
        创建新会话 / Create new session
        
        Args:
            display_name: 显示名称 / Display name
            mode: Agent模式 / Agent mode
            interaction_mode: 交互模式 / Interaction mode
            parent_id: 父会话ID / Parent session ID
            branch_point: 分支点 / Branch point
        
        Returns:
            新会话 / New session
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = SessionData(
            id=session_id,
            display_name=display_name or f"Session {now.strftime('%Y-%m-%d %H:%M')}",
            created_at=now,
            updated_at=now,
            parent_id=parent_id,
            branch_point=branch_point,
            mode=mode,
            interaction_mode=interaction_mode,
        )
        
        await self.storage.save(session)
        self._current_session = session
        
        if self.verbose:
            console.print(f"[green]✓ 创建会话: {session.id}[/green]")
        
        return session
    
    async def load_session(self, session_id: str) -> Optional[SessionData]:
        """
        加载会话 / Load session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            会话数据 / Session data
        """
        session = await self.storage.load(session_id)
        if session:
            self._current_session = session
            if self.verbose:
                console.print(f"[green]✓ 加载会话: {session_id}[/green]")
        return session
    
    async def save_current_session(self) -> bool:
        """
        保存当前会话 / Save current session
        
        Returns:
            是否成功 / Whether successful
        """
        if not self._current_session:
            return False
        
        self._current_session.updated_at = datetime.utcnow()
        await self.storage.save(self._current_session)
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话 / Delete session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            是否成功 / Whether successful
        """
        success = await self.storage.delete(session_id)
        if success and self._current_session and self._current_session.id == session_id:
            self._current_session = None
        return success
    
    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionData]:
        """
        列出会话 / List sessions
        
        Args:
            limit: 最大数量 / Maximum count
            offset: 偏移量 / Offset
        
        Returns:
            会话列表 / Session list
        """
        return await self.storage.list(limit=limit, offset=offset)
    
    async def search_sessions(
        self,
        query: str,
        limit: int = 20,
    ) -> List[SessionData]:
        """
        搜索会话 / Search sessions
        
        Args:
            query: 搜索关键词 / Search keyword
            limit: 最大数量 / Maximum count
        
        Returns:
            匹配的会话列表 / Matched session list
        """
        return await self.storage.search(query, limit=limit)
    
    async def fork_session(
        self,
        session_id: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Optional[SessionData]:
        """
        分叉会话 / Fork session
        
        Args:
            session_id: 要分叉的会话ID / Session ID to fork
            display_name: 新会话名称 / New session name
        
        Returns:
            新会话 / New session
        """
        source_id = session_id or (self._current_session.id if self._current_session else None)
        if not source_id:
            return None
        
        source = await self.storage.load(source_id)
        if not source:
            return None
        
        branch_point = len(source.messages)
        
        forked = await self.create_session(
            display_name=display_name or f"{source.display_name} (fork)",
            mode=source.mode,
            interaction_mode=source.interaction_mode,
            parent_id=source_id,
            branch_point=branch_point,
        )
        
        forked.messages = source.messages.copy()
        await self.storage.save(forked)
        
        if self.verbose:
            console.print(f"[green]✓ 分叉会话: {source_id} → {forked.id}[/green]")
        
        return forked
    
    async def archive_session(self, session_id: str) -> bool:
        """
        归档会话 / Archive session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            是否成功 / Whether successful
        """
        return await self.storage.update_metadata(session_id, {"archived": True})
    
    async def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加消息到当前会话 / Add message to current session
        
        Args:
            role: 角色 / Role
            content: 内容 / Content
            metadata: 元数据 / Metadata
        
        Returns:
            消息索引 / Message index
        """
        if not self._current_session:
            await self.create_session()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self._current_session.messages.append(message)
        self._current_session.updated_at = datetime.utcnow()
        await self.storage.save(self._current_session)
        
        return len(self._current_session.messages) - 1
    
    async def get_messages(
        self,
        start: int = 0,
        end: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取当前会话的消息 / Get messages from current session
        
        Args:
            start: 起始索引 / Start index
            end: 结束索引 / End index
        
        Returns:
            消息列表 / Message list
        """
        if not self._current_session:
            return []
        return self._current_session.messages[start:end]
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计 / Get storage statistics
        
        Returns:
            统计信息 / Statistics
        """
        return await self.storage.get_stats()
    
    def set_interaction_mode(self, mode: InteractionMode | str) -> bool:
        """
        设置当前会话的交互模式 / Set interaction mode for current session
        
        Args:
            mode: 交互模式 / Interaction mode
        
        Returns:
            是否成功 / Whether successful
        """
        if not self._current_session:
            return False
        
        if isinstance(mode, str):
            try:
                mode = InteractionMode(mode.lower())
            except ValueError:
                return False
        
        self._current_session.interaction_mode = mode.value
        return True
