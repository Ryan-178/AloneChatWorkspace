"""
/clear 命令 - 清除对话历史 / Clear conversation history
"""

from rich.console import Console

console = Console()


def clear_command(args: list, obj: dict, session_manager, registry, **kwargs) -> str:
    """
    清除对话历史 / Clear conversation history
    
    用法 / Usage: /clear
    """
    if session_manager:
        session_manager.clear_messages()
        console.print("[green]✓ 对话历史已清除 / Conversation history cleared[/green]")
    else:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
    
    return "clear"
