"""
数据层 / Data Layer

提供轨迹记录、数据收集、质量评估和数据导出功能
Provides trajectory recording, data collection, quality evaluation and data export functionality

核心策略：数据收集而非直接训练
Core strategy: Data collection instead of direct training
"""

from .trajectory import InteractionStep, Trajectory, TrajectoryRecorder
from .collector import DataCollector
from .quality import QualityEvaluator
from .exporter import DataExporter

__all__ = [
    "InteractionStep",
    "Trajectory",
    "TrajectoryRecorder",
    "DataCollector",
    "QualityEvaluator",
    "DataExporter",
]
