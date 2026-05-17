"""
/rewind 命令 - 回退对话 / Rewind conversation
"""

from rich.console import Console
from rich.prompt import IntPrompt

console = Console()


def rewind_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    回退对话 / Rewind conversation
    
    用法 / Usage:
        /rewind        - 交互式回退 / Interactive rewind
        /rewind <n>    - 回退n条消息 / Rewind n messages
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return
    
    messages = session_manager.get_messages()
    
    if not messages:
        console.print("[yellow]无消息可回退 / No messages to rewind[/yellow]")
        return
    
    if args:
        try:
            n = int(args[0])
        except ValueError:
            console.print("[red]无效的数字 / Invalid number[/red]")
            return
    else:
        console.print(f"\n[cyan]当前消息数 / Current messages: {len(messages)}[/cyan]\n")
        
        for i, msg in enumerate(messages[-5:], start=max(0, len(messages)-5)):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            console.print(f"  [dim]{i}[/dim] [{role}] {content}...")
        
        n = IntPrompt.ask("\n回退多少条消息？ / How many messages to rewind?", default=1)
    
    if n <= 0:
        console.print("[yellow]未回退任何消息 / No messages rewound[/yellow]")
        return
    
    if n > len(messages):
        console.print(f"[red]无法回退 {n} 条消息，只有 {len(messages)} 条 / Cannot rewind {n} messages, only {len(messages)} exist[/red]")
        return
    
    session_manager.current_session.messages = messages[:-n]
    session_manager.save_current_session()
    
    console.print(f"[green]✓ 已回退 {n} 条消息 / Rewound {n} messages[/green]")
    console.print(f"[dim]剩余消息数 / Remaining messages: {len(session_manager.current_session.messages)}[/dim]")
