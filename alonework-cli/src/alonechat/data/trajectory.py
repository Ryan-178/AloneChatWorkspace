"""
轨迹记录模块 / Trajectory Recording Module

记录完整的用户-Agent交互过程，输出可用于训练的结构化数据
Records complete user-Agent interaction process, outputs structured data for training
"""

from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime
from uuid import uuid4
import json


@dataclass
class InteractionStep:
    """
    交互步骤 / Interaction Step
    
    记录单次交互的完整信息
    Records complete information of a single interaction
    """
    step_id: str
    timestamp: str
    
    user_input: str | None = None
    
    agent_thought: str | None = None
    
    action_type: str = ""
    action_params: dict[str, Any] = field(default_factory=dict)
    
    observation: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    
    reward: float = 0.0
    feedback: str | None = None
    
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)
    
    def to_training_format(self) -> dict[str, Any]:
        """
        转换为训练数据格式 / Convert to training data format
        
        只保留训练所需的字段
        Only keeps fields needed for training
        """
        return {
            "thought": self.agent_thought,
            "action": {
                "type": self.action_type,
                "params": self.action_params,
            },
            "observation": self.observation,
            "reward": self.reward,
            "success": self.success,
        }


@dataclass
class Trajectory:
    """
    完整轨迹 / Complete Trajectory
    
    记录一次完整的用户-Agent交互过程
    Records a complete user-Agent interaction process
    """
    trajectory_id: str
    session_id: str
    start_time: str
    end_time: str | None = None
    
    task_description: str = ""
    task_type: str = ""
    
    steps: list[InteractionStep] = field(default_factory=list)
    
    initial_state: dict[str, Any] = field(default_factory=dict)
    final_state: dict[str, Any] = field(default_factory=dict)
    
    quality_score: float = 0.0
    is_successful: bool = False
    
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: InteractionStep) -> None:
        """
        添加交互步骤 / Add interaction step
        
        Args:
            step: 交互步骤 / Interaction step
        """
        self.steps.append(step)
    
    @property
    def step_count(self) -> int:
        """获取步骤数量 / Get step count"""
        return len(self.steps)
    
    @property
    def total_reward(self) -> float:
        """获取总奖励 / Get total reward"""
        return sum(step.reward for step in self.steps)
    
    @property
    def avg_reward(self) -> float:
        """获取平均奖励 / Get average reward"""
        if not self.steps:
            return 0.0
        return self.total_reward / len(self.steps)
    
    @property
    def success_rate(self) -> float:
        """获取成功率 / Get success rate"""
        if not self.steps:
            return 0.0
        return sum(1 for step in self.steps if step.success) / len(self.steps)
    
    @property
    def duration_seconds(self) -> float | None:
        """获取持续时间（秒）/ Get duration in seconds"""
        if not self.end_time:
            return None
        try:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        data = asdict(self)
        data["steps"] = [step.to_dict() for step in self.steps]
        return data
    
    def to_training_format(self) -> dict[str, Any]:
        """
        转换为训练数据格式 / Convert to training data format
        
        输出可用于训练的结构化数据
        Outputs structured data for training
        """
        return {
            "id": self.trajectory_id,
            "task": {
                "description": self.task_description,
                "type": self.task_type,
            },
            "trajectory": [step.to_training_format() for step in self.steps],
            "outcome": {
                "success": self.is_successful,
                "quality_score": self.quality_score,
                "final_state": self.final_state,
            },
            "statistics": {
                "step_count": self.step_count,
                "total_reward": self.total_reward,
                "avg_reward": self.avg_reward,
                "success_rate": self.success_rate,
                "duration_seconds": self.duration_seconds,
            },
            "metadata": self.metadata,
        }
    
    def to_json(self, ensure_ascii: bool = False) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_training_format(), ensure_ascii=ensure_ascii)


