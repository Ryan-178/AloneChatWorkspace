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

    注意 / Note:
    - 产品与交互层使用 Work / Code 命名
    - Product and interaction layers use Work / Code naming
    - 框架内部保留 MTC 以保持兼容
    - Internally, MTC is retained for compatibility
    """
    MTC = "MTC"
    CODE = "CODE"


class InteractionMode(str, Enum):
    """
    交互模式枚举 - Interaction Mode Enum
    定义用户交互的模式，控制工具执行的审批流程
    Defines user interaction modes, controlling tool execution approval flow
    
    PLAN: 只读探索模式，无工具执行 / Read-only exploration mode, no tool execution
    AGENT: 默认交互模式，工具执行需审批 / Default interaction mode, tool execution requires approval
    YOLO: 自动批准模式，信任工作区 / Auto-approve mode, trust workspace
    """
    PLAN = "plan"
    AGENT = "agent"
    YOLO = "yolo"


class ModeConfig(BaseModel):
    """
    模式配置 - Mode Configuration
    配置特定模式的参数和限制
    Configures parameters and restrictions for a specific mode
    """
    mode: InteractionMode = Field(default=InteractionMode.AGENT, description="交互模式 / Interaction mode")
    auto_approve_tools: bool = Field(default=False, description="是否自动批准工具执行 / Whether to auto-approve tool execution")
    require_confirmation: List[str] = Field(default_factory=lambda: ["shell", "file_write", "file_delete"], description="需要确认的工具列表 / Tools requiring confirmation")
    max_auto_approve_cost: float = Field(default=1.0, description="最大自动批准成本 / Maximum cost for auto-approval")
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


class AgentRole(str, Enum):
    """
    Agent角色枚举 - Agent Role Enum
    定义多Agent协作中的角色类型（Mavis架构）
    Defines role types in multi-agent collaboration (Mavis architecture)
    
    LEADER: 统筹、规划、调度、聚合 / Orchestrates, plans, dispatches, aggregates
    WORKER: 执行具体任务 / Executes specific tasks
    VERIFIER: 验收、质量门禁 / Validates, quality gate
    """
    LEADER = "leader"
    WORKER = "worker"
    VERIFIER = "verifier"


class RoleConfig(BaseModel):
    """
    角色配置 - Role Configuration
    配置特定角色的参数和能力
    Configures parameters and capabilities for a specific role
    """
    role: AgentRole = Field(..., description="角色类型 / Role type")
    capabilities: List[str] = Field(default_factory=list, description="角色能力列表 / Role capabilities list")
    tools: List[str] = Field(default_factory=list, description="可用工具列表 / Available tools list")
    max_retries: int = Field(default=3, description="最大重试次数 / Maximum retry count")
    timeout: int = Field(default=300, description="超时时间(秒) / Timeout in seconds")
    model_id: Optional[str] = Field(default=None, description="使用的模型ID / Model ID to use")
    system_prompt_template: Optional[str] = Field(default=None, description="系统提示词模板 / System prompt template")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="任务优先级 / Task priority")


class WorkerState(str, Enum):
    """
    Worker状态枚举 - Worker State Enum
    定义Worker在Team Engine中的生命周期状态
    Defines Worker lifecycle states in Team Engine
    """
    PENDING = "pending"
    PRODUCING = "producing"
    VERIFYING = "verifying"
    DONE = "done"
    RETRY = "retry"
    FAILED = "failed"


class TeamPhase(str, Enum):
    """
    Team阶段枚举 - Team Phase Enum
    定义Team执行的主要阶段
    Defines main phases of Team execution
    """
    PLANNING = "planning"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    AGGREGATING = "aggregating"
    DONE = "done"
    FAILED = "failed"


class SubTask(BaseModel):
    """
    子任务模型 - SubTask Model
    表示由Leader分配给Worker的子任务
    Represents a subtask assigned by Leader to Worker
    """
    id: str = Field(..., description="子任务ID / Subtask ID")
    description: str = Field(..., description="任务描述 / Task description")
    assigned_to: Optional[str] = Field(default=None, description="分配给的Worker ID / Assigned Worker ID")
    status: WorkerState = Field(default=WorkerState.PENDING, description="任务状态 / Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="优先级 / Priority")
    dependencies: List[str] = Field(default_factory=list, description="依赖的子任务ID / Dependent subtask IDs")
    result: Optional[Any] = Field(default=None, description="执行结果 / Execution result")
    error: Optional[str] = Field(default=None, description="错误信息 / Error message")
    retry_count: int = Field(default=0, description="重试次数 / Retry count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据 / Metadata")


class VerificationResult(BaseModel):
    """
    验证结果模型 - Verification Result Model
    表示Verifier对Worker输出的验证结果
    Represents Verifier's validation result of Worker output
    """
    subtask_id: str = Field(..., description="子任务ID / Subtask ID")
    passed: bool = Field(..., description="是否通过 / Whether passed")
    score: float = Field(default=0.0, description="质量分数(0-1) / Quality score (0-1)")
    feedback: str = Field(default="", description="反馈信息 / Feedback message")
    issues: List[str] = Field(default_factory=list, description="问题列表 / Issues list")
    suggestions: List[str] = Field(default_factory=list, description="改进建议 / Improvement suggestions")
    verifier_id: str = Field(..., description="Verifier ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TeamState(BaseModel):
    """
    Team状态模型 - Team State Model
    表示整个Team的当前状态
    Represents the current state of the entire Team
    """
    team_id: str = Field(..., description="Team ID")
    phase: TeamPhase = Field(default=TeamPhase.PLANNING, description="当前阶段 / Current phase")
    leader_state: WorkerState = Field(default=WorkerState.PENDING, description="Leader状态 / Leader state")
    workers: Dict[str, WorkerState] = Field(default_factory=dict, description="Worker状态映射 / Worker state mapping")
    verifiers: Dict[str, WorkerState] = Field(default_factory=dict, description="Verifier状态映射 / Verifier state mapping")
    subtasks: Dict[str, SubTask] = Field(default_factory=dict, description="子任务映射 / Subtask mapping")
    results: Dict[str, Any] = Field(default_factory=dict, description="结果映射 / Results mapping")
    errors: List[str] = Field(default_factory=list, description="错误列表 / Errors list")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="开始时间 / Start time")
    end_time: Optional[datetime] = Field(default=None, description="结束时间 / End time")
