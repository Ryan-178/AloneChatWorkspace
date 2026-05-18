"""
代码加密模块 / Code Encryption Module

提供 / Provides:
- AES-256-GCM加密 / AES-256-GCM encryption
- 代码安全上传 / Secure code upload
- 密钥本地管理 / Local key management
"""

import os
import base64
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag

import yaml


@dataclass
class EncryptionResult:
    """加密结果 / Encryption Result"""
    ciphertext: bytes
    nonce: bytes
    salt: bytes
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode(),
            "nonce": base64.b64encode(self.nonce).decode(),
            "salt": base64.b64encode(self.salt).decode(),
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EncryptionResult":
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            nonce=base64.b64decode(data["nonce"]),
            salt=base64.b64decode(data["salt"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class DeepSeekConfigLoader:
    """DeepSeek配置加载器 / DeepSeek Config Loader"""
    
    _instance: Optional["DeepSeekConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """加载配置 / Load configuration"""
        config_path = Path(__file__).parent / "deepseek_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置 / Get default configuration"""
        return {
            "deepseek": {
                "encryption": {
                    "enabled": True,
                    "algorithm": "AES-256-GCM",
                    "key_length": 32,
                    "salt_length": 16,
                    "nonce_length": 12,
                },
                "context": {
                    "max_tokens": 1000000,
                },
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值 / Get configuration value"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def get_instance(cls) -> "DeepSeekConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


deepseek_config = DeepSeekConfigLoader.get_instance()


class CodeEncryptor:
    """
    代码加密器 / Code Encryptor
    
    使用AES-256-GCM加密代码 / Encrypt code using AES-256-GCM
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        初始化加密器 / Initialize encryptor
        
        Args:
            master_key: 主密钥，如果不提供则自动生成 / Master key, auto-generated if not provided
        """
        self._config = deepseek_config.get("deepseek.encryption", {})
        self._key_length = self._config.get("key_length", 32)
        self._salt_length = self._config.get("salt_length", 16)
        self._nonce_length = self._config.get("nonce_length", 12)
        
        if master_key is None:
            master_key = self._get_or_create_master_key()
        
        self._master_key = master_key
    
    def _get_or_create_master_key(self) -> str:
        """获取或创建主密钥 / Get or create master key"""
        key_file = Path.home() / ".alonechat" / ".key"
        
        if key_file.exists():
            return key_file.read_text().strip()
        
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        machine_id = self._get_machine_id()
        master_key = hashlib.sha256(machine_id.encode()).hexdigest()
        
        key_file.write_text(master_key)
        key_file.chmod(0o600)
        
        return master_key
    
    def _get_machine_id(self) -> str:
        """获取机器标识 / Get machine identifier"""
        try:
            import platform
            info = [
                platform.node(),
                platform.system(),
                platform.machine(),
                str(os.getuid() if hasattr(os, 'getuid') else 0),
            ]
            return "-".join(info)
        except Exception:
            return "alonechat-default-machine"
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        派生加密密钥 / Derive encryption key
        
        Args:
            salt: 盐值 / Salt
            
        Returns:
            派生密钥 / Derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self._key_length,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self._master_key.encode())
    
    def encrypt(self, plaintext: str) -> EncryptionResult:
        """
        加密数据 / Encrypt data
        
        Args:
            plaintext: 明文 / Plaintext
            
        Returns:
            加密结果 / Encryption result
        """
        salt = os.urandom(self._salt_length)
        nonce = os.urandom(self._nonce_length)
        
        key = self._derive_key(salt)
        
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            salt=salt,
            timestamp=datetime.now(),
        )
    
    def decrypt(self, encrypted: EncryptionResult) -> str:
        """
        解密数据 / Decrypt data
        
        Args:
            encrypted: 加密结果 / Encryption result
            
        Returns:
            明文 / Plaintext
        """
        key = self._derive_key(encrypted.salt)
        
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None)
        
        return plaintext.decode()
    
    def encrypt_code(self, code: str) -> Dict[str, Any]:
        """
        加密代码 / Encrypt code
        
        Args:
            code: 代码内容 / Code content
            
        Returns:
            加密数据字典 / Encrypted data dictionary
        """
        result = self.encrypt(code)
        return result.to_dict()
    
    def decrypt_code(self, encrypted_data: Dict[str, Any]) -> str:
        """
        解密代码 / Decrypt code
        
        Args:
            encrypted_data: 加密数据字典 / Encrypted data dictionary
            
        Returns:
            代码内容 / Code content
        """
        result = EncryptionResult.from_dict(encrypted_data)
        return self.decrypt(result)
    
    def encrypt_file(self, file_path: Path) -> Dict[str, Any]:
        """
        加密文件 / Encrypt file
        
        Args:
            file_path: 文件路径 / File path
            
        Returns:
            加密数据字典 / Encrypted data dictionary
        """
        content = file_path.read_text(encoding="utf-8")
        return self.encrypt_code(content)
    
    def decrypt_to_file(
        self,
        encrypted_data: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        解密到文件 / Decrypt to file
        
        Args:
            encrypted_data: 加密数据字典 / Encrypted data dictionary
            output_path: 输出路径 / Output path
        """
        content = self.decrypt_code(encrypted_data)
        output_path.write_text(content, encoding="utf-8")


class SecureUploader:
    """
    安全上传器 / Secure Uploader
    
    加密代码后上传到API / Encrypt code and upload to API
    """
    
    def __init__(self, encryptor: Optional[CodeEncryptor] = None):
        self.encryptor = encryptor or CodeEncryptor()
        self._encryption_enabled = deepseek_config.get(
            "deepseek.encryption.enabled", True
        )
    
    def prepare_code_for_upload(
        self,
        code: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        准备代码用于上传 / Prepare code for upload
        
        Args:
            code: 代码内容 / Code content
            metadata: 元数据 / Metadata
            
        Returns:
            准备上传的数据 / Prepared upload data
        """
        if self._encryption_enabled:
            encrypted = self.encryptor.encrypt_code(code)
            
            return {
                "encrypted": True,
                "data": encrypted,
                "metadata": metadata or {},
            }
        else:
            return {
                "encrypted": False,
                "data": code,
                "metadata": metadata or {},
            }
    
    def process_response(
        self,
        response: Dict[str, Any],
    ) -> str:
        """
        处理响应 / Process response
        
        Args:
            response: API响应 / API response
            
        Returns:
            解密后的内容 / Decrypted content
        """
        if response.get("encrypted"):
            return self.encryptor.decrypt_code(response["data"])
        else:
            return response.get("data", "")
