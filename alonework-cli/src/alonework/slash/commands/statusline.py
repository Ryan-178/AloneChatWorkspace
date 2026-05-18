"""
/statusline å½ä»¤ - èªå®ä¹ç¶ææ  / Custom status bar

æä¾ / Provides:
- èªå®ä¹ç»ç«¯æç¤ºç¬¦ / Custom terminal prompt
- ç¶ææ æ ¼å¼éç½® / Status bar format configuration
- å®æ¶ç¶ææ´æ?/ Real-time status updates
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from alonework.configs import config

console = Console()


def statusline_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    èªå®ä¹ç¶ææ  / Custom status bar

    ç¨æ³ / Usage:
        /statusline                        - æ¾ç¤ºå½åç¶ææ éç½® / Show current status bar config
        /statusline set <format>           - è®¾ç½®ç¶ææ æ ¼å¼ / Set status bar format
        /statusline reset                  - éç½®ä¸ºé»è®?/ Reset to default
        /statusline toggle                 - åæ¢æ¾ç¤º/éè / Toggle show/hide
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
        console.print("[red]ç¨æ³ / Usage: /statusline [set <format>|reset|toggle][/red]")
        console.print("[dim]ç¤ºä¾ / Example: /statusline set 'AloneChat | {model} | {tokens} tokens'[/dim]")


def _show_current_statusline(obj: dict) -> None:
    """æ¾ç¤ºå½åç¶ææ éç½® / Show current status bar configuration"""
    from alonework import __version__

    statusline_config = obj.get("_statusline_config", {})
    format_str = statusline_config.get("format", obj.get("_statusline_format", "AloneChat | {model}"))
    enabled = statusline_config.get("enabled", obj.get("_statusline_enabled", True))
    current_format = statusline_config.get("format", format_str)

    table = Table(show_header=True)
    table.add_column("é¡¹ç® / Item", style="cyan")
    table.add_column("å?/ Value", style="green")

    table.add_row("çæ¬ / Version", __version__)
    table.add_row("ç¶ææ  / Status bar", "å¯ç¨ / Enabled" if enabled else "ç¦ç¨ / Disabled")
    table.add_row("æ ¼å¼ / Format", current_format)

    model_name = obj.get("model_name", "deepseek-v4-flash")
    preview = current_format.format(model=model_name, tokens="0", session="current")
    table.add_row("é¢è§ / Preview", preview)

    console.print(Panel(table, title="[bold cyan]ç¶ææ éç½® / Status Bar Config[/bold cyan]"))
    console.print()
    console.print("[dim]å¯ç¨åé / Available variables:[/dim]")
    console.print("  [cyan]{model}[/cyan]    - å½åæ¨¡å / Current model")
    console.print("  [cyan]{tokens}[/cyan]   - Tokenä½¿ç¨é?/ Token usage")
    console.print("  [cyan]{session}[/cyan]  - ä¼è¯åç§° / Session name")
    console.print("  [cyan]{mode}[/cyan]     - å½åæ¨¡å¼ / Current mode")
    console.print("  [cyan]{cwd}[/cyan]      - å·¥ä½ç®å½ / Working directory\n")


def _set_statusline_format(format_str: str, obj: dict) -> None:
    """è®¾ç½®ç¶ææ æ ¼å¼ / Set status bar format"""
    if "_statusline_config" not in obj:
        obj["_statusline_config"] = {}
    obj["_statusline_config"]["format"] = format_str
    obj["_statusline_format"] = format_str
    console.print(f"[green]ç¶ææ æ ¼å¼å·²æ´æ?/ Status bar format updated:[/green]")
    console.print(f"[cyan]{format_str}[/cyan]")


def _reset_statusline(obj: dict) -> None:
    """éç½®ç¶ææ  / Reset status bar"""
    default_format = "AloneChat | {model}"
    if "_statusline_config" in obj:
        obj["_statusline_config"]["format"] = default_format
    obj["_statusline_format"] = default_format
    obj["_statusline_enabled"] = True
    console.print("[green]ç¶ææ å·²éç½®ä¸ºé»è®¤ / Status bar reset to default[/green]")


def _toggle_statusline(obj: dict) -> None:
    """åæ¢ç¶ææ æ¾ç¤º / Toggle status bar display"""
    if "_statusline_config" not in obj:
        obj["_statusline_config"] = {}
    current = obj["_statusline_config"].get("enabled", obj.get("_statusline_enabled", True))
    obj["_statusline_config"]["enabled"] = not current
    obj["_statusline_enabled"] = not current
    status = "å¯ç¨ / Enabled" if not current else "ç¦ç¨ / Disabled"
    console.print(f"[green]ç¶ææ å·²{status} / Status bar {status}[/green]")


def render_statusline(obj: dict, tokens: Optional[int] = None) -> str:
    """
    æ¸²æç¶ææ ææ¬ / Render status bar text

    Args:
        obj: CLIä¸ä¸æå¯¹è±?/ CLI context object
        tokens: Tokenä½¿ç¨é?/ Token usage count

    Returns:
        ç¶ææ ææ¬ / Status bar text
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
