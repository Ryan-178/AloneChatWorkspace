"""
/permissions å½ä»¤ - ç®¡çæé / Manage permissions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def permissions_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ç®¡çæé / Manage permissions
    
    ç¨æ³ / Usage:
        /permissions              - æ¾ç¤ºæéç¶æ?/ Show permission status
        /permissions allow <tool> - åè®¸å·¥å· / Allow tool
        /permissions deny <tool>  - æç»å·¥å· / Deny tool
        /permissions mode <mode>  - è®¾ç½®æ¨¡å¼ / Set mode
    """
    from alonework.permissions import PermissionManager, PermissionMode
    
    perm_manager = PermissionManager()
    
    if not args:
        perm_manager.show_status()
        return
    
    subcommand = args[0]
    
    if subcommand == "allow" and len(args) >= 2:
        tool = args[1]
        perm_manager.allow(tool)
        console.print(f"[green]â?å·²åè®¸å·¥å?/ Tool allowed: {tool}[/green]")
        return
    
    if subcommand == "deny" and len(args) >= 2:
        tool = args[1]
        perm_manager.deny(tool)
        console.print(f"[green]â?å·²æç»å·¥å?/ Tool denied: {tool}[/green]")
        return
    
    if subcommand == "mode" and len(args) >= 2:
        mode_str = args[1].lower()
        try:
            mode = PermissionMode(mode_str)
            perm_manager.set_mode(mode)
            console.print(f"[green]â?å·²è®¾ç½®æ¨¡å¼?/ Mode set: {mode.value}[/green]")
        except ValueError:
            console.print(f"[red]æ ææ¨¡å¼ / Invalid mode: {mode_str}[/red]")
            console.print("[dim]å¯ç¨æ¨¡å¼ / Available modes: accept, plan, review, default[/dim]")
        return
    
    if subcommand == "reset":
        from pathlib import Path
        config_file = Path.home() / ".alonechat" / "permissions.json"
        if config_file.exists():
            config_file.unlink()
        console.print("[green]â?æéå·²éç½?/ Permissions reset[/green]")
        return
    
    console.print(Panel(
        "[bold cyan]/permissions å½ä»¤å¸®å© / Command Help[/bold cyan]\n\n"
        "ç¨æ³ / Usage:\n"
        "  /permissions              æ¾ç¤ºæéç¶æ?/ Show status\n"
        "  /permissions allow <tool> åè®¸å·¥å· / Allow tool\n"
        "  /permissions deny <tool>  æç»å·¥å· / Deny tool\n"
        "  /permissions mode <mode>  è®¾ç½®æ¨¡å¼ / Set mode\n"
        "  /permissions reset        éç½®æé / Reset permissions\n\n"
        "[dim]æ¨¡å¼ / Modes: accept, plan, review, default[/dim]",
        border_style="cyan"
    ))
