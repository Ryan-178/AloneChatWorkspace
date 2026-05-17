"""
/vim 命令 - Vim模式 / Vim mode
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


def vim_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    Vim模式 / Vim mode
    
    用法 / Usage: /vim
    """
    obj["_vim_mode"] = True
    
    console.print(Panel(
        "[bold cyan]Vim模式已启用 / Vim Mode Enabled[/bold cyan]\n\n"
        "按键绑定 / Key bindings:\n"
        "• [cyan]i[/cyan] - 插入模式 / Insert mode\n"
        "• [cyan]Esc[/cyan] - 命令模式 / Command mode\n"
        "• [cyan]:q[/cyan] - 退出 / Quit\n"
        "• [cyan]:w[/cyan] - 保存会话 / Save session\n\n"
        "[dim]注意: Vim模式功能开发中 / Note: Vim mode is in development[/dim]",
        border_style="cyan"
    ))
