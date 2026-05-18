"""
/usage å½ä»¤ - æ¾ç¤ºå¥é¤ä½¿ç¨æåµ / Show plan usage

æ¾ç¤ºå½åä½¿ç¨éãå¥é¤éå¶åéé¢ä¿¡æ¯ / Shows current usage, plan limits and quota info
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, Percentage

console = Console()

from alonework import __version__


def _estimate_tokens(text: str) -> int:
    """ä¼°ç®tokenæ?/ Estimate token count"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def usage_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æ¾ç¤ºå¥é¤ä½¿ç¨æåµ / Show plan usage

    æ¾ç¤º / Displays:
    - å¥é¤çæ¬ / Plan version
    - ä¼è¯éå¶ / Session limits
    - Tokenä½¿ç¨éé¢ / Token usage quota
    - è¿åº¦æ¡å±ç¤?/ Progress bar visualization

    ç¨æ³ / Usage: /usage
    """
    console.print("\n[bold cyan]å¥é¤ä½¿ç¨æåµ / Plan Usage[/bold cyan]\n")

    plan_name = "DeepSeek V4 Flash (åè´¹å¥é¤ / Free Tier)"
    max_context = 1000000
    max_sessions = 1000
    max_messages_per_session = 10000

    current_sessions = 0
    total_messages = 0
    total_tokens = 0

    if session_manager:
        sessions = session_manager.list_sessions(limit=max_sessions)
        current_sessions = len(sessions)

        for session in sessions:
            total_messages += len(session.messages)
            for msg in session.messages:
                content = msg.get("content", "")
                total_tokens += _estimate_tokens(content)

    plan_info = Table(show_header=True)
    plan_info.add_column("å¥é¤é¡?/ Plan Item", style="cyan")
    plan_info.add_column("å½å / Current", style="green")
    plan_info.add_column("éå¶ / Limit", style="yellow")
    plan_info.add_column("ä½¿ç¨ç?/ Usage", style="magenta")

    session_ratio = (current_sessions / max_sessions) * 100 if max_sessions > 0 else 0
    plan_info.add_row(
        "ä¼è¯æ?/ Sessions",
        str(current_sessions),
        str(max_sessions),
        f"{session_ratio:.1f}%"
    )

    msg_ratio = (total_messages / (max_sessions * max_messages_per_session)) * 100
    plan_info.add_row(
        "æ¶æ¯æ?/ Messages",
        str(total_messages),
        f"{max_sessions * max_messages_per_session:,}",
        f"{msg_ratio:.2f}%"
    )

    token_ratio = (total_tokens / max_context) * 100
    plan_info.add_row(
        "Tokenä½¿ç¨ / Token usage",
        f"{total_tokens:,}",
        f"{max_context:,}",
        f"{token_ratio:.2f}%"
    )

    console.print(plan_info)

    console.print("\n[bold]ä½¿ç¨è¿åº¦ / Usage Progress[/bold]\n")

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )

    with progress:
        session_task = progress.add_task(
            "[cyan]ä¼è¯ / Sessions", total=max_sessions
        )
        progress.update(session_task, completed=min(current_sessions, max_sessions))

        token_task = progress.add_task(
            "[green]Token / Tokens", total=max_context
        )
        progress.update(token_task, completed=min(total_tokens, max_context))

    console.print(Panel(
        "[bold]å¥é¤è¯¦æ / Plan Details[/bold]\n\n"
        f"â?å¥é¤çæ¬ / Plan version: {__version__}\n"
        f"â?æ¨¡å / Model: DeepSeek V4 Flash\n"
        f"â?ä¸ä¸æçªå?/ Context window: {max_context:,} tokens\n"
        f"â?åä¼è¯æ¶æ¯ä¸é?/ Messages per session: {max_messages_per_session:,}\n"
        f"â?ä¼è¯ä¿çæ?/ Session retention: {max_sessions:,}\n\n"
        "[dim]å®ä»· / Pricing:\n"
        "â?è¾å¥ / Input: $0.001 / 1M tokens\n"
        "â?è¾åº / Output: $0.002 / 1M tokens\n"
        "â?ç¼å­å½ä¸­ / Cache hit: ~99.98% å½ä¸­ç[/dim]\n\n"
        "[dim]å¥é¤éé¢ä»ä¾åè?/ Plan limits are approximate[/dim]",
        border_style="dim",
        title="å¥é¤ä¿¡æ¯ / Plan Info",
    ))

    console.print()
