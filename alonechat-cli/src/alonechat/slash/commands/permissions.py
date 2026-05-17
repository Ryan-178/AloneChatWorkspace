"""
/permissions 命令 - 管理权限 / Manage permissions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def permissions_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理权限 / Manage permissions
    
    用法 / Usage:
        /permissions              - 显示权限状态 / Show permission status
        /permissions allow <tool> - 允许工具 / Allow tool
        /permissions deny <tool>  - 拒绝工具 / Deny tool
        /permissions mode <mode>  - 设置模式 / Set mode
    """
    from alonechat.permissions import PermissionManager, PermissionMode
    
    perm_manager = PermissionManager()
    
    if not args:
        perm_manager.show_status()
        return
    
    subcommand = args[0]
    
    if subcommand == "allow" and len(args) >= 2:
        tool = args[1]
        perm_manager.allow(tool)
        console.print(f"[green]✓ 已允许工具 / Tool allowed: {tool}[/green]")
        return
    
    if subcommand == "deny" and len(args) >= 2:
        tool = args[1]
        perm_manager.deny(tool)
        console.print(f"[green]✓ 已拒绝工具 / Tool denied: {tool}[/green]")
        return
    
    if subcommand == "mode" and len(args) >= 2:
        mode_str = args[1].lower()
        try:
            mode = PermissionMode(mode_str)
            perm_manager.set_mode(mode)
            console.print(f"[green]✓ 已设置模式 / Mode set: {mode.value}[/green]")
        except ValueError:
            console.print(f"[red]无效模式 / Invalid mode: {mode_str}[/red]")
            console.print("[dim]可用模式 / Available modes: accept, plan, review, default[/dim]")
        return
    
    if subcommand == "reset":
        from pathlib import Path
        config_file = Path.home() / ".alonechat" / "permissions.json"
        if config_file.exists():
            config_file.unlink()
        console.print("[green]✓ 权限已重置 / Permissions reset[/green]")
        return
    
    console.print(Panel(
        "[bold cyan]/permissions 命令帮助 / Command Help[/bold cyan]\n\n"
        "用法 / Usage:\n"
        "  /permissions              显示权限状态 / Show status\n"
        "  /permissions allow <tool> 允许工具 / Allow tool\n"
        "  /permissions deny <tool>  拒绝工具 / Deny tool\n"
        "  /permissions mode <mode>  设置模式 / Set mode\n"
        "  /permissions reset        重置权限 / Reset permissions\n\n"
        "[dim]模式 / Modes: accept, plan, review, default[/dim]",
        border_style="cyan"
    ))
