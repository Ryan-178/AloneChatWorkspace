"""
权限规则 / Permission Rules

定义权限规则和模式 / Defines permission rules and modes
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PermissionMode(Enum):
    """权限模式 / Permission mode"""
    ACCEPT = "accept"       # 自动接受所有 / Accept all
    PLAN = "plan"           # 计划模式 / Plan mode
    REVIEW = "review"       # 审查模式 / Review mode
    DEFAULT = "default"     # 默认模式（逐个提示）/ Default mode (prompt each)


class PermissionAction(Enum):
    """权限动作 / Permission action"""
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"


@dataclass
class PermissionRule:
    """
    权限规则 / Permission rule
    
    定义对特定工具的权限 / Defines permission for specific tool
    """
    tool: str               # 工具名称或模式 / Tool name or pattern
    action: PermissionAction  # 权限动作 / Permission action
    scope: Optional[str] = None  # 作用域（如特定命令）/ Scope (e.g., specific command)
    
    def matches(self, tool_name: str, command: Optional[str] = None) -> bool:
        """检查是否匹配 / Check if matches"""
        if self.tool == "*":
            return True
        
        if self.tool.endswith("*"):
            prefix = self.tool[:-1]
            if tool_name.startswith(prefix):
                return True
        
        if self.tool == tool_name:
            if self.scope is None:
                return True
            if command and self.scope in command:
                return True
        
        return False


DEFAULT_ALLOWED_TOOLS: list[str] = [
    "Read",
    "Glob",
    "Grep",
    "LS",
]

DEFAULT_DENIED_TOOLS: list[str] = []

TOOL_DESCRIPTIONS: dict[str, str] = {
    "Read": "读取文件 / Read files",
    "Write": "写入文件 / Write files",
    "Edit": "编辑文件 / Edit files",
    "Delete": "删除文件 / Delete files",
    "Bash": "执行命令 / Execute commands",
    "Glob": "搜索文件 / Search files",
    "Grep": "搜索内容 / Search content",
    "LS": "列出目录 / List directory",
    "WebSearch": "网络搜索 / Web search",
    "WebFetch": "获取网页 / Fetch web page",
}
