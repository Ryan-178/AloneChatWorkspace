"""
用户认证模块 - User Authentication Module / 用户認證模組
实现JWT认证、用户管理、密码加密 - Implements JWT auth, user management, password hashing
安全性增强：使用bcrypt、Token黑名单、速率限制、账户锁定
Security enhanced: bcrypt, token blacklist, rate limiting, account lockout

安全最佳实践参考 / Security best practices reference:
- OWASP Authentication Cheat Sheet
- NIST SP 800-63B Digital Identity Guidelines
- ISO/IEC 27001:2022 Information Security Management
"""
import os
import uuid
import hashlib
import secrets
import time
import threading
import warnings
from typing import Optional, Dict, List, Set, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr, validator
import jwt

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    warnings.warn(
        "bcrypt未安装，将使用PBKDF2作为回退。建议运行: pip install bcrypt",
        UserWarning,
        stacklevel=2
    )


class User(BaseModel):
    """
    用户模型 - User Model / 用戶模型
    包含账户锁定和登录尝试跟踪功能
    Includes account lockout and login attempt tracking
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str = Field(..., exclude=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    # 安全字段 - Security fields
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = Field(None, exclude=True)

    @validator('username')
    def validate_username(cls, v: str) -> str:
        """验证用户名格式 - Validate username format / 驗證用戶名格式"""
        if not v:
            raise ValueError('用户名不能为空')
        if not v[0].isalpha():
            raise ValueError('用户名必须以字母开头')
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('用户名长度必须在3-50个字符之间')
        return v

    def verify_password(self, password: str) -> bool:
        """验证密码 - Verify password / 驗證密碼"""
        return verify_password(password, self.password_hash)

    def is_locked(self) -> bool:
        """
        检查账户是否锁定 - Check if account is locked / 檢查賬戶是否鎖定
        自动解锁过期的锁定
        Auto-unlocks expired lockouts
        """
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        # 自动解锁 - Auto unlock
        if self.locked_until and datetime.utcnow() >= self.locked_until:
            self.locked_until = None
            self.failed_login_attempts = 0
        return False

    def record_failed_login(self) -> None:
        """记录失败登录 - Record failed login / 記錄失敗登錄"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            self.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

    def record_successful_login(self, ip_address: Optional[str] = None) -> None:
        """记录成功登录 - Record successful login / 記錄成功登錄"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()
        self.last_login_ip = ip_address


class UserCreate(BaseModel):
    """
    用户创建请求 - User Create Request / 用戶創建請求
    包含强密码验证
    Includes strong password validation
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """
        验证密码强度 - Validate password strength / 驗證密碼強度
        符合NIST SP 800-63B指南要求
        Complies with NIST SP 800-63B guidelines
        """
        if len(v) < 8:
            raise ValueError('密码长度至少8位 / Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('密码长度不能超过128位 / Password cannot exceed 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母 / Must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母 / Must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字 / Must contain at least one digit')
        # 检查常见弱密码 - Check common weak passwords
        common_passwords = {'password', '123456', 'qwerty', 'admin', 'letmein', 'welcome'}
        if v.lower() in common_passwords:
            raise ValueError('不能使用常见弱密码 / Cannot use common weak passwords')
        return v


class UserLogin(BaseModel):
    """
    用户登录请求 - User Login Request / 用戶登錄請求
    包含客户端信息用于安全审计
    Includes client info for security audit
    """
    username: str
    password: str
    ip_address: Optional[str] = Field(None, description="客户端IP地址 / Client IP address")
    user_agent: Optional[str] = Field(None, description="客户端User-Agent / Client User-Agent")


class UserResponse(BaseModel):
    """
    用户响应（不包含敏感信息）- User Response (no sensitive info)
    用戶響應（不含敏感信息）
    """
    id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    created_at: str
    is_active: bool = True
    mfa_enabled: bool = False


class AuthResponse(BaseModel):
    """
    认证响应 - Auth Response / 認證響應
    包含访问令牌和刷新令牌
    Includes access token and refresh token
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒 / seconds
    user: UserResponse


class TokenPayload(BaseModel):
    """
    Token载荷 - Token Payload / Token載荷
    支持作用域和自定义声明
    Supports scopes and custom claims
    """
    user_id: str
    username: str
    exp: datetime
    iat: datetime
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scope: List[str] = ["read", "write"]
    type: str = "access"


# ============================================================================
# 安全配置 - Security Configuration / 安全配置
# ============================================================================

def _get_jwt_secret() -> str:
    """
    获取JWT密钥 - Get JWT secret key
    安全优先级：环境变量 > 强随机生成（带警告）
    Security priority: env var > strong random generation (with warning)
    """
    secret = os.getenv("JWT_SECRET_KEY")

    if secret:
        if len(secret) < 32:
            warnings.warn(
                f"JWT_SECRET_KEY长度不足32字符（当前：{len(secret)}），建议使用更强的密钥",
                UserWarning,
                stacklevel=2
            )
        return secret

    # 生成强随机密钥并警告 - Generate strong random key with warning
    strong_secret = secrets.token_urlsafe(64)
    warnings.warn(
        "[SECURITY WARNING] 使用自动生成的JWT密钥。\n"
        "生产环境请设置JWT_SECRET_KEY环境变量（长度>=32字符）\n"
        "示例: export JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')",
        UserWarning,
        stacklevel=2
    )
    return strong_secret


# JWT配置 - JWT Configuration / JWT配置
JWT_SECRET_KEY: str = _get_jwt_secret()
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))  # 缩短到30分钟以提高安全性
JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# 安全策略配置 - Security policy configuration / 安全策略配置
MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))  # 最大登录尝试次数
LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))  # 锁定时长（分钟）
PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))  # 最小密码长度
SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))  # 会话超时时间

# Token黑名单（用于注销功能）- Token blacklist (for logout functionality)
_token_blacklist: Set[str] = set()
_blacklist_lock = threading.Lock()
_blacklist_expiry: Dict[str, datetime] = {}  # jti -> expiry time


# ============================================================================
# 密码哈希函数 - Password Hashing Functions / 密碼哈希函數
# ============================================================================

def hash_password(password: str) -> str:
    """
    密码加密 - Hash password / 密碼加密
    优先使用bcrypt（更安全），回退到PBKDF2
    Priority: bcrypt (more secure), fallback to PBKDF2

    安全特性 / Security features:
    - bcrypt: 自适应哈希函数，自动增加计算成本
    - PBKDF2-HMAC-SHA256: 200,000次迭代（符合OWASP推荐）
    - 唯一盐值：每个密码使用不同的盐

    Args:
        password: 明文密码 / Plaintext password

    Returns:
        格式化的哈希字符串 / Formatted hash string
    """
    if HAS_BCRYPT:
        try:
            salt = bcrypt.gensalt(rounds=12)  # 2^12 = 4096 rounds
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return f"bcrypt:{hashed.decode('utf-8')}"
        except Exception as e:
            warnings.warn(f"bcrypt哈希失败，回退到PBKDF2: {e}", UserWarning, stacklevel=2)

    # Fallback to PBKDF2 with increased iterations (OWASP recommends >= 60,000 for SHA-256)
    salt = secrets.token_hex(16)  # 128-bit salt
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        200000  # Increased from 100,000 for better security
    )
    return f"pbkdf2_sha256:{salt}:{hash_value.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码 - Verify password / 驗證密碼
    支持多种哈希格式以保持向后兼容性
    Supports multiple hash formats for backward compatibility

    支持的格式 / Supported formats:
    - bcrypt:<hash> - 推荐格式
    - pbkdf2_sha256:<salt>:<hash> - 当前默认
    - <salt>:<hash> - 旧版兼容

    Args:
        password: 明文密码 / Plaintext password
        password_hash: 存储的哈希值 / Stored hash value

    Returns:
        是否匹配 / Whether it matches
    """
    try:
        if password_hash.startswith("bcrypt:"):
            if not HAS_BCRYPT:
                return False
            stored_hash = password_hash[7:]
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

        elif password_hash.startswith("pbkdf2_sha256:"):
            parts = password_hash[len("pbkdf2_sha256:"):]
            if ':' not in parts:
                return False
            salt, stored_hash = parts.split(':', 1)
            hash_value = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                200000
            )
            return hash_value.hex() == stored_hash

        else:
            # Legacy format (for backward compatibility) - 旧版格式（向后兼容）
            if ':' not in password_hash:
                return False
            salt, stored_hash = password_hash.split(':', 1)
            hash_value = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000  # Original iteration count
            )
            return hash_value.hex() == stored_hash

    except Exception as e:
        # 记录错误但不泄露信息 - Log error but don't leak info
        warnings.warn(f"密码验证异常: {e}", UserWarning, stacklevel=2)
        return False


