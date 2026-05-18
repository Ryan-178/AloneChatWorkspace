"""
/compact 命令 - 压缩对话上下文 / Compact conversation context

功能 / Features:
- 智能压缩对话历史 / Smart compress conversation history
- 支持无限长度对话 / Support unlimited length conversation
- AI智能摘要 / AI smart summarization
- 可配置压缩策略 / Configurable compression strategy

版本 / Version: 0.2.47
"""

from rich.console import Console
from rich.table import Table
from typing import Optional, List, Dict, Any

console = Console()


def compact_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    压缩对话上下文 / Compact conversation context
    
    用法 / Usage: 
        /compact                     智能压缩对话 / Smart compact
        /compact --aggressive        激进压缩（保留更少）/ Aggressive compact
        /compact --summary           显示压缩摘要 / Show compression summary
        /compact --auto              启用自动压缩 / Enable auto compact
        /compact [instructions]      带指令压缩 / Compact with instructions
    
    示例 / Examples:
        /compact                     压缩对话 / Compact conversation
        /compact --aggressive        激进压缩 / Aggressive compact
        /compact "保留关键决策"       带指令压缩 / Compact with instructions
    """
    instructions = None
    aggressive = False
    show_summary = False
    enable_auto = False
    
    for arg in args:
        if arg == "--aggressive":
            aggressive = True
        elif arg == "--summary":
            show_summary = True
        elif arg == "--auto":
            enable_auto = True
        elif not arg.startswith("--"):
            instructions = arg
    
    if enable_auto:
        _enable_auto_compact(obj, session_manager)
        return
    
    if session_manager and session_manager.current_session:
        messages = session_manager.get_messages()
        
        if len(messages) <= 10:
            console.print("[yellow]对话较短，无需压缩 / Conversation is short, no need to compact[/yellow]")
            return
        
        preserve_count = 4 if aggressive else 6
        keep_recent = messages[-preserve_count:]
        to_compress = messages[:-preserve_count]
        
        summary = _generate_summary(to_compress, instructions, aggressive)
        
        compressed_messages = [
            {
                "role": "system",
                "content": summary,
                "timestamp": "",
                "compressed": True,
            }
        ] + keep_recent
        
        original_count = len(messages)
        compressed_count = len(compressed_messages)
        compression_ratio = (1 - compressed_count / original_count) * 100
        
        session_manager.current_session.messages = compressed_messages
        session_manager.current_session.compressed = True
        session_manager.current_session.compression_summary = summary
        session_manager.save_current_session()
        
        console.print(f"[green]✓ 对话已压缩 / Conversation compacted[/green]")
        console.print(f"[dim]从 {original_count} 条消息压缩到 {compressed_count} 条[/dim]")
        console.print(f"[dim]压缩率: {compression_ratio:.1f}%[/dim]")
        
        if show_summary:
            console.print(f"\n[cyan]压缩摘要 / Compression Summary:[/cyan]")
            console.print(f"[dim]{summary[:500]}{'...' if len(summary) > 500 else ''}[/dim]")
    else:
        console.print("[yellow]无活动会话 / No active session[/yellow]")


def _generate_summary(
    messages: List[Dict],
    instructions: Optional[str] = None,
    aggressive: bool = False,
) -> str:
    """
    生成压缩摘要 / Generate compression summary
    
    Args:
        messages: 要压缩的消息列表 / Messages to compress
        instructions: 压缩指令 / Compression instructions
        aggressive: 是否激进压缩 / Whether aggressive compression
    
    Returns:
        压缩摘要 / Compression summary
    """
    summary_lines = ["[对话智能摘要 / Conversation Summary]"]
    summary_lines.append(f"原始消息数 / Original messages: {len(messages)}")
    
    topics = set()
    decisions = []
    tasks = []
    key_info = []
    
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        if role == "user":
            if len(content) > 20:
                topics.add(content[:50].strip())
        
        lower_content = content.lower()
        
        if any(kw in lower_content for kw in ["决定", "decision", "选择", "选择"]):
            decisions.append(content[:100])
        
        if any(kw in lower_content for kw in ["任务", "task", "需要", "need"]):
            tasks.append(content[:100])
        
        if any(kw in lower_content for kw in ["重要", "important", "关键", "key"]):
            key_info.append(content[:100])
    
    if topics:
        topic_list = list(topics)[:5]
        summary_lines.append(f"\n主要话题 / Main topics:")
        for topic in topic_list:
            summary_lines.append(f"  - {topic}")
    
    if decisions and not aggressive:
        summary_lines.append(f"\n关键决策 / Key decisions:")
        for decision in decisions[:3]:
            summary_lines.append(f"  - {decision}")
    
    if tasks and not aggressive:
        summary_lines.append(f"\n任务列表 / Tasks:")
        for task in tasks[:3]:
            summary_lines.append(f"  - {task}")
    
    if key_info:
        summary_lines.append(f"\n重要信息 / Important info:")
        for info in key_info[:3]:
            summary_lines.append(f"  - {info}")
    
    if instructions:
        summary_lines.append(f"\n压缩指令 / Compact instructions: {instructions}")
    
    return "\n".join(summary_lines)


def _enable_auto_compact(obj: dict, session_manager) -> None:
    """
    启用自动压缩 / Enable auto compact
    
    设置自动压缩标志，在对话达到阈值时自动压缩
    """
    if session_manager and session_manager.current_session:
        session_manager.current_session.metadata["auto_compact"] = True
        threshold = obj.get("compact_threshold", 100)
        session_manager.current_session.metadata["compact_threshold"] = threshold
        session_manager.save_current_session()
        
        console.print(f"[green]✓ 自动压缩已启用 / Auto compact enabled[/green]")
        console.print(f"[dim]压缩阈值: {threshold} 条消息 / Compact threshold: {threshold} messages[/dim]")
    else:
        console.print("[yellow]无活动会话 / No active session[/yellow]")


def auto_compact_check(
    session_manager,
    threshold: int = 100,
    aggressive: bool = False,
) -> bool:
    """
    自动压缩检查 / Auto compact check
    
    检查是否需要自动压缩，如果需要则执行压缩
    
    Args:
        session_manager: 会话管理器 / Session manager
        threshold: 压缩阈值 / Compression threshold
        aggressive: 是否激进压缩 / Whether aggressive compression
    
    Returns:
        是否执行了压缩 / Whether compression was performed
    """
    if not session_manager or not session_manager.current_session:
        return False
    
    metadata = session_manager.current_session.metadata
    if not metadata.get("auto_compact", False):
        return False
    
    threshold = metadata.get("compact_threshold", threshold)
    messages = session_manager.get_messages()
    
    if len(messages) >= threshold:
        compact_command(
            args=["--aggressive"] if aggressive else [],
            obj={},
            session_manager=session_manager,
            registry=None,
        )
        return True
    
    return False


def show_compact_status(session_manager) -> None:
    """
    显示压缩状态 / Show compact status
    
    显示当前会话的压缩状态和统计信息
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return
    
    session = session_manager.current_session
    
    table = Table(title="压缩状态 / Compact Status")
    table.add_column("属性", style="cyan")
    table.add_column("值", style="green")
    
    table.add_row("会话名称 / Session name", session.get_name())
    table.add_row("当前消息数 / Current messages", str(len(session.messages)))
    table.add_row("已压缩 / Compressed", "是 / Yes" if session.compressed else "否 / No")
    
    auto_compact = session.metadata.get("auto_compact", False)
    table.add_row("自动压缩 / Auto compact", "已启用 / Enabled" if auto_compact else "未启用 / Disabled")
    
    if auto_compact:
        threshold = session.metadata.get("compact_threshold", 100)
        table.add_row("压缩阈值 / Threshold", str(threshold))
    
    if session.compression_summary:
        summary_preview = session.compression_summary[:100] + "..."
        table.add_row("压缩摘要 / Summary", summary_preview)
    
    console.print(table)
