"""
行动环境模块 / Action Environment Module

提供Agent行动的完整环境，记录交互轨迹（不做训练）
Provides complete environment for Agent actions, records interaction trajectories (no training)
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from datetime import datetime


class ActionType(Enum):
    """
    行动类型 / Action Types
    
    定义Agent可以执行的各种行动类型
    Defines various action types that Agent can execute
    """
    TOOL_CALL = "tool_call"
    CODE_GENERATE = "code_generate"
    CODE_EXECUTE = "code_execute"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    COMMUNICATE = "communicate"
    OBSERVE = "observe"
    REFLECT = "reflect"
    PLAN = "plan"
    DELEGATE = "delegate"


@dataclass
class Action:
    """
    行动定义 / Action Definition
    
    定义一个具体的行动
    Defines a specific action
    """
    type: ActionType
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "type": self.type.value,
            "name": self.name,
            "params": self.params,
            "metadata": self.metadata,
        }


@dataclass
class Observation:
    """
    观察结果 / Observation Result
    
    Agent执行行动后观察到的环境状态
    Environment state observed by Agent after executing action
    """
    world_state: dict[str, Any]
    agent_state: dict[str, Any]
    recent_actions: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    errors: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "world_state": self.world_state,
            "agent_state": self.agent_state,
            "recent_actions": self.recent_actions,
            "messages": self.messages,
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


@dataclass
class Reward:
    """
    奖励信号 / Reward Signal
    
    用于数据收集，非训练
    Used for data collection, not training
    """
    values: dict[str, float] = field(default_factory=dict)
    
    def add(self, name: str, value: float) -> None:
        """
        添加奖励分量 / Add reward component
        
        Args:
            name: 奖励名称 / Reward name
            value: 奖励值 / Reward value
        """
        self.values[name] = value
    
    def total(self) -> float:
        """获取总奖励 / Get total reward"""
        return sum(self.values.values())
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "values": self.values,
            "total": self.total(),
        }


@dataclass
class ActionResult:
    """
    行动结果 / Action Result
    
    执行行动后的结果
    Result after executing action
    """
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class ActionEnvironment:
    """
    行动环境 / Action Environment
    
    提供Agent行动的完整环境，记录交互轨迹（不做训练）
    Provides complete environment for Agent actions, records interaction trajectories (no training)
    
    核心理念：从"静态推理"到"为了行动而思考"
    Core philosophy: From static reasoning to thinking for action
    """
    
    def __init__(
        self,
        config: dict[str, Any] | None = None,
        trajectory_recorder: Any = None,
    ):
        """
        初始化行动环境 / Initialize action environment
        
        Args:
            config: 配置字典 / Configuration dictionary
            trajectory_recorder: 轨迹记录器 / Trajectory recorder
        """
        from .sandbox import Sandbox
        from .state import EnvironmentState
        from .feedback import FeedbackSystem
        
        self.config = config or {}
        self.sandbox = Sandbox(self.config.get("sandbox", {}))
        self.state = EnvironmentState()
        self.feedback_system = FeedbackSystem(self.config.get("feedback", {}))
        self.trajectory_recorder = trajectory_recorder
        
        self._action_handlers: dict[ActionType, Any] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """设置默认行动处理器 / Setup default action handlers"""
        self._action_handlers = {
            ActionType.OBSERVE: self._handle_observe,
            ActionType.REFLECT: self._handle_reflect,
            ActionType.COMMUNICATE: self._handle_communicate,
        }
    
    def register_handler(
        self,
        action_type: ActionType,
        handler: Any,
    ) -> None:
        """
        注册行动处理器 / Register action handler
        
        Args:
            action_type: 行动类型 / Action type
            handler: 处理函数 / Handler function
        """
        self._action_handlers[action_type] = handler
    
    async def step(
        self,
        agent_id: str,
        action: Action,
        agent_thought: str | None = None,
    ) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        """
        执行一步行动 / Execute one action step
        
        这是环境的核心方法，实现了"行动-观察-反馈"循环
        This is the core method, implements "action-observation-feedback" loop
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 要执行的行动 / Action to execute
            agent_thought: Agent的思考过程 / Agent's thought process
            
        Returns:
            tuple: (observation, reward, done, info)
            - observation: 行动后的观察 / Observation after action
            - reward: 奖励信号 / Reward signal
            - done: 是否结束 / Whether done
            - info: 额外信息 / Additional info
        """
        if not self.sandbox.is_valid_action(action):
            return self._invalid_action_response(action)
        
        result = await self._execute_action(agent_id, action)
        
        self.state.update(agent_id, action, result)
        
        observation = self.feedback_system.collect_observation(
            self.state, agent_id
        )
        
        reward = self.feedback_system.calculate_reward(
            action, result, self.state
        )
        
        done = self._check_done(action, result)
        
        if self.trajectory_recorder:
            self.trajectory_recorder.record_step(
                user_input=None,
                agent_thought=agent_thought,
                action_type=action.type.value,
                action_params=action.params,
                observation=observation.to_dict(),
                result=result.output if result.success else result.error,
                success=result.success,
                reward=reward.total(),
                feedback=None,
            )
        
        info = {
            "result": result,
            "action": action.to_dict(),
        }
        
        return observation, reward, done, info
    
    async def _execute_action(
        self,
        agent_id: str,
        action: Action,
    ) -> ActionResult:
        """
        执行具体行动 / Execute specific action
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动对象 / Action object
            
        Returns:
            行动结果 / Action result
        """
        handler = self._action_handlers.get(action.type)
        
        if handler:
            try:
                if callable(handler):
                    result = handler(agent_id, action)
                    if hasattr(result, '__await__'):
                        result = await result
                    return result
            except Exception as e:
                return ActionResult(
                    success=False,
                    error=str(e),
                    metadata={"action": action.to_dict()},
                )
        
        return ActionResult(
            success=False,
            error=f"No handler registered for action type: {action.type.value}",
            metadata={"action": action.to_dict()},
        )
    
    def _handle_observe(
        self,
        agent_id: str,
        action: Action,
    ) -> ActionResult:
        """
        处理观察行动 / Handle observe action
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动对象 / Action object
            
        Returns:
            行动结果 / Action result
        """
        aspects = action.params.get("aspects", ["all"])
        observation_data = {}
        
        if "all" in aspects or "world" in aspects:
            observation_data["world"] = self.state.world.to_dict()
        
        if "all" in aspects or "agent" in aspects:
            agent_state = self.state.agents.get(agent_id)
            observation_data["agent"] = agent_state.to_dict() if agent_state else {}
        
        if "all" in aspects or "history" in aspects:
            observation_data["history"] = self.state.get_recent_actions(agent_id, n=10)
        
        return ActionResult(
            success=True,
            output=observation_data,
            metadata={"aspects": aspects},
        )
    
    def _handle_reflect(
        self,
        agent_id: str,
        action: Action,
    ) -> ActionResult:
        """
        处理反思行动 / Handle reflect action
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动对象 / Action object
            
        Returns:
            行动结果 / Action result
        """
        depth = action.params.get("depth", 1)
        recent_actions = self.state.get_recent_actions(agent_id, n=depth * 5)
        recent_errors = self.state.get_recent_errors(agent_id, n=depth * 3)
        
        reflection = {
            "recent_actions": recent_actions,
            "recent_errors": recent_errors,
            "success_rate": self._calculate_success_rate(recent_actions),
            "suggestions": self._generate_reflection_suggestions(recent_errors),
        }
        
        return ActionResult(
            success=True,
            output=reflection,
            metadata={"depth": depth},
        )
    
    def _handle_communicate(
        self,
        agent_id: str,
        action: Action,
    ) -> ActionResult:
        """
        处理通信行动 / Handle communicate action
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动对象 / Action object
            
        Returns:
            行动结果 / Action result
        """
        target_agent = action.params.get("target")
        message = action.params.get("message")
        message_type = action.params.get("type", "info")
        
        if not target_agent or not message:
            return ActionResult(
                success=False,
                error="Missing target or message in communicate action",
            )
        
        self.state.add_message(
            from_agent=agent_id,
            to_agent=target_agent,
            message=message,
            message_type=message_type,
        )
        
        return ActionResult(
            success=True,
            output={"delivered": True, "target": target_agent},
            metadata={"message_type": message_type},
        )
    
    def _invalid_action_response(
        self,
        action: Action,
    ) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        """
        无效行动响应 / Invalid action response
        
        Args:
            action: 无效行动 / Invalid action
            
        Returns:
            无效行动的响应元组 / Response tuple for invalid action
        """
        observation = Observation(
            world_state={},
            agent_state={},
            recent_actions=[],
            messages=[],
            errors=[f"Invalid action: {action.type.value}"],
        )
        
        reward = Reward()
        reward.add("invalid_action", -1.0)
        
        return observation, reward, True, {"error": "Invalid action"}
    
    def _check_done(
        self,
        action: Action,
        result: ActionResult,
    ) -> bool:
        """
        检查是否结束 / Check if done
        
        Args:
            action: 行动对象 / Action object
            result: 行动结果 / Action result
            
        Returns:
            是否结束 / Whether done
        """
        return action.type in [ActionType.REFLECT] and result.success
    
    def _calculate_success_rate(
        self,
        actions: list[dict[str, Any]],
    ) -> float:
        """
        计算成功率 / Calculate success rate
        
        Args:
            actions: 行动列表 / List of actions
            
        Returns:
            成功率 / Success rate
        """
        if not actions:
            return 0.0
        
        success_count = sum(1 for a in actions if a.get("success", False))
        return success_count / len(actions)
    
    def _generate_reflection_suggestions(
        self,
        errors: list[str],
    ) -> list[str]:
        """
        生成反思建议 / Generate reflection suggestions
        
        Args:
            errors: 错误列表 / List of errors
            
        Returns:
            建议列表 / List of suggestions
        """
        suggestions = []
        
        if errors:
            suggestions.append("Consider reviewing recent errors and adjusting strategy")
        
        if len(errors) > 3:
            suggestions.append("Multiple errors detected, may need to replan")
        
        return suggestions
    
    def reset(self) -> None:
        """
        重置环境 / Reset environment
        
        清除所有状态，准备新的交互
        Clears all states, prepares for new interaction
        """
        self.state.reset()
    
    def get_state(self) -> dict[str, Any]:
        """
        获取环境状态 / Get environment state
        
        Returns:
            环境状态字典 / Environment state dictionary
        """
        return self.state.to_dict()
    
    def set_state(self, state: dict[str, Any]) -> None:
        """
        设置环境状态 / Set environment state
        
        Args:
            state: 环境状态字典 / Environment state dictionary
        """
        self.state.from_dict(state)
    
    def checkpoint(self) -> dict[str, Any]:
        """
        创建检查点 / Create checkpoint
        
        Returns:
            检查点数据 / Checkpoint data
        """
        return self.state.to_dict()
    
    def restore(self, checkpoint: dict[str, Any]) -> None:
        """
        从检查点恢复 / Restore from checkpoint
        
        Args:
            checkpoint: 检查点数据 / Checkpoint data
        """
        self.state.from_dict(checkpoint)
