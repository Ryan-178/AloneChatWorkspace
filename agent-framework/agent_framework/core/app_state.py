"""
应用状态定义 / Application State Definition

参考 claude-code-claude 的 AppState 模式
Reference: claude-code-claude's AppState pattern

定义全局应用状态结构
Defines global application state structure
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from datetime import datetime


class PermissionMode(Enum):
    """
    权限模式 / Permission Mode
    
    控制工具执行的权限级别
    Controls permission level for tool execution
    """
    DEFAULT = "default"      # 默认模式，需要确认 / Default mode, requires confirmation
    PLAN = "plan"            # 计划模式，只读 / Plan mode, read-only
    BYPASS = "bypass"        # 跳过权限检查 / Bypass permission checks
    YOLO = "yolo"            # 自动批准所有 / Auto-approve all


class TaskStatus(Enum):
    """
    任务状态 / Task Status
    
    任务生命周期状态
    Task lifecycle status
    """
    PENDING = "pending"      # 等待执行 / Awaiting execution
    RUNNING = "running"      # 正在执行 / Currently executing
    COMPLETED = "completed"  # 已完成 / Completed successfully
    FAILED = "failed"        # 执行失败 / Failed to execute
    KILLED = "killed"        # 已终止 / Terminated


@dataclass
class ToolPermissionContext:
    """
    工具权限上下文 / Tool Permission Context
    
    控制工具执行权限的配置
    Configuration controlling tool execution permissions
    """
    mode: PermissionMode = PermissionMode.DEFAULT
    always_allow_rules: Dict[str, List[str]] = field(default_factory=dict)
    always_deny_rules: Dict[str, List[str]] = field(default_factory=dict)
    always_ask_rules: Dict[str, List[str]] = field(default_factory=dict)
    is_bypass_permissions_mode_available: bool = False


@dataclass
class MCPState:
    """
    MCP 状态 / MCP State
    
    Model Context Protocol 相关状态
    Model Context Protocol related state
    """
    clients: List[Any] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)
    commands: List[Any] = field(default_factory=list)
    resources: Dict[str, List[Any]] = field(default_factory=dict)
    plugin_reconnect_key: int = 0


@dataclass
class TaskState:
    """
    任务状态 / Task State
    
    单个任务的状态信息
    State information for a single task
    """
    id: str
    type: str  # local_bash, local_agent, remote_agent, etc.
    status: TaskStatus = TaskStatus.PENDING
    description: str = ""
    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    end_time: Optional[float] = None
    output_file: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SessionState:
    """
    会话状态 / Session State
    
    当前会话的相关状态
    Current session related state
    """
    id: Optional[str] = None
    name: Optional[str] = None
    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    message_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass
class ModelState:
    """
    模型状态 / Model State
    
    当前使用的模型配置
    Current model configuration
    """
    main_model: Optional[str] = None
    small_fast_model: Optional[str] = None
    advisor_model: Optional[str] = None
    effort_value: Optional[str] = None  # low, medium, high


@dataclass
class NotificationState:
    """
    通知状态 / Notification State
    
    通知队列管理
    Notification queue management
    """
    current: Optional[Any] = None
    queue: List[Any] = field(default_factory=list)


@dataclass
class AppState:
    """
    全局应用状态 / Global Application State
    
    应用的完整状态定义，参考 claude-code-claude 的 AppState
    Complete application state definition, referencing claude-code-claude's AppState
    
    使用示例 / Usage Example:
        from agent_framework.core.app_state import AppState
        from agent_framework.core.store import create_store
        
        # 创建应用状态存储 / Create app state store
        store = create_store(AppState())
        
        # 更新状态 / Update state
        store.set_state(lambda s: AppState(
            **{**s.__dict__, 'verbose': True}
        ))
    """
    # 基础设置 / Basic settings
    verbose: bool = False
    debug: bool = False
    
    # 权限上下文 / Permission context
    tool_permission_context: ToolPermissionContext = field(default_factory=ToolPermissionContext)
    
    # MCP 状态 / MCP state
    mcp: MCPState = field(default_factory=MCPState)
    
    # 任务管理 / Task management
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    
    # 会话状态 / Session state
    session: SessionState = field(default_factory=SessionState)
    
    # 模型状态 / Model state
    model: ModelState = field(default_factory=ModelState)
    
    # 通知状态 / Notification state
    notifications: NotificationState = field(default_factory=NotificationState)
    
    # 思考模式 / Thinking mode
    thinking_enabled: bool = True
    
    # 流式输出 / Streaming output
    streaming_enabled: bool = True
    
    # 当前工作目录 / Current working directory
    cwd: Optional[str] = None
    
    # 活跃的覆盖层 / Active overlays
    active_overlays: Set[str] = field(default_factory=set)
    
    # 自定义状态扩展 / Custom state extensions
    extensions: Dict[str, Any] = field(default_factory=dict)


def get_default_app_state() -> AppState:
    """
    获取默认应用状态 / Get default app state
    
    返回一个新的 AppState 实例，使用默认值
    Returns a new AppState instance with default values
    
    Returns:
        默认 AppState 实例 / Default AppState instance
    """
    return AppState()


def update_app_state(
    state: AppState,
    **kwargs
) -> AppState:
    """
    更新应用状态 / Update app state
    
    创建一个新的 AppState 实例，更新指定的字段
    Creates a new AppState instance with updated fields
    
    Args:
        state: 原始状态 / Original state
        **kwargs: 要更新的字段 / Fields to update
        
    Returns:
        新的 AppState 实例 / New AppState instance
        
    使用示例 / Usage Example:
        new_state = update_app_state(old_state, verbose=True, debug=False)
    """
    current_dict = state.__dict__.copy()
    current_dict.update(kwargs)
    return AppState(**current_dict)
