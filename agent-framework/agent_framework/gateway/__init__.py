# Gateway模块 - Agent网关系统
from .core import GatewayCore
from .types import MsgContext, Session, SessionState
from .session import SessionManager
from .router import MessageRouter
from .tools import ToolExecutor
from .agent import ReActAgent, AgentState

AgentGateway = GatewayCore
ToolRegistry = ToolExecutor
get_tool_registry = lambda: ToolExecutor()

__all__ = [
    "GatewayCore",
    "AgentGateway",
    "MsgContext",
    "Session",
    "SessionState",
    "SessionManager",
    "MessageRouter",
    "ToolExecutor",
    "ToolRegistry",
    "get_tool_registry",
    "ReActAgent",
    "AgentState",
]
