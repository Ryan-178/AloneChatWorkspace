"""
è¿åº¦æ¾ç¤ºæ¨¡å / Progress Display Module

æä¾ / Provides:
- æµå¼è¿åº¦æ¾ç¤º / Streaming progress display
- ä»»å¡è¿åº¦è¿½è¸ª / Task progress tracking
- ç¶ææç¤ºå¨ / Status indicators
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

from alonework.configs import config


class TaskStatus(Enum):
    """ä»»å¡ç¶ææä¸?/ Task Status Enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProgressTask:
    """
    è¿åº¦ä»»å¡æ°æ®ç±?/ Progress Task Data Class
    
    Attributes:
        id: ä»»å¡ID / Task ID
        name: ä»»å¡åç§° / Task name
        status: ä»»å¡ç¶æ?/ Task status
        progress: è¿åº¦å?/ Progress value
        total: æ»æ° / Total count
        start_time: å¼å§æ¶é?/ Start time
        end_time: ç»ææ¶é´ / End time
        message: æ¶æ¯ / Message
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
        """è®¡ç®å·²ç¨æ¶é´ / Calculate elapsed time"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time()
        return end - self.start_time
    
    @property
    def is_complete(self) -> bool:
        """æ£æ¥ä»»å¡æ¯å¦å®æ?/ Check if task is complete"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)


class ProgressManager:
    """
    è¿åº¦ç®¡çå?/ Progress Manager
    
    ç®¡çå¤ä¸ªä»»å¡çè¿åº¦ç¶æ?/ Manage progress status of multiple tasks
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        åå§åè¿åº¦ç®¡çå¨ / Initialize progress manager
        
        Args:
            console: Richæ§å¶å°å®ä¾?/ Rich console instance
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
        æ·»å ä»»å¡ / Add task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            name: ä»»å¡åç§° / Task name
            total: æ»æ° / Total count
            
        Returns:
            åå»ºçä»»å?/ Created task
        """
        task = ProgressTask(id=task_id, name=name, total=total)
        self.tasks[task_id] = task
        return task
    
    def start_task(self, task_id: str, message: str = "") -> None:
        """
        å¼å§ä»»å?/ Start task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            message: æ¶æ¯ / Message
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
        æ´æ°ä»»å¡è¿åº¦ / Update task progress
        
        Args:
            task_id: ä»»å¡ID / Task ID
            progress: è¿åº¦å?/ Progress value
            message: æ¶æ¯ / Message
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
        å®æä»»å¡ / Complete task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            success: æ¯å¦æå / Whether success
            message: æ¶æ¯ / Message
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
        è·³è¿ä»»å¡ / Skip task
        
        Args:
            task_id: ä»»å¡ID / Task ID
            reason: åå  / Reason
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.SKIPPED
            task.end_time = time()
            task.message = reason
    
    def get_summary(self) -> dict:
        """
        è·åä»»å¡æè¦ / Get task summary
        
        Returns:
            æè¦å­å¸ / Summary dictionary
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
        æ¸²ææè¦é¢æ¿ / Render summary panel
        
        Returns:
            Riché¢æ¿ / Rich panel
        """
        summary = self.get_summary()
        styles = config.get_ui_styles()
        
        content = Text()
        total_label = self._messages.get("total_label", "æ»è®¡")
        completed_label = self._messages.get("completed_label", "å®æ")
        failed_label = self._messages.get("failed_label", "å¤±è´¥")
        skipped_label = self._messages.get("skipped_label", "è·³è¿")
        title = self._messages.get("task_summary_title", "ä»»å¡æè¦")
        
        content.append(f"{total_label}: {summary['total']}  ", style=styles.get("bold", "bold"))
        content.append(f"{completed_label}: {summary['completed']}  ", style=styles.get("green", "green"))
        if summary['failed'] > 0:
            content.append(f"{failed_label}: {summary['failed']}  ", style=styles.get("red", "red"))
        if summary['skipped'] > 0:
            content.append(f"{skipped_label}: {summary['skipped']}  ", style=styles.get("yellow", "yellow"))
        
        return Panel(content, title=title, border_style=styles.get("blue", "blue"))


class StreamingProgress:
    """
    æµå¼è¿åº¦æ¾ç¤º / Streaming Progress Display
    
    ç¨äºæ¾ç¤ºæµå¼è¾åºçè¿åº?/ Used for displaying streaming output progress
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        åå§åæµå¼è¿åº?/ Initialize streaming progress
        
        Args:
            console: Richæ§å¶å°å®ä¾?/ Rich console instance
        """
        self.console = console or Console()
        streaming_config = config.get("progress.streaming", {})
        spinner_type = streaming_config.get("spinner_type", "dots")
        self._spinner = Spinner(spinner_type)
        self._buffer: list[str] = []
        self._buffer_size = streaming_config.get("buffer_display_size", 50)
    
    def __enter__(self):
        """ä¸ä¸æç®¡çå¨å¥å£ / Context manager entry"""
        return self
    
    def __exit__(self, *args):
        """ä¸ä¸æç®¡çå¨åºå£ / Context manager exit"""
        self.flush()
    
    def update(self, chunk: str, status: Optional[str] = None) -> None:
        """
        æ´æ°è¿åº¦ / Update progress
        
        Args:
            chunk: æ°æ®å?/ Data chunk
            status: ç¶æææ?/ Status text
        """
        if status is None:
            status = config.get("progress.messages.default_status", "çæä¸?)
        
        self._buffer.append(chunk)
        text = Text()
        text.append(f"{status}: ", style=config.get("ui.styles.cyan", "cyan"))
        text.append("".join(self._buffer[-self._buffer_size:]))
        self.console.print(text, end="\r")
    
    def flush(self) -> str:
        """
        å·æ°ç¼å²å?/ Flush buffer
        
        Returns:
            ç¼å²åºåå®?/ Buffer content
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
    åå»ºè¿åº¦æ?/ Create progress bar
    
    Args:
        description: æè¿°ææ¬ / Description text
        total: æ»æ° / Total count
        
    Returns:
        Richè¿åº¦æ?/ Rich progress bar
    """
    if description is None:
        description = config.get("progress.messages.default_description", "å¤çä¸?)
    
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
    å¸¦è¿åº¦çæµå¼å¤ç / Stream with progress
    
    Args:
        iterator: æ°æ®è¿­ä»£å?/ Data iterator
        console: Richæ§å¶å°å®ä¾?/ Rich console instance
        status: ç¶æææ?/ Status text
        
    Returns:
        å®æ´åå®¹ / Complete content
    """
    if console is None:
        console = Console()
    if status is None:
        status = config.get("progress.messages.default_status", "çæä¸?)
    
    result = []
    
    with console.status(f"[bold green]{status}...[/bold green]"):
        for chunk in iterator:
            result.append(chunk)
    
    return "".join(result)
