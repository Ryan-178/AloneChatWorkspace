"""
è¾åºæ ·å¼éç½®å è½½å?/ Output Style Config Loader

ä»YAMLæä»¶å è½½è¾åºæ ·å¼éç½® / Load output style configuration from YAML file

çæ¬ / Version: 2.0.32
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class StyleConfig:
    """
    æ ·å¼éç½® / Style Config
    
    æä¾è¾åºæ ·å¼éç½®çè®¿é?/ Provides access to output style configuration
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """å è½½YAMLéç½® / Load YAML config"""
        config_path = Path(__file__).parent / "output_style.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
    
    def reload(self) -> None:
        """éæ°å è½½éç½® / Reload config"""
        self._load_config()
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        è·åéç½®å?/ Get config value
        
        Args:
            *keys: éç½®é®è·¯å¾?/ Config key path
            default: é»è®¤å?/ Default value
        
        Returns:
            éç½®å?/ Config value
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
        """è·åä¸»é¢éç½® / Get theme config"""
        return self.get("theme", default={})
    
    @property
    def message_styles(self) -> Dict[str, Any]:
        """è·åæ¶æ¯æ ·å¼ / Get message styles"""
        return self.get("message", default={})
    
    @property
    def code_block(self) -> Dict[str, Any]:
        """è·åä»£ç åæ ·å¼?/ Get code block styles"""
        return self.get("code_block", default={})
    
    @property
    def progress(self) -> Dict[str, Any]:
        """è·åè¿åº¦æ¡æ ·å¼?/ Get progress bar styles"""
        return self.get("progress", default={})
    
    @property
    def table(self) -> Dict[str, Any]:
        """è·åè¡¨æ ¼æ ·å¼ / Get table styles"""
        return self.get("table", default={})
    
    @property
    def deprecated_restored(self) -> Dict[str, Any]:
        """è·åå¼ç¨æ¢å¤æ ·å¼ / Get deprecated restored styles"""
        return self.get("deprecated_restored", default={})
    
    def get_message_style(self, role: str) -> Dict[str, Any]:
        """
        è·åæå®è§è²çæ¶æ¯æ ·å¼?/ Get message style for role
        
        Args:
            role: è§è²ï¼user, assistant, systemç­ï¼/ Role
        
        Returns:
            æ¶æ¯æ ·å¼ / Message style
        """
        return self.get("message", role, default={
            "prefix": "",
            "style": "default",
        })


def get_style_config() -> StyleConfig:
    """è·åæ ·å¼éç½®åä¾ / Get style config singleton"""
    return StyleConfig()


def format_message_prefix(role: str) -> str:
    """
    æ ¼å¼åæ¶æ¯åç¼ / Format message prefix
    
    Args:
        role: è§è² / Role
    
    Returns:
        å¸¦æ ·å¼çåç¼ / Styled prefix
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
    è·åè¾åºæ ¼å¼éç½® / Get output format config
    
    Args:
        format_name: æ ¼å¼åç§° / Format name
    
    Returns:
        æ ¼å¼éç½® / Format config
    """
    config = get_style_config()
    return config.get("output_formats", format_name, default={})
