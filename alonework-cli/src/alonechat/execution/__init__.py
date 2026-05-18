"""
任务执行模块

负责：
- 任务调度
- 进度追踪
- 结果收集
- 错误处理
"""

import asyncio
from typing import Any, Callable
from datetime import datetime
from pathlib import Path
import json

from alonechat.planning import Task, TaskStatus, TaskType
from alonechat.models import ModelRouter


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.handlers: dict[TaskType, Callable] = {}
        self.progress_callback: Callable | None = None
        self.log_file = Path(".alonechat/logs/tasks.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def register_handler(self, task_type: TaskType, handler: Callable) -> None:
        """
        注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.handlers[task_type] = handler
    
    def set_progress_callback(self, callback: Callable) -> None:
        """
        设置进度回调
        
        Args:
            callback: 回调函数
        """
        self.progress_callback = callback
    
    async def execute(self, task: Task) -> Any:
        """
        执行任务
        
        Args:
            task: 任务定义
            
        Returns:
            执行结果
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
        执行单个任务
        
        Args:
            task: 任务定义
            
        Returns:
            执行结果
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
        
        raise ValueError(f"不支持的任务类型: {task.task_type}")
    
    async def _execute_with_subtasks(self, task: Task) -> Any:
        """
        执行带子任务的任务
        
        Args:
            task: 任务定义
            
        Returns:
            执行结果
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
        执行子任务
        
        Args:
            task: 子任务
            results: 结果字典
            completed: 已完成集合
        """
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
        """处理代码生成任务"""
        prompt = f"""
请生成以下代码：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请直接输出代码，不要包含markdown标记。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_code_understanding(self, task: Task) -> str:
        """处理代码理解任务"""
        prompt = f"""
请分析以下代码：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请提供详细的分析结果。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_code_refactoring(self, task: Task) -> str:
        """处理代码重构任务"""
        prompt = f"""
请重构以下代码：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请输出重构后的代码。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_file_processing(self, task: Task) -> str:
        """处理文件处理任务"""
        return f"文件处理完成: {task.description}"
    
    async def _handle_testing(self, task: Task) -> str:
        """处理测试任务"""
        prompt = f"""
请生成测试代码：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请输出完整的测试代码。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_documentation(self, task: Task) -> str:
        """处理文档生成任务"""
        prompt = f"""
请生成文档：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请输出完整的文档内容。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    async def _handle_analysis(self, task: Task) -> str:
        """处理分析任务"""
        prompt = f"""
请分析以下内容：

任务：{task.name}
描述：{task.description}
参数：{task.parameters}

请提供详细的分析报告。
"""
        
        return self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
    
    def _log_task(self, task: Task, start_time: datetime) -> None:
        """记录任务日志"""
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
    """任务监控器"""
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.logs: list[dict[str, Any]] = []
    
    def track(self, task: Task) -> None:
        """追踪任务"""
        self.tasks[task.id] = task
    
    def update(self, task_id: str, status: TaskStatus, message: str = "") -> None:
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.logs.append({
                "task_id": task_id,
                "status": status.value,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            })
    
    def get_status(self, task_id: str) -> TaskStatus | None:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None
    
    def get_progress(self) -> dict[str, Any]:
        """获取整体进度"""
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
