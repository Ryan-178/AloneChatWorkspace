"""
数据导出模块 / Data Export Module

导出训练数据到各种格式
Exports training data to various formats
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime

from .trajectory import Trajectory


class DataExporter:
    """
    数据导出器 / Data Exporter
    
    导出训练数据到各种格式
    Exports training data to various formats
    """
    
    def __init__(self, output_dir: Path | str):
        """
        初始化数据导出器 / Initialize data exporter
        
        Args:
            output_dir: 输出目录 / Output directory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_jsonl(
        self,
        trajectories: list[Trajectory],
        filename: str = "training_data.jsonl",
        high_quality_only: bool = True,
        min_quality: float = 0.5,
    ) -> Path:
        """
        导出为JSONL格式 / Export to JSONL format
        
        每行一条轨迹数据，适合训练
        Each line is a trajectory, suitable for training
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            filename: 文件名 / Filename
            high_quality_only: 仅导出高质量数据 / Export only high-quality data
            min_quality: 最低质量阈值 / Minimum quality threshold
            
        Returns:
            输出路径 / Output path
        """
        output_path = self.output_dir / filename
        
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for trajectory in trajectories:
                if high_quality_only and trajectory.quality_score < min_quality:
                    continue
                
                data = trajectory.to_training_format()
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                count += 1
        
        return output_path
    
    def export_to_json(
        self,
        data: dict[str, Any],
        filename: str,
    ) -> Path:
        """
        导出为JSON格式 / Export to JSON format
        
        Args:
            data: 数据字典 / Data dictionary
            filename: 文件名 / Filename
            
        Returns:
            输出路径 / Output path
        """
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_trajectories_to_json(
        self,
        trajectories: list[Trajectory],
        filename: str = "training_data.json",
        high_quality_only: bool = True,
        min_quality: float = 0.5,
    ) -> Path:
        """
        导出轨迹为JSON格式 / Export trajectories to JSON format
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            filename: 文件名 / Filename
            high_quality_only: 仅导出高质量数据 / Export only high-quality data
            min_quality: 最低质量阈值 / Minimum quality threshold
            
        Returns:
            输出路径 / Output path
        """
        filtered = trajectories
        if high_quality_only:
            filtered = [t for t in trajectories if t.quality_score >= min_quality]
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": len(filtered),
            "trajectories": [t.to_training_format() for t in filtered],
        }
        
        return self.export_to_json(data, filename)
    
    def export_statistics(
        self,
        trajectories: list[Trajectory],
        filename: str = "statistics.json",
    ) -> Path:
        """
        导出统计信息 / Export statistics
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            filename: 文件名 / Filename
            
        Returns:
            输出路径 / Output path
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_trajectories": len(trajectories),
            "successful_count": sum(1 for t in trajectories if t.is_successful),
            "high_quality_count": sum(1 for t in trajectories if t.quality_score >= 0.5),
            "quality_distribution": self._quality_distribution(trajectories),
            "task_type_distribution": self._task_type_distribution(trajectories),
            "step_count_distribution": self._step_count_distribution(trajectories),
            "avg_statistics": self._avg_statistics(trajectories),
        }
        
        return self.export_to_json(stats, filename)
    
    def _quality_distribution(self, trajectories: list[Trajectory]) -> dict[str, int]:
        """
        质量分布 / Quality distribution
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            分布字典 / Distribution dictionary
        """
        bins = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        
        for t in trajectories:
            score = t.quality_score
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
    
    def _task_type_distribution(self, trajectories: list[Trajectory]) -> dict[str, int]:
        """
        任务类型分布 / Task type distribution
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            分布字典 / Distribution dictionary
        """
        dist: dict[str, int] = {}
        for t in trajectories:
            task_type = t.task_type or "unknown"
            dist[task_type] = dist.get(task_type, 0) + 1
        return dist
    
    def _step_count_distribution(self, trajectories: list[Trajectory]) -> dict[str, int]:
        """
        步骤数分布 / Step count distribution
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            分布字典 / Distribution dictionary
        """
        dist: dict[str, int] = {}
        for t in trajectories:
            count = t.step_count
            bucket = f"{(count // 5) * 5}-{(count // 5) * 5 + 4}"
            dist[bucket] = dist.get(bucket, 0) + 1
        return dist
    
    def _avg_statistics(self, trajectories: list[Trajectory]) -> dict[str, float]:
        """
        平均统计信息 / Average statistics
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            
        Returns:
            平均统计字典 / Average statistics dictionary
        """
        if not trajectories:
            return {
                "avg_quality_score": 0.0,
                "avg_step_count": 0.0,
                "avg_reward": 0.0,
                "avg_success_rate": 0.0,
            }
        
        return {
            "avg_quality_score": sum(t.quality_score for t in trajectories) / len(trajectories),
            "avg_step_count": sum(t.step_count for t in trajectories) / len(trajectories),
            "avg_reward": sum(t.avg_reward for t in trajectories) / len(trajectories),
            "avg_success_rate": sum(t.success_rate for t in trajectories) / len(trajectories),
        }
    
    def export_by_task_type(
        self,
        trajectories: list[Trajectory],
        output_dir: Path | str | None = None,
    ) -> dict[str, Path]:
        """
        按任务类型导出 / Export by task type
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            output_dir: 输出目录 / Output directory
            
        Returns:
            任务类型到输出路径的映射 / Mapping from task type to output path
        """
        output_dir = Path(output_dir) if output_dir else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result: dict[str, Path] = {}
        
        groups: dict[str, list[Trajectory]] = {}
        for t in trajectories:
            task_type = t.task_type or "unknown"
            if task_type not in groups:
                groups[task_type] = []
            groups[task_type].append(t)
        
        for task_type, group_trajectories in groups.items():
            filename = f"{task_type}_training_data.jsonl"
            exporter = DataExporter(output_dir)
            path = exporter.export_to_jsonl(group_trajectories, filename, high_quality_only=False)
            result[task_type] = path
        
        return result
    
    def export_report(
        self,
        trajectories: list[Trajectory],
        filename: str = "report.json",
    ) -> Path:
        """
        导出完整报告 / Export complete report
        
        Args:
            trajectories: 轨迹列表 / List of trajectories
            filename: 文件名 / Filename
            
        Returns:
            输出路径 / Output path
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_trajectories": len(trajectories),
                "successful_count": sum(1 for t in trajectories if t.is_successful),
                "high_quality_count": sum(1 for t in trajectories if t.quality_score >= 0.5),
                "total_steps": sum(t.step_count for t in trajectories),
            },
            "quality": {
                "distribution": self._quality_distribution(trajectories),
                "avg_score": sum(t.quality_score for t in trajectories) / len(trajectories) if trajectories else 0,
            },
            "task_types": self._task_type_distribution(trajectories),
            "steps": {
                "distribution": self._step_count_distribution(trajectories),
                "avg_count": sum(t.step_count for t in trajectories) / len(trajectories) if trajectories else 0,
            },
            "rewards": {
                "avg_total": sum(t.total_reward for t in trajectories) / len(trajectories) if trajectories else 0,
                "avg_per_step": sum(t.avg_reward for t in trajectories) / len(trajectories) if trajectories else 0,
            },
        }
        
        return self.export_to_json(report, filename)
