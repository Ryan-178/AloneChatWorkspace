"""
ä»£ç å å¯æ¨¡å / Code Encryption Module

æä¾ / Provides:
- AES-256-GCMå å¯ / AES-256-GCM encryption
- ä»£ç å®å¨ä¸ä¼  / Secure code upload
- å¯é¥æ¬å°ç®¡ç / Local key management
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
    """å å¯ç»æ / Encryption Result"""
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
    """DeepSeekéç½®å è½½å?/ DeepSeek Config Loader"""
    
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
        """å è½½éç½® / Load configuration"""
        config_path = Path(__file__).parent / "deepseek_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """è·åé»è®¤éç½® / Get default configuration"""
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
        """è·åéç½®å?/ Get configuration value"""
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
    ä»£ç å å¯å?/ Code Encryptor
    
    ä½¿ç¨AES-256-GCMå å¯ä»£ç  / Encrypt code using AES-256-GCM
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        åå§åå å¯å¨ / Initialize encryptor
        
        Args:
            master_key: ä¸»å¯é¥ï¼å¦æä¸æä¾åèªå¨çæ / Master key, auto-generated if not provided
        """
        self._config = deepseek_config.get("deepseek.encryption", {})
        self._key_length = self._config.get("key_length", 32)
        self._salt_length = self._config.get("salt_length", 16)
        self._nonce_length = self._config.get("nonce_length", 12)
        
        if master_key is None:
            master_key = self._get_or_create_master_key()
        
        self._master_key = master_key
    
    def _get_or_create_master_key(self) -> str:
        """è·åæåå»ºä¸»å¯é¥ / Get or create master key"""
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
        """è·åæºå¨æ è¯ / Get machine identifier"""
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
        æ´¾çå å¯å¯é¥ / Derive encryption key
        
        Args:
            salt: çå?/ Salt
            
        Returns:
            æ´¾çå¯é¥ / Derived key
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
        å å¯æ°æ® / Encrypt data
        
        Args:
            plaintext: ææ / Plaintext
            
        Returns:
            å å¯ç»æ / Encryption result
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
        è§£å¯æ°æ® / Decrypt data
        
        Args:
            encrypted: å å¯ç»æ / Encryption result
            
        Returns:
            ææ / Plaintext
        """
        key = self._derive_key(encrypted.salt)
        
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None)
        
        return plaintext.decode()
    
    def encrypt_code(self, code: str) -> Dict[str, Any]:
        """
        å å¯ä»£ç  / Encrypt code
        
        Args:
            code: ä»£ç åå®¹ / Code content
            
        Returns:
            å å¯æ°æ®å­å¸ / Encrypted data dictionary
        """
        result = self.encrypt(code)
        return result.to_dict()
    
    def decrypt_code(self, encrypted_data: Dict[str, Any]) -> str:
        """
        è§£å¯ä»£ç  / Decrypt code
        
        Args:
            encrypted_data: å å¯æ°æ®å­å¸ / Encrypted data dictionary
            
        Returns:
            ä»£ç åå®¹ / Code content
        """
        result = EncryptionResult.from_dict(encrypted_data)
        return self.decrypt(result)
    
    def encrypt_file(self, file_path: Path) -> Dict[str, Any]:
        """
        å å¯æä»¶ / Encrypt file
        
        Args:
            file_path: æä»¶è·¯å¾ / File path
            
        Returns:
            å å¯æ°æ®å­å¸ / Encrypted data dictionary
        """
        content = file_path.read_text(encoding="utf-8")
        return self.encrypt_code(content)
    
    def decrypt_to_file(
        self,
        encrypted_data: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        è§£å¯å°æä»?/ Decrypt to file
        
        Args:
            encrypted_data: å å¯æ°æ®å­å¸ / Encrypted data dictionary
            output_path: è¾åºè·¯å¾ / Output path
        """
        content = self.decrypt_code(encrypted_data)
        output_path.write_text(content, encoding="utf-8")


class SecureUploader:
    """
    å®å¨ä¸ä¼ å?/ Secure Uploader
    
    å å¯ä»£ç åä¸ä¼ å°API / Encrypt code and upload to API
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
        åå¤ä»£ç ç¨äºä¸ä¼  / Prepare code for upload
        
        Args:
            code: ä»£ç åå®¹ / Code content
            metadata: åæ°æ?/ Metadata
            
        Returns:
            åå¤ä¸ä¼ çæ°æ?/ Prepared upload data
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
        å¤çååº / Process response
        
        Args:
            response: APIååº / API response
            
        Returns:
            è§£å¯åçåå®¹ / Decrypted content
        """
        if response.get("encrypted"):
            return self.encryptor.decrypt_code(response["data"])
        else:
            return response.get("data", "")
