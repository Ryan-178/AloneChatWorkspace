"""
文件处理器模块

将各种格式的文件转换为 DeepSeek 可理解的文本表示
"""

from .base_processor import BaseFileProcessor
from .registry import FileProcessorRegistry, get_processor

__all__ = [
    "BaseFileProcessor",
    "FileProcessorRegistry",
    "get_processor",
]
