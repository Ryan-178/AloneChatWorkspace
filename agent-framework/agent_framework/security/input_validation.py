"""
安全中间件和输入验证 - Security Middleware & Input Validation / 安全中間件和輸入驗證
防止SQL注入、XSS、命令注入等攻击
Prevents SQL injection, XSS, command injection, and other attacks

安全层架构 / Security Layer Architecture:
1. 输入验证 (Input Validation) - 验证所有外部输入
2. 输出编码 (Output Encoding) - 安全地输出数据
3. 速率限制 (Rate Limiting) - 防止滥用
4. CSRF保护 (CSRF Protection) - 跨站请求伪造防护
5. 安全头 (Security Headers) - HTTP安全响应头

参考标准 / Reference Standards:
- OWASP ASVS (Application Security Verification Standard)
- OWASP Proactive Controls
- CWE/SANS Top 25 Most Dangerous Software Errors
"""
import re
import html
import json
import time
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union, Pattern
from dataclasses import dataclass, field
from functools import wraps
from enum import Enum

try:
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


# ============================================================================
# 输入验证器 - Input Validator / 輸入驗證器
# ============================================================================

class ValidationError(Exception):
    """验证错误 - Validation Error / 驗證錯誤"""
    def __init__(self, message: str, field: str = "", code: str = "INVALID_INPUT"):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


@dataclass
class ValidationRule:
    """
    验证规则 - Validation Rule / 驗證規則
    定义字段的验证约束
    Defines validation constraints for a field

    Attributes:
        field_name: 字段名 / Field name
        required: 是否必需 / Whether required
        min_length: 最小长度 / Min length
        max_length: 最大长度 / Max length
        pattern: 正则表达式模式 / Regex pattern
        allowed_values: 允许的值列表 / List of allowed values
        custom_validator: 自定义验证函数 / Custom validator function
    """
    field_name: str = ""
    required: bool = False
    min_length: int = 0
    max_length: int = 10000
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None
    error_message: str = ""


