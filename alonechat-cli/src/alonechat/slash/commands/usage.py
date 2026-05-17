"""
/usage 命令 - 显示使用限制 / Show usage limits
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def usage_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    显示使用限制 / Show usage limits
    
    用法 / Usage: /usage
    """
    console.print("\n[bold cyan]使用限制 / Usage Limits[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("限制项 / Limit", style="cyan")
    table.add_column("当前 / Current", style="green")
    table.add_column("最大 / Maximum", style="yellow")
    
    if session_manager:
        sessions = session_manager.list_sessions(limit=1000)
        table.add_row("会话数 / Sessions", str(len(sessions)), "无限制 / Unlimited")
        
        total_messages = 0
        for session in sessions:
            total_messages += len(session.messages)
        table.add_row("消息数 / Messages", str(total_messages), "无限制 / Unlimited")
    else:
        table.add_row("会话数 / Sessions", "0", "无限制 / Unlimited")
        table.add_row("消息数 / Messages", "0", "无限制 / Unlimited")
    
    table.add_row("上下文窗口 / Context window", "1,000,000", "1,000,000 tokens")
    
    console.print(table)
    
    console.print(Panel(
        "[bold]DeepSeek V4 Flash 定价 / Pricing:[/bold]\n\n"
        "• 输入 / Input: $0.001 / 1M tokens\n"
        "• 输出 / Output: $0.002 / 1M tokens\n"
        "• 缓存命中 / Cache hit: ~99.98% 命中率\n\n"
        "[dim]价格仅供参考，以官方为准 / Prices are approximate[/dim]",
        border_style="dim"
    ))
    
    console.print()
