"""
日志系统模块 / Log System Module

提供 / Provides:
- 结构化日志 / Structured logging
- 日志级别控制 / Log level control
- 文件输出 / File output
- 终端美化输出 / Terminal beautified output
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

from alonechat.configs import config


class LogLevel(Enum):
    """日志级别枚举 / Log Level Enum"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogConfig:
    """日志配置 / Log Configuration"""
    level: LogLevel = LogLevel.INFO
    file_path: Optional[Path] = None
    console_output: bool = True
    rich_format: bool = True
    show_timestamp: bool = True
    show_module: bool = False


class AloneChatLogger:
    """
    AloneChat日志器 / AloneChat Logger
    
    单例模式的日志管理器 / Singleton pattern log manager
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
        """添加文件处理器 / Add file handler"""
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
        """输出成功消息 / Output success message"""
        symbol = config.get("log.messages.success_symbol", "✓")
        self.console.print(f"[bold green]{symbol}[/bold green] {message}")
    
    def fail(self, message: str) -> None:
        """输出失败消息 / Output failure message"""
        symbol = config.get("log.messages.fail_symbol", "✗")
        self.console.print(f"[bold red]{symbol}[/bold red] {message}")
    
    def step(self, step_num: int, total: int, message: str) -> None:
        """输出步骤消息 / Output step message"""
        self.console.print(
            f"[bold cyan][{step_num}/{total}][/bold cyan] {message}"
        )
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别 / Set log level"""
        self.log_config.level = level
        self._logger.setLevel(level.value)
    
    @classmethod
    def get_instance(cls) -> "AloneChatLogger":
        """获取单例实例 / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_logger(
    level: LogLevel = LogLevel.INFO,
    file_path: Optional[Path] = None,
) -> AloneChatLogger:
    """获取日志器实例 / Get logger instance"""
    log_config = LogConfig(level=level, file_path=file_path)
    return AloneChatLogger(log_config)


logger = AloneChatLogger.get_instance()
