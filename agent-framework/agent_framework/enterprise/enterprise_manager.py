"""
Enterprise settings manager - enforces organizational policies via managed settings
Overrides local config with enterprise-deployed policies from plist/registry/YAML
"""
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agent_framework.enterprise.managed_settings import ManagedSettings


@dataclass
class EnterprisePolicy:
    allowed_commands: List[str] = field(default_factory=list)
    forbidden_commands: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    denied_tools: List[str] = field(default_factory=list)
    default_permission_mode: str = "default"
    max_concurrent_sessions: int = 10
    enable_audit_logging: bool = True
    enable_data_protection: bool = True
    allowed_output_formats: List[str] = field(default_factory=lambda: ["markdown", "txt"])
    api_rate_limit: int = 60
    allowed_models: List[str] = field(default_factory=list)
    enterprise_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "EnterprisePolicy":
        return cls(
            allowed_commands=data.get("allowed_commands", []),
            forbidden_commands=data.get("forbidden_commands", []),
            allowed_tools=data.get("allowed_tools", []),
            denied_tools=data.get("denied_tools", []),
            default_permission_mode=data.get("default_permission_mode", "default"),
            max_concurrent_sessions=data.get("max_concurrent_sessions", 10),
            enable_audit_logging=data.get("enable_audit_logging", True),
            enable_data_protection=data.get("enable_data_protection", True),
            allowed_output_formats=data.get("allowed_output_formats", ["markdown", "txt"]),
            api_rate_limit=data.get("api_rate_limit", 60),
            allowed_models=data.get("allowed_models", []),
            enterprise_config=data.get("enterprise_config", {}),
        )

    def to_dict(self) -> dict:
        return {
            "allowed_commands": self.allowed_commands,
            "forbidden_commands": self.forbidden_commands,
            "allowed_tools": self.allowed_tools,
            "denied_tools": self.denied_tools,
            "default_permission_mode": self.default_permission_mode,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "enable_audit_logging": self.enable_audit_logging,
            "enable_data_protection": self.enable_data_protection,
            "allowed_output_formats": self.allowed_output_formats,
            "api_rate_limit": self.api_rate_limit,
            "allowed_models": self.allowed_models,
            "enterprise_config": self.enterprise_config,
        }


class EnterpriseManager:
    _instance: Optional["EnterpriseManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._managed_settings = ManagedSettings()
        self._policy = self._load_policy()

    def _load_policy(self) -> EnterprisePolicy:
        all_settings = self._managed_settings.get_all()
        policy = EnterprisePolicy()
        policy.allowed_commands = all_settings.get("allowed_commands", policy.allowed_commands)
        policy.forbidden_commands = all_settings.get("forbidden_commands", policy.forbidden_commands)
        policy.allowed_tools = all_settings.get("allowed_tools", policy.allowed_tools)
        policy.denied_tools = all_settings.get("denied_tools", policy.denied_tools)
        policy.default_permission_mode = all_settings.get("default_permission_mode", policy.default_permission_mode)
        policy.max_concurrent_sessions = all_settings.get("max_concurrent_sessions", policy.max_concurrent_sessions)
        policy.enable_audit_logging = all_settings.get("enable_audit_logging", policy.enable_audit_logging)
        policy.enable_data_protection = all_settings.get("enable_data_protection", policy.enable_data_protection)
        policy.allowed_output_formats = all_settings.get("allowed_output_formats", policy.allowed_output_formats)
        policy.api_rate_limit = all_settings.get("api_rate_limit", policy.api_rate_limit)
        policy.allowed_models = all_settings.get("allowed_models", policy.allowed_models)
        policy.enterprise_config = all_settings.get("enterprise_config", {})
        return policy

    @property
    def policy(self) -> EnterprisePolicy:
        return self._policy

    def is_command_allowed(self, command: str) -> bool:
        cmd_name = command.split()[0] if command else ""
        if cmd_name in self._policy.forbidden_commands:
            return False
        if self._policy.allowed_commands:
            return cmd_name in self._policy.allowed_commands
        return True

    def is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name in self._policy.denied_tools:
            return False
        if self._policy.allowed_tools:
            return tool_name in self._policy.allowed_tools
        return True

    def is_model_allowed(self, model_name: str) -> bool:
        if not self._policy.allowed_models:
            return True
        return model_name in self._policy.allowed_models

    def get_merged_config(self, local_config: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(local_config)
        if self._policy.allowed_commands:
            merged["allowed_commands"] = self._policy.allowed_commands
        if self._policy.forbidden_commands:
            merged["forbidden_commands"] = self._policy.forbidden_commands
        if self._policy.default_permission_mode != "default":
            merged["permission_mode"] = self._policy.default_permission_mode
        if self._policy.enterprise_config:
            merged["enterprise"] = self._policy.enterprise_config
        return merged

    def reload(self) -> None:
        self._managed_settings = ManagedSettings()
        self._policy = self._load_policy()

    def to_dict(self) -> dict:
        return self._policy.to_dict()
