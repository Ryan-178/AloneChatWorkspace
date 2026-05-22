"""
/usage 命令 - 显示套餐使用情况 / Show plan usage

显示当前使用量、套餐限制和配额信息 / Shows current usage, plan limits and quota info
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn

console = Console()

from alonechat import __version__


def _estimate_tokens(text: str) -> int:
    """估算token数 / Estimate token count"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def usage_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    显示套餐使用情况 / Show plan usage

    显示 / Displays:
    - 套餐版本 / Plan version
    - 会话限制 / Session limits
    - Token使用配额 / Token usage quota
    - 进度条展示 / Progress bar visualization

    用法 / Usage: /usage
    """
    console.print("\n[bold cyan]套餐使用情况 / Plan Usage[/bold cyan]\n")

    plan_name = "DeepSeek V4 Flash (免费套餐 / Free Tier)"
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
    plan_info.add_column("套餐项 / Plan Item", style="cyan")
    plan_info.add_column("当前 / Current", style="green")
    plan_info.add_column("限制 / Limit", style="yellow")
    plan_info.add_column("使用率 / Usage", style="magenta")

    session_ratio = (current_sessions / max_sessions) * 100 if max_sessions > 0 else 0
    plan_info.add_row(
        "会话数 / Sessions",
        str(current_sessions),
        str(max_sessions),
        f"{session_ratio:.1f}%"
    )

    msg_ratio = (total_messages / (max_sessions * max_messages_per_session)) * 100
    plan_info.add_row(
        "消息数 / Messages",
        str(total_messages),
        f"{max_sessions * max_messages_per_session:,}",
        f"{msg_ratio:.2f}%"
    )

    token_ratio = (total_tokens / max_context) * 100
    plan_info.add_row(
        "Token使用 / Token usage",
        f"{total_tokens:,}",
        f"{max_context:,}",
        f"{token_ratio:.2f}%"
    )

    console.print(plan_info)

    console.print("\n[bold]使用进度 / Usage Progress[/bold]\n")

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )

    with progress:
        session_task = progress.add_task(
            "[cyan]会话 / Sessions", total=max_sessions
        )
        progress.update(session_task, completed=min(current_sessions, max_sessions))

        token_task = progress.add_task(
            "[green]Token / Tokens", total=max_context
        )
        progress.update(token_task, completed=min(total_tokens, max_context))

    console.print(Panel(
        "[bold]套餐详情 / Plan Details[/bold]\n\n"
        f"• 套餐版本 / Plan version: {__version__}\n"
        f"• 模型 / Model: DeepSeek V4 Flash\n"
        f"• 上下文窗口 / Context window: {max_context:,} tokens\n"
        f"• 单会话消息上限 / Messages per session: {max_messages_per_session:,}\n"
        f"• 会话保留数 / Session retention: {max_sessions:,}\n\n"
        "[dim]定价 / Pricing:\n"
        "• 输入 / Input: $0.001 / 1M tokens\n"
        "• 输出 / Output: $0.002 / 1M tokens\n"
        "• 缓存命中 / Cache hit: ~99.98% 命中率[/dim]\n\n"
        "[dim]套餐配额仅供参考 / Plan limits are approximate[/dim]",
        border_style="dim",
        title="套餐信息 / Plan Info",
    ))

    console.print()
