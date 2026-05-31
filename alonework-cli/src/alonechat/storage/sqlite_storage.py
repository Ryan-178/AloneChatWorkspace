"""
SQLite会话存储 - SQLite Session Storage

使用SQLite作为会话存储后端
Use SQLite as session storage backend
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

from alonechat.storage.base_storage import BaseSessionStorage, SessionData


class SQLiteSessionStorage(BaseSessionStorage):
    """
    SQLite会话存储 - SQLite Session Storage
    
    使用aiosqlite实现异步SQLite存储
    Implements async SQLite storage with aiosqlite
    
    特性 / Features:
    - 异步操作 / Async operations
    - 完整CRUD / Full CRUD
    - 搜索功能 / Search functionality
    - 自动迁移 / Auto migration
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str):
        """
        初始化SQLite存储 / Initialize SQLite storage
        
        Args:
            db_path: 数据库文件路径 / Database file path
        """
        if not HAS_AIOSQLITE:
            raise ImportError("aiosqlite is required. Install with: pip install aiosqlite")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """确保数据库已初始化 / Ensure database is initialized"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                );
                
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    parent_id TEXT,
                    branch_point INTEGER,
                    mode TEXT DEFAULT 'agent',
                    interaction_mode TEXT DEFAULT 'agent',
                    metadata TEXT,
                    agent_config TEXT
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_id);
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            """)
            
            cursor = await db.execute("SELECT version FROM schema_version")
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (self.SCHEMA_VERSION,)
                )
            
            await db.commit()
        
        self._initialized = True
    
    async def save(self, session: SessionData) -> None:
        """
        保存会话 / Save session
        
        Args:
            session: 会话数据 / Session data
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO sessions (
                    id, display_name, created_at, updated_at,
                    parent_id, branch_point, mode, interaction_mode,
                    metadata, agent_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.display_name,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.parent_id,
                session.branch_point,
                session.mode,
                session.interaction_mode,
                json.dumps(session.metadata),
                json.dumps(session.agent_config),
            ))
            
            await db.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session.id,)
            )
            
            for msg in session.messages:
                await db.execute("""
                    INSERT INTO messages (session_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session.id,
                    msg.get("role", "user"),
                    msg.get("content", ""),
                    msg.get("timestamp", datetime.utcnow().isoformat()),
                    json.dumps(msg.get("metadata", {})),
                ))
            
            await db.commit()
    
    async def load(self, session_id: str) -> Optional[SessionData]:
        """
        加载会话 / Load session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            会话数据 / Session data
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            session = SessionData(
                id=row[0],
                display_name=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
                parent_id=row[4],
                branch_point=row[5],
                mode=row[6] or "agent",
                interaction_mode=row[7] or "agent",
                metadata=json.loads(row[8]) if row[8] else {},
                agent_config=json.loads(row[9]) if row[9] else {},
            )
            
            cursor = await db.execute(
                "SELECT role, content, timestamp, metadata FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,)
            )
            async for msg_row in cursor:
                session.messages.append({
                    "role": msg_row[0],
                    "content": msg_row[1],
                    "timestamp": msg_row[2],
                    "metadata": json.loads(msg_row[3]) if msg_row[3] else {},
                })
            
            return session
    
    async def delete(self, session_id: str) -> bool:
        """
        删除会话 / Delete session
        
        Args:
            session_id: 会话ID / Session ID
        
        Returns:
            是否成功 / Whether successful
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def list(self, limit: int = 50, offset: int = 0) -> List[SessionData]:
        """
        列出会话 / List sessions
        
        Args:
            limit: 最大数量 / Maximum count
            offset: 偏移量 / Offset
        
        Returns:
            会话列表 / Session list
        """
        await self._ensure_initialized()
        
        sessions = []
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, display_name, created_at, updated_at,
                       parent_id, branch_point, mode, interaction_mode,
                       metadata, agent_config
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            async for row in cursor:
                session = SessionData(
                    id=row[0],
                    display_name=row[1],
                    created_at=datetime.fromisoformat(row[2]),
                    updated_at=datetime.fromisoformat(row[3]),
                    parent_id=row[4],
                    branch_point=row[5],
                    mode=row[6] or "agent",
                    interaction_mode=row[7] or "agent",
                    metadata=json.loads(row[8]) if row[8] else {},
                    agent_config=json.loads(row[9]) if row[9] else {},
                )
                sessions.append(session)
        
        return sessions
    
    async def search(self, query: str, limit: int = 20) -> List[SessionData]:
        """
        搜索会话 / Search sessions
        
        Args:
            query: 搜索关键词 / Search keyword
            limit: 最大数量 / Maximum count
        
        Returns:
            匹配的会话列表 / Matched session list
        """
        await self._ensure_initialized()
        
        sessions = []
        search_pattern = f"%{query}%"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT s.id, s.display_name, s.created_at, s.updated_at,
                       s.parent_id, s.branch_point, s.mode, s.interaction_mode,
                       s.metadata, s.agent_config
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.display_name LIKE ?
                   OR m.content LIKE ?
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (search_pattern, search_pattern, limit))
            
            async for row in cursor:
                session = SessionData(
                    id=row[0],
                    display_name=row[1],
                    created_at=datetime.fromisoformat(row[2]),
                    updated_at=datetime.fromisoformat(row[3]),
                    parent_id=row[4],
                    branch_point=row[5],
                    mode=row[6] or "agent",
                    interaction_mode=row[7] or "agent",
                    metadata=json.loads(row[8]) if row[8] else {},
                    agent_config=json.loads(row[9]) if row[9] else {},
                )
                sessions.append(session)
        
        return sessions
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计 / Get storage statistics
        
        Returns:
            统计信息 / Statistics
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM messages")
            total_messages = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sessions WHERE metadata LIKE ?",
                ('%"archived": true%',)
            )
            archived = (await cursor.fetchone())[0]
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "archived": archived,
                "db_path": str(self.db_path),
            }
