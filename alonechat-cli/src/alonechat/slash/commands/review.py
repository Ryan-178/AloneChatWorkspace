"""
/review 命令 - 请求代码审查 / Request code review
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def review_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    请求代码审查 / Request code review
    
    用法 / Usage: /review [file-path]
    """
    target = args[0] if args else None
    
    console.print(Panel(
        "[bold cyan]代码审查模式 / Code Review Mode[/bold cyan]\n\n"
        "审查请求已准备 / Review request prepared\n\n"
        "[dim]请输入您的审查请求，例如：/dim]\n"
        "[dim]• 审查当前文件的代码质量 /dim]\n"
        "[dim]• 检查安全漏洞 /dim]\n"
        "[dim]• 分析性能问题 /dim]",
        border_style="cyan"
    ))
    
    if target:
        target_path = Path(target)
        if target_path.exists():
            console.print(f"\n[cyan]目标文件 / Target file: {target}[/cyan]")
        else:
            console.print(f"\n[yellow]文件不存在 / File not found: {target}[/yellow]")
    
    console.print("\n[dim]提示: 直接输入审查请求开始审查 / Tip: Enter review request to start[/dim]")
