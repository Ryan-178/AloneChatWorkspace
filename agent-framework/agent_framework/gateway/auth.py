"""
用户认证模块 - User Authentication
实现JWT认证、用户管理、密码加密
"""
import os
import uuid
import hashlib
import secrets
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
import jwt


class User(BaseModel):
    """用户模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str = Field(..., exclude=True)
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return verify_password(password, self.password_hash)


class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应（不包含敏感信息）"""
    id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    created_at: str


class AuthResponse(BaseModel):
    """认证响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Token载荷"""
    user_id: str
    username: str
    exp: datetime
    iat: datetime
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def hash_password(password: str) -> str:
    """密码加密"""
    salt = secrets.token_hex(16)
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{hash_value.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = password_hash.split(':')
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hash_value.hex() == stored_hash
    except Exception:
        return False


def create_access_token(user: User) -> str:
    """创建访问令牌"""
    now = datetime.utcnow()
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user: User) -> str:
    """创建刷新令牌"""
    now = datetime.utcnow()
    expire = now + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    
    payload = {
        "user_id": user.id,
        "username": user.username,
        "type": "refresh",
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._users_by_username: Dict[str, str] = {}
        self._users_by_email: Dict[str, str] = {}
        self._refresh_tokens: Dict[str, str] = {}
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """创建用户"""
        if username in self._users_by_username:
            raise ValueError(f"用户名已存在: {username}")
        
        if email in self._users_by_email:
            raise ValueError(f"邮箱已存在: {email}")
        
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )
        
        self._users[user.id] = user
        self._users_by_username[username] = user.id
        self._users_by_email[email] = user.id
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        user_id = self._users_by_username.get(username)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        user_id = self._users_by_email.get(email)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = self.get_user_by_username(username)
        if user and user.verify_password(password) and user.is_active:
            return user
        return None
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """更新用户"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if key == 'password':
                user.password_hash = hash_password(value)
            elif hasattr(user, key) and key not in ['id', 'password_hash']:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = self._users.pop(user_id, None)
        if user:
            self._users_by_username.pop(user.username, None)
            self._users_by_email.pop(user.email, None)
            return True
        return False
    
    def list_users(self, limit: int = 20, offset: int = 0) -> List[User]:
        """列出用户"""
        users = list(self._users.values())
        return users[offset:offset + limit]
    
    def store_refresh_token(self, user_id: str, refresh_token: str) -> None:
        """存储刷新令牌"""
        self._refresh_tokens[refresh_token] = user_id
    
    def validate_refresh_token(self, refresh_token: str) -> Optional[str]:
        """验证刷新令牌"""
        user_id = self._refresh_tokens.get(refresh_token)
        if user_id:
            payload = decode_token(refresh_token)
            if payload and payload.get("type") == "refresh":
                return user_id
        return None
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """撤销刷新令牌"""
        if refresh_token in self._refresh_tokens:
            del self._refresh_tokens[refresh_token]
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_users": len(self._users),
            "active_users": sum(1 for u in self._users.values() if u.is_active),
        }


user_manager = UserManager()
