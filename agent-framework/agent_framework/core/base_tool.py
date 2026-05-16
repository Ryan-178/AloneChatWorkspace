from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = Field(default=True)
    default: Optional[Any] = Field(default=None)
    enum: Optional[List[Any]] = Field(default=None)


class ToolDef(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for parameters")


class ToolResult(BaseModel):
    success: bool = Field(default=True)
    data: Any = Field(default=None)
    error: Optional[str] = Field(default=None)
    execution_time_ms: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        pass

    def get_definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )
