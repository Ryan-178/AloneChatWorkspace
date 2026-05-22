"""
数据收集模块 / Data Collection Module

收集并整理交互数据
Collects and organizes interaction data
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime
from dataclasses import dataclass, field

from .trajectory import Trajectory


@dataclass
class SessionData:
    """
    会话数据 / Session Data
    
    包含一个会话的所有轨迹数据
    Contains all trajectory data for a session
    """
    session_id: str
    timestamp: str
    trajectories: list[dict[str, Any]]
    statistics: dict[str, Any]
    
    def to_json(self, ensure_ascii: bool = False) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps({
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "trajectories": self.trajectories,
            "statistics": self.statistics,
        }, ensure_ascii=ensure_ascii, indent=2)


class DataCollector:
    """
    数据收集器 / Data Collector
    
    收集并整理交互数据
    Collects and organizes interaction data
    """
    
    def __init__(self, output_dir: Path | str | None = None):
        """
        初始化数据收集器 / Initialize data collector
        
        Args:
            output_dir: 输出目录 / Output directory
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_session_data(
        self,
        session_id: str,
        trajectories: list[Trajectory],
    ) -> SessionData:
        """
        收集会话数据 / Collect session data
        
        Args:
            session_id: 会话ID / Session ID
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            会话数据 / Session data
        """
        return SessionData(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            trajectories=[t.to_training_format() for t in trajectories],
            statistics=self._compute_statistics(trajectories),
        )
    
    def collect_trajectory_data(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, Any]:
        """
        收集轨迹数据 / Collect trajectory data
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            轨迹数据字典 / Trajectory data dictionary
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "trajectories": [t.to_training_format() for t in trajectories],
            "statistics": self._compute_statistics(trajectories),
        }
    
    def _compute_statistics(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, Any]:
        """
        计算统计信息 / Compute statistics
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            统计信息字典 / Statistics dictionary
        """
        if not trajectories:
            return {
                "total_trajectories": 0,
                "total_steps": 0,
                "successful_trajectories": 0,
                "high_quality_trajectories": 0,
                "avg_quality_score": 0.0,
                "avg_steps": 0.0,
                "avg_success_rate": 0.0,
            }
        
        total_steps = sum(t.step_count for t in trajectories)
        successful = sum(1 for t in trajectories if t.is_successful)
        high_quality = sum(1 for t in trajectories if t.quality_score >= 0.5)
        
        return {
            "total_trajectories": len(trajectories),
            "total_steps": total_steps,
            "successful_trajectories": successful,
            "high_quality_trajectories": high_quality,
            "avg_quality_score": sum(t.quality_score for t in trajectories) / len(trajectories),
            "avg_steps": total_steps / len(trajectories),
            "avg_success_rate": successful / len(trajectories),
        }
    
    def filter_by_quality(
        self,
        trajectories: list[Trajectory],
        min_quality: float = 0.5,
    ) -> list[Trajectory]:
        """
        按质量过滤轨迹 / Filter trajectories by quality
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            min_quality: 最低质量阈值 / Minimum quality threshold
            
        Returns:
            过滤后的轨迹列表 / Filtered list of trajectories
        """
        return [t for t in trajectories if t.quality_score >= min_quality]
    
    def filter_by_success(
        self,
        trajectories: list[Trajectory],
        successful_only: bool = True,
    ) -> list[Trajectory]:
        """
        按成功状态过滤轨迹 / Filter trajectories by success status
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            successful_only: 仅保留成功的 / Keep only successful ones
            
        Returns:
            过滤后的轨迹列表 / Filtered list of trajectories
        """
        if successful_only:
            return [t for t in trajectories if t.is_successful]
        return [t for t in trajectories if not t.is_successful]
    
    def filter_by_task_type(
        self,
        trajectories: list[Trajectory],
        task_type: str,
    ) -> list[Trajectory]:
        """
        按任务类型过滤轨迹 / Filter trajectories by task type
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            task_type: 任务类型 / Task type
            
        Returns:
            过滤后的轨迹列表 / Filtered list of trajectories
        """
        return [t for t in trajectories if t.task_type == task_type]
    
    def filter_by_session(
        self,
        trajectories: list[Trajectory],
        session_id: str,
    ) -> list[Trajectory]:
        """
        按会话过滤轨迹 / Filter trajectories by session
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            session_id: 会话ID / Session ID
            
        Returns:
            过滤后的轨迹列表 / Filtered list of trajectories
        """
        return [t for t in trajectories if t.session_id == session_id]
    
    def group_by_task_type(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, list[Trajectory]]:
        """
        按任务类型分组 / Group by task type
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            分组字典 / Grouped dictionary
        """
        groups: dict[str, list[Trajectory]] = {}
        for t in trajectories:
            task_type = t.task_type or "unknown"
            if task_type not in groups:
                groups[task_type] = []
            groups[task_type].append(t)
        return groups
    
    def group_by_session(
        self,
        trajectories: list[Trajectory],
    ) -> dict[str, list[Trajectory]]:
        """
        按会话分组 / Group by session
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            分组字典 / Grouped dictionary
        """
        groups: dict[str, list[Trajectory]] = {}
        for t in trajectories:
            if t.session_id not in groups:
                groups[t.session_id] = []
            groups[t.session_id].append(t)
        return groups
    
    def save_session_data(
        self,
        session_data: SessionData,
        filename: str | None = None,
    ) -> Path | None:
        """
        保存会话数据 / Save session data
        
        Args:
            session_data: 会话数据 / Session data
            filename: 文件名 / Filename
            
        Returns:
            保存路径 / Save path
        """
        if not self.output_dir:
            return None
        
        filename = filename or f"session_{session_data.session_id}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(session_data.to_json(ensure_ascii=False))
        
        return output_path
