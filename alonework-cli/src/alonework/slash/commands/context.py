"""
/context å½ä»¤ - åæä¸ä¸æå ç¨å¹¶æä¾ä¼åå»ºè®® / Analyze context usage and provide optimization suggestions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def _estimate_tokens(text: str) -> int:
    """ä¼°ç®tokenæ?/ Estimate token count"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def _analyze_context(messages: list[dict]) -> dict:
    """åæä¸ä¸æä½¿ç¨æå?/ Analyze context usage"""
    total_tokens = 0
    user_tokens = 0
    assistant_tokens = 0
    system_tokens = 0
    code_blocks = 0
    long_messages = 0
    message_count = len(messages)

    for msg in messages:
        content = msg.get("content", "")
        tokens = _estimate_tokens(content)
        total_tokens += tokens

        role = msg.get("role", "")
        if role == "user":
            user_tokens += tokens
        elif role == "assistant":
            assistant_tokens += tokens
        else:
            system_tokens += tokens

        if "```" in content:
            code_blocks += content.count("```") // 2

        if tokens > 2000:
            long_messages += 1

    return {
        "message_count": message_count,
        "total_tokens": total_tokens,
        "user_tokens": user_tokens,
        "assistant_tokens": assistant_tokens,
        "system_tokens": system_tokens,
        "code_blocks": code_blocks,
        "long_messages": long_messages,
    }


def _generate_suggestions(analysis: dict, max_context: int = 1000000) -> list[dict]:
    """çæä¼åå»ºè®® / Generate optimization suggestions"""
    suggestions = []
    usage_ratio = analysis["total_tokens"] / max_context

    if usage_ratio > 0.8:
        suggestions.append({
            "level": "critical",
            "action": "/compact",
            "description": "ä¸ä¸æä½¿ç¨çè¶è¿80%ï¼å»ºè®®ç«å³åç¼?/ Context usage exceeds 80%, compact recommended",
        })
    elif usage_ratio > 0.5:
        suggestions.append({
            "level": "warning",
            "action": "/compact",
            "description": "ä¸ä¸æä½¿ç¨çè¶è¿50%ï¼èèåç¼© / Context usage exceeds 50%, consider compacting",
        })

    if analysis["long_messages"] > 5:
        suggestions.append({
            "level": "warning",
            "action": "/clear",
            "description": f"å­å¨ {analysis['long_messages']} æ¡é¿æ¶æ¯ï¼å»ºè®®æ¸çæåç¼© / {analysis['long_messages']} long messages found, consider cleaning up",
        })

    if analysis["code_blocks"] > 10:
        suggestions.append({
            "level": "info",
            "action": "/compact",
            "description": f"æ£æµå° {analysis['code_blocks']} ä¸ªä»£ç åï¼åç¼©å¯ä¼å / {analysis['code_blocks']} code blocks detected, compression may help",
        })

    if analysis["message_count"] > 50:
        suggestions.append({
            "level": "info",
            "action": "/fork",
            "description": f"å¯¹è¯è½®æ¬¡è¾å¤ï¼{analysis['message_count']}æ¡ï¼ï¼å¯èèååæ°ä¼è¯?/ Many turns ({analysis['message_count']}), consider forking",
        })

    if usage_ratio < 0.2 and analysis["message_count"] > 10:
        suggestions.append({
            "level": "success",
            "action": "-",
            "description": "ä¸ä¸æä½¿ç¨è¯å¥½ï¼æ éä¼å / Context usage is healthy, no optimization needed",
        })

    return suggestions


def context_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    åæä¸ä¸æå ç¨å¹¶æä¾ä¼åå»ºè®® / Analyze context usage and provide optimization suggestions

    ç¨æ³ / Usage: /context
    å«å / Aliases: /ctx
    """
    console.print("\n[bold cyan]ä¸ä¸æåæ?/ Context Analysis[/bold cyan]\n")

    max_context = 1000000
    messages = []

    if session_manager and session_manager.current_session:
        messages = session_manager.get_messages()
    else:
        console.print("[yellow]æ æ´»å¨ä¼è¯ï¼æ æ³åæä¸ä¸æ?/ No active session, cannot analyze context[/yellow]")
        return

    analysis = _analyze_context(messages)
    usage_ratio = analysis["total_tokens"] / max_context

    overview = Table(show_header=False)
    overview.add_column("ææ  / Metric", style="cyan")
    overview.add_column("å?/ Value", style="green")

    overview.add_row("æ¶æ¯æ»æ° / Total messages", str(analysis["message_count"]))
    overview.add_row("ä¼°ç®æ»Token / Estimated total tokens", f"{analysis['total_tokens']:,}")
    overview.add_row("ä¸ä¸æä½¿ç¨ç / Context usage", f"{usage_ratio:.1%}")
    overview.add_row("ç¨æ·Token / User tokens", f"{analysis['user_tokens']:,}")
    overview.add_row("å©æToken / Assistant tokens", f"{analysis['assistant_tokens']:,}")
    overview.add_row("ä»£ç åæ° / Code blocks", str(analysis["code_blocks"]))
    overview.add_row("é¿æ¶æ¯æ° / Long messages", str(analysis["long_messages"]))
    overview.add_row("ä¸ä¸æä¸é?/ Context limit", f"{max_context:,} tokens")

    console.print(overview)

    suggestions = _generate_suggestions(analysis, max_context)
    if suggestions:
        console.print("\n[bold yellow]ä¼åå»ºè®® / Optimization Suggestions[/bold yellow]\n")
        for s in suggestions:
            if s["level"] == "critical":
                icon = "[red]â?ä¸¥é[/red]"
            elif s["level"] == "warning":
                icon = "[yellow]â?å»ºè®®[/yellow]"
            elif s["level"] == "info":
                icon = "[cyan]â?æç¤º[/cyan]"
            else:
                icon = "[green]â?è¯å¥½[/green]"

            panel = Panel(
                f"{icon}\n"
                f"[bold]æä½ / Action:[/bold] [cyan]/{s['action']}[/cyan]\n"
                f"{s['description']}",
                border_style="dim"
            )
            console.print(panel)

    console.print()
