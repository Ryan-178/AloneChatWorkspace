"""
/statusline 命令 - 自定义状态栏 / Custom status bar

提供 / Provides:
- 自定义终端提示符 / Custom terminal prompt
- 状态栏格式配置 / Status bar format configuration
- 实时状态更新 / Real-time status updates
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from alonechat.configs import config

console = Console()


def statusline_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    自定义状态栏 / Custom status bar

    用法 / Usage:
        /statusline                        - 显示当前状态栏配置 / Show current status bar config
        /statusline set <format>           - 设置状态栏格式 / Set status bar format
        /statusline reset                  - 重置为默认 / Reset to default
        /statusline toggle                 - 切换显示/隐藏 / Toggle show/hide
    """
    if not args:
        _show_current_statusline(obj)
        return

    subcommand = args[0].lower()

    if subcommand == "set" and len(args) > 1:
        _set_statusline_format(" ".join(args[1:]), obj)
    elif subcommand == "reset":
        _reset_statusline(obj)
    elif subcommand == "toggle":
        _toggle_statusline(obj)
    else:
        console.print("[red]用法 / Usage: /statusline [set <format>|reset|toggle][/red]")
        console.print("[dim]示例 / Example: /statusline set 'AloneChat | {model} | {tokens} tokens'[/dim]")


def _show_current_statusline(obj: dict) -> None:
    """显示当前状态栏配置 / Show current status bar configuration"""
    from alonechat import __version__

    statusline_config = obj.get("_statusline_config", {})
    format_str = statusline_config.get("format", obj.get("_statusline_format", "AloneChat | {model}"))
    enabled = statusline_config.get("enabled", obj.get("_statusline_enabled", True))
    current_format = statusline_config.get("format", format_str)

    table = Table(show_header=True)
    table.add_column("项目 / Item", style="cyan")
    table.add_column("值 / Value", style="green")

    table.add_row("版本 / Version", __version__)
    table.add_row("状态栏 / Status bar", "启用 / Enabled" if enabled else "禁用 / Disabled")
    table.add_row("格式 / Format", current_format)

    model_name = obj.get("model_name", "deepseek-v4-flash")
    preview = current_format.format(model=model_name, tokens="0", session="current")
    table.add_row("预览 / Preview", preview)

    console.print(Panel(table, title="[bold cyan]状态栏配置 / Status Bar Config[/bold cyan]"))
    console.print()
    console.print("[dim]可用变量 / Available variables:[/dim]")
    console.print("  [cyan]{model}[/cyan]    - 当前模型 / Current model")
    console.print("  [cyan]{tokens}[/cyan]   - Token使用量 / Token usage")
    console.print("  [cyan]{session}[/cyan]  - 会话名称 / Session name")
    console.print("  [cyan]{mode}[/cyan]     - 当前模式 / Current mode")
    console.print("  [cyan]{cwd}[/cyan]      - 工作目录 / Working directory\n")


def _set_statusline_format(format_str: str, obj: dict) -> None:
    """设置状态栏格式 / Set status bar format"""
    if "_statusline_config" not in obj:
        obj["_statusline_config"] = {}
    obj["_statusline_config"]["format"] = format_str
    obj["_statusline_format"] = format_str
    console.print(f"[green]状态栏格式已更新 / Status bar format updated:[/green]")
    console.print(f"[cyan]{format_str}[/cyan]")


def _reset_statusline(obj: dict) -> None:
    """重置状态栏 / Reset status bar"""
    default_format = "AloneChat | {model}"
    if "_statusline_config" in obj:
        obj["_statusline_config"]["format"] = default_format
    obj["_statusline_format"] = default_format
    obj["_statusline_enabled"] = True
    console.print("[green]状态栏已重置为默认 / Status bar reset to default[/green]")


def _toggle_statusline(obj: dict) -> None:
    """切换状态栏显示 / Toggle status bar display"""
    if "_statusline_config" not in obj:
        obj["_statusline_config"] = {}
    current = obj["_statusline_config"].get("enabled", obj.get("_statusline_enabled", True))
    obj["_statusline_config"]["enabled"] = not current
    obj["_statusline_enabled"] = not current
    status = "启用 / Enabled" if not current else "禁用 / Disabled"
    console.print(f"[green]状态栏已{status} / Status bar {status}[/green]")


def render_statusline(obj: dict, tokens: Optional[int] = None) -> str:
    """
    渲染状态栏文本 / Render status bar text

    Args:
        obj: CLI上下文对象 / CLI context object
        tokens: Token使用量 / Token usage count

    Returns:
        状态栏文本 / Status bar text
    """
    statusline_config = obj.get("_statusline_config", {})
    enabled = statusline_config.get("enabled", obj.get("_statusline_enabled", True))
    if not enabled:
        return ""

    model_name = obj.get("model_name", "deepseek-v4-flash")
    session_name = ""
    if obj.get("session_manager"):
        try:
            info = obj["session_manager"].get_session_info()
            if info.get("has_session"):
                session_name = info["id"][:8]
        except Exception:
            pass

    import os
    format_str = statusline_config.get("format", obj.get("_statusline_format", "AloneChat | {model}"))

    try:
        return format_str.format(
            model=model_name,
            tokens=str(tokens or 0),
            session=session_name,
            mode=obj.get("_mode", "chat"),
            cwd=os.path.basename(os.getcwd()),
        )
    except Exception:
        return format_str
