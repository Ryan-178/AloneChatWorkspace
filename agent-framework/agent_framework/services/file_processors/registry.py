"""
文件处理器注册中心

统一管理和调度各种文件处理器
"""

from typing import Dict, Optional, Type
from pathlib import Path
from .base_processor import BaseFileProcessor


class FileProcessorRegistry:
    """文件处理器注册中心"""
    
    def __init__(self):
        self._processors: Dict[str, BaseFileProcessor] = {}
        self._extension_map: Dict[str, str] = {}
    
    def register(self, processor: BaseFileProcessor) -> None:
        """
        注册文件处理器
        
        Args:
            processor: 处理器实例
        """
        processor_name = processor.__class__.__name__
        self._processors[processor_name] = processor
        
        # 建立扩展名映射
        for ext in processor.get_supported_extensions():
            self._extension_map[ext.lower()] = processor_name
    
    def get_processor(self, extension: str) -> Optional[BaseFileProcessor]:
        """
        根据扩展名获取处理器
        
        Args:
            extension: 文件扩展名
            
        Returns:
            处理器实例，如果不存在返回 None
        """
        ext = extension.lower()
        if ext not in self._extension_map:
            return None
        
        processor_name = self._extension_map[ext]
        return self._processors.get(processor_name)
    
    def get_processor_for_file(self, file_path: Path) -> Optional[BaseFileProcessor]:
        """
        根据文件路径获取处理器
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理器实例
        """
        return self.get_processor(file_path.suffix)
    
    def list_supported_extensions(self) -> list[str]:
        """
        列出所有支持的扩展名
        
        Returns:
            扩展名列表
        """
        return list(self._extension_map.keys())
    
    def list_processors(self) -> list[str]:
        """
        列出所有处理器名称
        
        Returns:
            处理器名称列表
        """
        return list(self._processors.keys())


# 全局注册中心实例
_registry = FileProcessorRegistry()


def register_processor(processor: BaseFileProcessor) -> None:
    """注册处理器到全局注册中心"""
    _registry.register(processor)


def get_processor(extension: str) -> Optional[BaseFileProcessor]:
    """从全局注册中心获取处理器"""
    return _registry.get_processor(extension)


def get_registry() -> FileProcessorRegistry:
    """获取全局注册中心"""
    return _registry


# 自动注册内置处理器
def _auto_register():
    """自动注册内置处理器"""
    try:
        from .document_processor import DocumentProcessor
        register_processor(DocumentProcessor())
    except ImportError:
        pass
    
    try:
        from .spreadsheet_processor import SpreadsheetProcessor
        register_processor(SpreadsheetProcessor())
    except ImportError:
        pass
    
    try:
        from .presentation_processor import PresentationProcessor
        register_processor(PresentationProcessor())
    except ImportError:
        pass
    
    try:
        from .code_processor import CodeProcessor
        register_processor(CodeProcessor())
    except ImportError:
        pass
    
    try:
        from .image_processor import ImageProcessor
        register_processor(ImageProcessor())
    except ImportError:
        pass
    
    try:
        from .text_processor import TextProcessor
        register_processor(TextProcessor())
    except ImportError:
        pass


# 模块加载时自动注册
_auto_register()
