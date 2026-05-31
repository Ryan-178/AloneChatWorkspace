"""
Enterprise managed settings module
Supports macOS plist, Windows Registry, and YAML-based enterprise configuration
"""
from agent_framework.enterprise.managed_settings import ManagedSettings
from agent_framework.enterprise.enterprise_manager import EnterpriseManager

__all__ = [
    "ManagedSettings",
    "EnterpriseManager",
]
