"""
进度显示模块 / Progress Display Module

提供 / Provides:
- 流式进度显示 / Streaming progress display
- 任务进度追踪 / Task progress tracking
- 状态指示器 / Status indicators
"""

from typing import Optional, Iterator
from dataclasses import dataclass, field
from time import time
from enum import Enum

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner

from alonechat.configs import config


class TaskStatus(Enum):
    """任务状态枚举 / Task Status Enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProgressTask:
    """
    进度任务数据类 / Progress Task Data Class
    
    Attributes:
        id: 任务ID / Task ID
        name: 任务名称 / Task name
        status: 任务状态 / Task status
        progress: 进度值 / Progress value
        total: 总数 / Total count
        start_time: 开始时间 / Start time
        end_time: 结束时间 / End time
        message: 消息 / Message
    """
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    total: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    message: str = ""
    
    @property
    def elapsed(self) -> float:
        """计算已用时间 / Calculate elapsed time"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time()
        return end - self.start_time
    
    @property
    def is_complete(self) -> bool:
        """检查任务是否完成 / Check if task is complete"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)


class ProgressManager:
    """
    进度管理器 / Progress Manager
    
    管理多个任务的进度状态 / Manage progress status of multiple tasks
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        初始化进度管理器 / Initialize progress manager
        
        Args:
            console: Rich控制台实例 / Rich console instance
        """
        self.console = console or Console()
        self.tasks: dict[str, ProgressTask] = {}
        self._current_task: Optional[str] = None
        self._messages = config.get_progress_messages()
    
    def add_task(
        self,
        task_id: str,
        name: str,
        total: Optional[int] = None,
    ) -> ProgressTask:
        """
        添加任务 / Add task
        
        Args:
            task_id: 任务ID / Task ID
            name: 任务名称 / Task name
            total: 总数 / Total count
            
        Returns:
            创建的任务 / Created task
        """
        task = ProgressTask(id=task_id, name=name, total=total)
        self.tasks[task_id] = task
        return task
    
    def start_task(self, task_id: str, message: str = "") -> None:
        """
        开始任务 / Start task
        
        Args:
            task_id: 任务ID / Task ID
            message: 消息 / Message
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.start_time = time()
            task.message = message
            self._current_task = task_id
    
    def update_task(
        self,
        task_id: str,
        progress: Optional[float] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        更新任务进度 / Update task progress
        
        Args:
            task_id: 任务ID / Task ID
            progress: 进度值 / Progress value
            message: 消息 / Message
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if progress is not None:
                task.progress = progress
            if message is not None:
                task.message = message
    
    def complete_task(
        self,
        task_id: str,
        success: bool = True,
        message: str = "",
    ) -> None:
        """
        完成任务 / Complete task
        
        Args:
            task_id: 任务ID / Task ID
            success: 是否成功 / Whether success
            message: 消息 / Message
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.end_time = time()
            task.message = message
            if task.total is not None:
                task.progress = task.total
    
    def skip_task(self, task_id: str, reason: str = "") -> None:
        """
        跳过任务 / Skip task
        
        Args:
            task_id: 任务ID / Task ID
            reason: 原因 / Reason
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.SKIPPED
            task.end_time = time()
            task.message = reason
    
    def get_summary(self) -> dict:
        """
        获取任务摘要 / Get task summary
        
        Returns:
            摘要字典 / Summary dictionary
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in self.tasks.values() if t.status == TaskStatus.SKIPPED)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": total - completed - failed - skipped,
            "success_rate": completed / total if total > 0 else 0,
        }
    
    def render_summary(self) -> Panel:
        """
        渲染摘要面板 / Render summary panel
        
        Returns:
            Rich面板 / Rich panel
        """
        summary = self.get_summary()
        styles = config.get_ui_styles()
        
        content = Text()
        total_label = self._messages.get("total_label", "总计")
        completed_label = self._messages.get("completed_label", "完成")
        failed_label = self._messages.get("failed_label", "失败")
        skipped_label = self._messages.get("skipped_label", "跳过")
        title = self._messages.get("task_summary_title", "任务摘要")
        
        content.append(f"{total_label}: {summary['total']}  ", style=styles.get("bold", "bold"))
        content.append(f"{completed_label}: {summary['completed']}  ", style=styles.get("green", "green"))
        if summary['failed'] > 0:
            content.append(f"{failed_label}: {summary['failed']}  ", style=styles.get("red", "red"))
        if summary['skipped'] > 0:
            content.append(f"{skipped_label}: {summary['skipped']}  ", style=styles.get("yellow", "yellow"))
        
        return Panel(content, title=title, border_style=styles.get("blue", "blue"))


class StreamingProgress:
    """
    流式进度显示 / Streaming Progress Display
    
    用于显示流式输出的进度 / Used for displaying streaming output progress
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        初始化流式进度 / Initialize streaming progress
        
        Args:
            console: Rich控制台实例 / Rich console instance
        """
        self.console = console or Console()
        streaming_config = config.get("progress.streaming", {})
        spinner_type = streaming_config.get("spinner_type", "dots")
        self._spinner = Spinner(spinner_type)
        self._buffer: list[str] = []
        self._buffer_size = streaming_config.get("buffer_display_size", 50)
    
    def __enter__(self):
        """上下文管理器入口 / Context manager entry"""
        return self
    
    def __exit__(self, *args):
        """上下文管理器出口 / Context manager exit"""
        self.flush()
    
    def update(self, chunk: str, status: Optional[str] = None) -> None:
        """
        更新进度 / Update progress
        
        Args:
            chunk: 数据块 / Data chunk
            status: 状态文本 / Status text
        """
        if status is None:
            status = config.get("progress.messages.default_status", "生成中")
        
        self._buffer.append(chunk)
        text = Text()
        text.append(f"{status}: ", style=config.get("ui.styles.cyan", "cyan"))
        text.append("".join(self._buffer[-self._buffer_size:]))
        self.console.print(text, end="\r")
    
    def flush(self) -> str:
        """
        刷新缓冲区 / Flush buffer
        
        Returns:
            缓冲区内容 / Buffer content
        """
        content = "".join(self._buffer)
        self._buffer.clear()
        self.console.print()
        return content


def create_progress_bar(
    description: Optional[str] = None,
    total: Optional[int] = None,
) -> Progress:
    """
    创建进度条 / Create progress bar
    
    Args:
        description: 描述文本 / Description text
        total: 总数 / Total count
        
    Returns:
        Rich进度条 / Rich progress bar
    """
    if description is None:
        description = config.get("progress.messages.default_description", "处理中")
    
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=Console(),
    )


def stream_with_progress(
    iterator: Iterator[str],
    console: Optional[Console] = None,
    status: Optional[str] = None,
) -> str:
    """
    带进度的流式处理 / Stream with progress
    
    Args:
        iterator: 数据迭代器 / Data iterator
        console: Rich控制台实例 / Rich console instance
        status: 状态文本 / Status text
        
    Returns:
        完整内容 / Complete content
    """
    if console is None:
        console = Console()
    if status is None:
        status = config.get("progress.messages.default_status", "生成中")
    
    result = []
    
    with console.status(f"[bold green]{status}...[/bold green]"):
        for chunk in iterator:
            result.append(chunk)
    
    return "".join(result)
