"""
/status å½ä»¤ - æ¾ç¤ºå½åç¶æ?/ Show current status
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def status_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æ¾ç¤ºå½åç¶æ?/ Show current status
    
    ç¨æ³ / Usage: /status
    """
    from alonework import __version__
    
    console.print("\n[bold cyan]AloneChat ç¶æ?/ Status[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("é¡¹ç® / Item", style="cyan")
    table.add_column("å?/ Value", style="green")
    
    table.add_row("çæ¬ / Version", __version__)
    
    model_name = obj.get("model_name", "deepseek-v4-flash")
    table.add_row("æ¨¡å / Model", model_name)
    
    output_format = obj.get("output_format", "text")
    table.add_row("è¾åºæ ¼å¼ / Output format", output_format)
    
    verbose = obj.get("verbose", False)
    table.add_row("è¯¦ç»æ¨¡å¼ / Verbose", "æ?/ Yes" if verbose else "å?/ No")
    
    table.add_row("å·¥ä½ç®å½ / Working directory", str(Path.cwd()))
    
    if session_manager:
        session_info = session_manager.get_session_info()
        if session_info["has_session"]:
            table.add_row("ä¼è¯ID / Session ID", session_info["id"][:12] + "...")
            table.add_row("æ¶æ¯æ?/ Messages", str(session_info["message_count"]))
        else:
            table.add_row("ä¼è¯ / Session", "æ?/ None")
    
    console.print(table)
    
    config_manager = obj.get("config_manager")
    if config_manager and config_manager.config_path.exists():
        console.print(f"\n[dim]éç½®æä»¶ / Config: {config_manager.config_path}[/dim]")
    
    console.print()
