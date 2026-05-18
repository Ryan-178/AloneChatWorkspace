"""
/rewind å½ä»¤ - åéå¯¹è¯ / Rewind conversation
"""

from rich.console import Console
from rich.prompt import IntPrompt

console = Console()


def rewind_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    åéå¯¹è¯ / Rewind conversation
    
    ç¨æ³ / Usage:
        /rewind        - äº¤äºå¼åé / Interactive rewind
        /rewind <n>    - åénæ¡æ¶æ?/ Rewind n messages
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")
        return
    
    messages = session_manager.get_messages()
    
    if not messages:
        console.print("[yellow]æ æ¶æ¯å¯åé / No messages to rewind[/yellow]")
        return
    
    if args:
        try:
            n = int(args[0])
        except ValueError:
            console.print("[red]æ æçæ°å­?/ Invalid number[/red]")
            return
    else:
        console.print(f"\n[cyan]å½åæ¶æ¯æ?/ Current messages: {len(messages)}[/cyan]\n")
        
        for i, msg in enumerate(messages[-5:], start=max(0, len(messages)-5)):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            console.print(f"  [dim]{i}[/dim] [{role}] {content}...")
        
        n = IntPrompt.ask("\nåéå¤å°æ¡æ¶æ¯ï¼ / How many messages to rewind?", default=1)
    
    if n <= 0:
        console.print("[yellow]æªåéä»»ä½æ¶æ¯ / No messages rewound[/yellow]")
        return
    
    if n > len(messages):
        console.print(f"[red]æ æ³åé {n} æ¡æ¶æ¯ï¼åªæ {len(messages)} æ?/ Cannot rewind {n} messages, only {len(messages)} exist[/red]")
        return
    
    session_manager.current_session.messages = messages[:-n]
    session_manager.save_current_session()
    
    console.print(f"[green]â?å·²åé {n} æ¡æ¶æ?/ Rewound {n} messages[/green]")
    console.print(f"[dim]å©ä½æ¶æ¯æ?/ Remaining messages: {len(session_manager.current_session.messages)}[/dim]")
