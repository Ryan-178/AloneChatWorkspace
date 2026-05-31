"""
Agent Framework Core Module
Agent框架核心模块

提供核心类型定义和基础抽象类
Provides core type definitions and base abstract classes
"""

from agent_framework.core.types import (
    AgentState,
    MessageRole,
    Message,
    ToolCall,
    ToolResult,
    AgentMode,
    InteractionMode,
    ModeConfig,
    FilePermission,
    ExecutionEnvironment,
    TaskStatus,
    TaskPriority,
)
from agent_framework.core.base_agent import BaseAgent
from agent_framework.core.base_llm import BaseLLM
from agent_framework.core.base_memory import BaseMemory
from agent_framework.core.base_tool import BaseTool, ToolDef, ToolResult as ToolResultDef
from agent_framework.core.mode_manager import ModeManager
from agent_framework.core.dual_mode_manager import DualModeManager, ModeConfig as AgentModeConfig, ModeSwitchReason

# 新架构组件 / New architecture components
from agent_framework.core.store import Store, create_store, StoreManager, get_store_manager
from agent_framework.core.app_state import (
    AppState,
    PermissionMode,
    TaskStatus as AppStateTaskStatus,
    ToolPermissionContext,
    MCPState,
    TaskState,
    SessionState,
    ModelState,
    NotificationState,
    get_default_app_state,
    update_app_state
)
from agent_framework.core.tool import (
    Tool,
    ToolResult as NewToolResult,
    ValidationResult,
    PermissionResult,
    ToolProgress,
    ToolUseContext,
    Tools,
    find_tool_by_name,
    filter_enabled_tools
)
from agent_framework.core.tool_builder import (
    build_tool,
    create_tool,
    ToolRegistry,
    get_tool_registry
)
from agent_framework.core.command import (
    Command,
    CommandType,
    CommandSource,
    CommandResult,
    CommandContext,
    Commands,
    find_command_by_name,
    filter_enabled_commands,
    format_command_help
)
from agent_framework.core.command_registry import (
    CommandRegistry,
    get_command_registry,
    execute_command
)
from agent_framework.core.query_engine import (
    QueryEngine,
    SimpleQueryEngine,
    ModelClient,
    ToolExecutor,
    QueryParams,
    QueryResult,
    StreamEvent,
    Message as QueryMessage,
    MessageRole as QueryMessageRole
)

__all__ = [
    # 原有导出 / Original exports
    "AgentState",
    "MessageRole",
    "Message",
    "ToolCall",
    "ToolResult",
    "AgentMode",
    "InteractionMode",
    "ModeConfig",
    "FilePermission",
    "ExecutionEnvironment",
    "TaskStatus",
    "TaskPriority",
    "BaseAgent",
    "BaseLLM",
    "BaseMemory",
    "BaseTool",
    "ToolDef",
    "ToolResultDef",
    "ModeManager",
    "DualModeManager",
    "AgentModeConfig",
    "ModeSwitchReason",
    
    # 状态管理 / State Management
    "Store",
    "create_store",
    "StoreManager",
    "get_store_manager",
    "AppState",
    "PermissionMode",
    "AppStateTaskStatus",
    "ToolPermissionContext",
    "MCPState",
    "TaskState",
    "SessionState",
    "ModelState",
    "NotificationState",
    "get_default_app_state",
    "update_app_state",
    
    # 工具系统 / Tool System
    "Tool",
    "NewToolResult",
    "ValidationResult",
    "PermissionResult",
    "ToolProgress",
    "ToolUseContext",
    "Tools",
    "find_tool_by_name",
    "filter_enabled_tools",
    "build_tool",
    "create_tool",
    "ToolRegistry",
    "get_tool_registry",
    
    # 命令系统 / Command System
    "Command",
    "CommandType",
    "CommandSource",
    "CommandResult",
    "CommandContext",
    "Commands",
    "find_command_by_name",
    "filter_enabled_commands",
    "format_command_help",
    "CommandRegistry",
    "get_command_registry",
    "execute_command",
    
    # 查询引擎 / Query Engine
    "QueryEngine",
    "SimpleQueryEngine",
    "ModelClient",
    "ToolExecutor",
    "QueryParams",
    "QueryResult",
    "StreamEvent",
    "QueryMessage",
    "QueryMessageRole",
]
