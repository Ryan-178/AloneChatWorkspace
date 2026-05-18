"""
服务模块 / Services Module

提供多格式文件的文本化转换和生成能力 / Provides multi-format file processing and generation
提供任务管理能力 / Provides task management capabilities
"""

from .file_processors import get_processor, FileProcessorRegistry
from .file_generators import file_generator
from .task_manager import TaskManager, ManagedTask, TaskDependencyGraph, task_manager

__all__ = [
    "get_processor",
    "FileProcessorRegistry",
    "file_generator",
    "TaskManager",
    "ManagedTask",
    "TaskDependencyGraph",
    "task_manager",
]
