"""
结构化日志模块 - Structured Logging
支持JSON格式日志、分级日志、日志上下文
"""
import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加上下文
        if hasattr(record, "context") and record.context:
            log_obj["context"] = record.context
        
        # 添加异常信息
        if record.exc_info and self.include_traceback:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""
    
    COLORS = {
        LogLevel.DEBUG: "\033[36m",    # Cyan
        LogLevel.INFO: "\033[32m",     # Green
        LogLevel.WARNING: "\033[33m",  # Yellow
        LogLevel.ERROR: "\033[31m",    # Red
        LogLevel.CRITICAL: "\033[35m"  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        log_line = f"{color}[{timestamp}] [{record.levelname}] [{record.name}]{self.RESET} {record.getMessage()}"
        
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


_loggers: Dict[str, logging.Logger] = {}


def get_logger(
    name: str,
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[Path] = None,
    structured: bool = False
) -> logging.Logger:
    """获取或创建logger"""
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.value))
    logger.propagate = False
    
    # 清除已有的handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredLogFormatter())
    else:
        console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)
    
    # 文件handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(StructuredLogFormatter())
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def log_with_context(
    logger: logging.Logger,
    level: LogLevel,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **extra_fields
):
    """带上下文记录日志"""
    log_level = getattr(logging, level.value)
    extra = {
        "context": context or {},
        "extra_fields": extra_fields
    }
    logger.log(log_level, message, extra=extra)


def set_global_level(level: LogLevel):
    """设置全局日志级别"""
    for logger in _loggers.values():
        logger.setLevel(getattr(logging, level.value))