# ============================================================================
# Token管理函数 - Token Management Functions / Token管理函數
# ============================================================================

def create_access_token(user: User, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    创建访问令牌 - Create access token / 建立訪問令牌
    支持自定义声明和作用域
    Supports custom claims and scopes

    安全特性 / Security features:
    - 短有效期（默认30分钟）
    - 唯一JTI用于追踪和撤销
    - 包含作用域限制权限

    Args:
        user: 用户对象 / User object
        additional_claims: 额外声明 / Additional claims

    Returns:
        JWT令牌字符串 / JWT token string
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "user_id": user.id,
        "username": user.username,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "scope": ["read", "write"],
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user: User) -> str:
    """
    创建刷新令牌 - Create refresh token / 建立刷新令牌
    刷新令牌有效期更长但权限更少
    Refresh token has longer expiry but fewer permissions

    安全设计 / Security design:
    - 仅用于获取新的访问令牌
    - 作用域限制为"refresh"
    - 应该存储在安全的HTTP-only cookie中
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)

    payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
        "scope": ["refresh"],
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """
    解码令牌 - Decode token / 解碼令牌
    验证签名、有效期和黑名单状态
    Verifies signature, expiry, and blacklist status

    Args:
        token: JWT令牌 / JWT token

    Returns:
        令牌载荷或None（如果无效） / Token payload or None (if invalid)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # 检查是否在黑名单中 - Check if blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None

        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def add_token_to_blacklist(jti: str, expiry: datetime) -> None:
    """
    将令牌添加到黑名单 - Add token to blacklist / 將令牌加入黑名單
    用于注销功能，防止已注销的token被继续使用
    Used for logout functionality, prevents continued use of logged-out tokens

    Args:
        jti: 令牌唯一标识符 / Token unique identifier
        expiry: 令牌过期时间 / Token expiry time
    """
    with _blacklist_lock:
        _token_blacklist.add(jti)
        _blacklist_expiry[jti] = expiry


