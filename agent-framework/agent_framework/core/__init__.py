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

__all__ = [
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
]
