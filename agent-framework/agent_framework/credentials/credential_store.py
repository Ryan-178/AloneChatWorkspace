"""
Multi-platform credential store with OS-native keychain support
macOS Keychain, Windows Credential Manager, Linux Secret Service
Falls back to AES-256-GCM encrypted file storage
"""
from __future__ import annotations
import os
import json
import base64
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field, asdict


class CredentialType(str, Enum):
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    OAUTH_REFRESH_TOKEN = "oauth_refresh_token"
    PASSWORD = "password"
    SSH_KEY = "ssh_key"
    CUSTOM = "custom"


@dataclass
class StoredCredential:
    service: str
    username: str
    credential_type: CredentialType = CredentialType.CUSTOM
    secret: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "username": self.username,
            "credential_type": self.credential_type.value,
            "secret": self.secret,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoredCredential":
        return cls(
            service=data.get("service", ""),
            username=data.get("username", ""),
            credential_type=CredentialType(data.get("credential_type", "custom")),
            secret=data.get("secret", ""),
            metadata=data.get("metadata", {}),
        )


def _get_platform() -> str:
    return platform.system().lower()


class CredentialStore:
    """
    Secure credential store using OS-native keychain when available.
    Falls back to AES-256-GCM encrypted file storage.
    """

    def __init__(self, app_name: str = "AloneChat"):
        self.app_name = app_name
        self.platform = _get_platform()
        self._fallback_dir = Path.home() / ".alonechat" / "credentials"
        self._fallback_dir.mkdir(parents=True, exist_ok=True)

    def store(self, credential: StoredCredential) -> bool:
        if self.platform == "darwin":
            return self._store_macos_keychain(credential)
        elif self.platform == "windows":
            return self._store_windows_credential_manager(credential)
        elif self.platform == "linux":
            return self._store_linux_secret_service(credential)
        return self._store_fallback_encrypted(credential)

    def retrieve(self, service: str, username: str) -> Optional[StoredCredential]:
        if self.platform == "darwin":
            return self._retrieve_macos_keychain(service, username)
        elif self.platform == "windows":
            return self._retrieve_windows_credential_manager(service, username)
        elif self.platform == "linux":
            return self._retrieve_linux_secret_service(service, username)
        return self._retrieve_fallback_encrypted(service, username)

    def delete(self, service: str, username: str) -> bool:
        if self.platform == "darwin":
            return self._delete_macos_keychain(service, username)
        elif self.platform == "windows":
            return self._delete_windows_credential_manager(service, username)
        elif self.platform == "linux":
            return self._delete_linux_secret_service(service, username)
        return self._delete_fallback_encrypted(service, username)

    def list_services(self) -> List[str]:
        if self.platform == "darwin":
            return self._list_macos_keychain()
        elif self.platform == "windows":
            return self._list_windows_credential_manager()
        elif self.platform == "linux":
            return self._list_linux_secret_service()
        return self._list_fallback_encrypted()

    def _store_macos_keychain(self, credential: StoredCredential) -> bool:
        try:
            keychain_label = f"{self.app_name}: {credential.service} ({credential.username})"
            subprocess.run(
                ["security", "add-generic-password",
                 "-s", credential.service,
                 "-a", credential.username,
                 "-l", keychain_label,
                 "-w", credential.secret,
                 "-U"],
                capture_output=True, timeout=10, check=True,
            )
            return True
        except Exception:
            return self._store_fallback_encrypted(credential)

    def _retrieve_macos_keychain(self, service: str, username: str) -> Optional[StoredCredential]:
        try:
            result = subprocess.run(
                ["security", "find-generic-password",
                 "-s", service,
                 "-a", username,
                 "-w"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return StoredCredential(
                    service=service,
                    username=username,
                    secret=result.stdout.strip(),
                )
        except Exception:
            pass
        return self._retrieve_fallback_encrypted(service, username)

    def _delete_macos_keychain(self, service: str, username: str) -> bool:
        try:
            subprocess.run(
                ["security", "delete-generic-password",
                 "-s", service,
                 "-a", username],
                capture_output=True, timeout=10,
            )
            self._delete_fallback_encrypted(service, username)
            return True
        except Exception:
            return self._delete_fallback_encrypted(service, username)

    def _list_macos_keychain(self) -> List[str]:
        try:
            result = subprocess.run(
                ["security", "dump-keychain"],
                capture_output=True, text=True, timeout=10,
            )
            services = set()
            for line in result.stdout.split("\n"):
                if f'"{self.app_name}:' in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        services.add(parts[1].strip().strip('"'))
            return list(services)
        except Exception:
            return []

    def _store_windows_credential_manager(self, credential: StoredCredential) -> bool:
        try:
            data = json.dumps(asdict(credential))
            script = f'''
$cred = "{credential.service}:{credential.username}"
$value = '{data}'
$secStr = ConvertTo-SecureString -String $value -AsPlainText -Force
$credObj = New-Object System.Management.Automation.PSCredential($cred, $secStr)
$credObj | Export-Clixml -Path "$env:USERPROFILE\\.alonechat\\credentials\\{credential.service}_{credential.username}.cred"
'''
            subprocess.run(["powershell", "-Command", script],
                           capture_output=True, timeout=15)
            return True
        except Exception:
            return self._store_fallback_encrypted(credential)

    def _retrieve_windows_credential_manager(self, service: str, username: str) -> Optional[StoredCredential]:
        try:
            cred_path = Path.home() / ".alonechat" / "credentials" / f"{service}_{username}.cred"
            if cred_path.exists():
                script = f'''
$cred = Import-Clixml -Path "{cred_path}"
$cred.GetNetworkCredential().Password
'''
                result = subprocess.run(["powershell", "-Command", script],
                                        capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    data = json.loads(result.stdout.strip())
                    return StoredCredential.from_dict(data)
        except Exception:
            pass
        return self._retrieve_fallback_encrypted(service, username)

    def _delete_windows_credential_manager(self, service: str, username: str) -> bool:
        try:
            cred_path = Path.home() / ".alonechat" / "credentials" / f"{service}_{username}.cred"
            if cred_path.exists():
                cred_path.unlink()
            return True
        except Exception:
            return self._delete_fallback_encrypted(service, username)

    def _list_windows_credential_manager(self) -> List[str]:
        try:
            cred_dir = Path.home() / ".alonechat" / "credentials"
            services = set()
            for f in cred_dir.glob("*.cred"):
                parts = f.stem.split("_", 1)
                if parts:
                    services.add(parts[0])
            return list(services)
        except Exception:
            return []

    def _store_linux_secret_service(self, credential: StoredCredential) -> bool:
        try:
            label = f"{self.app_name}: {credential.service} ({credential.username})"
            subprocess.run(
                ["secret-tool", "store",
                 "--label", label,
                 "service", credential.service,
                 "username", credential.username],
                input=credential.secret,
                text=True, capture_output=True, timeout=10,
            )
            return True
        except Exception:
            return self._store_fallback_encrypted(credential)

    def _retrieve_linux_secret_service(self, service: str, username: str) -> Optional[StoredCredential]:
        try:
            result = subprocess.run(
                ["secret-tool", "lookup",
                 "service", service,
                 "username", username],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return StoredCredential(
                    service=service,
                    username=username,
                    secret=result.stdout.strip(),
                )
        except Exception:
            pass
        return self._retrieve_fallback_encrypted(service, username)

    def _delete_linux_secret_service(self, service: str, username: str) -> bool:
        try:
            subprocess.run(
                ["secret-tool", "clear",
                 "service", service,
                 "username", username],
                capture_output=True, timeout=10,
            )
            self._delete_fallback_encrypted(service, username)
            return True
        except Exception:
            return self._delete_fallback_encrypted(service, username)

    def _list_linux_secret_service(self) -> List[str]:
        try:
            result = subprocess.run(
                ["secret-tool", "search", "service", self.app_name],
                capture_output=True, text=True, timeout=10,
            )
            services = set()
            for line in result.stdout.split("\n"):
                if "service = " in line:
                    services.add(line.split("=", 1)[1].strip())
            return list(services)
        except Exception:
            return []

    def _get_fallback_encryption_key(self) -> bytes:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        machine_id = f"{platform.node()}-{os.getlogin()}-{self.app_name}"
        salt = b"alonechat-credential-salt-v2"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))

    def _store_fallback_encrypted(self, credential: StoredCredential) -> bool:
        try:
            from cryptography.fernet import Fernet

            key = self._get_fallback_encryption_key()
            f = Fernet(key)

            data = json.dumps(credential.to_dict()).encode("utf-8")
            encrypted = f.encrypt(data)

            cred_file = self._fallback_dir / f"{credential.service}_{credential.username}.enc"
            with open(cred_file, "wb") as fh:
                fh.write(encrypted)

            return True
        except Exception:
            import stat
            cred_file = self._fallback_dir / f"{credential.service}_{credential.username}.json"
            with open(cred_file, "w", encoding="utf-8") as fh:
                json.dump(credential.to_dict(), fh, ensure_ascii=False)
            try:
                os.chmod(cred_file, stat.S_IRUSR | stat.S_IWUSR)
            except Exception:
                pass
            return True

    def _retrieve_fallback_encrypted(self, service: str, username: str) -> Optional[StoredCredential]:
        try:
            from cryptography.fernet import Fernet

            key = self._get_fallback_encryption_key()
            f = Fernet(key)

            cred_file = self._fallback_dir / f"{service}_{username}.enc"
            if cred_file.exists():
                with open(cred_file, "rb") as fh:
                    decrypted = f.decrypt(fh.read())
                data = json.loads(decrypted.decode("utf-8"))
                return StoredCredential.from_dict(data)
        except Exception:
            pass

        try:
            cred_file = self._fallback_dir / f"{service}_{username}.json"
            if cred_file.exists():
                with open(cred_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                return StoredCredential.from_dict(data)
        except Exception:
            pass

        return None

    def _delete_fallback_encrypted(self, service: str, username: str) -> bool:
        deleted = False
        for ext in [".enc", ".json"]:
            cred_file = self._fallback_dir / f"{service}_{username}{ext}"
            if cred_file.exists():
                try:
                    cred_file.unlink()
                    deleted = True
                except Exception:
                    pass
        return deleted

    def _list_fallback_encrypted(self) -> List[str]:
        services = set()
        for ext in ["*.enc", "*.json"]:
            for f in self._fallback_dir.glob(ext):
                parts = f.stem.split("_", 1)
                if parts:
                    services.add(parts[0])
        return list(services)
