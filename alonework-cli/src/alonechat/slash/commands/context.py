"""
/context 命令 - 分析上下文占用并提供优化建议 / Analyze context usage and provide optimization suggestions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def _estimate_tokens(text: str) -> int:
    """估算token数 / Estimate token count"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def _analyze_context(messages: list[dict]) -> dict:
    """分析上下文使用情况 / Analyze context usage"""
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
    """生成优化建议 / Generate optimization suggestions"""
    suggestions = []
    usage_ratio = analysis["total_tokens"] / max_context

    if usage_ratio > 0.8:
        suggestions.append({
            "level": "critical",
            "action": "/compact",
            "description": "上下文使用率超过80%，建议立即压缩 / Context usage exceeds 80%, compact recommended",
        })
    elif usage_ratio > 0.5:
        suggestions.append({
            "level": "warning",
            "action": "/compact",
            "description": "上下文使用率超过50%，考虑压缩 / Context usage exceeds 50%, consider compacting",
        })

    if analysis["long_messages"] > 5:
        suggestions.append({
            "level": "warning",
            "action": "/clear",
            "description": f"存在 {analysis['long_messages']} 条长消息，建议清理或压缩 / {analysis['long_messages']} long messages found, consider cleaning up",
        })

    if analysis["code_blocks"] > 10:
        suggestions.append({
            "level": "info",
            "action": "/compact",
            "description": f"检测到 {analysis['code_blocks']} 个代码块，压缩可优化 / {analysis['code_blocks']} code blocks detected, compression may help",
        })

    if analysis["message_count"] > 50:
        suggestions.append({
            "level": "info",
            "action": "/fork",
            "description": f"对话轮次较多（{analysis['message_count']}条），可考虑分叉新会话 / Many turns ({analysis['message_count']}), consider forking",
        })

    if usage_ratio < 0.2 and analysis["message_count"] > 10:
        suggestions.append({
            "level": "success",
            "action": "-",
            "description": "上下文使用良好，无需优化 / Context usage is healthy, no optimization needed",
        })

    return suggestions


def context_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    分析上下文占用并提供优化建议 / Analyze context usage and provide optimization suggestions

    用法 / Usage: /context
    别名 / Aliases: /ctx
    """
    console.print("\n[bold cyan]上下文分析 / Context Analysis[/bold cyan]\n")

    max_context = 1000000
    messages = []

    if session_manager and session_manager.current_session:
        messages = session_manager.get_messages()
    else:
        console.print("[yellow]无活动会话，无法分析上下文 / No active session, cannot analyze context[/yellow]")
        return

    analysis = _analyze_context(messages)
    usage_ratio = analysis["total_tokens"] / max_context

    overview = Table(show_header=False)
    overview.add_column("指标 / Metric", style="cyan")
    overview.add_column("值 / Value", style="green")

    overview.add_row("消息总数 / Total messages", str(analysis["message_count"]))
    overview.add_row("估算总Token / Estimated total tokens", f"{analysis['total_tokens']:,}")
    overview.add_row("上下文使用率 / Context usage", f"{usage_ratio:.1%}")
    overview.add_row("用户Token / User tokens", f"{analysis['user_tokens']:,}")
    overview.add_row("助手Token / Assistant tokens", f"{analysis['assistant_tokens']:,}")
    overview.add_row("代码块数 / Code blocks", str(analysis["code_blocks"]))
    overview.add_row("长消息数 / Long messages", str(analysis["long_messages"]))
    overview.add_row("上下文上限 / Context limit", f"{max_context:,} tokens")

    console.print(overview)

    suggestions = _generate_suggestions(analysis, max_context)
    if suggestions:
        console.print("\n[bold yellow]优化建议 / Optimization Suggestions[/bold yellow]\n")
        for s in suggestions:
            if s["level"] == "critical":
                icon = "[red]⚠ 严重[/red]"
            elif s["level"] == "warning":
                icon = "[yellow]⚠ 建议[/yellow]"
            elif s["level"] == "info":
                icon = "[cyan]ℹ 提示[/cyan]"
            else:
                icon = "[green]✓ 良好[/green]"

            panel = Panel(
                f"{icon}\n"
                f"[bold]操作 / Action:[/bold] [cyan]/{s['action']}[/cyan]\n"
                f"{s['description']}",
                border_style="dim"
            )
            console.print(panel)

    console.print()
