"""
RLM调度器 / RLM Dispatcher

低成本子任务调度器，智能路由子任务到最合适的模型
Low-cost subtask dispatcher, intelligently routes subtasks to the most suitable model
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """
    任务复杂度 / Task Complexity
    """
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"


class ModelTier(str, Enum):
    """
    模型层级 / Model Tier
    """
    FLASH = "flash"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class ModelProfile:
    """
    模型配置 / Model Profile
    """
    model_id: str
    tier: ModelTier
    input_cost: float
    output_cost: float
    context_window: int
    capabilities: List[str] = field(default_factory=list)
    quality_score: float = 0.8


@dataclass
class SubtaskProfile:
    """
    子任务配置 / Subtask Profile
    """
    task_id: str
    description: str
    complexity: TaskComplexity
    required_capabilities: List[str] = field(default_factory=list)
    estimated_tokens: int = 1000
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class RLMDipatcher:
    """
    RLM调度器 / RLM Dispatcher

    功能：
    - 智能路由子任务到最合适的模型
    - 成本优化：简单任务用便宜模型，复杂任务用强模型
    - 质量保证：确保任务质量满足要求
    - 动态调整：根据历史表现调整路由策略

    Features:
    - Intelligently routes subtasks to the most suitable model
    - Cost optimization: Use cheap models for simple tasks, strong models for complex tasks
    - Quality assurance: Ensure task quality meets requirements
    - Dynamic adjustment: Adjust routing strategy based on historical performance
    """

    DEFAULT_MODEL_PROFILES = {
        ModelTier.FLASH: ModelProfile(
            model_id="deepseek-chat",
            tier=ModelTier.FLASH,
            input_cost=0.14,
            output_cost=0.28,
            context_window=64000,
            capabilities=["chat", "code", "general"],
            quality_score=0.75,
        ),
        ModelTier.STANDARD: ModelProfile(
            model_id="deepseek-reasoner",
            tier=ModelTier.STANDARD,
            input_cost=0.55,
            output_cost=2.19,
            context_window=64000,
            capabilities=["chat", "code", "reasoning", "complex"],
            quality_score=0.85,
        ),
        ModelTier.PREMIUM: ModelProfile(
            model_id="claude-3-5-sonnet",
            tier=ModelTier.PREMIUM,
            input_cost=3.0,
            output_cost=15.0,
            context_window=200000,
            capabilities=["chat", "code", "reasoning", "vision", "complex"],
            quality_score=0.95,
        ),
    }

    COMPLEXITY_TO_TIER = {
        TaskComplexity.TRIVIAL: ModelTier.FLASH,
        TaskComplexity.SIMPLE: ModelTier.FLASH,
        TaskComplexity.MEDIUM: ModelTier.STANDARD,
        TaskComplexity.COMPLEX: ModelTier.STANDARD,
        TaskComplexity.CRITICAL: ModelTier.PREMIUM,
    }

    def __init__(
        self,
        cost_optimization: bool = True,
        quality_threshold: float = 0.8,
        custom_profiles: Optional[Dict[ModelTier, ModelProfile]] = None,
    ):
        self.cost_optimization = cost_optimization
        self.quality_threshold = quality_threshold
        self._model_profiles = custom_profiles or self.DEFAULT_MODEL_PROFILES
        self._routing_history: List[Dict[str, Any]] = []
        self._performance_stats: Dict[str, Dict[str, float]] = {}

    def assess_complexity(self, task: SubtaskProfile) -> TaskComplexity:
        """
        评估任务复杂度 / Assess task complexity

        Args:
            task: 子任务配置

        Returns:
            任务复杂度
        """
        description = task.description.lower()

        complexity_keywords = {
            TaskComplexity.TRIVIAL: ["fix typo", "rename", "format", "lint"],
            TaskComplexity.SIMPLE: ["add", "update", "change", "modify"],
            TaskComplexity.MEDIUM: ["implement", "create", "refactor", "optimize"],
            TaskComplexity.COMPLEX: ["design", "architect", "integrate", "migrate"],
            TaskComplexity.CRITICAL: ["security", "critical", "breaking", "major"],
        }

        for complexity, keywords in complexity_keywords.items():
            if any(kw in description for kw in keywords):
                return complexity

        if task.estimated_tokens > 10000:
            return TaskComplexity.COMPLEX
        elif task.estimated_tokens > 5000:
            return TaskComplexity.MEDIUM
        elif task.estimated_tokens > 1000:
            return TaskComplexity.SIMPLE

        return task.complexity

    def route(self, task: SubtaskProfile) -> ModelProfile:
        """
        路由任务到模型 / Route task to model

        Args:
            task: 子任务配置

        Returns:
            选中的模型配置
        """
        complexity = self.assess_complexity(task)

        if self.cost_optimization:
            tier = self._optimize_for_cost(task, complexity)
        else:
            tier = self.COMPLEXITY_TO_TIER[complexity]

        for cap in task.required_capabilities:
            profile = self._model_profiles[tier]
            if cap not in profile.capabilities:
                for t, p in self._model_profiles.items():
                    if cap in p.capabilities:
                        tier = t
                        break

        selected_model = self._model_profiles[tier]

        self._routing_history.append({
            "task_id": task.task_id,
            "complexity": complexity.value,
            "selected_tier": tier.value,
            "selected_model": selected_model.model_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        logger.debug(
            f"Routed task {task.task_id} (complexity: {complexity.value}) "
            f"to {selected_model.model_id} (tier: {tier.value})"
        )

        return selected_model

    def _optimize_for_cost(
        self,
        task: SubtaskProfile,
        complexity: TaskComplexity,
    ) -> ModelTier:
        """
        成本优化路由 / Cost-optimized routing
        """
        base_tier = self.COMPLEXITY_TO_TIER[complexity]

        if complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]:
            return ModelTier.FLASH

        if complexity == TaskComplexity.MEDIUM:
            flash_profile = self._model_profiles[ModelTier.FLASH]
            if flash_profile.quality_score >= self.quality_threshold:
                return ModelTier.FLASH
            return ModelTier.STANDARD

        return base_tier

    def estimate_cost(
        self,
        task: SubtaskProfile,
        model: ModelProfile,
    ) -> float:
        """
        估算任务成本 / Estimate task cost

        Args:
            task: 子任务配置
            model: 模型配置

        Returns:
            估算成本（美元）
        """
        input_cost = (task.estimated_tokens / 1_000_000) * model.input_cost
        output_cost = (task.estimated_tokens * 0.5 / 1_000_000) * model.output_cost
        return input_cost + output_cost

    def get_optimal_batch(
        self,
        tasks: List[SubtaskProfile],
        budget: float,
    ) -> List[SubtaskProfile]:
        """
        在预算内获取最优任务批次 / Get optimal task batch within budget

        Args:
            tasks: 任务列表
            budget: 预算（美元）

        Returns:
            可执行的任务列表
        """
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        selected = []
        remaining_budget = budget

        for task in sorted_tasks:
            model = self.route(task)
            cost = self.estimate_cost(task, model)

            if cost <= remaining_budget:
                selected.append(task)
                remaining_budget -= cost

        return selected

    def record_performance(
        self,
        task_id: str,
        model_id: str,
        success: bool,
        quality_score: float,
        actual_cost: float,
    ) -> None:
        """
        记录执行表现 / Record execution performance
        """
        if model_id not in self._performance_stats:
            self._performance_stats[model_id] = {
                "total_tasks": 0,
                "success_count": 0,
                "avg_quality": 0.0,
                "total_cost": 0.0,
            }

        stats = self._performance_stats[model_id]
        stats["total_tasks"] += 1
        if success:
            stats["success_count"] += 1
        stats["avg_quality"] = (
            (stats["avg_quality"] * (stats["total_tasks"] - 1) + quality_score)
            / stats["total_tasks"]
        )
        stats["total_cost"] += actual_cost

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取调度统计 / Get dispatch statistics
        """
        return {
            "total_routed": len(self._routing_history),
            "model_stats": self._performance_stats.copy(),
            "cost_optimization_enabled": self.cost_optimization,
            "quality_threshold": self.quality_threshold,
        }

    def get_routing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取路由历史 / Get routing history
        """
        return self._routing_history[-limit:]
