"""
åå°ä»»å¡ç®¡çå?/ Background Task Manager

ç®¡çåå°ä»»å¡çæ§è¡ãç¶æè¿½è¸ªåç»ææ¶é / Manages background task execution, status tracking and result collection
æ°æ®å­å¨å?YAML æä»¶ä¸?/ Data stored in YAML file
"""

import asyncio
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

from alonework.background.task import BackgroundTask, TaskStatus, TaskPriority


class BackgroundManager:
    """
    åå°ä»»å¡ç®¡çå?/ Background Task Manager
    
    ç®¡çææåå°ä»»å¡ççå½å¨æ / Manages lifecycle of all background tasks
    """
    
    DEFAULT_TASKS_FILE = Path.home() / ".alonechat" / "background_tasks.yaml"
    MAX_CONCURRENT_TASKS = 5
    DEFAULT_TIMEOUT = 300
    
    def __init__(
        self,
        tasks_file: Optional[Path] = None,
        max_concurrent: int = MAX_CONCURRENT_TASKS,
    ):
        """
        åå§ååå°ä»»å¡ç®¡çå¨ / Initialize background task manager
        
        Args:
            tasks_file: ä»»å¡å­å¨æä»¶ / Task storage file
            max_concurrent: æå¤§å¹¶åæ° / Max concurrent tasks
        """
        self.tasks_file = tasks_file or self.DEFAULT_TASKS_FILE
        self.max_concurrent = max_concurrent
        
        self._tasks: Dict[str, BackgroundTask] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        self._ensure_tasks_file()
        self._load_tasks()
    
    def _ensure_tasks_file(self) -> None:
        """ç¡®ä¿ä»»å¡æä»¶å­å¨ / Ensure tasks file exists"""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.tasks_file.exists():
            self._save_tasks()
    
    def _load_tasks(self) -> None:
        """ä»?YAML æä»¶å è½½ä»»å¡ / Load tasks from YAML file"""
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                for task_data in data.get("tasks", []):
                    task = BackgroundTask.from_dict(task_data)
                    if not task.is_finished:
                        task.status = TaskStatus.PENDING
                    self._tasks[task.id] = task
        except Exception:
            pass
    
    def _save_tasks(self) -> None:
        """ä¿å­ä»»å¡å?YAML æä»¶ / Save tasks to YAML file"""
        try:
            data = {
                "version": 1,
                "last_updated": datetime.utcnow().isoformat(),
                "tasks": [task.to_dict() for task in self._tasks.values()],
            }
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            pass
    
    def create_task(
        self,
        name: str,
        command: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: int = DEFAULT_TIMEOUT,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BackgroundTask:
        """
        åå»ºåå°ä»»å¡ / Create background task
        
        Args:
            name: ä»»å¡åç§° / Task name
            command: æ§è¡å½ä»¤ / Execute command
            description: ä»»å¡æè¿° / Task description
            priority: ä¼åçº?/ Priority
            timeout: è¶æ¶ç§æ° / Timeout in seconds
            dependencies: ä¾èµä»»å¡IDåè¡¨ / Dependency task IDs
            metadata: åæ°æ?/ Metadata
            
        Returns:
            åå»ºçä»»å?/ Created task
        """
        task = BackgroundTask(
            name=name,
            command=command,
            description=description,
            priority=priority,
            timeout_seconds=timeout,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        with self._lock:
            self._tasks[task.id] = task
            self._save_tasks()
        
        return task
    
    def submit_task(
        self,
        task: BackgroundTask,
        executor: Callable[..., Any],
        *args,
        **kwargs,
    ) -> None:
        """
        æäº¤ä»»å¡æ§è¡ / Submit task for execution
        
        Args:
            task: ä»»å¡å¯¹è±¡ / Task object
            executor: æ§è¡å½æ° / Execute function
            *args: ä½ç½®åæ° / Positional arguments
            **kwargs: å³é®å­åæ?/ Keyword arguments
        """
        def run_task():
            task.start()
            self._save_tasks()
            self._notify_callbacks(task.id, "started")
            
            try:
                result = executor(*args, **kwargs)
                task.complete(str(result) if result else None)
            except Exception as e:
                task.fail(str(e))
            
            self._save_tasks()
            self._notify_callbacks(task.id, "completed")
        
        with self._lock:
            self._tasks[task.id] = task
        
        self._executor.submit(run_task)
    
    async def submit_task_async(
        self,
        task: BackgroundTask,
        executor: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """
        å¼æ­¥æäº¤ä»»å¡æ§è¡ / Submit task for async execution
        
        Args:
            task: ä»»å¡å¯¹è±¡ / Task object
            executor: æ§è¡å½æ° / Execute function
            *args: ä½ç½®åæ° / Positional arguments
            **kwargs: å³é®å­åæ?/ Keyword arguments
            
        Returns:
            æ§è¡ç»æ / Execution result
        """
        task.start()
        self._save_tasks()
        self._notify_callbacks(task.id, "started")
        
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await asyncio.wait_for(
                    executor(*args, **kwargs),
                    timeout=task.timeout_seconds,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, executor, *args),
                    timeout=task.timeout_seconds,
                )
            
            task.complete(str(result) if result else None)
            return result
            
        except asyncio.TimeoutError:
            task.timeout()
            raise
        except Exception as e:
            task.fail(str(e))
            raise
        finally:
            self._save_tasks()
            self._notify_callbacks(task.id, "completed")
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """
        è·åä»»å¡ / Get task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            
        Returns:
            ä»»å¡å¯¹è±¡æ?None / Task object or None
        """
        return self._tasks.get(task_id)
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        include_finished: bool = True,
    ) -> List[BackgroundTask]:
        """
        ååºä»»å¡ / List tasks
        
        Args:
            status: è¿æ»¤ç¶æ?/ Filter status
            include_finished: æ¯å¦åå«å·²å®æä»»å?/ Whether to include finished tasks
            
        Returns:
            ä»»å¡åè¡¨ / Task list
        """
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if not include_finished:
            tasks = [t for t in tasks if not t.is_finished]
        
        return sorted(tasks, key=lambda t: t.priority.value, reverse=True)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        åæ¶ä»»å¡ / Cancel task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            
        Returns:
            æ¯å¦æå / Whether successful
        """
        task = self._tasks.get(task_id)
        if task and not task.is_finished:
            task.cancel()
            self._save_tasks()
            self._notify_callbacks(task_id, "cancelled")
            return True
        return False
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[BackgroundTask]:
        """
        ç­å¾ä»»å¡å®æ / Wait for task completion
        
        Args:
            task_id: ä»»å¡ID / Task ID
            timeout: è¶æ¶ç§æ° / Timeout in seconds
            
        Returns:
            å®æçä»»å¡æ None / Completed task or None
        """
        import time
        start_time = time.time()
        
        while True:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            if task.is_finished:
                return task
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.1)
    
    def register_callback(
        self,
        task_id: str,
        callback: Callable[[BackgroundTask, str], None],
    ) -> None:
        """
        æ³¨åä»»å¡åè° / Register task callback
        
        Args:
            task_id: ä»»å¡ID / Task ID
            callback: åè°å½æ° / Callback function
        """
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)
    
    def _notify_callbacks(self, task_id: str, event: str) -> None:
        """
        éç¥åè° / Notify callbacks
        
        Args:
            task_id: ä»»å¡ID / Task ID
            event: äºä»¶ç±»å / Event type
        """
        task = self._tasks.get(task_id)
        if not task:
            return
        
        for callback in self._callbacks.get(task_id, []):
            try:
                callback(task, event)
            except Exception:
                pass
    
    def clear_finished_tasks(self) -> int:
        """
        æ¸é¤å·²å®æä»»å?/ Clear finished tasks
        
        Returns:
            æ¸é¤æ°é / Cleared count
        """
        with self._lock:
            finished_ids = [
                tid for tid, task in self._tasks.items()
                if task.is_finished
            ]
            for tid in finished_ids:
                del self._tasks[tid]
                self._callbacks.pop(tid, None)
            
            self._save_tasks()
        
        return len(finished_ids)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        è·åç»è®¡ä¿¡æ¯ / Get statistics
        
        Returns:
            ç»è®¡ä¿¡æ¯å­å¸ / Statistics dict
        """
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "running": len([t for t in tasks if t.is_running]),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
        }
    
    def shutdown(self) -> None:
        """å³é­ç®¡çå?/ Shutdown manager"""
        self._executor.shutdown(wait=False)
        self._save_tasks()
