"""
文件处理服务模块

提供多格式文件的文本化转换和生成能力
"""

from .file_processors import get_processor, FileProcessorRegistry
from .file_generators import file_generator

__all__ = [
    "get_processor",
    "FileProcessorRegistry",
    "file_generator",
]