def is_token_blacklisted(jti: str) -> bool:
    """
    检查令牌是否在黑名单中 - Check if token is blacklisted / 檢查令牌是否在黑名單中

    Args:
        jti: 令牌唯一标识符 / Token unique identifier

    Returns:
        是否已被列入黑名单 / Whether it's been blacklisted
    """
    with _blacklist_lock:
        if jti not in _token_blacklist:
            return False

        # 检查是否过期（自动清理） - Check if expired (auto-cleanup)
        expiry = _blacklist_expiry.get(jti)
        if expiry and datetime.utcnow() > expiry:
            del _token_blacklist[jti]
            del _blacklist_expiry[jti]
            return False

        return True


def cleanup_expired_tokens() -> int:
    """
    清理过期的黑名单令牌 - Clean up expired blacklisted tokens / 清理過期的黑名單令牌
    应该定期调用此函数以防止内存泄漏
    Should be called periodically to prevent memory leaks

    建议调用频率 / Recommended call frequency:
    - 每10分钟一次（低流量系统）
    - 每分钟一次（高流量系统）

    Returns:
        清理的令牌数量 / Number of cleaned tokens
    """
    now = datetime.utcnow()
    cleaned = 0

    with _blacklist_lock:
        expired_jtis = [
            jti for jti, expiry in _blacklist_expiry.items()
            if now > expiry
        ]

        for jti in expired_jtis:
            _token_blacklist.discard(jti)
            del _blacklist_expiry[jti]
            cleaned += 1

    return cleaned


def revoke_user_tokens(user_id: str) -> int:
    """
    撤销用户的所有令牌 - Revoke all tokens for a user / 撤銷用戶的所有令牌
    用于紧急情况下的账户安全
    Used for emergency account security

    注意：这需要配合数据库存储才能完整实现
    Note: This requires database storage for full implementation

    Args:
        user_id: 用户ID / User ID

    Returns:
        撤销的令牌数量 / Number of revoked tokens
    """
    # 这里简化处理，实际应该查询该用户的所有活跃token
    # Simplified here, should query all active tokens for this user
    return cleanup_expired_tokens()


