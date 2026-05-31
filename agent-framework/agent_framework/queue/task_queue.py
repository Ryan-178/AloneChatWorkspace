"""
持久化任务队列 / Persistent Task Queue

支持定时任务和cron调度
Supports scheduled tasks and cron scheduling
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """
    任务状态 / Task Status
    """
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


@dataclass
class TaskItem:
    """
    任务项 / Task Item
    """
    id: str
    name: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    result: Optional[Any] = None
    tags: List[str] = field(default_factory=list)
    cron_expression: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error": self.error,
            "tags": self.tags,
            "cron_expression": self.cron_expression,
        }


class TaskQueue:
    """
    持久化任务队列 / Persistent Task Queue

    功能：
    - 持久化任务存储（SQLite）
    - 优先级队列
    - 定时任务支持
    - Cron表达式调度
    - 任务重试机制
    - 并发控制

    Features:
    - Persistent task storage (SQLite)
    - Priority queue
    - Scheduled task support
    - Cron expression scheduling
    - Task retry mechanism
    - Concurrency control
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        max_concurrent: int = 4,
        poll_interval: float = 1.0,
    ):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".alonechat" / "data" / "tasks.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval

        self._handlers: Dict[str, Callable] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._initialized = False

    async def initialize(self) -> None:
        """
        初始化任务队列 / Initialize task queue
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    scheduled_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error TEXT,
                    result TEXT,
                    tags TEXT,
                    cron_expression TEXT
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_scheduled ON tasks(scheduled_at)
            """)

            await db.commit()

        self._initialized = True
        logger.info("Task queue initialized")

    async def enqueue(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: int = 5,
        scheduled_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> str:
        """
        入队任务 / Enqueue task

        Args:
            name: 任务名称（用于匹配处理器）
            payload: 任务载荷
            priority: 优先级（1-10，越高越优先）
            scheduled_at: 计划执行时间
            tags: 标签列表
            max_retries: 最大重试次数

        Returns:
            任务ID
        """
        if not self._initialized:
            await self.initialize()

        task_id = str(uuid.uuid4())[:12]
        task = TaskItem(
            id=task_id,
            name=name,
            payload=payload,
            status=TaskStatus.SCHEDULED if scheduled_at else TaskStatus.QUEUED,
            priority=priority,
            scheduled_at=scheduled_at,
            tags=tags or [],
            max_retries=max_retries,
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tasks (
                    id, name, payload, status, priority,
                    created_at, scheduled_at, tags, max_retries
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.name,
                json.dumps(task.payload),
                task.status.value,
                task.priority,
                task.created_at.isoformat(),
                task.scheduled_at.isoformat() if task.scheduled_at else None,
                json.dumps(task.tags),
                task.max_retries,
            ))
            await db.commit()

        logger.debug(f"Enqueued task: {task_id} ({name})")
        return task_id

    async def schedule_cron(
        self,
        name: str,
        payload: Dict[str, Any],
        cron_expression: str,
        priority: int = 5,
    ) -> str:
        """
        调度cron任务 / Schedule cron task

        Args:
            name: 任务名称
            payload: 任务载荷
            cron_expression: Cron表达式
            priority: 优先级

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())[:12]
        task = TaskItem(
            id=task_id,
            name=name,
            payload=payload,
            status=TaskStatus.SCHEDULED,
            priority=priority,
            cron_expression=cron_expression,
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tasks (
                    id, name, payload, status, priority,
                    created_at, cron_expression
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.name,
                json.dumps(task.payload),
                task.status.value,
                task.priority,
                task.created_at.isoformat(),
                task.cron_expression,
            ))
            await db.commit()

        logger.info(f"Scheduled cron task: {task_id} ({cron_expression})")
        return task_id

    def register_handler(self, name: str, handler: Callable) -> None:
        """
        注册任务处理器 / Register task handler

        Args:
            name: 任务名称
            handler: 处理函数（async callable）
        """
        self._handlers[name] = handler
        logger.debug(f"Registered handler for: {name}")

    async def dequeue(self, limit: int = 10) -> List[TaskItem]:
        """
        出队待执行任务 / Dequeue tasks to execute

        Args:
            limit: 最大数量

        Returns:
            任务列表
        """
        if not self._initialized:
            await self.initialize()

        now = datetime.utcnow().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM tasks
                WHERE status IN ('queued', 'scheduled')
                AND (scheduled_at IS NULL OR scheduled_at <= ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            """, (now, limit)) as cursor:
                rows = await cursor.fetchall()

            tasks = []
            for row in rows:
                task = TaskItem(
                    id=row["id"],
                    name=row["name"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    status=TaskStatus(row["status"]),
                    priority=row["priority"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row["scheduled_at"] else None,
                    retry_count=row["retry_count"],
                    max_retries=row["max_retries"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    cron_expression=row["cron_expression"],
                )
                tasks.append(task)

            return tasks

    async def start(self) -> None:
        """
        启动任务队列处理 / Start task queue processing
        """
        if not self._initialized:
            await self.initialize()

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task queue started")

    async def stop(self) -> None:
        """
        停止任务队列 / Stop task queue
        """
        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        for task_id, task in self._running_tasks.items():
            task.cancel()

        logger.info("Task queue stopped")

    async def _scheduler_loop(self) -> None:
        """
        调度器循环 / Scheduler loop
        """
        while self._running:
            try:
                tasks = await self.dequeue(limit=self.max_concurrent)

                for task in tasks:
                    if len(self._running_tasks) >= self.max_concurrent:
                        break

                    if task.id not in self._running_tasks:
                        asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _execute_task(self, task: TaskItem) -> None:
        """
        执行任务 / Execute task
        """
        handler = self._handlers.get(task.name)
        if not handler:
            logger.warning(f"No handler for task: {task.name}")
            await self._update_task_status(task.id, TaskStatus.FAILED, error="No handler")
            return

        await self._update_task_status(task.id, TaskStatus.RUNNING)

        try:
            result = handler(task.payload)
            if asyncio.iscoroutine(result):
                result = await result

            await self._update_task_status(
                task.id,
                TaskStatus.COMPLETED,
                result=result,
            )

            logger.info(f"Task completed: {task.id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task failed: {task.id} - {error_msg}")

            if task.retry_count < task.max_retries:
                await self._update_task_status(
                    task.id,
                    TaskStatus.QUEUED,
                    retry_count=task.retry_count + 1,
                )
            else:
                await self._update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    error=error_msg,
                )

    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Optional[str] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        """
        更新任务状态 / Update task status
        """
        now = datetime.utcnow().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            updates = ["status = ?"]
            params = [status.value]

            if status == TaskStatus.RUNNING:
                updates.append("started_at = ?")
                params.append(now)
            elif status == TaskStatus.COMPLETED:
                updates.append("completed_at = ?")
                params.append(now)
                if result is not None:
                    updates.append("result = ?")
                    params.append(json.dumps(result))

            if error:
                updates.append("error = ?")
                params.append(error)

            if retry_count is not None:
                updates.append("retry_count = ?")
                params.append(retry_count)

            params.append(task_id)

            await db.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            await db.commit()

    async def get_task(self, task_id: str) -> Optional[TaskItem]:
        """
        获取任务 / Get task
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return TaskItem(
                        id=row["id"],
                        name=row["name"],
                        payload=json.loads(row["payload"]) if row["payload"] else {},
                        status=TaskStatus(row["status"]),
                        priority=row["priority"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
        return None

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
    ) -> List[TaskItem]:
        """
        列出任务 / List tasks
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if status:
                async with db.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with db.execute(
                    "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()

            tasks = []
            for row in rows:
                tasks.append(TaskItem(
                    id=row["id"],
                    name=row["name"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    status=TaskStatus(row["status"]),
                    priority=row["priority"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                ))
            return tasks

    async def cancel(self, task_id: str) -> bool:
        """
        取消任务 / Cancel task
        """
        await self._update_task_status(task_id, TaskStatus.CANCELLED)
        return True

    async def clear_completed(self, before: Optional[datetime] = None) -> int:
        """
        清除已完成任务 / Clear completed tasks
        """
        async with aiosqlite.connect(self.db_path) as db:
            if before:
                await db.execute(
                    "DELETE FROM tasks WHERE status = ? AND completed_at < ?",
                    (TaskStatus.COMPLETED.value, before.isoformat()),
                )
            else:
                await db.execute(
                    "DELETE FROM tasks WHERE status = ?",
                    (TaskStatus.COMPLETED.value,),
                )
            await db.commit()
            return db.changes

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取队列统计 / Get queue statistics
        """
        return {
            "running_tasks": len(self._running_tasks),
            "max_concurrent": self.max_concurrent,
            "registered_handlers": list(self._handlers.keys()),
            "is_running": self._running,
        }


from enum import Enum
