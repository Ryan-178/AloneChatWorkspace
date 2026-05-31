"""
统一错误处理和结构化日志 - Unified Error Handling & Structured Logging
統一錯誤處理和結構化日誌

提供标准化的异常类、错误响应格式和结构化日志记录
Provides standardized exception classes, error response formats, and structured logging

设计原则 / Design Principles:
- 错误分类清晰 (Clear error categorization)
- 上下文信息丰富 (Rich context information)
- 可追踪性 (Traceability)
- 国际化支持 (i18n support)

参考实现 / Reference implementations:
- RFC 7807 (Problem Details for HTTP APIs)
- Google Cloud Error Reporting
- Sentry error tracking
"""
import sys
import traceback
import logging
import json
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps
import asyncio


# ============================================================================
# 错误码枚举 - Error Code Enumeration / 錯誤碼枚舉
# ============================================================================

class ErrorCode(Enum):
    """
    错误码枚举 - Error Code Enumeration / 錯誤碼枚舉
    定义所有业务和技术错误的标准化代码
    Defines standardized codes for all business and technical errors

    格式规范 / Format specification:
    - MODULE_CATEGORY_SPECIFIC_ERROR
    - 示例: AUTH_LOGIN_001, API_RATE_LIMIT_001
    """

    # 认证和授权错误 - Authentication & Authorization Errors
    AUTH_INVALID_CREDENTIALS = ("AUTH", "AUTH_INVALID_CREDENTIALS", 401)
    AUTH_TOKEN_EXPIRED = ("AUTH", "AUTH_TOKEN_EXPIRED", 401)
    AUTH_TOKEN_INVALID = ("AUTH", "AUTH_TOKEN_INVALID", 401)
    AUTH_TOKEN_REVOKED = ("AUTH", "AUTH_TOKEN_REVOKED", 401)
    AUTH_SESSION_NOT_FOUND = ("AUTH", "AUTH_SESSION_NOT_FOUND", 404)
    AUTH_ACCOUNT_LOCKED = ("AUTH", "AUTH_ACCOUNT_LOCKED", 423)
    AUTH_PERMISSION_DENIED = ("AUTH", "AUTH_PERMISSION_DENIED", 403)
    AUTH_MFA_REQUIRED = ("AUTH", "AUTH_MFA_REQUIRED", 403)
    AUTH_PASSWORD_WEAK = ("AUTH", "AUTH_PASSWORD_WEAK", 400)
    AUTH_USER_NOT_FOUND = ("AUTH", "AUTH_USER_NOT_FOUND", 404)
    AUTH_USER_EXISTS = ("AUTH", "AUTH_USER_EXISTS", 409)
    AUTH_EMAIL_EXISTS = ("AUTH", "AUTH_EMAIL_EXISTS", 409)

    # 输入验证错误 - Input Validation Errors
    VALIDATION_REQUIRED_FIELD = ("VAL", "VALIDATION_REQUIRED_FIELD", 400)
    VALIDATION_INVALID_TYPE = ("VAL", "VALIDATION_INVALID_TYPE", 400)
    VALIDATION_TOO_SHORT = ("VAL", "VALIDATION_TOO_SHORT", 400)
    VALIDATION_TOO_LONG = ("VAL", "VALIDATION_TOO_LONG", 400)
    VALIDATION_INVALID_FORMAT = ("VAL", "VALIDATION_INVALID_FORMAT", 400)
    VALIDATION_INVALID_VALUE = ("VAL", "VALIDATION_INVALID_VALUE", 400)
    VALIDATION_SQL_INJECTION = ("VAL", "VALIDATION_SQL_INJECTION", 400)
    VALIDATION_COMMAND_INJECTION = ("VAL", "VALIDATION_COMMAND_INJECTION", 400)
    VALIDATION_XSS_DETECTED = ("VAL", "VALIDATION_XSS_DETECTED", 400)

    # 资源错误 - Resource Errors
    RESOURCE_NOT_FOUND = ("RES", "RESOURCE_NOT_FOUND", 404)
    RESOURCE_ALREADY_EXISTS = ("RES", "RESOURCE_ALREADY_EXISTS", 409)
    RESOURCE_CONFLICT = ("RES", "RESOURCE_CONFLICT", 409)
    RESOURCE_DELETED = ("RES", "RESOURCE_DELETED", 410)
    RESOURCE_FORBIDDEN = ("RES", "RESOURCE_FORBIDDEN", 403)

    # 业务逻辑错误 - Business Logic Errors
    BIZ_TASK_FAILED = ("BIZ", "BIZ_TASK_FAILED", 500)
    BIZ_OPERATION_TIMEOUT = ("BIZ", "BIZ_OPERATION_TIMEOUT", 504)
    BIZ_QUOTA_EXCEEDED = ("BIZ", "BIZ_QUOTA_EXCEEDED", 429)
    BIZ_INVALID_STATE = ("BIZ", "BIZ_INVALID_STATE", 400)
    BIZ_DEPENDENCY_FAILED = ("BIZ", "BIZ_DEPENDENCY_FAILED", 424)

    # 系统错误 - System Errors
    SYS_INTERNAL_ERROR = ("SYS", "SYS_INTERNAL_ERROR", 500)
    SYS_DATABASE_ERROR = ("SYS", "SYS_DATABASE_ERROR", 503)
    SYS_SERVICE_UNAVAILABLE = ("SYS", "SYS_SERVICE_UNAVAILABLE", 503)
    SYS_CONFIGURATION_ERROR = ("SYS", "SYS_CONFIGURATION_ERROR", 500)
    SYS_DEPENDENCY_FAILURE = ("SYS", "SYS_DEPENDENCY_FAILURE", 502)
    SYS_RATE_LIMIT_EXCEEDED = ("SYS", "SYS_RATE_LIMIT_EXCEEDED", 429)

    # 外部服务错误 - External Service Errors
    EXT_LLM_ERROR = ("EXT", "EXT_LLM_ERROR", 502)
    EXT_NETWORK_ERROR = ("EXT", "EXT_NETWORK_ERROR", 502)
    EXT_API_ERROR = ("EXT", "EXT_API_ERROR", 502)
    EXT_TIMEOUT = ("EXT", "EXT_TIMEOUT", 504)


