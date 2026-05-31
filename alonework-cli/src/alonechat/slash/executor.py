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
            handle_mode_command,
            copy_command,
            diff_command,
            effort_command,
            files_command,
            hooks_command,
            memory_command,
            rename_command,
            resume_command,
            session_command,
            skills_command,
            tasks_command,
            tag_command,
            theme_command,
            color_command,
            feedback_command,
            fast_command,
            output_style_command,
            share_command,
            stickers_command,
            upgrade_command,
        )
        from alonechat.slash.commands.agents import agents_command
        from alonechat.slash.commands.permissions import permissions_command
        from alonechat.slash.commands.mcp import mcp_slash_command
        from alonechat.slash.commands.rewind import rewind_command
        from alonechat.slash.commands.vim import vim_command
        from alonechat.slash.commands.init import init_slash_command
        from alonechat.slash.commands.statusline import statusline_command
        
        def mode_command_wrapper(args: list, obj: dict, session_manager=None, registry=None) -> str:
            """Mode command wrapper to adapt to slash command signature"""
            mode_manager = obj.get("mode_manager")
            if mode_manager is None:
                from alonechat.modes import CliModeManager
                mode_manager = CliModeManager()
                obj["mode_manager"] = mode_manager
            return handle_mode_command(args, mode_manager)
        
        builtin_commands = [
            SlashCommand(
                name="agents",
                description="管理子代理 / Manage subagents",
                handler=agents_command,
                aliases=["agent"],
                category="agents",
            ),
            SlashCommand(
                name="branch",
                description="管理会话分支 / Manage session branches (v2.1.77)",
                handler=branch_command,
                aliases=["branches"],
                category="session",
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
                name="context",
                description="分析上下文占用并提供优化建议 / Analyze context and suggest optimization (v2.1.74)",
                handler=context_command,
                aliases=["ctx"],
                category="info",
            ),
            SlashCommand(
                name="cost",
                description="显示token使用统计 / Show token usage statistics",
                handler=cost_command,
                category="info",
            ),
            SlashCommand(
                name="doctor",
                description="检查安装健康状态，含版本更新信息 / Check health with version updates (v2.1.6)",
                handler=doctor_command,
                category="debug",
            ),
            SlashCommand(
                name="fork",
                description="分叉当前会话 / Fork current session (v2.1.77)",
                handler=fork_command,
                category="session",
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
                name="mode",
                description="切换交互模式 (plan/agent/yolo) / Switch interaction mode",
                handler=mode_command_wrapper,
                aliases=["mo"],
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
                name="stats",
                description="显示使用统计，支持日期过滤 / Show usage stats with date filter (v2.1.6)",
                handler=stats_command,
                category="info",
            ),
            SlashCommand(
                name="usage",
                description="显示套餐限制和配额使用 / Show plan limits and quota usage (v2.0.0)",
                handler=usage_command,
                category="info",
            ),
            SlashCommand(
                name="vim",
                description="Vim模式 / Vim mode",
                handler=vim_command,
                category="editor",
            ),
            SlashCommand(
                name="statusline",
                description="自定义状态栏 / Custom status bar",
                handler=statusline_command,
                aliases=["sl"],
                category="settings",
            ),
            SlashCommand(
                name="plan",
                description="创建执行计划 / Create execution plan (v2.1.72)",
                handler=plan_command,
                category="actions",
            ),
            SlashCommand(
                name="remote-control",
                description="桥接会话到远程 / Bridge session to remote (v2.1.79)",
                handler=remote_control_command,
                aliases=["remote"],
                category="integrations",
            ),
            SlashCommand(
                name="reload-plugins",
                description="无需重启激活插件更改 / Reload plugins without restart (v2.1.69)",
                handler=reload_plugins_command,
                aliases=["reload"],
                category="actions",
            ),
            SlashCommand(
                name="debug",
                description="排查当前会话故障 / Troubleshoot current session (v2.1.30)",
                handler=debug_command,
                category="debug",
            ),
            SlashCommand(
                name="keybindings",
                description="自定义键盘快捷键 / Custom keyboard shortcuts (v2.1.18)",
                handler=keybindings_command,
                aliases=["keys", "shortcuts"],
                category="settings",
            ),
            SlashCommand(
                name="claude-api",
                description="通过Claude API构建应用 / Build apps with Claude API (v2.1.69)",
                handler=claude_api_command,
                aliases=["claude"],
                category="integrations",
            ),
            SlashCommand(
                name="terminal-setup",
                description="终端配置，支持Kitty/Alacritty/Zed/Warp / Terminal setup (v2.0.74)",
                handler=terminal_setup_command,
                aliases=["terminal"],
                category="settings",
            ),
            SlashCommand(
                name="todos",
                description="列出当前待办事项 / List current todos (v1.0.94)",
                handler=todos_command,
                aliases=["todo"],
                category="info",
            ),
            SlashCommand(
                name="export",
                description="导出对话以便共享 / Export conversation for sharing (v1.0.44)",
                handler=export_command,
                aliases=["save"],
                category="actions",
            ),
            # v2.1.80 新增命令 / New commands
            SlashCommand(
                name="copy",
                description="复制最后响应到剪贴板 / Copy last response to clipboard",
                handler=copy_command,
                aliases=["cp"],
                category="actions",
            ),
            SlashCommand(
                name="diff",
                description="查看未提交的更改 / View uncommitted changes",
                handler=diff_command,
                aliases=["d"],
                category="info",
            ),
            SlashCommand(
                name="effort",
                description="设置模型努力级别 / Set effort level",
                handler=effort_command,
                aliases=["ef"],
                category="settings",
            ),
            SlashCommand(
                name="files",
                description="列出当前上下文中的文件 / List files in context",
                handler=files_command,
                aliases=["f"],
                category="info",
            ),
            SlashCommand(
                name="hooks",
                description="查看工具事件钩子配置 / View hook configurations",
                handler=hooks_command,
                aliases=["hk"],
                category="settings",
            ),
            SlashCommand(
                name="memory",
                description="编辑记忆文件 / Edit memory files",
                handler=memory_command,
                aliases=["mem"],
                category="actions",
            ),
            SlashCommand(
                name="rename",
                description="重命名当前会话 / Rename current session",
                handler=rename_command,
                aliases=["rn"],
                category="session",
            ),
            SlashCommand(
                name="resume",
                description="恢复之前的会话 / Resume previous session",
                handler=resume_command,
                aliases=["res"],
                category="session",
            ),
            SlashCommand(
                name="session",
                description="会话管理 / Session management",
                handler=session_command,
                aliases=["ses"],
                category="session",
            ),
            SlashCommand(
                name="skills",
                description="管理技能 / Manage skills",
                handler=skills_command,
                aliases=["sk"],
                category="actions",
            ),
            SlashCommand(
                name="tasks",
                description="管理后台任务 / Manage background tasks",
                handler=tasks_command,
                aliases=["t"],
                category="info",
            ),
            SlashCommand(
                name="tag",
                description="管理会话标签 / Manage session tags",
                handler=tag_command,
                category="session",
            ),
            SlashCommand(
                name="theme",
                description="切换主题 / Switch theme",
                handler=theme_command,
                category="settings",
            ),
            SlashCommand(
                name="color",
                description="设置代理颜色 / Set agent color",
                handler=color_command,
                category="settings",
            ),
            SlashCommand(
                name="feedback",
                description="发送反馈 / Send feedback",
                handler=feedback_command,
                aliases=["fb"],
                category="actions",
            ),
            SlashCommand(
                name="fast",
                description="切换快速模式 / Toggle fast mode",
                handler=fast_command,
                category="settings",
            ),
            SlashCommand(
                name="output-style",
                description="设置输出样式 / Set output style",
                handler=output_style_command,
                aliases=["os"],
                category="settings",
            ),
            SlashCommand(
                name="share",
                description="分享会话 / Share session",
                handler=share_command,
                category="actions",
            ),
            SlashCommand(
                name="stickers",
                description="趣味贴纸 / Fun stickers",
                handler=stickers_command,
                aliases=["sticker"],
                category="general",
            ),
            SlashCommand(
                name="upgrade",
                description="升级AloneWork CLI / Upgrade AloneWork CLI",
                handler=upgrade_command,
                aliases=["update"],
                category="actions",
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
