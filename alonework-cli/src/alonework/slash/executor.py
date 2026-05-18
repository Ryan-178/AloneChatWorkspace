"""
Slashå½ä»¤æ§è¡å?/ Slash Command Executor

æ§è¡slashå½ä»¤ / Executes slash commands
"""

from typing import Any, Optional
from rich.console import Console

from alonework.slash.registry import SlashCommandRegistry, SlashCommand
from alonework.slash.parser import SlashCommandParser
from alonework.slash.custom_loader import CustomCommandLoader

console = Console()


class SlashCommandExecutor:
    """Slashå½ä»¤æ§è¡å?/ Slash Command Executor"""
    
    def __init__(self, obj: dict, session_manager=None):
        self.obj = obj
        self.session_manager = session_manager
        self.registry = SlashCommandRegistry()
        self.custom_loader = CustomCommandLoader()
        self._register_builtin_commands()
        self._register_custom_commands()
    
    def _register_builtin_commands(self) -> None:
        """æ³¨ååç½®å½ä»¤ / Register built-in commands"""
        from alonework.slash.commands import (
            clear_command,
            compact_command,
            config_command,
            context_command,
            cost_command,
            doctor_command,
            help_command,
            model_command,
            review_command,
            stats_command,
            status_command,
            usage_command,
            fork_command,
            branch_command,
            plan_command,
            remote_control_command,
            reload_plugins_command,
            debug_command,
            keybindings_command,
            claude_api_command,
            terminal_setup_command,
            todos_command,
            export_command,
        )
        from alonework.slash.commands.agents import agents_command
        from alonework.slash.commands.permissions import permissions_command
        from alonework.slash.commands.mcp import mcp_slash_command
        from alonework.slash.commands.rewind import rewind_command
        from alonework.slash.commands.vim import vim_command
        from alonework.slash.commands.init import init_slash_command
        from alonework.slash.commands.statusline import statusline_command
        
        builtin_commands = [
            SlashCommand(
                name="agents",
                description="ç®¡çå­ä»£ç?/ Manage subagents",
                handler=agents_command,
                aliases=["agent"],
                category="agents",
            ),
            SlashCommand(
                name="branch",
                description="ç®¡çä¼è¯åæ¯ / Manage session branches (v2.1.77)",
                handler=branch_command,
                aliases=["branches"],
                category="session",
            ),
            SlashCommand(
                name="clear",
                description="æ¸é¤å¯¹è¯åå² / Clear conversation history",
                handler=clear_command,
                aliases=["cls"],
                category="session",
            ),
            SlashCommand(
                name="compact",
                description="åç¼©å¯¹è¯ä¸ä¸æ?/ Compact conversation context",
                handler=compact_command,
                category="session",
            ),
            SlashCommand(
                name="config",
                description="æå¼éç½®çé¢ / Open config interface",
                handler=config_command,
                aliases=["cfg"],
                category="settings",
            ),
            SlashCommand(
                name="context",
                description="åæä¸ä¸æå ç¨å¹¶æä¾ä¼åå»ºè®® / Analyze context and suggest optimization (v2.1.74)",
                handler=context_command,
                aliases=["ctx"],
                category="info",
            ),
            SlashCommand(
                name="cost",
                description="æ¾ç¤ºtokenä½¿ç¨ç»è®¡ / Show token usage statistics",
                handler=cost_command,
                category="info",
            ),
            SlashCommand(
                name="doctor",
                description="æ£æ¥å®è£å¥åº·ç¶æï¼å«çæ¬æ´æ°ä¿¡æ?/ Check health with version updates (v2.1.6)",
                handler=doctor_command,
                category="debug",
            ),
            SlashCommand(
                name="fork",
                description="ååå½åä¼è¯ / Fork current session (v2.1.77)",
                handler=fork_command,
                category="session",
            ),
            SlashCommand(
                name="help",
                description="æ¾ç¤ºå¸®å©ä¿¡æ¯ / Show help information",
                handler=help_command,
                aliases=["h", "?"],
                category="general",
            ),
            SlashCommand(
                name="mcp",
                description="ç®¡çMCPæå¡å?/ Manage MCP servers",
                handler=mcp_slash_command,
                category="integrations",
            ),
            SlashCommand(
                name="model",
                description="åæ¢æ¨¡å / Switch model",
                handler=model_command,
                aliases=["m"],
                category="settings",
            ),
            SlashCommand(
                name="permissions",
                description="ç®¡çæé / Manage permissions",
                handler=permissions_command,
                aliases=["perm"],
                category="settings",
            ),
            SlashCommand(
                name="init",
                description="åå§åé¡¹ç?/ Initialize project",
                handler=init_slash_command,
                category="project",
            ),
            SlashCommand(
                name="review",
                description="è¯·æ±ä»£ç å®¡æ¥ / Request code review",
                handler=review_command,
                aliases=["r"],
                category="actions",
            ),
            SlashCommand(
                name="rewind",
                description="åéå¯¹è¯ / Rewind conversation",
                handler=rewind_command,
                aliases=["rw"],
                category="session",
            ),
            SlashCommand(
                name="status",
                description="æ¾ç¤ºå½åç¶æ?/ Show current status",
                handler=status_command,
                aliases=["st"],
                category="info",
            ),
            SlashCommand(
                name="stats",
                description="æ¾ç¤ºä½¿ç¨ç»è®¡ï¼æ¯ææ¥æè¿æ»?/ Show usage stats with date filter (v2.1.6)",
                handler=stats_command,
                category="info",
            ),
            SlashCommand(
                name="usage",
                description="æ¾ç¤ºå¥é¤éå¶åéé¢ä½¿ç?/ Show plan limits and quota usage (v2.0.0)",
                handler=usage_command,
                category="info",
            ),
            SlashCommand(
                name="vim",
                description="Vimæ¨¡å¼ / Vim mode",
                handler=vim_command,
                category="editor",
            ),
            SlashCommand(
                name="statusline",
                description="èªå®ä¹ç¶ææ  / Custom status bar",
                handler=statusline_command,
                aliases=["sl"],
                category="settings",
            ),
            SlashCommand(
                name="plan",
                description="åå»ºæ§è¡è®¡å / Create execution plan (v2.1.72)",
                handler=plan_command,
                category="actions",
            ),
            SlashCommand(
                name="remote-control",
                description="æ¡¥æ¥ä¼è¯å°è¿ç¨?/ Bridge session to remote (v2.1.79)",
                handler=remote_control_command,
                aliases=["remote"],
                category="integrations",
            ),
            SlashCommand(
                name="reload-plugins",
                description="æ ééå¯æ¿æ´»æä»¶æ´æ?/ Reload plugins without restart (v2.1.69)",
                handler=reload_plugins_command,
                aliases=["reload"],
                category="actions",
            ),
            SlashCommand(
                name="debug",
                description="ææ¥å½åä¼è¯æé / Troubleshoot current session (v2.1.30)",
                handler=debug_command,
                category="debug",
            ),
            SlashCommand(
                name="keybindings",
                description="èªå®ä¹é®çå¿«æ·é® / Custom keyboard shortcuts (v2.1.18)",
                handler=keybindings_command,
                aliases=["keys", "shortcuts"],
                category="settings",
            ),
            SlashCommand(
                name="claude-api",
                description="éè¿Claude APIæå»ºåºç¨ / Build apps with Claude API (v2.1.69)",
                handler=claude_api_command,
                aliases=["claude"],
                category="integrations",
            ),
            SlashCommand(
                name="terminal-setup",
                description="ç»ç«¯éç½®ï¼æ¯æKitty/Alacritty/Zed/Warp / Terminal setup (v2.0.74)",
                handler=terminal_setup_command,
                aliases=["terminal"],
                category="settings",
            ),
            SlashCommand(
                name="todos",
                description="ååºå½åå¾åäºé¡¹ / List current todos (v1.0.94)",
                handler=todos_command,
                aliases=["todo"],
                category="info",
            ),
            SlashCommand(
                name="export",
                description="å¯¼åºå¯¹è¯ä»¥ä¾¿å±äº« / Export conversation for sharing (v1.0.44)",
                handler=export_command,
                aliases=["save"],
                category="actions",
            ),
        ]
        
        for cmd in builtin_commands:
            self.registry.register(cmd)
    
    def _register_custom_commands(self) -> None:
        """æ³¨åèªå®ä¹å½ä»?/ Register custom commands"""
        custom_commands = self.custom_loader.load_all()
        
        for custom_cmd in custom_commands:
            slash_cmd = self.custom_loader.to_slash_command(custom_cmd)
            self.registry.register(slash_cmd)
    
    def execute(self, name: str, args: list[str] = None) -> Any:
        """æ§è¡å½ä»¤ / Execute command"""
        args = args or []
        
        command = self.registry.get(name)
        
        if command is None:
            console.print(f"[red]æªç¥å½ä»¤ / Unknown command: /{name}[/red]")
            console.print("[dim]è¾å¥ /help æ¥çå¯ç¨å½ä»¤ / Type /help for available commands[/dim]")
            return None
        
        try:
            return command.handler(
                args=args,
                obj=self.obj,
                session_manager=self.session_manager,
                registry=self.registry,
            )
        except Exception as e:
            console.print(f"[red]å½ä»¤æ§è¡éè¯¯ / Command execution error: {e}[/red]")
            return None
    
    def execute_raw(self, text: str) -> Any:
        """æ§è¡åå§å½ä»¤ææ¬ / Execute raw command text"""
        parsed = SlashCommandParser.parse(text)
        
        if not parsed.is_valid:
            console.print(f"[red]{parsed.error}[/red]")
            return None
        
        return self.execute(parsed.name, parsed.args)
    
    def get_completions(self, prefix: str) -> list[str]:
        """è·åè¡¥å¨å»ºè®® / Get completion suggestions"""
        return self.registry.get_completions(prefix)
    
    def list_commands(self, category: Optional[str] = None) -> list[SlashCommand]:
        """ååºææå½ä»?/ List all commands"""
        return self.registry.list_commands(category)
