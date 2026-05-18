"""
鏃ュ織绯荤粺妯″潡 / Log System Module

鎻愪緵 / Provides:
- 缁撴瀯鍖栨棩蹇?/ Structured logging
- 鏃ュ織绾у埆鎺у埗 / Log level control
- 鏂囦欢杈撳嚭 / File output
- 缁堢缇庡寲杈撳嚭 / Terminal beautified output
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from alonework.configs import config


class LogLevel(Enum):
    """鏃ュ織绾у埆鏋氫妇 / Log Level Enum"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogConfig:
    """鏃ュ織閰嶇疆 / Log Configuration"""
    level: LogLevel = LogLevel.INFO
    file_path: Optional[Path] = None
    console_output: bool = True
    rich_format: bool = True
    show_timestamp: bool = True
    show_module: bool = False


class AloneChatLogger:
    """
    AloneChat鏃ュ織鍣?/ AloneChat Logger
    
    鍗曚緥妯″紡鐨勬棩蹇楃鐞嗗櫒 / Singleton pattern log manager
    """
    
    _instance: Optional["AloneChatLogger"] = None
    
    def __new__(cls, log_config: Optional[LogConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_config: Optional[LogConfig] = None):
        if self._initialized:
            return
        
        self._initialized = True
        self.log_config = log_config or LogConfig()
        self.console = Console()
        
        logger_name = config.get("log.format.logger_name", "alonechat")
        self._logger = logging.getLogger(logger_name)
        
        default_level = config.get("log.default_level", "INFO")
        self._logger.setLevel(getattr(LogLevel, default_level, LogLevel.INFO).value)
        self._logger.handlers.clear()
        
        if self.log_config.rich_format and self.log_config.console_output:
            rich_handler = RichHandler(
                console=self.console,
                show_time=self.log_config.show_timestamp,
                show_path=self.log_config.show_module,
                rich_tracebacks=True,
            )
            self._logger.addHandler(rich_handler)
        
        if self.log_config.file_path:
            self._add_file_handler(self.log_config.file_path)
    
    def _add_file_handler(self, path: Path) -> None:
        """娣诲姞鏂囦欢澶勭悊鍣?/ Add file handler"""
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_format = config.get("log.format.file_format", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(logging.Formatter(file_format))
        self._logger.addHandler(file_handler)
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(message, *args, **kwargs)
    
    def success(self, message: str) -> None:
        """杈撳嚭鎴愬姛娑堟伅 / Output success message"""
        symbol = config.get("log.messages.success_symbol", "鉁?)
        self.console.print(f"[bold green]{symbol}[/bold green] {message}")
    
    def fail(self, message: str) -> None:
        """杈撳嚭澶辫触娑堟伅 / Output failure message"""
        symbol = config.get("log.messages.fail_symbol", "鉁?)
        self.console.print(f"[bold red]{symbol}[/bold red] {message}")
    
    def step(self, step_num: int, total: int, message: str) -> None:
        """杈撳嚭姝ラ娑堟伅 / Output step message"""
        self.console.print(
            f"[bold cyan][{step_num}/{total}][/bold cyan] {message}"
        )
    
    def set_level(self, level: LogLevel) -> None:
        """璁剧疆鏃ュ織绾у埆 / Set log level"""
        self.log_config.level = level
        self._logger.setLevel(level.value)
    
    @classmethod
    def get_instance(cls) -> "AloneChatLogger":
        """鑾峰彇鍗曚緥瀹炰緥 / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_logger(
    level: LogLevel = LogLevel.INFO,
    file_path: Optional[Path] = None,
) -> AloneChatLogger:
    """鑾峰彇鏃ュ織鍣ㄥ疄渚?/ Get logger instance"""
    log_config = LogConfig(level=level, file_path=file_path)
    return AloneChatLogger(log_config)


logger = AloneChatLogger.get_instance()
