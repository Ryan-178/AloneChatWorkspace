"""
环境层 / Environment Layer

提供Agent行动的完整环境，包括工具、资源、反馈机制
Provides complete environment for Agent actions, including tools, resources, feedback mechanisms

核心理念：从"静态推理"到"为了行动而思考"
Core philosophy: From static reasoning to thinking for action
"""

from .action_env import ActionEnvironment, Action, ActionType, Observation, Reward, ActionResult
from .feedback import FeedbackSystem
from .state import EnvironmentState, WorldState, AgentState
from .sandbox import Sandbox

__all__ = [
    "ActionEnvironment",
    "Action",
    "ActionType",
    "Observation",
    "Reward",
    "ActionResult",
    "FeedbackSystem",
    "EnvironmentState",
    "WorldState",
    "AgentState",
    "Sandbox",
]