# ============================================================================
# 自定义异常类 - Custom Exception Classes / 自定義異常類
# ============================================================================

class BaseAppError(Exception):
    """
    应用基础异常 - Base Application Exception / 應用基礎異常
    所有业务异常的基类
    Base class for all business exceptions

    Attributes:
        code: 错误码 / Error code
        message: 用户友好的消息 / User-friendly message
        details: 详细信息（可能包含技术细节） / Details (may contain technical info)
        http_status: HTTP状态码 / HTTP status code
        context: 上下文数据 / Context data
        cause: 原始异常 / Original exception
        request_id: 关联的请求ID / Associated request ID
        timestamp: 发生时间 / Occurrence time
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SYS_INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        http_status: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = http_status or code.value[2]
        self.context = context or {}
        self.cause = cause
        self.request_id = request_id or ""
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - Convert to dictionary / 轉換為字典"""
        return {
            "error": {
                "code": f"{self.code.value[0]}_{self.code.value[1]}",
                "message": self.message,
                "details": self.details,
            },
            "http_status": self.http_status,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }

    def to_response_dict(self) -> Dict[str, Any]:
        """转换为API响应格式 - Convert to API response format / 轉換為API響應格式"""
        return {
            "success": False,
            "error": {
                "code": f"{self.code.value[0]}_{self.code.value[1]}",
                "message": self.message,
                "details": self.details if _is_debug_mode() else {},
            },
            "request_id": self.request_id,
        }


class ValidationError(BaseAppError):
    """验证错误 - Validation Error / 驗證錯誤"""

    def __init__(
        self,
        message: str,
        field: str = "",
        value: Any = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            details={"field": field, "value": str(value)[:100]},
            **kwargs
        )
        self.field = field
        self.value = value