class InputValidator:
    """
    输入验证器 - Input Validator / 輸入驗證器
    提供全面的输入验证功能
    Provides comprehensive input validation capabilities

    使用示例 / Usage example:
    ```python
    validator = InputValidator()

    # 简单验证
    validator.validate_string("username", "john_doe", required=True, min_length=3)

    # 批量验证
    rules = [
        ValidationRule("username", required=True, min_length=3, max_length=50),
        ValidationRule("email", required=True, pattern=r"^[^@]+@[^@]+\.[^@]+$"),
        ValidationRule("age", custom_validator=lambda v: isinstance(v, int) and 0 < v < 150),
    ]
    validator.validate_batch(data, rules)
    ```
    """

    # 常用正则模式 - Common regex patterns / 常用正則模式
    PATTERNS = {
        "username": r"^[a-zA-Z][a-zA-Z0-9_-]{2,49}$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "password_strong": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$",
        "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        "url": r"^https?://[^\s/$.?#].[^\s]*$",
        "ip_address": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        "session_id": r"^[a-zA-Z0-9_-]{10,100}$",
        "api_key": r"^[a-zA-Z0-9]{20,64}$",
        "safe_filename": r"^[a-zA-Z0-9._-]{1,255}$",
        "sql_safe": r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|EXECUTE)\b)",
        "command_injection": r"[;|&`$(){}[\]]",  # 危险字符
    }

    def __init__(self):
        """初始化验证器 - Initialize validator / 初始化驗證器"""
        self._compiled_patterns: Dict[str, Pattern] = {}
        for name, pattern in self.PATTERNS.items():
            try:
                self._compiled_patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def validate_string(
        self,
        value: Any,
        field_name: str = "",
        required: bool = False,
        min_length: int = 0,
        max_length: int = 10000,
        pattern: Optional[str] = None,
        allowed_values: Optional[List[Any]] = None,
        strip_whitespace: bool = True,
        sanitize_html: bool = True,
    ) -> str:
        """
        验证字符串 - Validate string / 驗證字符串

        Args:
            value: 要验证的值 / Value to validate
            field_name: 字段名（用于错误消息） / Field name (for error messages)
            required: 是否必需 / Whether required
            min_length: 最小长度 / Min length
            max_length: 最大长度 / Max length
            pattern: 正则表达式 / Regex pattern
            allowed_values: 允许的值列表 / Allowed values list
            strip_whitespace: 是否去除首尾空白 / Strip whitespace
            sanitize_html: 是否清理HTML标签 / Sanitize HTML tags

        Returns:
            验证后的字符串 / Validated string

        Raises:
            ValidationError: 如果验证失败 / If validation fails
        """
        # 检查必需性 - Check requirement
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                raise ValidationError(
                    f"{field_name} is required / {field_name}是必填项",
                    field=field_name,
                    code="REQUIRED_FIELD"
                )
            return ""

        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string / {field_name}必须是字符串",
                field=field_name,
                code="INVALID_TYPE"
            )

        # 去除空白 - Strip whitespace
        if strip_whitespace:
            value = value.strip()

        # 清理HTML - Sanitize HTML
        if sanitize_html:
            value = self.sanitize_html(value)

        # 长度检查 - Length check
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters / {field_name}至少需要{min_length}个字符",
                field=field_name,
                code="TOO_SHORT"
            )

        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters / {field_name}最多{max_length}个字符",
                field=field_name,
                code="TOO_LONG"
            )

        # 正则表达式检查 - Regex check
        if pattern:
            compiled = re.compile(pattern)
            if not compiled.match(value):
                raise ValidationError(
                    f"{field_name} format is invalid / {field_name}格式无效",
                    field=field_name,
                    code="INVALID_FORMAT"
                )

        # 允许值检查 - Allowed values check
        if allowed_values and value not in allowed_values:
            raise ValidationError(
                f"{field_name} must be one of: {allowed_values} / {field_name}必须是: {allowed_values}之一",
                field=field_name,
                code="INVALID_VALUE"
            )

        return value

    def validate_integer(
        self,
        value: Any,
        field_name: str = "",
        required: bool = False,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> int:
        """验证整数 - Validate integer / 驗證整數"""
        if value is None:
            if required:
                raise ValidationError(f"{field_name} is required", field=field_name)
            return 0

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be an integer / {field_name}必须是整数",
                field=field_name,
                code="INVALID_INTEGER"
            )

        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be >= {min_value}",
                field=field_name,
                code="VALUE_TOO_SMALL"
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must be <= {max_value}",
                field=field_name,
                code="VALUE_TOO_LARGE"
            )

        return int_value

    def validate_email(self, email: str, field_name: str = "email") -> str:
        """验证邮箱 - Validate email / 驗證郵箱"""
        return self.validate_string(
            email,
            field_name=field_name,
            required=True,
            max_length=254,
            pattern=self.PATTERNS["email"]
        )

    def validate_username(self, username: str) -> str:
        """验证用户名 - Validate username / 驗證用戶名"""
        return self.validate_string(
            username,
            field_name="username",
            required=True,
            min_length=3,
            max_length=50,
            pattern=self.PATTERNS["username"]
        )

    def validate_password_strength(self, password: str) -> str:
        """验证密码强度 - Validate password strength / 驗證密碼強度"""
        if len(password) < 8:
            raise ValidationError("Password too short / 密码太短", code="WEAK_PASSWORD")

        if len(password) > 128:
            raise ValidationError("Password too long / 密码太长", code="PASSWORD_TOO_LONG")

        checks = {
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "digit": any(c.isdigit() for c in password),
        }

        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise ValidationError(
                f"Password missing: {', '.join(failed)} / 密码缺少: {', '.join(failed)}",
                code="WEAK_PASSWORD"
            )

        # 检查常见弱密码 - Check common weak passwords
        common = {"password", "12345678", "qwerty123", "admin123"}
        if password.lower() in common:
            raise ValidationError("Common weak password / 常见弱密码", code="COMMON_PASSWORD")

        return password

    def check_sql_injection(self, value: str) -> bool:
        """
        检查SQL注入 - Check SQL injection / 檢查SQL注入
        返回True如果检测到潜在注入
        Returns True if potential injection detected
        """
        pattern = self._compiled_patterns.get("sql_safe")
        if pattern and pattern.search(value):
            return True
        return False

    def check_command_injection(self, value: str) -> bool:
        """
        检查命令注入 - Check command injection / 檢查命令注入
        返回True如果检测到危险字符
        Returns True if dangerous chars detected
        """
        pattern = self._compiled_patterns.get("command_injection")
        if pattern and pattern.search(value):
            return True
        return False

    def validate_batch(
        self,
        data: Dict[str, Any],
        rules: List[ValidationRule]
    ) -> Dict[str, Any]:
        """
        批量验证 - Batch validation / 批量驗證
        根据规则列表验证多个字段
        Validates multiple fields based on rule list

        Args:
            data: 要验证的数据字典 / Data dictionary to validate
            rules: 验证规则列表 / List of validation rules

        Returns:
            验证后的数据字典 / Validated data dictionary

        Raises:
            ValidationError: 如果任何字段验证失败 / If any field validation fails
        """
        validated_data = {}

        for rule in rules:
            value = data.get(rule.field_name)

            if rule.custom_validator:
                if not rule.custom_validator(value):
                    raise ValidationError(
                        rule.error_message or f"{rule.field_name} validation failed",
                        field=rule.field_name,
                        code="CUSTOM_VALIDATION_FAILED"
                    )
                validated_data[rule.field_name] = value
            else:
                validated_data[rule.field_name] = self.validate_string(
                    value,
                    field_name=rule.field_name,
                    required=rule.required,
                    min_length=rule.min_length,
                    max_length=rule.max_length,
                    pattern=rule.pattern,
                    allowed_values=rule.allowed_values
                )

        return validated_data

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        清理HTML文本 - Sanitize HTML text / 清理HTML文本
        移除或转义危险的HTML标签
        Remove or escape dangerous HTML tags

        Args:
            text: 要清理的文本 / Text to sanitize

        Returns:
            安全的文本 / Safe text
        """
        if not text:
            return text

        # 转义HTML特殊字符 - Escape HTML special chars
        text = html.escape(text, quote=True)

        # 移除危险标签模式 - Remove dangerous tag patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
        ]

        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名 - Sanitize filename / 清理文件名
        移除路径遍历字符和危险字符
        Removes path traversal and dangerous characters

        Args:
            filename: 文件名 / Filename

        Returns:
            安全的文件名 / Safe filename
        """
        # 移除路径分隔符 - Remove path separators
        filename = filename.replace("/", "").replace("\\", "")

        # 移除危险字符 - Remove dangerous chars
        dangerous = {'..', '\x00', '|', ';', '&', '$', '`', '(', ')', '{', '}'}
        for char in dangerous:
            filename = filename.replace(char, '')

        # 只保留安全字符 - Keep only safe chars
        filename = re.sub(r'[^\w\-_.]', '_', filename)

        # 限制长度 - Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = f"{name[:250]}.{ext}" if ext else filename[:255]

        return filename or "unnamed_file"


