"""
待办事项模型 / Todo Item Model

定义待办事项的数据结构 / Defines data structure for todo items
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from dataclasses import dataclass, field


class TodoStatus(Enum):
    """待办状态 / Todo status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoPriority(Enum):
    """待办优先级 / Todo priority"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TodoItem:
    """
    待办事项 / Todo Item
    
    表示一个待办任务 / Represents a todo task
    """
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    subtask_ids: List[str] = field(default_factory=list)
    
    def mark_in_progress(self) -> None:
        """标记为进行中 / Mark as in progress"""
        self.status = TodoStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """标记为已完成 / Mark as completed"""
        self.status = TodoStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self) -> None:
        """标记为已取消 / Mark as cancelled"""
        self.status = TodoStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def update_content(self, content: str) -> None:
        """
        更新内容 / Update content
        
        Args:
            content: 新内容 / New content
        """
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def set_priority(self, priority: TodoPriority) -> None:
        """
        设置优先级 / Set priority
        
        Args:
            priority: 优先级 / Priority
        """
        self.priority = priority
        self.updated_at = datetime.utcnow()
    
    def set_due_date(self, due_date: Optional[datetime]) -> None:
        """
        设置截止日期 / Set due date
        
        Args:
            due_date: 截止日期 / Due date
        """
        self.due_date = due_date
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """
        添加标签 / Add tag
        
        Args:
            tag: 标签 / Tag
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """
        移除标签 / Remove tag
        
        Args:
            tag: 标签 / Tag
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def add_subtask(self, subtask_id: str) -> None:
        """
        添加子任务 / Add subtask
        
        Args:
            subtask_id: 子任务ID / Subtask ID
        """
        if subtask_id not in self.subtask_ids:
            self.subtask_ids.append(subtask_id)
            self.updated_at = datetime.utcnow()
    
    def remove_subtask(self, subtask_id: str) -> None:
        """
        移除子任务 / Remove subtask
        
        Args:
            subtask_id: 子任务ID / Subtask ID
        """
        if subtask_id in self.subtask_ids:
            self.subtask_ids.remove(subtask_id)
            self.updated_at = datetime.utcnow()
    
    @property
    def is_overdue(self) -> bool:
        """是否过期 / Whether overdue"""
        if self.due_date and self.status not in {TodoStatus.COMPLETED, TodoStatus.CANCELLED}:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def is_finished(self) -> bool:
        """是否已完成 / Whether finished"""
        return self.status in {TodoStatus.COMPLETED, TodoStatus.CANCELLED}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dict"""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "subtask_ids": self.subtask_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        """从字典创建 / Create from dict"""
        item = cls(
            id=data.get("id", str(uuid4())[:8]),
            content=data.get("content", ""),
            status=TodoStatus(data.get("status", "pending")),
            priority=TodoPriority(data.get("priority", 2)),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            parent_id=data.get("parent_id"),
            subtask_ids=data.get("subtask_ids", []),
        )
        
        if data.get("created_at"):
            item.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            item.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("completed_at"):
            item.completed_at = datetime.fromisoformat(data["completed_at"])
        if data.get("due_date"):
            item.due_date = datetime.fromisoformat(data["due_date"])
        
        return item
