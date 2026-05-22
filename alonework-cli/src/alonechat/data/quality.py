"""
质量评估模块 / Quality Evaluation Module

评估交互质量，筛选高质量数据
Evaluates interaction quality, filters high-quality data
"""

from typing import Any
from dataclasses import dataclass, field

from .trajectory import Trajectory


@dataclass
class QualityWeights:
    """
    质量权重配置 / Quality Weights Configuration
    
    定义各维度的权重
    Defines weights for each dimension
    """
    task_completion: float = 0.4
    efficiency: float = 0.2
    reward: float = 0.2
    error_rate: float = 0.2
    
    def to_dict(self) -> dict[str, float]:
        """转换为字典 / Convert to dictionary"""
        return {
            "task_completion": self.task_completion,
            "efficiency": self.efficiency,
            "reward": self.reward,
            "error_rate": self.error_rate,
        }


@dataclass
class QualityResult:
    """
    质量评估结果 / Quality Evaluation Result
    
    包含详细的评估信息
    Contains detailed evaluation information
    """
    overall_score: float
    is_high_quality: bool
    components: dict[str, float]
    details: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "is_high_quality": self.is_high_quality,
            "components": self.components,
            "details": self.details,
        }


class QualityEvaluator:
    """
    质量评估器 / Quality Evaluator
    
    评估交互质量，筛选高质量数据
    Evaluates interaction quality, filters high-quality data
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化质量评估器 / Initialize quality evaluator
        
        Args:
            config: 配置字典 / Configuration dictionary
        """
        self.config = config or {}
        
        weights_config = self.config.get("weights", {})
        self.weights = QualityWeights(
            task_completion=weights_config.get("task_completion", 0.4),
            efficiency=weights_config.get("efficiency", 0.2),
            reward=weights_config.get("reward", 0.2),
            error_rate=weights_config.get("error_rate", 0.2),
        )
        
        self.min_quality_threshold = self.config.get("min_quality_threshold", 0.5)
        self.optimal_step_count = self.config.get("optimal_step_count", 10)
    
    def evaluate_trajectory(self, trajectory: Trajectory) -> QualityResult:
        """
        评估轨迹质量 / Evaluate trajectory quality
        
        Args:
            trajectory: 轨迹对象 / Trajectory object
            
        Returns:
            质量评估结果 / Quality evaluation result
        """
        components: dict[str, float] = {}
        details: dict[str, Any] = {}
        
        components["task_completion"] = self._evaluate_task_completion(trajectory)
        components["efficiency"] = self._evaluate_efficiency(trajectory)
        components["reward"] = self._evaluate_reward(trajectory)
        components["error_rate"] = self._evaluate_error_rate(trajectory)
        
        details["step_count"] = trajectory.step_count
        details["success_rate"] = trajectory.success_rate
        details["avg_reward"] = trajectory.avg_reward
        details["is_successful"] = trajectory.is_successful
        
        overall_score = (
            components["task_completion"] * self.weights.task_completion +
            components["efficiency"] * self.weights.efficiency +
            components["reward"] * self.weights.reward +
            components["error_rate"] * self.weights.error_rate
        )
        
        return QualityResult(
            overall_score=overall_score,
            is_high_quality=overall_score >= self.min_quality_threshold,
            components=components,
            details=details,
        )
    
    def _evaluate_task_completion(self, trajectory: Trajectory) -> float:
        """
        评估任务完成度 / Evaluate task completion
        
        成功完成的轨迹得分高，失败的得分低
        Successfully completed trajectories score high, failed ones score low
        """
        if trajectory.is_successful:
            return 1.0
        return 0.3
    
    def _evaluate_efficiency(self, trajectory: Trajectory) -> float:
        """
        评估效率 / Evaluate efficiency
        
        步骤数越接近最优值得分越高
        The closer the step count to the optimal value, the higher the score
        """
        step_count = trajectory.step_count
        if step_count == 0:
            return 0.0
        
        optimal = self.optimal_step_count
        
        if step_count <= optimal:
            return 1.0
        
        ratio = optimal / step_count
        return max(0.0, ratio)
    
    def _evaluate_reward(self, trajectory: Trajectory) -> float:
        """
        评估奖励 / Evaluate reward
        
        平均奖励越高得分越高
        Higher average reward means higher score
        """
        avg_reward = trajectory.avg_reward
        
        normalized = max(0.0, min(1.0, avg_reward + 0.5))
        return normalized
    
    def _evaluate_error_rate(self, trajectory: Trajectory) -> float:
        """
        评估错误率 / Evaluate error rate
        
        错误率越低得分越高
        Lower error rate means higher score
        """
        return trajectory.success_rate
    
    def is_high_quality(self, trajectory: Trajectory) -> bool:
        """
        判断是否为高质量数据 / Determine if data is high quality
        
        Args:
            trajectory: 轨迹对象 / Trajectory object
            
        Returns:
            是否高质量 / Whether high quality
        """
        result = self.evaluate_trajectory(trajectory)
        return result.is_high_quality
    
    def filter_high_quality(
        self,
        trajectories: list[Trajectory],
        min_quality: float | None = None,
    ) -> list[Trajectory]:
        """
        过滤高质量轨迹 / Filter high-quality trajectories
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            min_quality: 最低质量阈值 / Minimum quality threshold
            
        Returns:
            高质量轨迹列表 / List of high-quality trajectories
        """
        threshold = min_quality or self.min_quality_threshold
        return [t for t in trajectories if self.evaluate_trajectory(t).overall_score >= threshold]
    
    def rank_trajectories(
        self,
        trajectories: list[Trajectory],
    ) -> list[tuple[Trajectory, QualityResult]]:
        """
        排序轨迹 / Rank trajectories
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            排序后的(轨迹, 结果)列表 / Sorted list of (trajectory, result) tuples
        """
        results = [(t, self.evaluate_trajectory(t)) for t in trajectories]
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        return results
    
    def get_quality_distribution(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, int]:
        """
        获取质量分布 / Get quality distribution
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            质量分布字典 / Quality distribution dictionary
        """
        bins = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        
        for t in trajectories:
            score = self.evaluate_trajectory(t).overall_score
            
            if score < 0.2:
                bins["0.0-0.2"] += 1
            elif score < 0.4:
                bins["0.2-0.4"] += 1
            elif score < 0.6:
                bins["0.4-0.6"] += 1
            elif score < 0.8:
                bins["0.6-0.8"] += 1
            else:
                bins["0.8-1.0"] += 1
        
        return bins
    
    def get_statistics(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, Any]:
        """
        获取统计信息 / Get statistics
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            统计信息字典 / Statistics dictionary
        """
        if not trajectories:
            return {
                "total": 0,
                "high_quality_count": 0,
                "high_quality_ratio": 0.0,
                "avg_score": 0.0,
                "distribution": {},
            }
        
        results = [self.evaluate_trajectory(t) for t in trajectories]
        scores = [r.overall_score for r in results]
        high_quality_count = sum(1 for r in results if r.is_high_quality)
        
        return {
            "total": len(trajectories),
            "high_quality_count": high_quality_count,
            "high_quality_ratio": high_quality_count / len(trajectories),
            "avg_score": sum(scores) / len(scores),
            "distribution": self.get_quality_distribution(trajectories),
        }
