"""
/compact å½ä»¤ - åç¼©å¯¹è¯ä¸ä¸æ?/ Compact conversation context

åè½ / Features:
- æºè½åç¼©å¯¹è¯åå² / Smart compress conversation history
- æ¯ææ éé¿åº¦å¯¹è¯ / Support unlimited length conversation
- AIæºè½æè¦ / AI smart summarization
- å¯éç½®åç¼©ç­ç?/ Configurable compression strategy

çæ¬ / Version: 0.2.47
"""

from rich.console import Console
from rich.table import Table
from typing import Optional, List, Dict, Any

console = Console()


def compact_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    åç¼©å¯¹è¯ä¸ä¸æ?/ Compact conversation context
    
    ç¨æ³ / Usage: 
        /compact                     æºè½åç¼©å¯¹è¯ / Smart compact
        /compact --aggressive        æ¿è¿åç¼©ï¼ä¿çæ´å°ï¼? Aggressive compact
        /compact --summary           æ¾ç¤ºåç¼©æè¦ / Show compression summary
        /compact --auto              å¯ç¨èªå¨åç¼© / Enable auto compact
        /compact [instructions]      å¸¦æä»¤åç¼?/ Compact with instructions
    
    ç¤ºä¾ / Examples:
        /compact                     åç¼©å¯¹è¯ / Compact conversation
        /compact --aggressive        æ¿è¿åç¼?/ Aggressive compact
        /compact "ä¿çå³é®å³ç­"       å¸¦æä»¤åç¼?/ Compact with instructions
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
            console.print("[yellow]å¯¹è¯è¾ç­ï¼æ éåç¼© / Conversation is short, no need to compact[/yellow]")
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
        
        console.print(f"[green]â?å¯¹è¯å·²åç¼?/ Conversation compacted[/green]")
        console.print(f"[dim]ä»?{original_count} æ¡æ¶æ¯åç¼©å° {compressed_count} æ¡[/dim]")
        console.print(f"[dim]åç¼©ç? {compression_ratio:.1f}%[/dim]")
        
        if show_summary:
            console.print(f"\n[cyan]åç¼©æè¦ / Compression Summary:[/cyan]")
            console.print(f"[dim]{summary[:500]}{'...' if len(summary) > 500 else ''}[/dim]")
    else:
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")


def _generate_summary(
    messages: List[Dict],
    instructions: Optional[str] = None,
    aggressive: bool = False,
) -> str:
    """
    çæåç¼©æè¦ / Generate compression summary
    
    Args:
        messages: è¦åç¼©çæ¶æ¯åè¡¨ / Messages to compress
        instructions: åç¼©æä»¤ / Compression instructions
        aggressive: æ¯å¦æ¿è¿åç¼?/ Whether aggressive compression
    
    Returns:
        åç¼©æè¦ / Compression summary
    """
    summary_lines = ["[å¯¹è¯æºè½æè¦ / Conversation Summary]"]
    summary_lines.append(f"åå§æ¶æ¯æ?/ Original messages: {len(messages)}")
    
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
        
        if any(kw in lower_content for kw in ["å³å®", "decision", "éæ©", "éæ©"]):
            decisions.append(content[:100])
        
        if any(kw in lower_content for kw in ["ä»»å¡", "task", "éè¦?, "need"]):
            tasks.append(content[:100])
        
        if any(kw in lower_content for kw in ["éè¦", "important", "å³é®", "key"]):
            key_info.append(content[:100])
    
    if topics:
        topic_list = list(topics)[:5]
        summary_lines.append(f"\nä¸»è¦è¯é¢ / Main topics:")
        for topic in topic_list:
            summary_lines.append(f"  - {topic}")
    
    if decisions and not aggressive:
        summary_lines.append(f"\nå³é®å³ç­ / Key decisions:")
        for decision in decisions[:3]:
            summary_lines.append(f"  - {decision}")
    
    if tasks and not aggressive:
        summary_lines.append(f"\nä»»å¡åè¡¨ / Tasks:")
        for task in tasks[:3]:
            summary_lines.append(f"  - {task}")
    
    if key_info:
        summary_lines.append(f"\néè¦ä¿¡æ¯ / Important info:")
        for info in key_info[:3]:
            summary_lines.append(f"  - {info}")
    
    if instructions:
        summary_lines.append(f"\nåç¼©æä»¤ / Compact instructions: {instructions}")
    
    return "\n".join(summary_lines)


def _enable_auto_compact(obj: dict, session_manager) -> None:
    """
    å¯ç¨èªå¨åç¼© / Enable auto compact
    
    è®¾ç½®èªå¨åç¼©æ å¿ï¼å¨å¯¹è¯è¾¾å°éå¼æ¶èªå¨åç¼©
    """
    if session_manager and session_manager.current_session:
        session_manager.current_session.metadata["auto_compact"] = True
        threshold = obj.get("compact_threshold", 100)
        session_manager.current_session.metadata["compact_threshold"] = threshold
        session_manager.save_current_session()
        
        console.print(f"[green]â?èªå¨åç¼©å·²å¯ç?/ Auto compact enabled[/green]")
        console.print(f"[dim]åç¼©éå? {threshold} æ¡æ¶æ?/ Compact threshold: {threshold} messages[/dim]")
    else:
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")


def auto_compact_check(
    session_manager,
    threshold: int = 100,
    aggressive: bool = False,
) -> bool:
    """
    èªå¨åç¼©æ£æ?/ Auto compact check
    
    æ£æ¥æ¯å¦éè¦èªå¨åç¼©ï¼å¦æéè¦åæ§è¡åç¼©
    
    Args:
        session_manager: ä¼è¯ç®¡çå?/ Session manager
        threshold: åç¼©éå?/ Compression threshold
        aggressive: æ¯å¦æ¿è¿åç¼?/ Whether aggressive compression
    
    Returns:
        æ¯å¦æ§è¡äºåç¼?/ Whether compression was performed
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
    æ¾ç¤ºåç¼©ç¶æ?/ Show compact status
    
    æ¾ç¤ºå½åä¼è¯çåç¼©ç¶æåç»è®¡ä¿¡æ¯
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")
        return
    
    session = session_manager.current_session
    
    table = Table(title="åç¼©ç¶æ?/ Compact Status")
    table.add_column("å±æ?, style="cyan")
    table.add_column("å?, style="green")
    
    table.add_row("ä¼è¯åç§° / Session name", session.get_name())
    table.add_row("å½åæ¶æ¯æ?/ Current messages", str(len(session.messages)))
    table.add_row("å·²åç¼?/ Compressed", "æ?/ Yes" if session.compressed else "å?/ No")
    
    auto_compact = session.metadata.get("auto_compact", False)
    table.add_row("èªå¨åç¼© / Auto compact", "å·²å¯ç?/ Enabled" if auto_compact else "æªå¯ç?/ Disabled")
    
    if auto_compact:
        threshold = session.metadata.get("compact_threshold", 100)
        table.add_row("åç¼©éå?/ Threshold", str(threshold))
    
    if session.compression_summary:
        summary_preview = session.compression_summary[:100] + "..."
        table.add_row("åç¼©æè¦ / Summary", summary_preview)
    
    console.print(table)
