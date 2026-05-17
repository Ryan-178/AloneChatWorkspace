"""
/compact 命令 - 压缩对话上下文 / Compact conversation context
"""

from rich.console import Console

console = Console()


def compact_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    压缩对话上下文 / Compact conversation context
    
    用法 / Usage: /compact [instructions]
    """
    instructions = " ".join(args) if args else None
    
    if session_manager and session_manager.current_session:
        messages = session_manager.get_messages()
        if len(messages) > 10:
            keep_recent = messages[-6:]
            
            summary = f"[对话摘要 / Conversation Summary]\n"
            summary += f"原始消息数 / Original messages: {len(messages)}\n"
            summary += f"保留最近消息 / Kept recent messages: {len(keep_recent)}\n"
            
            if instructions:
                summary += f"压缩指令 / Compact instructions: {instructions}\n"
            
            session_manager.current_session.messages = [
                {"role": "system", "content": summary, "timestamp": ""}
            ] + keep_recent
            session_manager.save_current_session()
            
            console.print(f"[green]✓ 对话已压缩 / Conversation compacted[/green]")
            console.print(f"[dim]从 {len(messages)} 条消息压缩到 {len(keep_recent) + 1} 条[/dim]")
        else:
            console.print("[yellow]对话较短，无需压缩 / Conversation is short, no need to compact[/yellow]")
    else:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
