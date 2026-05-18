"""
核心类型定义 - Core Type Definitions
定义Agent框架中使用的所有核心枚举和数据类型
Defines all core enums and data types used in the Agent framework
"""
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime


class AgentState(str, Enum):
    """
    Agent状态枚举 - Agent State Enum
    表示Agent执行过程中的各种状态
    Represents various states during agent execution
    """
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"


class MessageRole(str, Enum):
    """
    消息角色枚举 - Message Role Enum
    定义消息的发送者角色
    Defines the sender role of a message
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """
    消息模型 - Message Model
    表示对话中的一条消息
    Represents a single message in a conversation
    """
    role: MessageRole = Field(..., description="消息角色 / Message role")
    content: str = Field(..., description="消息内容 / Message content")
    name: Optional[str] = Field(default=None, description="工具消息的工具名称 / Tool name for tool messages")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具调用列表 / Tool calls list")
    tool_call_id: Optional[str] = Field(default=None, description="工具调用ID / Tool call ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    """
    工具调用模型 - Tool Call Model
    表示一次工具调用请求
    Represents a tool call request
    """
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """
    工具执行结果 - Tool Execution Result
    表示工具执行后的返回结果
    Represents the result after tool execution
    """
    success: bool = Field(default=True)
    data: Any = Field(default=None)


class AgentMode(str, Enum):
    """
    Agent模式枚举 - Agent Mode Enum
    定义Agent的运行模式
    Defines the running mode of an Agent
    """
    MTC = "mtc"
    CODE = "code"


class ModeConfig(BaseModel):
    """
    模式配置 - Mode Configuration
    配置特定模式的参数和限制
    Configures parameters and restrictions for a specific mode
    """
    allowed_tools: List[str] = Field(default_factory=list, description="该模式允许的工具名称列表 / List of allowed tool names for this mode")
    sandbox_config: Optional[Dict[str, Any]] = Field(default=None, description="代码执行的沙箱配置 / Sandbox configuration for code execution")
    system_prompt: Optional[str] = Field(default=None, description="该模式的系统提示词 / System prompt for this mode")


class FilePermission(str, Enum):
    """
    文件权限枚举 - File Permission Enum
    定义文件操作的权限级别
    Defines permission levels for file operations
    """
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class ExecutionEnvironment(str, Enum):
    """
    执行环境枚举 - Execution Environment Enum
    定义代码执行的环境类型
    Defines the environment type for code execution
    """
    SANDBOX = "sandbox"
    HOST = "host"
    DOCKER = "docker"


class TaskStatus(str, Enum):
    """
    任务状态枚举 - Task Status Enum
    表示任务的生命周期状态
    Represents the lifecycle status of a task
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """
    任务优先级枚举 - Task Priority Enum
    定义任务的执行优先级
    Defines the execution priority of a task
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
