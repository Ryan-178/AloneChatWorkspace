"""
权限管理器 / Permission Manager

管理工具权限和规则 / Manages tool permissions and rules
"""

import json
from pathlib import Path
from typing import Optional
from rich.console import Console

from alonechat.permissions.rules import (
    PermissionRule,
    PermissionMode,
    PermissionAction,
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_DENIED_TOOLS,
    TOOL_DESCRIPTIONS,
)

console = Console()


class PermissionManager:
    """权限管理器 / Permission Manager"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".alonechat"
        self.config_dir = config_dir
        self.config_file = config_dir / "permissions.json"
        
        self.mode = PermissionMode.DEFAULT
        self._allowed: list[str] = list(DEFAULT_ALLOWED_TOOLS)
        self._denied: list[str] = list(DEFAULT_DENIED_TOOLS)
        self._rules: list[PermissionRule] = []
        
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置 / Load config"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                mode_str = data.get("mode", "default")
                try:
                    self.mode = PermissionMode(mode_str)
                except ValueError:
                    self.mode = PermissionMode.DEFAULT
                
                self._allowed = data.get("allowed", DEFAULT_ALLOWED_TOOLS)
                self._denied = data.get("denied", DEFAULT_DENIED_TOOLS)
                
            except Exception:
                pass
    
    def _save_config(self) -> None:
        """保存配置 / Save config"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "mode": self.mode.value,
            "allowed": self._allowed,
            "denied": self._denied,
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def set_mode(self, mode: PermissionMode) -> None:
        """设置权限模式 / Set permission mode"""
        self.mode = mode
        self._save_config()
    
    def allow(self, tool: str) -> None:
        """允许工具 / Allow tool"""
        if tool not in self._allowed:
            self._allowed.append(tool)
        if tool in self._denied:
            self._denied.remove(tool)
        self._save_config()
    
    def deny(self, tool: str) -> None:
        """拒绝工具 / Deny tool"""
        if tool not in self._denied:
            self._denied.append(tool)
        if tool in self._allowed:
            self._allowed.remove(tool)
        self._save_config()
    
    def is_allowed(self, tool_name: str, command: Optional[str] = None) -> bool:
        """
        检查工具是否被允许 / Check if tool is allowed
        
        Returns:
            True if allowed, False if denied, None if needs prompt
        """
        if self.mode == PermissionMode.ACCEPT:
            return True
        
        for tool in self._denied:
            if self._match_tool(tool, tool_name, command):
                return False
        
        for tool in self._allowed:
            if self._match_tool(tool, tool_name, command):
                return True
        
        return False
    
    def needs_prompt(self, tool_name: str) -> bool:
        """检查是否需要提示用户 / Check if needs user prompt"""
        if self.mode == PermissionMode.ACCEPT:
            return False
        if self.mode == PermissionMode.PLAN:
            return True
        
        return tool_name not in self._allowed and tool_name not in self._denied
    
    def _match_tool(
        self,
        pattern: str,
        tool_name: str,
        command: Optional[str] = None,
    ) -> bool:
        """匹配工具模式 / Match tool pattern"""
        if "(" in pattern and ")" in pattern:
            base, scope = pattern.split("(", 1)
            scope = scope.rstrip(")")
            
            if base != tool_name:
                return False
            
            if command and scope in command:
                return True
            return False
        
        if pattern.endswith("*"):
            return tool_name.startswith(pattern[:-1])
        
        return pattern == tool_name
    
    def get_allowed_tools(self) -> list[str]:
        """获取允许的工具列表 / Get allowed tools list"""
        return list(self._allowed)
    
    def get_denied_tools(self) -> list[str]:
        """获取拒绝的工具列表 / Get denied tools list"""
        return list(self._denied)
    
    def get_tool_description(self, tool_name: str) -> str:
        """获取工具描述 / Get tool description"""
        return TOOL_DESCRIPTIONS.get(tool_name, tool_name)
    
    def show_status(self) -> None:
        """显示权限状态 / Show permission status"""
        from rich.table import Table
        
        console.print("\n[bold cyan]权限状态 / Permission Status[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("工具 / Tool", style="cyan")
        table.add_column("描述 / Description")
        table.add_column("状态 / Status")
        
        all_tools = set(self._allowed) | set(self._denied) | set(TOOL_DESCRIPTIONS.keys())
        
        for tool in sorted(all_tools):
            desc = TOOL_DESCRIPTIONS.get(tool, "")
            if tool in self._allowed:
                status = "[green]允许 / Allowed[/green]"
            elif tool in self._denied:
                status = "[red]拒绝 / Denied[/red]"
            else:
                status = "[yellow]提示 / Prompt[/yellow]"
            table.add_row(tool, desc, status)
        
        console.print(table)
        console.print(f"\n[dim]模式 / Mode: {self.mode.value}[/dim]")
        console.print()
