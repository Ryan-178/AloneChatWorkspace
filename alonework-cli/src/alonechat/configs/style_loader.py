"""
输出样式配置加载器 / Output Style Config Loader

从YAML文件加载输出样式配置 / Load output style configuration from YAML file

版本 / Version: 2.0.32
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class StyleConfig:
    """
    样式配置 / Style Config
    
    提供输出样式配置的访问 / Provides access to output style configuration
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """加载YAML配置 / Load YAML config"""
        config_path = Path(__file__).parent / "output_style.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
    
    def reload(self) -> None:
        """重新加载配置 / Reload config"""
        self._load_config()
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        获取配置值 / Get config value
        
        Args:
            *keys: 配置键路径 / Config key path
            default: 默认值 / Default value
        
        Returns:
            配置值 / Config value
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    @property
    def theme(self) -> Dict[str, Any]:
        """获取主题配置 / Get theme config"""
        return self.get("theme", default={})
    
    @property
    def message_styles(self) -> Dict[str, Any]:
        """获取消息样式 / Get message styles"""
        return self.get("message", default={})
    
    @property
    def code_block(self) -> Dict[str, Any]:
        """获取代码块样式 / Get code block styles"""
        return self.get("code_block", default={})
    
    @property
    def progress(self) -> Dict[str, Any]:
        """获取进度条样式 / Get progress bar styles"""
        return self.get("progress", default={})
    
    @property
    def table(self) -> Dict[str, Any]:
        """获取表格样式 / Get table styles"""
        return self.get("table", default={})
    
    @property
    def deprecated_restored(self) -> Dict[str, Any]:
        """获取弃用恢复样式 / Get deprecated restored styles"""
        return self.get("deprecated_restored", default={})
    
    def get_message_style(self, role: str) -> Dict[str, Any]:
        """
        获取指定角色的消息样式 / Get message style for role
        
        Args:
            role: 角色（user, assistant, system等）/ Role
        
        Returns:
            消息样式 / Message style
        """
        return self.get("message", role, default={
            "prefix": "",
            "style": "default",
        })


def get_style_config() -> StyleConfig:
    """获取样式配置单例 / Get style config singleton"""
    return StyleConfig()


def format_message_prefix(role: str) -> str:
    """
    格式化消息前缀 / Format message prefix
    
    Args:
        role: 角色 / Role
    
    Returns:
        带样式的前缀 / Styled prefix
    """
    config = get_style_config()
    style = config.get_message_style(role)
    prefix = style.get("prefix", "")
    
    deprecated = config.deprecated_restored
    if deprecated.get("no_icon_message", False):
        return ""
    
    return prefix


def get_output_format_config(format_name: str) -> Dict[str, Any]:
    """
    获取输出格式配置 / Get output format config
    
    Args:
        format_name: 格式名称 / Format name
    
    Returns:
        格式配置 / Format config
    """
    config = get_style_config()
    return config.get("output_formats", format_name, default={})
