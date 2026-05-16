"""
License Manager
许可证管理 - 企业级授权控制
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import secrets
import base64


@dataclass
class LicenseInfo:
    """许可证信息"""
    license_key: str
    customer_id: str
    plan_name: str
    max_concurrent_requests: int
    max_tokens_per_month: int
    expires_at: datetime
    features: list
    created_at: datetime


class LicenseManager:
    """
    许可证管理器
    用于控制API访问权限和配额
    提供基于 HMAC 的许可证签名验证
    """

    def __init__(self, license_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.license_key = license_key
        self._licenses: Dict[str, LicenseInfo] = {}
        self._usage: Dict[str, Dict[str, Any]] = {}

        # 使用提供的密钥或从环境变量获取
        # 生产环境应该从安全存储获取
        if secret_key:
            self._secret_key = secret_key.encode("utf-8")
        else:
            import os
            env_key = os.environ.get("LICENSE_SECRET_KEY")
            if env_key:
                self._secret_key = env_key.encode("utf-8")
            else:
                # 生成随机密钥（仅用于开发，每次重启会变化）
                self._secret_key = secrets.token_bytes(32)

    def _compute_license_signature(self, license_info: LicenseInfo) -> str:
        """计算许可证的 HMAC 签名"""
        # 构建规范的许可证数据
        license_data = {
            "license_key": license_info.license_key,
            "customer_id": license_info.customer_id,
            "plan_name": license_info.plan_name,
            "max_concurrent_requests": license_info.max_concurrent_requests,
            "max_tokens_per_month": license_info.max_tokens_per_month,
            "expires_at": license_info.expires_at.isoformat(),
            "features": sorted(license_info.features),
            "created_at": license_info.created_at.isoformat(),
        }
        canonical = json.dumps(license_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hmac.new(
            self._secret_key,
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _verify_license_signature(self, license_info: LicenseInfo, signature: str) -> bool:
        """验证许可证的 HMAC 签名"""
        expected = self._compute_license_signature(license_info)
        return hmac.compare_digest(expected, signature)

    def create_signed_license(self, license_info: LicenseInfo) -> Dict[str, Any]:
        """创建带签名的许可证（用于颁发许可证）"""
        signature = self._compute_license_signature(license_info)
        return {
            "license_key": license_info.license_key,
            "customer_id": license_info.customer_id,
            "plan_name": license_info.plan_name,
            "max_concurrent_requests": license_info.max_concurrent_requests,
            "max_tokens_per_month": license_info.max_tokens_per_month,
            "expires_at": license_info.expires_at.isoformat(),
            "features": license_info.features,
            "created_at": license_info.created_at.isoformat(),
            "signature": signature,
        }

    def add_license(self, license_info: LicenseInfo, signature: Optional[str] = None):
        """添加许可证 - 需要有效的签名"""
        if signature is None:
            raise ValueError("License signature is required. Use create_signed_license() to generate a signed license.")

        if not self._verify_license_signature(license_info, signature):
            raise ValueError("Invalid license signature. License may have been tampered with.")

        self._licenses[license_info.license_key] = license_info

    def validate_license(self, license_key: str) -> tuple[bool, Optional[str]]:
        """验证许可证有效性"""
        if license_key not in self._licenses:
            return False, "Invalid license key"

        info = self._licenses[license_key]
        if datetime.now() > info.expires_at:
            return False, "License expired"

        return True, None

    def check_quota(self, license_key: str, tokens_used: int) -> tuple[bool, Optional[str]]:
        """检查配额是否超出"""
        valid, msg = self.validate_license(license_key)
        if not valid:
            return False, msg

        if license_key not in self._usage:
            self._usage[license_key] = {
                "tokens_used": 0,
                "concurrent_requests": 0,
                "reset_date": datetime.now() + timedelta(days=30),
            }

        usage = self._usage[license_key]
        info = self._licenses[license_key]

        if usage["tokens_used"] + tokens_used > info.max_tokens_per_month:
            return False, "Token quota exceeded"

        return True, None

    def record_usage(self, license_key: str, tokens_used: int):
        """记录使用情况"""
        if license_key in self._usage:
            self._usage[license_key]["tokens_used"] += tokens_used

    def get_license_info(self, license_key: str) -> Optional[LicenseInfo]:
        """获取许可证信息"""
        return self._licenses.get(license_key)

    def get_usage_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """获取使用信息"""
        return self._usage.get(license_key)
