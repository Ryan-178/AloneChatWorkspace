"""
配置管理模块 / Config Management Module

负责 / Responsible for:
- 配置文件读写 / Config file read/write
- API密钥加密存储 / API key encrypted storage
- 环境变量支持 / Environment variable support
"""

import os
from pathlib import Path
from typing import Any
import json
import tomli
import tomli_w
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class ConfigManager:
    """配置管理器 / Config Manager"""

    def __init__(self, config_path: str | None = None):
        """
        初始化配置管理器 / Initialize config manager

        Args:
            config_path: 配置文件路径，默认为当前目录的.aloneworkrc / Config file path, default is .aloneworkrc in current directory
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.cwd() / ".aloneworkrc"

        self._encryption_key = self._get_encryption_key()
        self._fernet = Fernet(self._encryption_key)

    def _get_encryption_key(self) -> bytes:
        """
        获取加密密钥 / Get encryption key

        使用机器特定的信息生成密钥，确保密钥的唯一性 / Use machine-specific info to generate key
        """
        import platform

        try:
            node_name = platform.node()
        except Exception:
            node_name = "alonework-machine"

        try:
            user_id = os.getuid() if hasattr(os, 'getuid') else 0
        except Exception:
            user_id = 0

        machine_id = f"{node_name}-{user_id}"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"alonework-salt",
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key

    def load_config(self) -> dict[str, Any]:
        """
        加载配置文件 / Load config file

        Returns:
            配置字典 / Config dict
        """
        if not self.config_path.exists():
            return {}

        content = self.config_path.read_text(encoding="utf-8")

        if self.config_path.suffix == ".json":
            return json.loads(content)
        else:
            return tomli.loads(content)

    def save_config(self, config: dict[str, Any]) -> None:
        """
        保存配置文件 / Save config file

        Args:
            config: 配置字典 / Config dict
        """
        content = tomli_w.dumps(config)
        self.config_path.write_text(content, encoding="utf-8")

    def encrypt_api_key(self, api_key: str) -> str:
        """
        加密API密钥 / Encrypt API key

        Args:
            api_key: 原始API密钥 / Original API key

        Returns:
            加密后的密钥 / Encrypted key
        """
        return self._fernet.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        解密API密钥 / Decrypt API key

        Args:
            encrypted_key: 加密的密钥 / Encrypted key

        Returns:
            原始API密钥 / Original API key
        """
        return self._fernet.decrypt(encrypted_key.encode()).decode()

    def get_api_key(self, provider: str) -> str | None:
        """
        获取API密钥 / Get API key

        优先级 / Priority:
        1. 环境变量 / Environment variable
        2. 配置文件 / Config file

        Args:
            provider: 提供商名称 / Provider name

        Returns:
            API密钥 / API key
        """
        env_var = f"{provider.upper()}_API_KEY"
        if env_key := os.getenv(env_var):
            return env_key

        config = self.load_config()
        provider_config = config.get("model", {}).get("providers", {}).get(provider, {})

        if encrypted_key := provider_config.get("api_key"):
            try:
                return self.decrypt_api_key(encrypted_key)
            except Exception:
                return encrypted_key

        return None
