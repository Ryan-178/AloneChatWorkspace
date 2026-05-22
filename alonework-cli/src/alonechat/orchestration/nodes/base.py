"""
基础节点抽象

定义所有工作流节点的通用接口和行为
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class NodeState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    node_id: str
    success: bool
    state: NodeState
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "success": self.success,
            "state": self.state.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat()
            if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at else None,
        }


@dataclass
class NodeContext:
    variables: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    parent_output: Any = None
    
    def get(self, key: str, default: Any = None) -> Any:
        if key in self.inputs:
            return self.inputs[key]
        if key in self.variables:
            return self.variables[key]
        return default
    
    def set(self, key: str, value: Any) -> None:
        self.outputs[key] = value


class BaseNode(ABC):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.id = node_id or str(uuid4())[:8]
        self.name = name or self.__class__.__name__
        self.description = description
        self.config = config or {}
        self._state: NodeState = NodeState.PENDING
        self._start_time: Optional[datetime] = None
    
    @property
    def state(self) -> NodeState:
        return self._state
    
    @abstractmethod
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        pass
    
    async def run(
        self,
        context: NodeContext,
    ) -> NodeResult:
        self._state = NodeState.RUNNING
        self._start_time = datetime.now()
        
        try:
            result = await self.execute(context)
            self._state = result.state
            return result
            
        except Exception as e:
            self._state = NodeState.FAILED
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error=str(e),
                started_at=self._start_time,
                completed_at=datetime.now(),
            )
    
    def validate(self) -> List[str]:
        errors = []
        if not self.name:
            errors.append("节点名称不能为空")
        return errors
    
    def reset(self) -> None:
        self._state = NodeState.PENDING
        self._start_time = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "config": self.config,
            "state": self._state.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BaseNode":
        return cls(
            node_id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
        )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
