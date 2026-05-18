"""
配置加载模块 / Configuration Loader Module
加载YAML配置文件，避免硬编码 / Load YAML config files to avoid hardcoding
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """配置加载器 / Configuration Loader"""
    
    _instance: Optional["ConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件 / Load configuration file"""
        config_path = Path(__file__).parent / "utils_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置 / Get default configuration"""
        return {
            "progress": {
                "messages": {
                    "default_status": "生成中",
                    "default_description": "处理中",
                    "task_summary_title": "任务摘要",
                    "total_label": "总计",
                    "completed_label": "完成",
                    "failed_label": "失败",
                    "skipped_label": "跳过",
                },
                "streaming": {
                    "buffer_display_size": 50,
                    "spinner_type": "dots",
                },
            },
            "log": {
                "messages": {
                    "success_symbol": "✓",
                    "fail_symbol": "✗",
                },
                "format": {
                    "file_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "logger_name": "alonechat",
                },
                "default_level": "INFO",
            },
            "commands": {
                "prefix": "/",
                "messages": {
                    "usage_label": "用法",
                    "example_label": "示例",
                    "command_help_title": "命令帮助",
                    "available_commands_title": "可用命令",
                    "command_column": "命令",
                    "description_column": "描述",
                    "alias_column": "别名",
                    "not_found_message": "未找到命令",
                },
                "defaults": {},
            },
            "history": {
                "default_max_size": 100,
                "history_dir": ".alonechat",
                "history_file": "history.json",
            },
            "autocompleter": {
                "min_partial_length": 3,
                "max_context_size": 100,
                "max_suggestions": 10,
                "max_matches_per_context": 3,
            },
            "ui": {
                "styles": {
                    "cyan": "cyan",
                    "green": "green",
                    "red": "red",
                    "yellow": "yellow",
                    "blue": "blue",
                    "dim": "dim",
                    "bold": "bold",
                },
            },
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值 / Get configuration value
        
        Args:
            key: 配置键，支持点分隔符 / Config key, supports dot notation
            default: 默认值 / Default value
            
        Returns:
            配置值 / Configuration value
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_progress_messages(self) -> Dict[str, str]:
        """获取进度消息配置 / Get progress messages config"""
        return self.get("progress.messages", {})
    
    def get_log_messages(self) -> Dict[str, str]:
        """获取日志消息配置 / Get log messages config"""
        return self.get("log.messages", {})
    
    def get_command_messages(self) -> Dict[str, str]:
        """获取命令消息配置 / Get command messages config"""
        return self.get("commands.messages", {})
    
    def get_default_commands(self) -> Dict[str, Dict]:
        """获取默认命令配置 / Get default commands config"""
        return self.get("commands.defaults", {})
    
    def get_history_config(self) -> Dict[str, Any]:
        """获取历史记录配置 / Get history config"""
        return self.get("history", {})
    
    def get_autocompleter_config(self) -> Dict[str, int]:
        """获取自动补全配置 / Get autocompleter config"""
        return self.get("autocompleter", {})
    
    def get_ui_styles(self) -> Dict[str, str]:
        """获取UI样式配置 / Get UI styles config"""
        return self.get("ui.styles", {})
    
    @classmethod
    def get_instance(cls) -> "ConfigLoader":
        """获取单例实例 / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


config = ConfigLoader.get_instance()
