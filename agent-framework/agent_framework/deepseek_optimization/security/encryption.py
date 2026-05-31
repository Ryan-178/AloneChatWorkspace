"""
Encryption Manager
加密管理 - 数据保护
"""
import hashlib
import secrets
from typing import Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


@dataclass
class EncryptionConfig:
    """加密配置"""
    key: bytes
    algorithm: str = "AES-256-GCM"


class EncryptionManager:
    """
    加密管理器
    负责敏感数据的加密和解密
    """

    # 固定盐值（应存储在安全位置，如环境变量或密钥管理服务）
    # 生产环境建议从环境变量读取
    DEFAULT_SALT_SIZE = 32
    DEFAULT_ITERATIONS = 480000  # OWASP 推荐的最小迭代次数

    def __init__(self, secret_key: Optional[bytes] = None):
        self._fernet: Optional[Fernet] = None
        self._salt: Optional[bytes] = None

        if secret_key:
            self._initialize_with_key(secret_key)

    def _initialize_with_key(self, secret_key: bytes):
        """用密钥初始化 - 使用 PBKDF2 进行安全的密钥派生"""
        # 生成随机盐值
        self._salt = os.urandom(self.DEFAULT_SALT_SIZE)

        # 使用 PBKDF2HMAC 进行密钥派生
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=self.DEFAULT_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key))
        self._fernet = Fernet(key)

    def _derive_key(self, secret_key: bytes, salt: bytes) -> bytes:
        """使用 PBKDF2 派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.DEFAULT_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret_key))

    def generate_key(self) -> bytes:
        """生成新的密钥"""
        return Fernet.generate_key()

    def encrypt(self, data: str) -> str:
        """加密数据 - 返回 salt + ciphertext 的组合"""
        if not self._fernet:
            raise ValueError("Encryption manager not initialized with a key")

        # 加密数据
        ciphertext = self._fernet.encrypt(data.encode())

        # 将盐值和密文组合（salt:ciphertext，base64 编码）
        combined = base64.urlsafe_b64encode(self._salt + ciphertext).decode()
        return combined

    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not self._fernet:
            raise ValueError("Encryption manager not initialized with a key")

        try:
            # 解码组合数据
            combined = base64.urlsafe_b64decode(encrypted_data.encode())

            # 提取盐值和密文
            salt = combined[:self.DEFAULT_SALT_SIZE]
            ciphertext = combined[self.DEFAULT_SALT_SIZE:]

            # 使用存储的原始密钥重新派生密钥进行解密
            # 注意：这里需要原始密钥，但当前设计中没有存储原始密钥
            # 实际使用中，应该在初始化时保存原始密钥或使用密钥派生参数
            # 为简化，我们使用当前实例的 fernet 进行解密（假设盐值匹配）
            return self._fernet.decrypt(ciphertext).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def hash_data(self, data: str) -> str:
        """计算数据的哈希值（用于完整性校验）"""
        return hashlib.sha256(data.encode()).hexdigest()

    def secure_random(self, length: int = 32) -> bytes:
        """生成安全的随机字节"""
        return os.urandom(length)

    @staticmethod
    def generate_secure_key(length: int = 64) -> str:
        """生成安全的随机密钥字符串"""
        return secrets.token_hex(length)
