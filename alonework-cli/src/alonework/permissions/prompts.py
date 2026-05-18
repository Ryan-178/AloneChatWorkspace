"""
æéæç¤ºå¤ç / Permission Prompts

å¤çæéè¯·æ±åç¨æ·äº¤äº?/ Handles permission requests and user interaction
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
    æç¤ºç¨æ·ææ / Prompt user for permission
    
    Args:
        tool_name: å·¥å·åç§° / Tool name
        action: å¨ä½æè¿° / Action description
        details: è¯¦ç»ä¿¡æ¯ / Details
    
    Returns:
        (allowed, remember) - æ¯å¦åè®¸ï¼æ¯å¦è®°ä½éæ©
    """
    console.print(f"\n[yellow]æéè¯·æ± / Permission Request:[/yellow]")
    console.print(f"[cyan]å·¥å· / Tool:[/cyan] {tool_name}")
    console.print(f"[cyan]å¨ä½ / Action:[/cyan] {action}")
    
    if details:
        console.print(f"[dim]{details}[/dim]")
    
    allowed = Confirm.ask("\næ¯å¦åè®¸ï¼?/ Allow?", default=True)
    
    remember = False
    if allowed:
        remember = Confirm.ask("è®°ä½æ­¤éæ©ï¼?/ Remember this choice?", default=False)
    
    return allowed, remember


def show_permission_denied(tool_name: str, action: str) -> None:
    """æ¾ç¤ºæéè¢«æç»?/ Show permission denied"""
    console.print(f"\n[red]æéè¢«æç»?/ Permission denied:[/red]")
    console.print(f"[dim]å·¥å· / Tool: {tool_name}[/dim]")
    console.print(f"[dim]å¨ä½ / Action: {action}[/dim]")
    console.print("[dim]ä½¿ç¨ /permissions å½ä»¤ç®¡çæé / Use /permissions to manage[/dim]\n")