# ============================================================================
# 安全中间件 - Security Middleware / 安全中間件
# ============================================================================

if HAS_FASTAPI:
    class SecurityMiddleware(BaseHTTPMiddleware):
        """
        安全中间件 - Security Middleware / 安全中間件
        为FastAPI应用添加多层安全防护
        Adds multi-layer security protection to FastAPI applications

        功能 / Features:
        - 安全响应头 (Security headers)
        - 请求大小限制 (Request size limit)
        - 请求ID追踪 (Request ID tracking)
        - 请求日志记录 (Request logging)
        - CORS增强 (Enhanced CORS)
        """

        def __init__(
            self,
            app,
            max_request_size: int = 10 * 1024 * 1024,  # 10MB
            enable_request_id: bool = True,
            enable_logging: bool = True,
            trusted_proxies: Optional[List[str]] = None,
        ):
            super().__init__(app)
            self.max_request_size = max_request_size
            self.enable_request_id = enable_request_id
            self.enable_logging = enable_logging
            self.trusted_proxies = set(trusted_proxies or [])
            self.validator = InputValidator()

        async def dispatch(self, request: Request, call_next):
            start_time = time.time()

            # 生成请求ID - Generate request ID
            request_id = request.headers.get("X-Request-ID") or secrets.token_urlsafe(16)

            # 获取客户端IP - Get client IP
            client_ip = self._get_client_ip(request)

            # 记录请求日志 - Log request
            if self.enable_logging:
                print(f"[{request_id}] {request.method} {request.url.path} from {client_ip}")

            # 检查请求大小 - Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Payload Too Large",
                        "request_id": request_id,
                        "message": f"Request exceeds maximum size of {self.max_request_size} bytes"
                    }
                )

            # 处理请求 - Process request
            response = await call_next(request)

            # 添加安全头 - Add security headers
            self._add_security_headers(response, request_id)

            # 添加性能头 - Add performance headers
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            response.headers["X-Request-ID"] = request_id

            return response

        def _get_client_ip(self, request: Request) -> str:
            """获取真实客户端IP - Get real client IP / 獲取真實客戶端IP"""
            # 检查代理头 - Check proxy headers
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for and self.trusted_proxies:
                ips = [ip.strip() for ip in forwarded_for.split(",")]
                return ips[0]

            real_ip = request.headers.get("X-Real-IP")
            if real_ip and self.trusted_proxies:
                return real_ip

            # Fallback to client host / 回退到客户端host
            return request.client.host if request.client else "unknown"

        @staticmethod
        def _add_security_headers(response: Response, request_id: str):
            """添加安全响应头 - Add security response headers / 添加安全響應頭"""
            headers = {
                # 防止MIME类型嗅探 - Prevent MIME sniffing
                "X-Content-Type-Options": "nosniff",
                # XSS保护 - XSS protection
                "X-XSS-Protection": "1; mode=block",
                # 点击劫持保护 - Clickjacking protection
                "X-Frame-Options": "DENY",
                # HSTS (HTTPS only) - HSTS
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                # 引用策略 - Referrer policy
                "Referrer-Policy": "strict-origin-when-cross-origin",
                # 内容安全策略 - Content Security Policy (basic)
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self'; "
                    "connect-src 'self'"
                ),
                # 权限策略 - Permissions Policy
                "Permissions-Policy": (
                    "camera=(), microphone=(), geolocation=(), payment=()"
                ),
                # 请求ID - Request ID
                "X-Request-ID": request_id,
            }

            for header, value in headers.items():
                if header not in response.headers:
                    response.headers[header] = value


