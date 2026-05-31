"""
/effort 命令 - 设置模型努力级别 / Set effort level for model usage

版本 / Version: 2.1.80
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

EFFORT_LEVELS = {
    "low": {
        "description": "快速简单实现 / Quick, straightforward implementation",
        "temperature": 0.3,
        "max_tokens": 2048,
    },
    "medium": {
        "description": "平衡方法，标准测试 / Balanced approach with standard testing",
        "temperature": 0.5,
        "max_tokens": 4096,
    },
    "high": {
        "description": "全面实现，广泛测试 / Comprehensive implementation with extensive testing",
        "temperature": 0.7,
        "max_tokens": 8192,
    },
    "max": {
        "description": "最大能力，最深推理 / Maximum capability with deepest reasoning",
        "temperature": 0.9,
        "max_tokens": 16384,
    },
    "auto": {
        "description": "使用模型默认级别 / Use default effort level for model",
        "temperature": None,
        "max_tokens": None,
    },
}


def _get_current_effort(obj: dict) -> str:
    """
    获取当前努力级别 / Get current effort level
    """
    return obj.get("effort_level", "auto")


def _set_effort(obj: dict, level: str) -> str:
    """
    设置努力级别 / Set effort level
    """
    obj["effort_level"] = level
    return level


def effort_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    设置模型努力级别 / Set effort level for model usage

    用法 / Usage:
        /effort                 显示当前级别 / Show current level
        /effort low             快速模式 / Quick mode
        /effort medium          平衡模式 / Balanced mode
        /effort high            全面模式 / Comprehensive mode
        /effort max             最大能力 / Maximum capability
        /effort auto            自动模式 / Auto mode
        /effort help            显示帮助 / Show help

    努力级别说明 / Effort Level Description:
        low    - 快速简单实现 / Quick implementation
        medium - 平衡方法与标准测试 / Balanced with standard testing
        high   - 全面实现与广泛测试 / Comprehensive with extensive testing
        max    - 最大能力与最深推理 / Maximum capability
        auto   - 使用模型默认级别 / Use model default
    """
    if not args or args[0] in ("status", "current"):
        current = _get_current_effort(obj)
        level_info = EFFORT_LEVELS.get(current, EFFORT_LEVELS["auto"])

        table = Table(show_header=False, box=None)
        table.add_column("属性 / Property", style="cyan")
        table.add_column("值 / Value", style="green")
        table.add_row("当前级别 / Current level", current)
        table.add_row("描述 / Description", level_info["description"])
        if level_info["temperature"] is not None:
            table.add_row("温度 / Temperature", str(level_info["temperature"]))
            table.add_row("最大tokens / Max tokens", str(level_info["max_tokens"]))

        console.print(Panel(table, title="努力级别 / Effort Level", border_style="cyan"))
        return

    if args[0] in ("help", "-h", "--help"):
        table = Table(show_header=True, title="可用努力级别 / Available Effort Levels")
        table.add_column("级别 / Level", style="cyan")
        table.add_column("描述 / Description", style="green")
        table.add_column("温度 / Temp", style="yellow")
        table.add_column("Max Tokens", style="yellow")
        for level, info in EFFORT_LEVELS.items():
            table.add_row(
                level,
                info["description"],
                str(info["temperature"]) if info["temperature"] is not None else "auto",
                str(info["max_tokens"]) if info["max_tokens"] is not None else "auto",
            )
        console.print(table)
        return

    level = args[0].lower()
    if level not in EFFORT_LEVELS:
        console.print(f"[red]无效级别 / Invalid level: {level}[/red]")
        console.print(f"[dim]可用级别 / Available: {', '.join(EFFORT_LEVELS.keys())}[/dim]")
        return

    _set_effort(obj, level)
    info = EFFORT_LEVELS[level]
    suffix = "" if level != "auto" else " (本次会话 / this session only)"
    console.print(f"[green]✓ 努力级别已设置为 {level}{suffix}[/green]")
    console.print(f"[dim]{info['description']}[/dim]")
