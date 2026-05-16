"""
文件处理器基类

定义文件处理器的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class BaseFileProcessor(ABC):
    """文件处理器基类"""
    
    @abstractmethod
    async def to_text(self, file_path: Path) -> str:
        """
        将文件转换为 DeepSeek 可理解的文本表示
        
        Args:
            file_path: 文件路径
            
        Returns:
            文本表示
        """
        pass
    
    @abstractmethod
    async def from_text(self, text: str, output_path: Path) -> bool:
        """
        从文本描述生成实际文件
        
        Args:
            text: 文本描述
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """
        返回支持的文件扩展名
        
        Returns:
            扩展名列表，如 ['.pdf', '.docx']
        """
        pass
    
    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            元数据字典
        """
        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }
    
    def can_process(self, file_path: Path) -> bool:
        """
        检查是否可以处理该文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        return file_path.suffix.lower() in self.get_supported_extensions()