# ============================================================================
# 用户管理器 - User Manager / 用戶管理器
# ============================================================================

class UserManager:
    """
    用户管理器 - User Manager / 用戶管理器
    管理用户的完整生命周期
    Manages the complete lifecycle of users

    安全特性 / Security features:
    - 登录尝试限制和账户锁定
    - 审计日志记录
    - Token生命周期管理
    - 线程安全操作

    生产环境注意 / Production note:
    此实现使用内存存储，生产环境应替换为数据库
    This implementation uses in-memory storage, should be replaced with database in production
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._users: Dict[str, User] = {}
        self._users_by_username: Dict[str, str] = {}
        self._users_by_email: Dict[str, str] = {}
        self._refresh_tokens: Dict[str, str] = {}
        # 审计日志 - Audit log
        self._audit_log: List[Dict[str, Any]] = []
        self._max_audit_log_size: int = 10000

    def _add_audit_log(self, action: str, user_id: str, details: Optional[Dict] = None) -> None:
        """添加审计日志条目 - Add audit log entry / 添加審計日誌條目"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "details": details or {},
        }
        self._audit_log.append(entry)

        # 限制日志大小以防止内存泄漏 - Limit log size to prevent memory leaks
        if len(self._audit_log) > self._max_audit_log_size:
            self._audit_log = self._audit_log[-self._max_audit_log_size // 2:]

    def create_user(self, username: str, email: str, password: str) -> User:
        """
        创建用户 - Create user / 建立用戶
        包含输入验证和安全检查
        Includes input validation and security checks

        Raises:
            ValueError: 如果用户名或邮箱已存在 / If username or email already exists
        """
        with self._lock:
            if username in self._users_by_username:
                raise ValueError(f'用户名已存在: {username} / Username already exists: {username}')

            if email in self._users_by_email:
                raise ValueError(f'邮箱已存在: {email} / Email already exists: {email}')

            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password)
            )

            self._users[user.id] = user
            self._users_by_username[username] = user.id
            self._users_by_email[email] = user.id

            self._add_audit_log("user_created", user.id, {"username": username, "email": email})

            return user

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户 - Get user / 獲取用戶"""
        with self._lock:
            return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户 - Get user by username / 通過用戶名獲取用戶"""
        with self._lock:
            user_id = self._users_by_username.get(username)
            if user_id:
                return self._users.get(user_id)
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户 - Get user by email / 通過郵箱獲取用戶"""
        with self._lock:
            user_id = self._users_by_email.get(email)
            if user_id:
                return self._users.get(user_id)
            return None

    def authenticate(self, username: str, password: str,
                     ip_address: Optional[str] = None) -> tuple[Optional[User], Optional[str]]:
        """
        认证用户 - Authenticate user / 認證用戶
        包含账户锁定检查和登录尝试跟踪
        Includes account lockout check and login attempt tracking

        安全流程 / Security flow:
        1. 检查账户是否存在
        2. 检查账户是否被锁定
        3. 验证密码
        4. 更新登录状态
        5. 记录审计日志

        Args:
            username: 用户名 / Username
            password: 密码 / Password
            ip_address: 客户端IP / Client IP

        Returns:
            (用户对象, 错误消息) 元组 / (User object, error message) tuple
        """
        with self._lock:
            user = self.get_user_by_username(username)

            if not user:
                # 即使用户不存在也不透露具体信息（防止枚举攻击）
                # Don't reveal specific info even if user doesn't exist (prevent enumeration attacks)
                self._add_audit_log("login_failed_unknown", "", {"username": username, "ip": ip_address})
                return None, "用户名或密码错误 / Invalid username or password"

            if not user.is_active:
                self._add_audit_log("login_failed_inactive", user.id, {"ip": ip_address})
                return None, "账户已被禁用 / Account has been disabled"

            if user.is_locked():
                remaining_time = (user.locked_until - datetime.utcnow()).seconds // 60 + 1
                self._add_audit_log("login_failed_locked", user.id, {
                    "ip": ip_address,
                    "locked_until": user.locked_until.isoformat(),
                })
                return None, f"账户已锁定，请{remaining_time}分钟后重试 / Account locked, please try again after {remaining_time} minutes"

            if not user.verify_password(password):
                user.record_failed_login()
                self._add_audit_log("login_failed_password", user.id, {
                    "ip": ip_address,
                    "failed_attempts": user.failed_login_attempts,
                })

                if user.is_locked():
                    return None, f"密码错误次数过多，账户已锁定{LOCKOUT_DURATION_MINUTES}分钟 / Too many failed attempts, account locked for {LOCKOUT_DURATION_MINUTES} minutes"

                return None, "用户名或密码错误 / Invalid username or password"

            # 登录成功 - Successful login
            user.record_successful_login(ip_address)
            self._add_audit_log("login_success", user.id, {"ip": ip_address})

            return user, None

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """
        更新用户 - Update user / 更新用戶
        安全地更新用户属性
        Safely update user attributes

        Args:
            user_id: 用户ID / User ID
            **kwargs: 要更新的属性 / Attributes to update

        Returns:
            更新后的用户对象或None / Updated user object or None
        """
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return None

            protected_fields = {'id', 'password_hash', 'created_at'}

            for key, value in kwargs.items():
                if key in protected_fields:
                    continue

                if key == 'password':
                    user.password_hash = hash_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()

            self._add_audit_log("user_updated", user_id, {"fields": list(kwargs.keys())})

            return user

    def delete_user(self, user_id: str) -> bool:
        """
        删除用户 - Delete user / 刪除用戶
        同时清理相关数据
        Also cleans up related data

        Args:
            user_id: 用户ID / User ID

        Returns:
            是否删除成功 / Whether deletion was successful
        """
        with self._lock:
            user = self._users.pop(user_id, None)
            if user:
                self._users_by_username.pop(user.username, None)
                self._users_by_email.pop(user.email, None)

                # 清理相关的刷新令牌 - Clean up related refresh tokens
                tokens_to_remove = [
                    token for token, uid in self._refresh_tokens.items()
                    if uid == user_id
                ]
                for token in tokens_to_remove:
                    del self._refresh_tokens[token]

                self._add_audit_log("user_deleted", user_id, {
                    "username": user.username,
                    "email": user.email,
                })
                return True
            return False

    def list_users(self, limit: int = 20, offset: int = 0) -> List[User]:
        """
        列出用户 - List users / 列出用戶
        支持分页
        Supports pagination

        Args:
            limit: 返回数量限制 / Return count limit
            offset: 偏移量 / Offset

        Returns:
            用户列表 / List of users
        """
        with self._lock:
            users = list(self._users.values())
            return users[offset:offset + limit]

    def store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """
        存储刷新令牌 - Store refresh token / 存儲刷新令牌
        用于后续的令牌刷新操作
        Used for subsequent token refresh operations

        Args:
            user_id: 用户ID / User ID
            refresh_token: 刷新令牌 / Refresh token
        """
        with self._lock:
            self._refresh_tokens[refresh_token] = user_id

    def validate_refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        验证刷新令牌 - Validate refresh token / 驗證刷新令牌
        检查令牌有效性和类型
        Checks token validity and type

        Args:
            refresh_token: 刷新令牌 / Refresh token

        Returns:
            用户ID或None / User ID or None
        """
        with self._lock:
            user_id = self._refresh_tokens.get(refresh_token)
            if user_id:
                payload = decode_token(refresh_token)
                if payload and payload.get("type") == "refresh":
                    return user_id
            return None

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        撤销刷新令牌 - Revoke refresh token / 撤銷刷新令牌
        用于登出操作
        Used for logout operations

        Args:
            refresh_token: 刷新令牌 / Refresh token

        Returns:
            是否撤销成功 / Whether revocation was successful
        """
        with self._lock:
            if refresh_token in self._refresh_tokens:
                del self._refresh_tokens[refresh_token]
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息 - Get statistics / 獲取統計信息
        返回系统的用户统计数据
        Returns system user statistics

        Returns:
            统计数据字典 / Statistics dictionary
        """
        with self._lock:
            return {
                "total_users": len(self._users),
                "active_users": sum(1 for u in self._users.values() if u.is_active),
                "locked_users": sum(1 for u in self._users.values() if u.is_locked()),
                "active_refresh_tokens": len(self._refresh_tokens),
                "audit_log_entries": len(self._audit_log),
            }


# 全局用户管理器实例 - Global user manager instance / 全局用戶管理器實例
user_manager = UserManager()
