"""
Slash命令执行器 / Slash Command Executor

执行slash命令 / Executes slash commands
"""

from typing import Any, Optional
from rich.console import Console

from alonechat.slash.registry import SlashCommandRegistry, SlashCommand
from alonechat.slash.parser import SlashCommandParser
from alonechat.slash.custom_loader import CustomCommandLoader

console = Console()


class SlashCommandExecutor:
    """Slash命令执行器 / Slash Command Executor"""
    
    def __init__(self, obj: dict, session_manager=None):
        self.obj = obj
        self.session_manager = session_manager
        self.registry = SlashCommandRegistry()
        self.custom_loader = CustomCommandLoader()
        self._register_builtin_commands()
        self._register_custom_commands()
    
    def _register_builtin_commands(self) -> None:
        """注册内置命令 / Register built-in commands"""
        from alonechat.slash.commands import (
            clear_command,
            compact_command,
            config_command,
            cost_command,
            doctor_command,
            help_command,
            model_command,
            review_command,
            status_command,
            usage_command,
        )
        from alonechat.slash.commands.agents import agents_command
        from alonechat.slash.commands.permissions import permissions_command
        from alonechat.slash.commands.mcp import mcp_slash_command
        from alonechat.slash.commands.rewind import rewind_command
        from alonechat.slash.commands.vim import vim_command
        from alonechat.slash.commands.init import init_slash_command
        
        builtin_commands = [
            SlashCommand(
                name="agents",
                description="管理子代理 / Manage subagents",
                handler=agents_command,
                aliases=["agent"],
                category="agents",
            ),
            SlashCommand(
                name="clear",
                description="清除对话历史 / Clear conversation history",
                handler=clear_command,
                aliases=["cls"],
                category="session",
            ),
            SlashCommand(
                name="compact",
                description="压缩对话上下文 / Compact conversation context",
                handler=compact_command,
                category="session",
            ),
            SlashCommand(
                name="config",
                description="打开配置界面 / Open config interface",
                handler=config_command,
                aliases=["cfg"],
                category="settings",
            ),
            SlashCommand(
                name="cost",
                description="显示token使用统计 / Show token usage statistics",
                handler=cost_command,
                category="info",
            ),
            SlashCommand(
                name="doctor",
                description="检查安装健康状态 / Check installation health",
                handler=doctor_command,
                category="debug",
            ),
            SlashCommand(
                name="help",
                description="显示帮助信息 / Show help information",
                handler=help_command,
                aliases=["h", "?"],
                category="general",
            ),
            SlashCommand(
                name="mcp",
                description="管理MCP服务器 / Manage MCP servers",
                handler=mcp_slash_command,
                category="integrations",
            ),
            SlashCommand(
                name="model",
                description="切换模型 / Switch model",
                handler=model_command,
                aliases=["m"],
                category="settings",
            ),
            SlashCommand(
                name="permissions",
                description="管理权限 / Manage permissions",
                handler=permissions_command,
                aliases=["perm"],
                category="settings",
            ),
            SlashCommand(
                name="init",
                description="初始化项目 / Initialize project",
                handler=init_slash_command,
                category="project",
            ),
            SlashCommand(
                name="review",
                description="请求代码审查 / Request code review",
                handler=review_command,
                aliases=["r"],
                category="actions",
            ),
            SlashCommand(
                name="rewind",
                description="回退对话 / Rewind conversation",
                handler=rewind_command,
                aliases=["rw"],
                category="session",
            ),
            SlashCommand(
                name="status",
                description="显示当前状态 / Show current status",
                handler=status_command,
                aliases=["st"],
                category="info",
            ),
            SlashCommand(
                name="usage",
                description="显示使用限制 / Show usage limits",
                handler=usage_command,
                category="info",
            ),
            SlashCommand(
                name="vim",
                description="Vim模式 / Vim mode",
                handler=vim_command,
                category="editor",
            ),
        ]
        
        for cmd in builtin_commands:
            self.registry.register(cmd)
    
    def _register_custom_commands(self) -> None:
        """注册自定义命令 / Register custom commands"""
        custom_commands = self.custom_loader.load_all()
        
        for custom_cmd in custom_commands:
            slash_cmd = self.custom_loader.to_slash_command(custom_cmd)
            self.registry.register(slash_cmd)
    
    def execute(self, name: str, args: list[str] = None) -> Any:
        """执行命令 / Execute command"""
        args = args or []
        
        command = self.registry.get(name)
        
        if command is None:
            console.print(f"[red]未知命令 / Unknown command: /{name}[/red]")
            console.print("[dim]输入 /help 查看可用命令 / Type /help for available commands[/dim]")
            return None
        
        try:
            return command.handler(
                args=args,
                obj=self.obj,
                session_manager=self.session_manager,
                registry=self.registry,
            )
        except Exception as e:
            console.print(f"[red]命令执行错误 / Command execution error: {e}[/red]")
            return None
    
    def execute_raw(self, text: str) -> Any:
        """执行原始命令文本 / Execute raw command text"""
        parsed = SlashCommandParser.parse(text)
        
        if not parsed.is_valid:
            console.print(f"[red]{parsed.error}[/red]")
            return None
        
        return self.execute(parsed.name, parsed.args)
    
    def get_completions(self, prefix: str) -> list[str]:
        """获取补全建议 / Get completion suggestions"""
        return self.registry.get_completions(prefix)
    
    def list_commands(self, category: Optional[str] = None) -> list[SlashCommand]:
        """列出所有命令 / List all commands"""
        return self.registry.list_commands(category)
