"""
会话管理器 / Session Manager

管理会话的生命周期 / Manages session lifecycle

增强功能 / Enhanced Features:
- 会话分叉 / Session fork/branch
- 显示名称设置 / Display name setting
- 代理配置覆盖 / Agent config override
- 自动压缩集成 / Auto compression integration
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from alonework.session.storage import SessionStorage, Session


class SessionManager:
    """
    会话管理器 / Session Manager

    增强功能 / Enhanced Features:
    - fork_session(): 分叉会话 / Fork session
    - set_display_name(): 设置显示名称 / Set display name
    - set_agent_config(): 设置代理配置 / Set agent config
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage = SessionStorage(storage_dir)
        self.current_session: Optional[Session] = None

    def create_session(
        self,
        session_id: Optional[str] = None,
        display_name: Optional[str] = None,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        创建新会话 / Create new session

        Args:
            session_id: 会话ID / Session ID
            display_name: 显示名称 / Display name
            agent_config: 代理配置 / Agent config
        """
        session = Session.create(session_id, display_name)
        session.metadata["cwd"] = str(Path.cwd())
        if agent_config:
            session.agent_config = agent_config
        self.storage.save(session)
        self.current_session = session
        return session

    def fork_session(
        self,
        branch_point: Optional[int] = None,
        display_name: Optional[str] = None,
    ) -> Optional[Session]:
        """
        分叉当前会话 / Fork current session

        保留原会话并创建新分支 / Keep original session and create new branch

        Args:
            branch_point: 分叉点消息索引（None表示当前所有消息）/ Branch point index
            display_name: 新会话显示名称 / New session display name

        Returns:
            新创建的分叉会话 / New forked session
        """
        if self.current_session is None:
            return None

        forked = self.current_session.fork(branch_point)
        if display_name:
            forked.display_name = display_name
        forked.metadata["cwd"] = str(Path.cwd())

        self.storage.save(forked)
        self.storage.save(self.current_session)

        self.current_session = forked
        return forked

    def set_display_name(self, name: str) -> bool:
        """
        设置当前会话显示名称 / Set current session display name

        Args:
            name: 显示名称 / Display name

        Returns:
            是否成功 / Whether successful
        """
        if self.current_session is None:
            return False

        self.current_session.display_name = name
        self.save_current_session()
        return True

    def set_agent_config(self, config: Dict[str, Any]) -> bool:
        """
        设置当前会话代理配置 / Set current session agent config

        Args:
            config: 代理配置 / Agent config

        Returns:
            是否成功 / Whether successful
        """
        if self.current_session is None:
            return False

        self.current_session.agent_config = config
        self.save_current_session()
        return True

    def get_agent_config(self) -> Dict[str, Any]:
        """
        获取当前会话代理配置 / Get current session agent config

        Returns:
            代理配置 / Agent config
        """
        if self.current_session:
            return self.current_session.agent_config.copy()
        return {}

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
