"""
Enterprise managed settings module
Supports macOS plist, Windows Registry, and YAML-based enterprise configuration
"""
from alonechat.enterprise.managed_settings import ManagedSettings
from alonechat.enterprise.enterprise_manager import EnterpriseManager

__all__ = [
    "ManagedSettings",
    "EnterpriseManager",
]
