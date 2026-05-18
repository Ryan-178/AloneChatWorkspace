"""
文件生成服务模块

使用 DeepSeek 生成各种格式的文件
"""

from .generator_service import FileGeneratorService, file_generator

__all__ = [
    "FileGeneratorService",
    "file_generator",
]
