"""
/clear 鍛戒护 - 娓呴櫎瀵硅瘽鍘嗗彶 / Clear conversation history
"""

from rich.console import Console

console = Console()


def clear_command(args: list, obj: dict, session_manager, registry, **kwargs) -> str:
    """
    娓呴櫎瀵硅瘽鍘嗗彶 / Clear conversation history
    
    鐢ㄦ硶 / Usage: /clear
    """
    if session_manager:
        session_manager.clear_messages()
        console.print("[green]鉁?瀵硅瘽鍘嗗彶宸叉竻闄?/ Conversation history cleared[/green]")
    else:
        console.print("[yellow]鏃犳椿鍔ㄤ細璇?/ No active session[/yellow]")
    
    return "clear"
