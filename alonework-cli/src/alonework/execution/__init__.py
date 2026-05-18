"""
ä»»å¡æ§è¡æ¨¡å

è´è´£ï¼?- ä»»å¡è°åº¦
- è¿åº¦è¿½è¸ª
- ç»ææ¶é
- éè¯¯å¤ç
"""

import asyncio
from typing import Any, Callable
from datetime import datetime
from pathlib import Path
import json

from alonework.planning import Task, TaskStatus, TaskType
from alonework.models import ModelRouter


class TaskExecutor:
    """ä»»å¡æ§è¡å?""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.handlers: dict[TaskType, Callable] = {}
        self.progress_callback: Callable | None = None
        self.log_file = Path(".alonechat/logs/tasks.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def register_handler(self, task_type: TaskType, handler: Callable) -> None:
        """
        æ³¨åä»»å¡å¤çå?        
        Args:
            task_type: ä»»å¡ç±»å
            handler: å¤çå½æ°
        """
        self.handlers[task_type] = handler
    
    def set_progress_callback(self, callback: Callable) -> None:
        """
        è®¾ç½®è¿åº¦åè°
        
        Args:
            callback: åè°å½æ°
        """
        self.progress_callback = callback
    
    async def execute(self, task: Task) -> Any:
        """
        æ§è¡ä»»å¡
        
        Args:
            task: ä»»å¡å®ä¹
            
        Returns:
            æ§è¡ç»æ
        """
        task.status = TaskStatus.RUNNING
        start_time = datetime.now()
        
        if self.progress_callback:
            self.progress_callback(task, "started")
        
        try:
            if task.subtasks:
                result = await self._execute_with_subtasks(task)
            else:
                result = await self._execute_single(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            
            if self.progress_callback:
                self.progress_callback(task, "completed")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            if self.progress_callback:
                self.progress_callback(task, "failed")
            
            raise
        
        finally:
            self._log_task(task, start_time)
        
        return task.result
    
    async def _execute_single(self, task: Task) -> Any:
        """
        æ§è¡åä¸ªä»»å¡
        
        Args:
            task: ä»»å¡å®ä¹
            
        Returns:
            æ§è¡ç»æ
        """
        if task.task_type in self.handlers:
            return await self.handlers[task.task_type](task)
        
        handler_map = {
            TaskType.CODE_GENERATION: self._handle_code_generation,
            TaskType.CODE_UNDERSTANDING: self._handle_code_understanding,
            TaskType.CODE_REFACTORING: self._handle_code_refactoring,
            TaskType.FILE_PROCESSING: self._handle_file_processing,
            TaskType.TESTING: self._handle_testing,
            TaskType.DOCUMENTATION: self._handle_documentation,
            TaskType.ANALYSIS: self._handle_analysis,
        }
        
        handler = handler_map.get(task.task_type)
        if handler:
            return await handler(task)
        
        raise ValueError(f"ä¸æ¯æçä»»å¡ç±»å: {task.task_type}")
    
    async def _execute_with_subtasks(self, task: Task) -> Any:
        """
        æ§è¡å¸¦å­ä»»å¡çä»»å?        
        Args:
            task: ä»»å¡å®ä¹
            
        Returns:
            æ§è¡ç»æ
        """
        results = {}
        completed = set()
        
        while len(completed) < len(task.subtasks):
            ready_tasks = [
                t for t in task.subtasks
                if t.id not in completed and t.is_ready(completed)
            ]
            
            if not ready_tasks:
                break
            
            await asyncio.gather(*[
                self._execute_subtask(t, results, completed)
                for t in ready_tasks
            ])
        
        return results
    
    async def _execute_subtask(
        self,
        task: Task,
        results: dict[str, Any],
        completed: set[str]
    ) -> None:
        """
        æ§è¡å­ä»»å?        
        Args:
            task: å­ä»»å?            results: ç»æå­å¸
            completed: å·²å®æéå?        """
        try:
            result = await self._execute_single(task)
            results[task.id] = result
            task.result = result
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            raise
        finally:
            completed.add(task.id)
    
    async def _handle_code_generation(self, task: Task) -> str:
        """å¤çä»£ç çæä»»å¡"""
        prompt = f"""
è¯·çæä»¥ä¸ä»£ç ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·ç´æ¥è¾åºä»£ç ï¼ä¸è¦åå«markdownæ è®°ã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_code_understanding(self, task: Task) -> str:
        """å¤çä»£ç çè§£ä»»å¡"""
        prompt = f"""
è¯·åæä»¥ä¸ä»£ç ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·æä¾è¯¦ç»çåæç»æã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_code_refactoring(self, task: Task) -> str:
        """å¤çä»£ç éæä»»å¡"""
        prompt = f"""
è¯·éæä»¥ä¸ä»£ç ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·è¾åºéæåçä»£ç ã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_file_processing(self, task: Task) -> str:
        """å¤çæä»¶å¤çä»»å¡"""
        return f"æä»¶å¤çå®æ: {task.description}"
    
    async def _handle_testing(self, task: Task) -> str:
        """å¤çæµè¯ä»»å¡"""
        prompt = f"""
è¯·çææµè¯ä»£ç ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·è¾åºå®æ´çæµè¯ä»£ç ã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_documentation(self, task: Task) -> str:
        """å¤çææ¡£çæä»»å¡"""
        prompt = f"""
è¯·çæææ¡£ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·è¾åºå®æ´çææ¡£åå®¹ã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_analysis(self, task: Task) -> str:
        """å¤çåæä»»å¡"""
        prompt = f"""
è¯·åæä»¥ä¸åå®¹ï¼

ä»»å¡ï¼{task.name}
æè¿°ï¼{task.description}
åæ°ï¼{task.parameters}

è¯·æä¾è¯¦ç»çåææ¥åã?"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    def _log_task(self, task: Task, start_time: datetime) -> None:
        """è®°å½ä»»å¡æ¥å¿"""
        log_entry = {
            "task_id": task.id,
            "name": task.name,
            "type": task.task_type.value,
            "status": task.status.value,
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": (datetime.now() - start_time).total_seconds(),
            "error": task.error,
        }
        
        logs = []
        if self.log_file.exists():
            logs = json.loads(self.log_file.read_text())
        
        logs.append(log_entry)
        self.log_file.write_text(json.dumps(logs, indent=2, ensure_ascii=False))


class TaskMonitor:
    """ä»»å¡çæ§å?""
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.logs: list[dict[str, Any]] = []
    
    def track(self, task: Task) -> None:
        """è¿½è¸ªä»»å¡"""
        self.tasks[task.id] = task
    
    def update(self, task_id: str, status: TaskStatus, message: str = "") -> None:
        """æ´æ°ä»»å¡ç¶æ?""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.logs.append({
                "task_id": task_id,
                "status": status.value,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            })
    
    def get_status(self, task_id: str) -> TaskStatus | None:
        """è·åä»»å¡ç¶æ?""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_progress(self) -> dict[str, Any]:
        """è·åæ´ä½è¿åº¦"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total - completed - failed - running,
            "progress": completed / total if total > 0 else 0,
        }
