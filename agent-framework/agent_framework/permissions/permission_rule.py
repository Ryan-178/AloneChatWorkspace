"""
Permission rules with wildcard and output redirection support
Supports patterns like Bash(npm *), Bash(git * main), Bash(python:*) matching python script.py > out
"""
from __future__ import annotations
import fnmatch
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PermissionMode(str, Enum):
    ACCEPT = "accept"
    PLAN = "plan"
    REVIEW = "review"
    DEFAULT = "default"


class PermissionAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"


_OUTPUT_REDIRECT_PATTERN = re.compile(r'\s*(>+>?|>>?|2>|&>|<|2>&1|&>|<<|<<<|\|)\s*')


def _strip_redirects(command: str) -> str:
    stripped = _OUTPUT_REDIRECT_PATTERN.sub(' ', command)
    return stripped.strip()


def _match_command_pattern(pattern: str, command: str) -> bool:
    if ':' in pattern and not pattern.startswith(':'):
        prefix_part, suffix_part = pattern.split(':', 1)
        if not command.startswith(prefix_part):
            return False
        remaining = command[len(prefix_part):].strip()
        if fnmatch.fnmatch(remaining, suffix_part):
            return True
        return False
    if fnmatch.fnmatch(command, pattern):
        return True
    return False


@dataclass
class PermissionRule:
    tool_pattern: str
    action: PermissionAction = PermissionAction.PROMPT
    command_pattern: Optional[str] = None
    allowed: list[str] = field(default_factory=list)
    denied: list[str] = field(default_factory=list)

    def matches(self, tool_name: str, command: Optional[str] = None, raw_command: Optional[str] = None) -> bool:
        if self.tool_pattern == "*":
            return True
        if not fnmatch.fnmatch(tool_name, self.tool_pattern):
            return False
        if self.command_pattern is None:
            return True
        if command is None:
            return False
        cmd_to_check = command.strip()
        if self.command_pattern.endswith(':') or self.command_pattern.endswith(':*'):
            prefix = self.command_pattern.rstrip(':').rstrip('*')
            if cmd_to_check.startswith(prefix):
                return True
            return False
        if ':' in self.command_pattern and not self.command_pattern.startswith(':'):
            if _match_command_pattern(self.command_pattern, cmd_to_check):
                return True
            return False
        if fnmatch.fnmatch(cmd_to_check, self.command_pattern):
            return True
        return False

    def matches_redirect(self, tool_name: str, raw_command: str) -> bool:
        if not fnmatch.fnmatch(tool_name, self.tool_pattern):
            return False
        stripped = _strip_redirects(raw_command)
        if ':' in self.command_pattern and not self.command_pattern.startswith(':'):
            return _match_command_pattern(self.command_pattern, stripped)
        if self.command_pattern and fnmatch.fnmatch(stripped, self.command_pattern):
            return True
        return self.matches(tool_name, stripped)

    def to_dict(self) -> dict:
        return {
            "tool_pattern": self.tool_pattern,
            "action": self.action.value,
            "command_pattern": self.command_pattern,
            "allowed": self.allowed,
            "denied": self.denied,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PermissionRule":
        return cls(
            tool_pattern=data.get("tool_pattern", ""),
            action=PermissionAction(data.get("action", "prompt")),
            command_pattern=data.get("command_pattern"),
            allowed=data.get("allowed", []),
            denied=data.get("denied", []),
        )


DEFAULT_ALLOWED_TOOLS: list[str] = [
    "Read", "Glob", "Grep", "LS",
]

DEFAULT_DENIED_TOOLS: list[str] = []

TOOL_DESCRIPTIONS: dict[str, str] = {
    "Read": "Read files",
    "Write": "Write files",
    "Edit": "Edit files",
    "Delete": "Delete files",
    "Bash": "Execute commands",
    "Glob": "Search files",
    "Grep": "Search content",
    "LS": "List directory",
    "WebSearch": "Web search",
    "WebFetch": "Fetch web page",
}
