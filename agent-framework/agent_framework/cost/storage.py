"""
成本存储 / Cost Storage

SQLite存储成本记录
SQLite storage for cost records
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from .types import (
    CostRecord,
    SessionCost,
    DailyCost,
    TokenUsage,
)

logger = logging.getLogger(__name__)


class CostStorage:
    """
    成本存储 / Cost Storage

    使用SQLite持久化成本数据
    Uses SQLite for cost data persistence
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".alonechat" / "data" / "costs.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """
        确保数据库已初始化 / Ensure database is initialized
        """
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cost_records (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_id TEXT,
                    model_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_read_tokens INTEGER DEFAULT 0,
                    cache_write_tokens INTEGER DEFAULT 0,
                    input_cost REAL DEFAULT 0,
                    output_cost REAL DEFAULT 0,
                    cache_cost REAL DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    metadata TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cache_read_tokens INTEGER DEFAULT 0,
                    total_cache_write_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    turn_count INTEGER DEFAULT 0,
                    model_costs TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_costs (
                    date TEXT PRIMARY KEY,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cache_read_tokens INTEGER DEFAULT 0,
                    total_cache_write_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    model_costs TEXT
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_session ON cost_records(session_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_timestamp ON cost_records(timestamp)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)
            """)

            await db.commit()

        self._initialized = True

    async def save_record(self, record: CostRecord) -> None:
        """
        保存成本记录 / Save cost record
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO cost_records (
                    id, session_id, turn_id, model_id, timestamp,
                    input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                    input_cost, output_cost, cache_cost, total_cost, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.session_id,
                record.turn_id,
                record.model_id,
                record.timestamp.isoformat(),
                record.usage.input_tokens,
                record.usage.output_tokens,
                record.usage.cache_read_tokens,
                record.usage.cache_write_tokens,
                record.input_cost,
                record.output_cost,
                record.cache_cost,
                record.total_cost,
                json.dumps(record.metadata),
            ))
            await db.commit()

    async def save_session(self, session: SessionCost) -> None:
        """
        保存会话成本 / Save session cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, start_time, end_time,
                    total_input_tokens, total_output_tokens,
                    total_cache_read_tokens, total_cache_write_tokens,
                    total_cost, turn_count, model_costs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.total_usage.input_tokens,
                session.total_usage.output_tokens,
                session.total_usage.cache_read_tokens,
                session.total_usage.cache_write_tokens,
                session.total_cost,
                session.turn_count,
                json.dumps(session.model_costs),
            ))
            await db.commit()

    async def save_daily(self, daily: DailyCost) -> None:
        """
        保存每日成本 / Save daily cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO daily_costs (
                    date, total_input_tokens, total_output_tokens,
                    total_cache_read_tokens, total_cache_write_tokens,
                    total_cost, session_count, model_costs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                daily.date,
                daily.total_usage.input_tokens,
                daily.total_usage.output_tokens,
                daily.total_usage.cache_read_tokens,
                daily.total_usage.cache_write_tokens,
                daily.total_cost,
                daily.session_count,
                json.dumps(daily.model_costs),
            ))
            await db.commit()

    async def load_record(self, record_id: str) -> Optional[CostRecord]:
        """
        加载成本记录 / Load cost record
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM cost_records WHERE id = ?",
                (record_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_record(row)
        return None

    async def load_session(self, session_id: str) -> Optional[SessionCost]:
        """
        加载会话成本 / Load session cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_session(row)
        return None

    async def load_daily(self, date: str) -> Optional[DailyCost]:
        """
        加载每日成本 / Load daily cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM daily_costs WHERE date = ?",
                (date,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_daily(row)
        return None

    async def list_records(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CostRecord]:
        """
        列出成本记录 / List cost records
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if session_id:
                async with db.execute(
                    """
                    SELECT * FROM cost_records
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                    """,
                    (session_id, limit, offset)
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    """
                    SELECT * FROM cost_records
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                ) as cursor:
                    rows = await cursor.fetchall()
            return [self._row_to_record(row) for row in rows]

    async def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SessionCost]:
        """
        列出会话成本 / List session costs
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
            return [self._row_to_session(row) for row in rows]

    async def list_daily(
        self,
        limit: int = 30,
    ) -> List[DailyCost]:
        """
        列出每日成本 / List daily costs
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM daily_costs
                ORDER BY date DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
            return [self._row_to_daily(row) for row in rows]

    async def delete_record(self, record_id: str) -> bool:
        """
        删除成本记录 / Delete cost record
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM cost_records WHERE id = ?",
                (record_id,)
            )
            await db.commit()
            return True

    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话成本 / Delete session cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM cost_records WHERE session_id = ?",
                (session_id,)
            )
            await db.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            await db.commit()
            return True

    async def get_total_cost(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取总成本 / Get total cost
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            if start_date and end_date:
                async with db.execute(
                    """
                    SELECT
                        SUM(total_cost) as total_cost,
                        SUM(total_input_tokens) as input_tokens,
                        SUM(total_output_tokens) as output_tokens
                    FROM sessions
                    WHERE start_time >= ? AND start_time <= ?
                    """,
                    (start_date, end_date)
                ) as cursor:
                    row = await cursor.fetchone()
            else:
                async with db.execute(
                    """
                    SELECT
                        SUM(total_cost) as total_cost,
                        SUM(total_input_tokens) as input_tokens,
                        SUM(total_output_tokens) as output_tokens
                    FROM sessions
                    """
                ) as cursor:
                    row = await cursor.fetchone()

            if row:
                return {
                    "total_cost": row[0] or 0,
                    "input_tokens": row[1] or 0,
                    "output_tokens": row[2] or 0,
                }
            return {"total_cost": 0, "input_tokens": 0, "output_tokens": 0}

    def _row_to_record(self, row: aiosqlite.Row) -> CostRecord:
        """转换行为记录对象 / Convert row to record object"""
        return CostRecord(
            id=row["id"],
            session_id=row["session_id"],
            turn_id=row["turn_id"],
            model_id=row["model_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            usage=TokenUsage(
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                cache_read_tokens=row["cache_read_tokens"],
                cache_write_tokens=row["cache_write_tokens"],
            ),
            input_cost=row["input_cost"],
            output_cost=row["output_cost"],
            cache_cost=row["cache_cost"],
            total_cost=row["total_cost"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def _row_to_session(self, row: aiosqlite.Row) -> SessionCost:
        """转换行为会话对象 / Convert row to session object"""
        return SessionCost(
            session_id=row["session_id"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            total_usage=TokenUsage(
                input_tokens=row["total_input_tokens"],
                output_tokens=row["total_output_tokens"],
                cache_read_tokens=row["total_cache_read_tokens"],
                cache_write_tokens=row["total_cache_write_tokens"],
            ),
            total_cost=row["total_cost"],
            turn_count=row["turn_count"],
            model_costs=json.loads(row["model_costs"]) if row["model_costs"] else {},
        )

    def _row_to_daily(self, row: aiosqlite.Row) -> DailyCost:
        """转换行为每日对象 / Convert row to daily object"""
        return DailyCost(
            date=row["date"],
            total_usage=TokenUsage(
                input_tokens=row["total_input_tokens"],
                output_tokens=row["total_output_tokens"],
                cache_read_tokens=row["total_cache_read_tokens"],
                cache_write_tokens=row["total_cache_write_tokens"],
            ),
            total_cost=row["total_cost"],
            session_count=row["session_count"],
            model_costs=json.loads(row["model_costs"]) if row["model_costs"] else {},
        )
