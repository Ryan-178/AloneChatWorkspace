"""
/fast 命令 - 切换快速模式 / Toggle fast mode

版本 / Version: 2.1.80
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


FAST_MODE_CONFIG = {
    "enabled": False,
    "streaming": True,
    "animations": True,
    "verbose_output": False,
    "confirmations": True,
}


def fast_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    切换快速模式 / Toggle fast mode

    快速模式禁用非必要功能以提升响应速度 /
    Fast mode disables non-essential features for faster responses

    用法 / Usage:
        /fast                  切换快速模式 / Toggle fast mode
        /fast on               启用快速模式 / Enable fast mode
        /fast off              禁用快速模式 / Disable fast mode
        /fast status           显示当前状态 / Show current status
        /fast config           显示配置详情 / Show config details

    快速模式影响 / Fast mode effects:
        - 禁用流式动画 / Disable streaming animations
        - 简化输出格式 / Simplify output format
        - 跳过确认提示 / Skip confirmation prompts
        - 禁用装饰性输出 / Disable decorative output
    """
    fast_config = obj.get("fast_mode", FAST_MODE_CONFIG.copy())

    if not args or args[0] == "toggle":
        fast_config["enabled"] = not fast_config.get("enabled", False)
        obj["fast_mode"] = fast_config
        state = "启用 / Enabled" if fast_config["enabled"] else "禁用 / Disabled"
        console.print(f"[green]✓ 快速模式: {state}[/green]")
        if fast_config["enabled"]:
            fast_config["streaming"] = False
            fast_config["animations"] = False
            fast_config["verbose_output"] = False
            fast_config["confirmations"] = False
            console.print("[dim]已禁用: 动画、流式输出、详细输出、确认提示[/dim]")
            console.print("[dim]Disabled: animations, streaming, verbose, confirmations[/dim]")
        else:
            fast_config["streaming"] = True
            fast_config["animations"] = True
            fast_config["verbose_output"] = False
            fast_config["confirmations"] = True
        return

    action = args[0]

    if action == "on":
        fast_config["enabled"] = True
        fast_config["streaming"] = False
        fast_config["animations"] = False
        fast_config["verbose_output"] = False
        fast_config["confirmations"] = False
        obj["fast_mode"] = fast_config
        console.print("[green]✓ 快速模式已启用 / Fast mode enabled[/green]")
        return

    if action == "off":
        fast_config["enabled"] = False
        fast_config["streaming"] = True
        fast_config["animations"] = True
        fast_config["verbose_output"] = False
        fast_config["confirmations"] = True
        obj["fast_mode"] = fast_config
        console.print("[green]✓ 快速模式已禁用 / Fast mode disabled[/green]")
        return

    if action == "status":
        enabled = fast_config.get("enabled", False)
        state = "[green]启用 / ON[/green]" if enabled else "[dim]禁用 / OFF[/dim]"
        console.print(f"[cyan]快速模式 / Fast mode: {state}[/cyan]")
        return

    if action == "config":
        table = Table(show_header=True, title="快速模式配置 / Fast Mode Config")
        table.add_column("设置 / Setting", style="cyan")
        table.add_column("值 / Value", style="green")
        table.add_column("描述 / Description", style="dim")

        settings = [
            ("enabled", fast_config.get("enabled", False), "快速模式 / Fast mode"),
            ("streaming", fast_config.get("streaming", True), "流式输出 / Streaming"),
            ("animations", fast_config.get("animations", True), "动画效果 / Animations"),
            ("verbose_output", fast_config.get("verbose_output", False), "详细输出 / Verbose"),
            ("confirmations", fast_config.get("confirmations", True), "确认提示 / Confirmations"),
        ]

        for name, value, desc in settings:
            value_str = "[green]开/ON[/green]" if value else "[dim]关/OFF[/dim]"
            table.add_row(name, value_str, desc)

        console.print(table)
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: on, off, status, config[/dim]")
