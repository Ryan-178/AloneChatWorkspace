"""
会话存储模块 - Session Storage Module

提供会话存储的抽象接口和具体实现
Provides abstract interface and concrete implementations for session storage

存储类型 / Storage Types:
- SQLite: 使用aiosqlite的异步SQLite存储
- JSON: 文件存储（用于迁移）

使用示例 / Usage Example:
    from alonechat.storage import SQLiteSessionStorage, SessionData
    
    storage = SQLiteSessionStorage("~/.alonechat/data/sessions.db")
    
    # 保存会话
    session = SessionData(id="session-1", display_name="My Session")
    await storage.save(session)
    
    # 加载会话
    session = await storage.load("session-1")
    
    # 列出会话
    sessions = await storage.list(limit=50)
    
    # 搜索会话
    results = await storage.search("关键词")
"""

from alonechat.storage.base_storage import (
    BaseSessionStorage,
    SessionData,
)
from alonechat.storage.sqlite_storage import SQLiteSessionStorage
from alonechat.storage.migration import MigrationTool

__all__ = [
    "BaseSessionStorage",
    "SessionData",
    "SQLiteSessionStorage",
    "MigrationTool",
]
