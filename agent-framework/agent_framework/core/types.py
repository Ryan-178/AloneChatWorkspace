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
