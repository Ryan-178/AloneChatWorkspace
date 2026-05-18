"""
åå°ä»»å¡æ¨¡å / Background Task Model

å®ä¹åå°ä»»å¡çæ°æ®ç»æ?/ Defines data structure for background tasks
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from uuid import uuid4
from dataclasses import dataclass, field


class TaskStatus(Enum):
    """ä»»å¡ç¶æ?/ Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """ä»»å¡ä¼åçº?/ Task priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BackgroundTask:
    """
    åå°ä»»å¡ / Background Task
    
    è¡¨ç¤ºä¸ä¸ªå¨åå°æ§è¡çä»»å?/ Represents a task executing in background
    """
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    command: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0
    
    def start(self) -> None:
        """æ è®°ä»»å¡å¼å§?/ Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Optional[str] = None) -> None:
        """
        æ è®°ä»»å¡å®æ / Mark task as completed
        
        Args:
            result: ä»»å¡ç»æ / Task result
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.progress = 1.0
    
    def fail(self, error: str) -> None:
        """
        æ è®°ä»»å¡å¤±è´¥ / Mark task as failed
        
        Args:
            error: éè¯¯ä¿¡æ¯ / Error message
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
    
    def cancel(self) -> None:
        """æ è®°ä»»å¡åæ¶ / Mark task as cancelled"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def timeout(self) -> None:
        """æ è®°ä»»å¡è¶æ¶ / Mark task as timed out"""
        self.status = TaskStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error = "Task timed out"
    
    def update_progress(self, progress: float) -> None:
        """
        æ´æ°è¿åº¦ / Update progress
        
        Args:
            progress: è¿åº¦å?(0.0 - 1.0) / Progress value (0.0 - 1.0)
        """
        self.progress = max(0.0, min(1.0, progress))
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """
        è·åæ§è¡æ¶é¿ï¼ç§ï¼?/ Get execution duration in seconds
        
        Returns:
            æ¶é¿æ?None / Duration or None
        """
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_finished(self) -> bool:
        """ä»»å¡æ¯å¦å·²å®æ?/ Whether task is finished"""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }
    
    @property
    def is_running(self) -> bool:
        """ä»»å¡æ¯å¦è¿è¡ä¸?/ Whether task is running"""
        return self.status == TaskStatus.RUNNING
    
    def to_dict(self) -> Dict[str, Any]:
        """
        è½¬æ¢ä¸ºå­å?/ Convert to dict
        
        Returns:
            å­å¸è¡¨ç¤º / Dict representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "duration_seconds": self.duration_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackgroundTask":
        """
        ä»å­å¸åå»?/ Create from dict
        
        Args:
            data: å­å¸æ°æ® / Dict data
            
        Returns:
            BackgroundTask å®ä¾ / BackgroundTask instance
        """
        task = cls(
            id=data.get("id", str(uuid4())[:8]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            command=data.get("command", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", 2)),
            timeout_seconds=data.get("timeout_seconds", 300),
            metadata=data.get("metadata", {}),
            dependencies=data.get("dependencies", []),
            result=data.get("result"),
            error=data.get("error"),
            progress=data.get("progress", 0.0),
        )
        
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            task.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return task
