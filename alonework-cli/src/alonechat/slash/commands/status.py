"""
/status 命令 - 显示当前状态 / Show current status
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def status_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    显示当前状态 / Show current status
    
    用法 / Usage: /status
    """
    from alonechat import __version__
    
    console.print("\n[bold cyan]AloneChat 状态 / Status[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("项目 / Item", style="cyan")
    table.add_column("值 / Value", style="green")
    
    table.add_row("版本 / Version", __version__)
    
    model_name = obj.get("model_name", "deepseek-v4-flash")
    table.add_row("模型 / Model", model_name)
    
    output_format = obj.get("output_format", "text")
    table.add_row("输出格式 / Output format", output_format)
    
    verbose = obj.get("verbose", False)
    table.add_row("详细模式 / Verbose", "是 / Yes" if verbose else "否 / No")
    
    table.add_row("工作目录 / Working directory", str(Path.cwd()))
    
    if session_manager:
        session_info = session_manager.get_session_info()
        if session_info["has_session"]:
            table.add_row("会话ID / Session ID", session_info["id"][:12] + "...")
            table.add_row("消息数 / Messages", str(session_info["message_count"]))
        else:
            table.add_row("会话 / Session", "无 / None")
    
    console.print(table)
    
    config_manager = obj.get("config_manager")
    if config_manager and config_manager.config_path.exists():
        console.print(f"\n[dim]配置文件 / Config: {config_manager.config_path}[/dim]")
    
    console.print()