# ============================================================================
# CSRF 保护 - CSRF Protection / CSRF 保護
# ============================================================================

class CSRFProtection:
    """
    CSRF保护 - CSRF Protection / CSRF 保護
    实现同步令牌模式的CSRF防护
    Implements Synchronizer Token Pattern for CSRF protection

    使用方法 / Usage:
    ```python
    csrf = CSRFProtection(secret_key="your-secret-key")

    # 生成token用于表单
    token = csrf.generate_token(session_id)

    # 验证提交的请求
    if csrf.validate_token(submitted_token, session_id):
        # 处理请求...
    ```

    """

    def __init__(self, secret_key: str, token_expiry: int = 3600):
        """
        初始化CSRF保护 - Initialize CSRF protection

        Args:
            secret_key: 用于签名token的密钥 / Key for signing tokens
            token_expiry: Token有效期（秒） / Token expiry in seconds
        """
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self._tokens: Dict[str, tuple] = {}  # session_id -> (token_hash, created_at)

    def generate_token(self, session_id: str) -> str:
        """
        生成CSRF token - Generate CSRF token / 生成CSRF token

        Args:
            session_id: 会话ID / Session ID

        Returns:
            CSRF token字符串 / CSRF token string
        """
        raw_token = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()))
        signature_data = f"{session_id}:{raw_token}:{timestamp}"

        signature = hmac.new(
            self.secret_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()

        token = f"{raw_token}:{signature}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # 存储token hash - Store token hash
        self._tokens[session_id] = (token_hash, time.time())

        return token

    def validate_token(self, token: str, session_id: str) -> bool:
        """
        验证CSRF token - Validate CSRF token / 驗證CSRF token

        Args:
            token: 提交的token / Submitted token
            session_id: 会话ID / Session ID

        Returns:
            是否有效 / Whether valid
        """
        if not token or not session_id:
            return False

        stored = self._tokens.get(session_id)
        if not stored:
            return False

        stored_hash, created_at = stored

        # 检查过期 - Check expiry
        if time.time() - created_at > self.token_expiry:
            del self._tokens[session_id]
            return False

        # 验证token - Verify token
        submitted_hash = hashlib.sha256(token.encode()).hexdigest()
        if not hmac.compare_digest(stored_hash, submitted_hash):
            return False

        # 验证后删除token（一次性使用） - Delete after use (single-use)
        del self._tokens[session_id]
        return True

    def cleanup_expired_tokens(self) -> int:
        """
        清理过期token - Clean up expired tokens / 清理過期token
        应该定期调用
        Should be called periodically

        Returns:
            清理的数量 / Number cleaned
        """
        now = time.time()
        expired_keys = [
            key for key, (_, created_at) in self._tokens.items()
            if now - created_at > self.token_expiry
        ]

        for key in expired_keys:
            del self._tokens[key]

        return len(expired_keys)


# ============================================================================
# 全局实例 - Global Instances / 全局實例
# ============================================================================

# 默认输入验证器实例 - Default input validator instance
_default_validator = InputValidator()


def get_validator() -> InputValidator:
    """获取默认验证器实例 - Get default validator instance / 獲取默認驗證器實例"""
    return _default_validator


def validate_input(value: Any, **kwargs) -> Any:
    """
    便捷验证函数 - Convenience validation function / 便捷驗證函數
    使用默认验证器进行快速验证
    Uses default validator for quick validation

    用法 / Usage:
    ```python
    username = validate_input("john_doe", field_name="username", required=True)
    email = validate_input("john@example.com", field_name="email", pattern=r"email")
    ```
    """
    return _default_validator.validate_string(value, **kwargs)


def sanitize_user_input(text: str) -> str:
    """
    便捷清理函数 - Convenience sanitization function / 便捷清理函數
    快速清理用户输入
    Quick sanitization of user input

    用法 / Usage:
    ```python
    clean_text = sanitize_user_input(user_input)
    ```
    """
    return _default_validator.sanitize_html(text)


# 导入hmac（延迟导入以避免依赖问题）
import hmac
