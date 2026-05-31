"""
/color 命令 - 设置代理颜色 / Set agent color

版本 / Version: 2.1.80
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

CONFIG_DIR = Path.cwd() / ".alonechat"
COLOR_FILE = CONFIG_DIR / "color.yaml"

AVAILABLE_COLORS = {
    "cyan": {"code": "cyan", "hex": "#00bcd4"},
    "green": {"code": "green", "hex": "#4caf50"},
    "blue": {"code": "blue", "hex": "#2196f3"},
    "magenta": {"code": "magenta", "hex": "#e91e63"},
    "yellow": {"code": "yellow", "hex": "#ffeb3b"},
    "red": {"code": "red", "hex": "#f44336"},
    "white": {"code": "white", "hex": "#ffffff"},
    "orange": {"code": "orange1", "hex": "#ff9800"},
    "purple": {"code": "purple", "hex": "#9c27b0"},
    "pink": {"code": "bright_magenta", "hex": "#ff4081"},
}


def _load_color_config() -> dict:
    """
    加载颜色配置 / Load color configuration
    """
    if not COLOR_FILE.exists():
        return {"agent_color": "cyan"}
    try:
        with open(COLOR_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"agent_color": "cyan"}
    except Exception:
        return {"agent_color": "cyan"}


def _save_color_config(config: dict) -> bool:
    """
    保存颜色配置 / Save color configuration
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(COLOR_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception:
        return False


def color_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    设置代理颜色 / Set agent color

    用法 / Usage:
        /color                  显示当前颜色 / Show current color
        /color list             列出可用颜色 / List available colors
        /color set <name>       设置颜色 / Set color
        /color reset            重置为默认 / Reset to default
        /color preview <name>   预览颜色 / Preview color

    示例 / Examples:
        /color set cyan
        /color set magenta
    """
    config = _load_color_config()
    current = config.get("agent_color", "cyan")

    if not args or args[0] == "status":
        color_info = AVAILABLE_COLORS.get(current, {})
        console.print(f"[bold {color_info.get('code', 'cyan')}]当前代理颜色 / Current agent color: {current}[/]")
        console.print(f"[dim]HEX: {color_info.get('hex', '-')}[/dim]")
        return

    if args[0] == "list":
        table = Table(show_header=True, title="可用颜色 / Available Colors")
        table.add_column("名称 / Name", style="cyan")
        table.add_column("预览 / Preview", style="green")
        table.add_column("HEX", style="yellow")
        table.add_column("当前 / Current", style="bold")

        for name, info in AVAILABLE_COLORS.items():
            is_current = " ← " if name == current else ""
            preview = Text("██████", style=info["code"])
            table.add_row(name, preview, info["hex"], is_current)

        console.print(table)
        return

    if args[0] == "preview":
        if len(args) < 2 or args[1] not in AVAILABLE_COLORS:
            console.print("[red]请指定有效颜色 / Please specify valid color[/red]")
            return
        color = AVAILABLE_COLORS[args[1]]
        console.print(f"[bold {color['code']}]颜色预览 / Color preview: {args[1]}[/]")
        console.print(f"[dim]HEX: {color['hex']}[/dim]")
        return

    if args[0] == "reset":
        config["agent_color"] = "cyan"
        _save_color_config(config)
        obj["agent_color"] = "cyan"
        console.print("[green]✓ 颜色已重置为cyan / Color reset to cyan[/green]")
        return

    if args[0] == "set":
        if len(args) < 2:
            console.print("[red]请指定颜色名称 / Please specify color name[/red]")
            return
        color_name = args[1].lower()
    else:
        color_name = args[0].lower()

    if color_name not in AVAILABLE_COLORS:
        console.print(f"[red]未知颜色 / Unknown color: {color_name}[/red]")
        console.print(f"[dim]可用颜色 / Available: {', '.join(AVAILABLE_COLORS.keys())}[/dim]")
        return

    config["agent_color"] = color_name
    _save_color_config(config)
    obj["agent_color"] = color_name
    color_info = AVAILABLE_COLORS[color_name]
    console.print(f"[bold {color_info['code']}]✓ 代理颜色已设置 / Agent color set: {color_name}[/]")
