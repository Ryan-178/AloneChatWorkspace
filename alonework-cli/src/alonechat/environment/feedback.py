"""
反馈系统模块 / Feedback System Module

实现行动-反馈闭环的关键组件
Key component for implementing action-feedback loop
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from .action_env import Action, ActionResult, Observation


@dataclass
class FeedbackConfig:
    """
    反馈配置 / Feedback Configuration
    
    定义奖励计算的权重
    Defines weights for reward calculation
    """
    task_completion_weight: float = 1.0
    efficiency_weight: float = 0.3
    code_quality_weight: float = 0.5
    collaboration_weight: float = 0.2
    
    def to_dict(self) -> dict[str, float]:
        """转换为字典 / Convert to dictionary"""
        return {
            "task_completion_weight": self.task_completion_weight,
            "efficiency_weight": self.efficiency_weight,
            "code_quality_weight": self.code_quality_weight,
            "collaboration_weight": self.collaboration_weight,
        }


class FeedbackSystem:
    """
    反馈系统 / Feedback System
    
    实现行动-反馈闭环的关键组件
    Key component for implementing action-feedback loop
    
    用于数据收集，非训练
    Used for data collection, not training
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化反馈系统 / Initialize feedback system
        
        Args:
            config: 配置字典 / Configuration dictionary
        """
        self.config = config or {}
        
        reward_weights = self.config.get("reward_weights", {})
        self.weights = FeedbackConfig(
            task_completion_weight=reward_weights.get("task_completion", 1.0),
            efficiency_weight=reward_weights.get("efficiency", 0.3),
            code_quality_weight=reward_weights.get("code_quality", 0.5),
            collaboration_weight=reward_weights.get("collaboration", 0.2),
        )
    
    def collect_observation(
        self,
        state: "EnvironmentState",
        agent_id: str,
    ) -> Observation:
        """
        收集观察 / Collect observation
        
        Args:
            state: 环境状态 / Environment state
            agent_id: Agent标识 / Agent identifier
            
        Returns:
            观察结果 / Observation result
        """
        world_state = state.world.to_dict()
        
        agent_state = {}
        if agent_id in state.agents:
            agent_state = state.agents[agent_id].to_dict()
        
        recent_actions = state.get_recent_actions(agent_id, n=10)
        
        messages = state.get_pending_messages(agent_id)
        
        errors = state.get_recent_errors(agent_id, n=5)
        
        return Observation(
            world_state=world_state,
            agent_state=agent_state,
            recent_actions=recent_actions,
            messages=messages,
            errors=errors,
        )
    
    def calculate_reward(
        self,
        action: Action,
        result: ActionResult,
        state: "EnvironmentState",
    ) -> "Reward":
        """
        计算奖励信号 / Calculate reward signal
        
        用于数据收集，非训练
        Used for data collection, not training
        
        Args:
            action: 行动对象 / Action object
            result: 行动结果 / Action result
            state: 环境状态 / Environment state
            
        Returns:
            奖励信号 / Reward signal
        """
        from .action_env import Reward
        
        reward = Reward()
        
        if result.success:
            reward.add("task_completion", self.weights.task_completion_weight)
        else:
            reward.add("task_failure", -0.5 * self.weights.task_completion_weight)
        
        efficiency_score = self._calculate_efficiency(action, result)
        reward.add("efficiency", efficiency_score * self.weights.efficiency_weight)
        
        if action.type.value in ["code_generate", "code_execute"]:
            quality_score = self._calculate_code_quality(result)
            reward.add("code_quality", quality_score * self.weights.code_quality_weight)
        
        collaboration_score = self._calculate_collaboration(action, state)
        reward.add("collaboration", collaboration_score * self.weights.collaboration_weight)
        
        return reward
    
    def _calculate_efficiency(
        self,
        action: Action,
        result: ActionResult,
    ) -> float:
        """
        计算效率分数 / Calculate efficiency score
        
        Args:
            action: 行动对象 / Action object
            result: 行动结果 / Action result
            
        Returns:
            效率分数 / Efficiency score
        """
        if not result.success:
            return 0.0
        
        base_score = 0.5
        
        if result.metadata.get("cached", False):
            base_score += 0.3
        
        if result.metadata.get("optimized", False):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _calculate_code_quality(
        self,
        result: ActionResult,
    ) -> float:
        """
        计算代码质量分数 / Calculate code quality score
        
        Args:
            result: 行动结果 / Action result
            
        Returns:
            代码质量分数 / Code quality score
        """
        if not result.success:
            return 0.0
        
        quality_score = 0.5
        
        if result.metadata.get("syntax_valid", True):
            quality_score += 0.2
        
        if result.metadata.get("tests_passed", False):
            quality_score += 0.2
        
        if result.metadata.get("lint_passed", False):
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _calculate_collaboration(
        self,
        action: Action,
        state: "EnvironmentState",
    ) -> float:
        """
        计算协作分数 / Calculate collaboration score
        
        Args:
            action: 行动对象 / Action object
            state: 环境状态 / Environment state
            
        Returns:
            协作分数 / Collaboration score
        """
        from .action_env import ActionType
        
        if action.type == ActionType.COMMUNICATE:
            return 0.8
        
        if action.type == ActionType.DELEGATE:
            return 0.6
        
        return 0.3
    
    def analyze_error(
        self,
        error: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        分析错误 / Analyze error
        
        Args:
            error: 错误信息 / Error message
            context: 上下文 / Context
            
        Returns:
            错误分析结果 / Error analysis result
        """
        analysis = {
            "error": error,
            "type": self._classify_error(error),
            "severity": self._assess_severity(error),
            "suggestions": self._generate_suggestions(error),
            "timestamp": datetime.now().isoformat(),
        }
        
        if context:
            analysis["context"] = context
        
        return analysis
    
    def _classify_error(self, error: str) -> str:
        """
        分类错误 / Classify error
        
        Args:
            error: 错误信息 / Error message
            
        Returns:
            错误类型 / Error type
        """
        error_lower = error.lower()
        
        if "syntax" in error_lower:
            return "syntax_error"
        elif "type" in error_lower:
            return "type_error"
        elif "value" in error_lower:
            return "value_error"
        elif "permission" in error_lower:
            return "permission_error"
        elif "timeout" in error_lower:
            return "timeout_error"
        elif "connection" in error_lower:
            return "connection_error"
        else:
            return "unknown_error"
    
    def _assess_severity(self, error: str) -> str:
        """
        评估严重程度 / Assess severity
        
        Args:
            error: 错误信息 / Error message
            
        Returns:
            严重程度 / Severity
        """
        error_lower = error.lower()
        
        critical_keywords = ["fatal", "critical", "crash", "memory"]
        high_keywords = ["error", "failed", "exception"]
        medium_keywords = ["warning", "deprecated"]
        
        for keyword in critical_keywords:
            if keyword in error_lower:
                return "critical"
        
        for keyword in high_keywords:
            if keyword in error_lower:
                return "high"
        
        for keyword in medium_keywords:
            if keyword in error_lower:
                return "medium"
        
        return "low"
    
    def _generate_suggestions(self, error: str) -> list[str]:
        """
        生成建议 / Generate suggestions
        
        Args:
            error: 错误信息 / Error message
            
        Returns:
            建议列表 / List of suggestions
        """
        suggestions = []
        error_type = self._classify_error(error)
        
        if error_type == "syntax_error":
            suggestions.append("Check code syntax and fix any parsing errors")
        elif error_type == "type_error":
            suggestions.append("Verify variable types and type conversions")
        elif error_type == "value_error":
            suggestions.append("Check input values and constraints")
        elif error_type == "permission_error":
            suggestions.append("Verify file/directory permissions")
        elif error_type == "timeout_error":
            suggestions.append("Consider increasing timeout or optimizing operation")
        elif error_type == "connection_error":
            suggestions.append("Check network connectivity and service availability")
        else:
            suggestions.append("Review the error and adjust approach accordingly")
        
        return suggestions
