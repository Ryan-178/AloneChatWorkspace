"""
/review å½ä»¤ - è¯·æ±ä»£ç å®¡æ¥ / Request code review
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def review_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    è¯·æ±ä»£ç å®¡æ¥ / Request code review
    
    ç¨æ³ / Usage: /review [file-path]
    """
    target = args[0] if args else None
    
    console.print(Panel(
        "[bold cyan]ä»£ç å®¡æ¥æ¨¡å¼ / Code Review Mode[/bold cyan]\n\n"
        "å®¡æ¥è¯·æ±å·²åå¤?/ Review request prepared\n\n"
        "[dim]è¯·è¾å¥æ¨çå®¡æ¥è¯·æ±ï¼ä¾å¦ï¼?dim]\n"
        "[dim]â?å®¡æ¥å½åæä»¶çä»£ç è´¨é?/dim]\n"
        "[dim]â?æ£æ¥å®å¨æ¼æ´?/dim]\n"
        "[dim]â?åææ§è½é®é¢ /dim]",
        border_style="cyan"
    ))
    
    if target:
        target_path = Path(target)
        if target_path.exists():
            console.print(f"\n[cyan]ç®æ æä»¶ / Target file: {target}[/cyan]")
        else:
            console.print(f"\n[yellow]æä»¶ä¸å­å?/ File not found: {target}[/yellow]")
    
    console.print("\n[dim]æç¤º: ç´æ¥è¾å¥å®¡æ¥è¯·æ±å¼å§å®¡æ?/ Tip: Enter review request to start[/dim]")
