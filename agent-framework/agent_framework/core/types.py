from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Tool name for tool messages")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Tool calls")
    tool_call_id: Optional[str] = Field(default=None, description="Tool call ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    success: bool = Field(default=True)
    data: Any = Field(default=None)


class AgentMode(str, Enum):
    MTC = "mtc"
    CODE = "code"


class ModeConfig(BaseModel):
    allowed_tools: List[str] = Field(default_factory=list, description="List of allowed tool names for this mode")
    sandbox_config: Optional[Dict[str, Any]] = Field(default=None, description="Sandbox configuration for code execution")
    system_prompt: Optional[str] = Field(default=None, description="System prompt for this mode")


class FilePermission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class ExecutionEnvironment(str, Enum):
    SANDBOX = "sandbox"
    HOST = "host"
    DOCKER = "docker"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