class TrajectoryRecorder:
    """
    轨迹记录器 / Trajectory Recorder
    
    记录完整的交互轨迹，不做训练
    Records complete interaction trajectories, no training performed
    
    核心策略：数据收集而非直接训练
    Core strategy: Data collection instead of direct training
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化轨迹记录器 / Initialize trajectory recorder
        
        Args:
            config: 配置字典 / Configuration dictionary
        """
        self.config = config or {}
        self.trajectories: dict[str, Trajectory] = {}
        self.current_trajectory: Trajectory | None = None
        
        self._auto_save = self.config.get("auto_save", False)
        self._output_dir = self.config.get("output_dir", None)
    
    def start_trajectory(
        self,
        session_id: str,
        task_description: str,
        task_type: str,
        initial_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        开始新轨迹 / Start new trajectory
        
        Args:
            session_id: 会话ID / Session ID
            task_description: 任务描述 / Task description
            task_type: 任务类型 / Task type
            initial_state: 初始状态 / Initial state
            metadata: 元数据 / Metadata
            
        Returns:
            轨迹ID / Trajectory ID
        """
        trajectory_id = str(uuid4())
        now = datetime.now().isoformat()
        
        self.current_trajectory = Trajectory(
            trajectory_id=trajectory_id,
            session_id=session_id,
            start_time=now,
            task_description=task_description,
            task_type=task_type,
            initial_state=initial_state or {},
            metadata=metadata or {},
        )
        
        self.trajectories[trajectory_id] = self.current_trajectory
        return trajectory_id
    
    def record_step(
        self,
        user_input: str | None = None,
        agent_thought: str | None = None,
        action_type: str = "",
        action_params: dict[str, Any] | None = None,
        observation: dict[str, Any] | None = None,
        result: Any = None,
        success: bool = False,
        reward: float = 0.0,
        feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        记录交互步骤 / Record interaction step
        
        Args:
            user_input: 用户输入 / User input
            agent_thought: Agent思考过程 / Agent thought process
            action_type: 行动类型 / Action type
            action_params: 行动参数 / Action parameters
            observation: 观察结果 / Observation result
            result: 执行结果 / Execution result
            success: 是否成功 / Whether successful
            reward: 奖励值 / Reward value
            feedback: 反馈信息 / Feedback information
            metadata: 元数据 / Metadata
            
        Returns:
            步骤ID / Step ID
        """
        if not self.current_trajectory:
            raise RuntimeError("No active trajectory. Call start_trajectory() first.")
        
        step_id = str(uuid4())
        now = datetime.now().isoformat()
        
        step = InteractionStep(
            step_id=step_id,
            timestamp=now,
            user_input=user_input,
            agent_thought=agent_thought,
            action_type=action_type,
            action_params=action_params or {},
            observation=observation or {},
            result=result,
            success=success,
            reward=reward,
            feedback=feedback,
            metadata=metadata or {},
        )
        
        self.current_trajectory.add_step(step)
        return step_id
    
    def end_trajectory(
        self,
        final_state: dict[str, Any] | None = None,
        quality_score: float = 0.0,
        is_successful: bool = False,
    ) -> Trajectory | None:
        """
        结束轨迹 / End trajectory
        
        Args:
            final_state: 最终状态 / Final state
            quality_score: 质量分数 / Quality score
            is_successful: 是否成功 / Whether successful
            
        Returns:
            完成的轨迹 / Completed trajectory
        """
        if not self.current_trajectory:
            return None
        
        self.current_trajectory.end_time = datetime.now().isoformat()
        self.current_trajectory.final_state = final_state or {}
        self.current_trajectory.quality_score = quality_score
        self.current_trajectory.is_successful = is_successful
        
        trajectory = self.current_trajectory
        self.current_trajectory = None
        
        return trajectory
    
    def get_trajectory(self, trajectory_id: str) -> Trajectory | None:
        """
        获取轨迹 / Get trajectory
        
        Args:
            trajectory_id: 轨迹ID / Trajectory ID
            
        Returns:
            轨迹对象 / Trajectory object
        """
        return self.trajectories.get(trajectory_id)
    
    def get_all_trajectories(self) -> list[Trajectory]:
        """
        获取所有轨迹 / Get all trajectories
        
        Returns:
            轨迹列表 / List of trajectories
        """
        return list(self.trajectories.values())
    
    def get_trajectories_by_session(self, session_id: str) -> list[Trajectory]:
        """
        按会话获取轨迹 / Get trajectories by session
        
        Args:
            session_id: 会话ID / Session ID
            
        Returns:
            轨迹列表 / List of trajectories
        """
        return [
            t for t in self.trajectories.values()
            if t.session_id == session_id
        ]
    
    def clear_trajectories(self) -> int:
        """
        清除所有轨迹 / Clear all trajectories
        
        Returns:
            清除的数量 / Number of cleared trajectories
        """
        count = len(self.trajectories)
        self.trajectories.clear()
        self.current_trajectory = None
        return count
    
    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息 / Get statistics
        
        Returns:
            统计信息字典 / Statistics dictionary
        """
        trajectories = self.get_all_trajectories()
        
        if not trajectories:
            return {
                "total_trajectories": 0,
                "total_steps": 0,
                "successful_trajectories": 0,
                "avg_quality_score": 0.0,
                "avg_steps": 0.0,
            }
        
        return {
            "total_trajectories": len(trajectories),
            "total_steps": sum(t.step_count for t in trajectories),
            "successful_trajectories": sum(1 for t in trajectories if t.is_successful),
            "avg_quality_score": sum(t.quality_score for t in trajectories) / len(trajectories),
            "avg_steps": sum(t.step_count for t in trajectories) / len(trajectories),
        }
