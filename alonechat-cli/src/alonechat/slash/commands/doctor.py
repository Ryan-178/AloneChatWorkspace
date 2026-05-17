"""
/doctor 命令 - 检查安装健康状态 / Check installation health
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def doctor_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    检查安装健康状态 / Check installation health
    
    用法 / Usage: /doctor
    """
    console.print("\n[bold cyan]AloneChat 健康检查 / Health Check[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("检查项 / Check", style="cyan")
    table.add_column("状态 / Status", style="green")
    table.add_column("详情 / Details")
    
    checks = []
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 10)
    checks.append((
        "Python 版本 / Python version",
        python_ok,
        python_version
    ))
    
    config_manager = obj.get("config_manager")
    if config_manager:
        config_exists = config_manager.config_path.exists()
        checks.append((
            "配置文件 / Config file",
            config_exists,
            str(config_manager.config_path) if config_exists else "未找到 / Not found"
        ))
    else:
        checks.append(("配置文件 / Config file", False, "不可用 / Unavailable"))
    
    session_dir = Path.home() / ".alonechat" / "sessions"
    session_dir_ok = session_dir.exists()
    checks.append((
        "会话目录 / Session directory",
        session_dir_ok,
        str(session_dir)
    ))
    
    try:
        import click
        checks.append(("Click 库 / Click library", True, click.__version__))
    except ImportError:
        checks.append(("Click 库 / Click library", False, "未安装 / Not installed"))
    
    try:
        import rich
        checks.append(("Rich 库 / Rich library", True, rich.__version__))
    except ImportError:
        checks.append(("Rich 库 / Rich library", False, "未安装 / Not installed"))
    
    for name, ok, details in checks:
        status = "[green]✓ OK[/green]" if ok else "[red]✗ 失败[/red]"
        table.add_row(name, status, details)
    
    console.print(table)
    
    all_ok = all(check[1] for check in checks)
    if all_ok:
        console.print("\n[green]✓ 所有检查通过 / All checks passed[/green]")
    else:
        console.print("\n[yellow]⚠ 部分检查未通过 / Some checks failed[/yellow]")
    
    console.print()