class AuthenticationError(BaseAppError):
    """认证错误 - Authentication Error / 認證錯誤"""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            **kwargs
        )


class AuthorizationError(BaseAppError):
    """授权错误 - Authorization Error / 授權錯誤"""

    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.AUTH_PERMISSION_DENIED,
            **kwargs
        )


class NotFoundError(BaseAppError):
    """资源未找到错误 - Not Found Error / 資源未找到錯誤"""

    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: str = "",
        **kwargs
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs
        )


class ConflictError(BaseAppError):
    """冲突错误 - Conflict Error / 衝突錯誤"""

    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_CONFLICT,
            http_status=409,
            **kwargs
        )


class RateLimitExceededError(BaseAppError):
    """速率限制错误 - Rate Limit Exceeded Error / 速率限制錯誤"""

    def __init__(
        self,
        retry_after_seconds: float = 60.0,
        limit_type: str = "global",
        **kwargs
    ):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after_seconds:.0f}s",
            code=ErrorCode.SYS_RATE_LIMIT_EXCEEDED,
            http_status=429,
            details={
                "retry_after_seconds": retry_after_seconds,
                "limit_type": limit_type,
            },
            **kwargs
        )
        self.retry_after = retry_after_seconds


class ExternalServiceError(BaseAppError):
    """外部服务错误 - External Service Error / 外部服務錯誤"""

    def __init__(
        self,
        service_name: str,
        original_error: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=f"{service_name} service error",
            code=ErrorCode.EXT_API_ERROR,
            details={"service": service_name, "original_error": original_error},
            **kwargs
        )


# ============================================================================
# 结构化日志 - Structured Logging / 結構化日誌
# ============================================================================

