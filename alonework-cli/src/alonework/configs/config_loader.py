"""
閰嶇疆鍔犺浇妯″潡 / Configuration Loader Module
鍔犺浇YAML閰嶇疆鏂囦欢锛岄伩鍏嶇‖缂栫爜 / Load YAML config files to avoid hardcoding
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """閰嶇疆鍔犺浇鍣?/ Configuration Loader"""
    
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
        """鍔犺浇閰嶇疆鏂囦欢 / Load configuration file"""
        config_path = Path(__file__).parent / "utils_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """鑾峰彇榛樿閰嶇疆 / Get default configuration"""
        return {
            "progress": {
                "messages": {
                    "default_status": "鐢熸垚涓?,
                    "default_description": "澶勭悊涓?,
                    "task_summary_title": "浠诲姟鎽樿",
                    "total_label": "鎬昏",
                    "completed_label": "瀹屾垚",
                    "failed_label": "澶辫触",
                    "skipped_label": "璺宠繃",
                },
                "streaming": {
                    "buffer_display_size": 50,
                    "spinner_type": "dots",
                },
            },
            "log": {
                "messages": {
                    "success_symbol": "鉁?,
                    "fail_symbol": "鉁?,
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
                    "usage_label": "鐢ㄦ硶",
                    "example_label": "绀轰緥",
                    "command_help_title": "鍛戒护甯姪",
                    "available_commands_title": "鍙敤鍛戒护",
                    "command_column": "鍛戒护",
                    "description_column": "鎻忚堪",
                    "alias_column": "鍒悕",
                    "not_found_message": "鏈壘鍒板懡浠?,
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
        鑾峰彇閰嶇疆鍊?/ Get configuration value
        
        Args:
            key: 閰嶇疆閿紝鏀寔鐐瑰垎闅旂 / Config key, supports dot notation
            default: 榛樿鍊?/ Default value
            
        Returns:
            閰嶇疆鍊?/ Configuration value
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
        """鑾峰彇杩涘害娑堟伅閰嶇疆 / Get progress messages config"""
        return self.get("progress.messages", {})
    
    def get_log_messages(self) -> Dict[str, str]:
        """鑾峰彇鏃ュ織娑堟伅閰嶇疆 / Get log messages config"""
        return self.get("log.messages", {})
    
    def get_command_messages(self) -> Dict[str, str]:
        """鑾峰彇鍛戒护娑堟伅閰嶇疆 / Get command messages config"""
        return self.get("commands.messages", {})
    
    def get_default_commands(self) -> Dict[str, Dict]:
        """鑾峰彇榛樿鍛戒护閰嶇疆 / Get default commands config"""
        return self.get("commands.defaults", {})
    
    def get_history_config(self) -> Dict[str, Any]:
        """鑾峰彇鍘嗗彶璁板綍閰嶇疆 / Get history config"""
        return self.get("history", {})
    
    def get_autocompleter_config(self) -> Dict[str, int]:
        """鑾峰彇鑷姩琛ュ叏閰嶇疆 / Get autocompleter config"""
        return self.get("autocompleter", {})
    
    def get_ui_styles(self) -> Dict[str, str]:
        """鑾峰彇UI鏍峰紡閰嶇疆 / Get UI styles config"""
        return self.get("ui.styles", {})
    
    @classmethod
    def get_instance(cls) -> "ConfigLoader":
        """鑾峰彇鍗曚緥瀹炰緥 / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


config = ConfigLoader.get_instance()
