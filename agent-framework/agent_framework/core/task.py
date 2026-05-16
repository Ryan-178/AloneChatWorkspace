from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .types import TaskPriority, TaskStatus


class TaskDependency(BaseModel):
    task_id: str = Field(..., description="依赖的任务ID")
    type: str = Field(..., description="依赖类型，如 'requires', 'blocks' 等")


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="任务唯一标识符 (UUID)")
    description: str = Field(..., description="任务描述")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    dependencies: List[TaskDependency] = Field(default_factory=list, description="任务依赖列表")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="任务优先级")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任务元数据")


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="产物唯一标识符 (UUID)")
    name: str = Field(..., description="产物名称")
    type: str = Field(..., description="文件类型，如 'document', 'data', 'report' 等")
    path: str = Field(..., description="文件路径")
    size: int = Field(..., description="文件大小 (字节)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="产物元数据")


class Reference(BaseModel):
    source: str = Field(..., description="来源")
    url: Optional[str] = Field(default=None, description="URL链接")
    title: str = Field(..., description="标题")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性分数 (0-1)")
