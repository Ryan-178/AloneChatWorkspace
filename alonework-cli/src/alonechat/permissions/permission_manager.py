"""
Central permission manager with YAML-driven rules
Supports wildcard patterns and output redirection in permission rules
"""
from __future__ import annotations
import os
import fnmatch
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from alonechat.permissions.permission_rule import (
    PermissionRule,
    PermissionMode,
    PermissionAction,
    _strip_redirects,
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_DENIED_TOOLS,
    TOOL_DESCRIPTIONS,
)
from alonechat.configs import get_permissions_config


class PermissionManager:
    _instance: Optional["PermissionManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: Optional[Path] = None):
        if self._initialized:
            return
        self._initialized = True

        if config_dir is None:
            config_dir = Path.home() / ".alonechat"
        self.config_dir = config_dir
        self.config_file = config_dir / "permissions.json"

        self.mode = PermissionMode.DEFAULT
        self._allowed: list[str] = list(DEFAULT_ALLOWED_TOOLS)
        self._denied: list[str] = list(DEFAULT_DENIED_TOOLS)
        self._rules: list[PermissionRule] = []

        self._load_from_yaml()
        self._load_config()

    def _load_from_yaml(self):
        config_data = get_permissions_config()
        yaml_allowed = config_data.get("allowed_tools")
        yaml_denied = config_data.get("denied_tools")
        if yaml_allowed:
            self._allowed = list(yaml_allowed)
        if yaml_denied:
            self._denied = list(yaml_denied)

        yaml_rules = config_data.get("rules", [])
        for rule_data in yaml_rules:
            self._rules.append(PermissionRule.from_dict(rule_data))

        mode_str = config_data.get("default_mode", "default")
        try:
            self.mode = PermissionMode(mode_str)
        except ValueError:
            self.mode = PermissionMode.DEFAULT

    def _load_config(self) -> None:
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                mode_str = data.get("mode", "default")
                try:
                    self.mode = PermissionMode(mode_str)
                except ValueError:
                    self.mode = PermissionMode.DEFAULT

                self._allowed = data.get("allowed", self._allowed)
                self._denied = data.get("denied", self._denied)

                rules_data = data.get("rules", [])
                for rd in rules_data:
                    rule = PermissionRule.from_dict(rd)
                    existing = [r for r in self._rules if r.tool_pattern == rule.tool_pattern]
                    if existing:
                        self._rules.remove(existing[0])
                    self._rules.append(rule)

            except Exception:
                pass

    def _save_config(self) -> None:
        import json
        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "mode": self.mode.value,
            "allowed": self._allowed,
            "denied": self._denied,
            "rules": [r.to_dict() for r in self._rules],
        }

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_mode(self, mode: PermissionMode) -> None:
        self.mode = mode
        self._save_config()

    def allow(self, tool: str, command_pattern: Optional[str] = None) -> None:
        if command_pattern:
            self._rules.append(PermissionRule(
                tool_pattern=tool,
                action=PermissionAction.ALLOW,
                command_pattern=command_pattern,
            ))
        else:
            if tool not in self._allowed:
                self._allowed.append(tool)
            if tool in self._denied:
                self._denied.remove(tool)
        self._save_config()

    def deny(self, tool: str, command_pattern: Optional[str] = None) -> None:
        if command_pattern:
            self._rules.append(PermissionRule(
                tool_pattern=tool,
                action=PermissionAction.DENY,
                command_pattern=command_pattern,
            ))
        else:
            if tool not in self._denied:
                self._denied.append(tool)
            if tool in self._allowed:
                self._allowed.remove(tool)
        self._save_config()

    def add_rule(self, rule: PermissionRule) -> None:
        self._rules.append(rule)
        self._save_config()

    def remove_rule(self, tool_pattern: str, command_pattern: Optional[str] = None) -> bool:
        before = len(self._rules)
        self._rules = [
            r for r in self._rules
            if not (r.tool_pattern == tool_pattern and r.command_pattern == command_pattern)
        ]
        if len(self._rules) < before:
            self._save_config()
            return True
        return False

    def is_allowed(
        self,
        tool_name: str,
        command: Optional[str] = None,
        raw_command: Optional[str] = None,
    ) -> bool:
        cmd = command or raw_command

        for rule in self._rules:
            if rule.action == PermissionAction.DENY:
                if cmd and raw_command and rule.matches_redirect(tool_name, raw_command):
                    return False
                if rule.matches(tool_name, cmd, raw_command):
                    return False

        for rule in self._rules:
            if rule.action == PermissionAction.ALLOW:
                if cmd and raw_command and rule.matches_redirect(tool_name, raw_command):
                    return True
                if rule.matches(tool_name, cmd, raw_command):
                    return True

        if self.mode == PermissionMode.ACCEPT:
            return True

        for tool in self._denied:
            if self._match_tool(tool, tool_name, cmd):
                return False

        for tool in self._allowed:
            if self._match_tool(tool, tool_name, cmd):
                return True

        return False

    def needs_prompt(self, tool_name: str) -> bool:
        if self.mode == PermissionMode.ACCEPT:
            return False
        if self.mode == PermissionMode.PLAN:
            return True

        for rule in self._rules:
            if rule.tool_pattern == "*" or fnmatch.fnmatch(tool_name, rule.tool_pattern):
                return rule.action == PermissionAction.PROMPT

        return tool_name not in self._allowed and tool_name not in self._denied

    def _match_tool(
        self,
        pattern: str,
        tool_name: str,
        command: Optional[str] = None,
    ) -> bool:
        if pattern.endswith("*"):
            return tool_name.startswith(pattern[:-1])
        if pattern == "*":
            return True

        if "(" in pattern and ")" in pattern:
            base, scope = pattern.split("(", 1)
            scope = scope.rstrip(")")

            if not fnmatch.fnmatch(tool_name, base):
                return False

            if command:
                stripped_cmd = _strip_redirects(command) if command else command
                if fnmatch.fnmatch(stripped_cmd, scope):
                    return True
                if scope in stripped_cmd:
                    return True
            return False

        return pattern == tool_name

    def get_rules(self) -> list[PermissionRule]:
        return list(self._rules)

    def get_allowed_tools(self) -> list[str]:
        return list(self._allowed)

    def get_denied_tools(self) -> list[str]:
        return list(self._denied)

    def get_tool_description(self, tool_name: str) -> str:
        return TOOL_DESCRIPTIONS.get(tool_name, tool_name)

    def reload(self) -> None:
        self._rules.clear()
        self._load_from_yaml()
        self._load_config()