class StructuredLogger:
    """
    结构化日志记录器 - Structured Logger / 結構化日誌記錄器
    提供JSON格式的结构化日志输出
    Provides JSON-formatted structured log output

    特性 / Features:
    - JSON格式输出 (JSON format output)
    - 上下文自动附加 (Automatic context attachment)
    - 性能指标记录 (Performance metrics recording)
    - 敏感数据过滤 (Sensitive data filtering)
    - 多级别支持 (Multi-level support)

    使用示例 / Usage example:
    ```python
    logger = StructuredLogger("my_module")

    logger.info("User login successful", user_id="123", ip="192.168.1.1")
    logger.error("Database connection failed", error=str(e), db_host="localhost")
    ```
    """

    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # 敏感字段列表（会被脱敏） - Sensitive fields list (will be masked)
    SENSITIVE_FIELDS = {
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "authorization", "cookie", "credit_card", "ssn", "social_security",
    }

    def __init__(
        self,
        name: str = "alonechat",
        level: str = "INFO",
        output_format: str = "json",  # json or text
        include_timestamp: bool = True,
        include_source: bool = True,
    ):
        """
        初始化结构化日志 - Initialize structured logger

        Args:
            name: 日志器名称 / Logger name
            level: 默认日志级别 / Default log level
            output_format: 输出格式 (json/text) / Output format
            include_timestamp: 是否包含时间戳 / Include timestamp
            include_source: 是否包含源码位置 / Include source location
        """
        self.name = name
        self.output_format = output_format.lower()
        self.include_timestamp = include_timestamp
        self.include_source = include_source

        # 创建Python logger - Create Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))

        # 避免重复处理器 - Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # 全局上下文 - Global context
        self._context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """设置全局上下文 - Set global context / 設置全局上下文"""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """清除全局上下文 - Clear global context / 清除全局上下文"""
        self._context.clear()

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        脱敏敏感数据 - Mask sensitive data / 脫敏感感數據

        Args:
            data: 原始数据字典 / Original data dictionary

        Returns:
            脱敏后的字典 / Masked dictionary
        """
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = value[:2] + "***" + value[-2:]
                else:
                    masked[key] = "***MASKED***"
            else:
                masked[key] = value
        return masked

    def _format_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> str:
        """
        格式化日志条目 - Format log entry / 格式化日誌條目

        Args:
            level: 日志级别 / Log level
            message: 日志消息 / Log message
            **kwargs: 附加字段 / Additional fields

        Returns:
            格式化后的字符串 / Formatted string
        """
        entry: Dict[str, Any] = {
            "level": level,
            "logger": self.name,
            "message": message,
        }

        if self.include_timestamp:
            entry["timestamp"] = datetime.utcnow().isoformat()

        if self.include_source:
            # 获取调用者信息 - Get caller info
            frame = sys._getframe(3)  # Skip _format_log_entry, debug/info/etc, wrapper
            entry["source"] = {
                "file": frame.f_code.co_filename.split("/")[-1],
                "line": frame.f_lineno,
                "function": frame.f_code.co_name,
            }

        # 合并上下文和参数 - Merge context and kwargs
        entry.update(self._context)
        entry.update(kwargs)

        # 脱敏敏感数据 - Mask sensitive data
        entry = self._mask_sensitive_data(entry)

        if self.output_format == "json":
            return json.dumps(entry, ensure_ascii=False, default=str)
        else:
            # 文本格式 - Text format
            parts = [f"[{entry.get('timestamp', '')}]"] if self.include_timestamp else []
            parts.append(f"[{level}]")
            parts.append(message)
            for k, v in kwargs.items():
                parts.append(f"{k}={v}")
            return " ".join(parts)

    def debug(self, message: str, **kwargs) -> None:
        """调试级别 - Debug level / 調試級別"""
        entry = self._format_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(entry)

    def info(self, message: str, **kwargs) -> None:
        """信息级别 - Info level / 信息級別"""
        entry = self._format_log_entry("INFO", message, **kwargs)
        self.logger.info(entry)

    def warning(self, message: str, **kwargs) -> None:
        """警告级别 - Warning level / 警告級別"""
        entry = self._format_log_entry("WARNING", message, **kwargs)
        self.logger.warning(entry)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """错误级别 - Error level / 錯誤級別"""
        if exc_info:
            kwargs["exception"] = traceback.format_exc()
        entry = self._format_log_entry("ERROR", message, **kwargs)
        self.logger.error(entry)

    def critical(self, message: str, **kwargs) -> None:
        """严重级别 - Critical level / 嚴重級別"""
        entry = self._format_log_entry("CRITICAL", message, **kwargs)
        self.logger.critical(entry)

    def exception(self, message: str, **kwargs) -> None:
        """异常级别（自动包含traceback） - Exception level (auto includes traceback)"""
        kwargs["exception"] = traceback.format_exc()
        entry = self._format_log_entry("ERROR", message, **kwargs)
        self.logger.error(entry)

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        记录API请求 - Log API request / 記錄API請求

        Args:
            method: HTTP方法 / HTTP method
            path: 请求路径 / Request path
            status_code: 响应状态码 / Response status code
            duration_ms: 处理时长（毫秒） / Processing duration (ms)
            client_ip: 客户端IP / Client IP
            user_id: 用户ID / User ID
        """
        self.info(
            "API Request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=client_ip,
            user_id=user_id,
            **kwargs
        )

    def log_error_with_context(
        self,
        error: Union[BaseAppError, Exception],
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        带上下文的错误日志 - Error logging with context / 帶上下文的錯誤日誌

        Args:
            error: 异常对象 / Exception object
            context: 额外上下文 / Additional context
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if isinstance(error, BaseAppError):
            error_data["error_code"] = f"{error.code.value[0]}_{error.code.value[1]}"
            error_data["request_id"] = error.request_id
            error_data["details"] = error.details
            if error.cause:
                error_data["cause"] = str(error.cause)

        if context:
            error_data.update(context)

        error_data.update(kwargs)

        self.error(
            "Application error occurred",
            exc_info=True,
            **error_data
        )

    def measure_time(self, operation: str):
        """
        性能测量装饰器/上下文管理器 - Performance measurement decorator/context manager
        用于测量代码块执行时间
        Used to measure execution time of code blocks

        用法示例 / Usage example:
        ```python
        with logger.measure_time("database_query"):
            result = db.execute(query)

        @logger.measure_time("expensive_function")
        def my_function():
            ...
        ```

        Args:
            operation: 操作名称 / Operation name

        Returns:
            上下文管理器或装饰器 / Context manager or decorator
        """
        class TimeContextManager:
            def __init__(self, op, logger_instance):
                self.op = op
                self.logger = logger_instance
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = (time.time() - self.start_time) * 1000
                self.logger.info(
                    f"{self.op} completed",
                    operation=self.op,
                    duration_ms=round(duration, 2),
                    success=exc_type is None
                )
                return False

        return TimeContextManager(operation, self)


# ============================================================================
# 全局实例和工具函数 - Global Instances & Utility Functions / 全局實例和工具函數
# ============================================================================

def _is_debug_mode() -> bool:
    """检查是否为调试模式 - Check if debug mode / 檢查是否為調試模式"""
    import os
    return os.getenv("DEBUG", "").lower() in ("true", "1", "yes")


# 默认日志器实例 - Default logger instance
_default_logger = StructuredLogger("alonechat")


def get_logger(name: str = "alonechat") -> StructuredLogger:
    """
    获取日志器实例 - Get logger instance / 獲取日誌器實例

    Args:
        name: 日志器名称 / Logger name

    Returns:
        结构化日志器 / Structured logger
    """
    if name == "alonechat":
        return _default_logger
    return StructuredLogger(name)


def handle_exception(
    exc: Exception,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False,
) -> BaseAppError:
    """
    统一异常处理 - Unified exception handling / 統一異常處理
    将任意异常转换为标准的BaseAppError
    Converts arbitrary exceptions to standard BaseAppError

    Args:
        exc: 原始异常 / Original exception
        request_id: 请求ID / Request ID
        context: 额外上下文 / Additional context
        reraise: 是否重新抛出 / Whether to re-raise

    Returns:
        标准化的应用异常 / Standardized application exception
    """
    logger = get_logger()

    if isinstance(exc, BaseAppError):
        app_error = exc
    elif isinstance(exc, ValueError):
        app_error = ValidationError(str(exc), **(context or {}))
    elif isinstance(exc, KeyError):
        app_error = NotFoundError(
            resource_type="Field",
            resource_id=str(exc),
            **(context or {})
        )
    elif isinstance(exc, PermissionError):
        app_error = AuthorizationError(str(exc), **(context or {}))
    else:
        app_error = BaseAppError(
            message="An unexpected error occurred / 发生意外错误",
            code=ErrorCode.SYS_INTERNAL_ERROR,
            details={"original_error": type(exc).__name__, "message": str(exc)},
            cause=exc,
            request_id=request_id,
        )

    # 记录错误日志 - Log error
    logger.log_error_with_context(app_error, context=context)

    if reraise:
        raise app_error

    return app_error


def async_exception_handler(func):
    """
    异步函数异常处理装饰器 - Async function exception handler decorator
    自动捕获并转换异步函数中的异常
    Automatically catches and converts exceptions in async functions

    用法 / Usage:
    ```python
    @async_exception_handler
    async def my_async_function():
        ...
    ```
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseAppError:
            raise
        except Exception as e:
            raise handle_exception(e)
    return wrapper


def sync_exception_handler(func):
    """
    同步函数异常处理装饰器 - Sync function exception handler decorator
    自动捕获并转换同步函数中的异常
    Automatically catches and converts exceptions in sync functions

    用法 / Usage:
    ```python
    @sync_exception_handler
    def my_sync_function():
        ...
    ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseAppError:
            raise
        except Exception as e:
            raise handle_exception(e)
    return wrapper


# 导入time模块（用于性能测量）
import time
