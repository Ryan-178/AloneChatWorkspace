"""
权限提示处理 / Permission Prompts

处理权限请求和用户交互 / Handles permission requests and user interaction
"""

from typing import Optional
from rich.console import Console
from rich.prompt import Confirm

console = Console()


def prompt_for_permission(
    tool_name: str,
    action: str,
    details: Optional[str] = None,
) -> tuple[bool, bool]:
    """
    提示用户授权 / Prompt user for permission
    
    Args:
        tool_name: 工具名称 / Tool name
        action: 动作描述 / Action description
        details: 详细信息 / Details
    
    Returns:
        (allowed, remember) - 是否允许，是否记住选择
    """
    console.print(f"\n[yellow]权限请求 / Permission Request:[/yellow]")
    console.print(f"[cyan]工具 / Tool:[/cyan] {tool_name}")
    console.print(f"[cyan]动作 / Action:[/cyan] {action}")
    
    if details:
        console.print(f"[dim]{details}[/dim]")
    
    allowed = Confirm.ask("\n是否允许？ / Allow?", default=True)
    
    remember = False
    if allowed:
        remember = Confirm.ask("记住此选择？ / Remember this choice?", default=False)
    
    return allowed, remember


def show_permission_denied(tool_name: str, action: str) -> None:
    """显示权限被拒绝 / Show permission denied"""
    console.print(f"\n[red]权限被拒绝 / Permission denied:[/red]")
    console.print(f"[dim]工具 / Tool: {tool_name}[/dim]")
    console.print(f"[dim]动作 / Action: {action}[/dim]")
    console.print("[dim]使用 /permissions 命令管理权限 / Use /permissions to manage[/dim]\n")
