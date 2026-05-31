"""
/output-style 命令 - 设置输出样式 / Set output style

版本 / Version: 2.1.80
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

CONFIG_DIR = Path.cwd() / ".alonechat"
STYLE_FILE = CONFIG_DIR / "output_style_override.yaml"

OUTPUT_STYLES = {
    "default": {
        "name": "默认样式 / Default Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": True,
        "timestamps": False,
        "emoji": True,
        "verbose": False,
    },
    "compact": {
        "name": "紧凑样式 / Compact Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": False,
        "timestamps": False,
        "emoji": False,
        "verbose": False,
    },
    "verbose": {
        "name": "详细样式 / Verbose Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": True,
        "timestamps": True,
        "emoji": True,
        "verbose": True,
    },
    "minimal": {
        "name": "极简样式 / Minimal Style",
        "code_block": False,
        "syntax_highlight": False,
        "line_numbers": False,
        "timestamps": False,
        "emoji": False,
        "verbose": False,
    },
    "dark": {
        "name": "深色样式 / Dark Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": True,
        "timestamps": False,
        "emoji": True,
        "verbose": False,
    },
    "light": {
        "name": "浅色样式 / Light Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": True,
        "timestamps": False,
        "emoji": True,
        "verbose": False,
    },
    "monokai": {
        "name": "Monokai样式 / Monokai Style",
        "code_block": True,
        "syntax_highlight": True,
        "line_numbers": True,
        "timestamps": False,
        "emoji": True,
        "verbose": False,
    },
}


def _load_style_config() -> dict:
    """
    加载输出样式配置 / Load output style configuration
    """
    if not STYLE_FILE.exists():
        return {"current_style": "default"}
    try:
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"current_style": "default"}
    except Exception:
        return {"current_style": "default"}


def _save_style_config(config: dict) -> bool:
    """
    保存输出样式配置 / Save output style configuration
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(STYLE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception:
        return False


def output_style_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    设置输出样式 / Set output style

    用法 / Usage:
        /output-style                  显示当前样式 / Show current style
        /output-style list             列出可用样式 / List available styles
        /output-style <name>           切换样式 / Switch style
        /output-style preview <name>   预览样式 / Preview style
        /output-style reset            重置为默认 / Reset to default

    可用样式 / Available styles:
        default, compact, verbose, minimal, dark, light, monokai
    """
    config = _load_style_config()
    current = config.get("current_style", "default")

    if not args or args[0] == "status":
        style_info = OUTPUT_STYLES.get(current, {})
        console.print(Panel(
            f"[bold]当前输出样式 / Current Output Style[/bold]\n\n"
            f"名称 / Name: {current}\n"
            f"描述 / Description: {style_info.get('name', '-')}\n"
            f"代码块 / Code block: {'✓' if style_info.get('code_block') else '✗'}\n"
            f"语法高亮 / Syntax highlight: {'✓' if style_info.get('syntax_highlight') else '✗'}\n"
            f"行号 / Line numbers: {'✓' if style_info.get('line_numbers') else '✗'}\n"
            f"时间戳 / Timestamps: {'✓' if style_info.get('timestamps') else '✗'}\n"
            f"表情 / Emoji: {'✓' if style_info.get('emoji') else '✗'}\n"
            f"详细模式 / Verbose: {'✓' if style_info.get('verbose') else '✗'}",
            border_style="cyan",
        ))
        return

    if args[0] == "list":
        table = Table(show_header=True, title="可用输出样式 / Available Output Styles")
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description", style="green")
        table.add_column("代码块 / Code", style="yellow")
        table.add_column("高亮 / Highlight", style="yellow")
        table.add_column("当前 / Current", style="bold")

        for name, info in OUTPUT_STYLES.items():
            is_current = " ← " if name == current else ""
            table.add_row(
                name,
                info["name"],
                "✓" if info["code_block"] else "✗",
                "✓" if info["syntax_highlight"] else "✗",
                is_current,
            )

        console.print(table)
        return

    if args[0] == "preview":
        if len(args) < 2 or args[1] not in OUTPUT_STYLES:
            console.print("[red]请指定有效样式 / Please specify valid style[/red]")
            return
        style = OUTPUT_STYLES[args[1]]
        console.print(Panel(
            f"[bold]样式预览 / Style Preview: {args[1]}[/bold]\n\n"
            f"名称 / Name: {style['name']}\n"
            f"代码块 / Code block: {'✓' if style['code_block'] else '✗'}\n"
            f"语法高亮 / Syntax highlight: {'✓' if style['syntax_highlight'] else '✗'}\n"
            f"行号 / Line numbers: {'✓' if style['line_numbers'] else '✗'}\n"
            f"时间戳 / Timestamps: {'✓' if style['timestamps'] else '✗'}\n"
            f"表情 / Emoji: {'✓' if style['emoji'] else '✗'}\n"
            f"详细 / Verbose: {'✓' if style['verbose'] else '✗'}",
            border_style="cyan",
        ))
        return

    if args[0] == "reset":
        config["current_style"] = "default"
        _save_style_config(config)
        obj["output_style"] = "default"
        console.print("[green]✓ 输出样式已重置 / Output style reset to default[/green]")
        return

    style_name = args[0].lower()
    if style_name not in OUTPUT_STYLES:
        console.print(f"[red]未知样式 / Unknown style: {style_name}[/red]")
        console.print(f"[dim]可用样式 / Available: {', '.join(OUTPUT_STYLES.keys())}[/dim]")
        return

    config["current_style"] = style_name
    _save_style_config(config)
    obj["output_style"] = style_name
    console.print(f"[green]✓ 输出样式已切换 / Output style switched: {style_name}[/green]")
    console.print(f"[dim]{OUTPUT_STYLES[style_name]['name']}[/dim]")
