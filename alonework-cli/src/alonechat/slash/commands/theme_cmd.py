"""
/theme 命令 - 切换主题 / Switch theme

版本 / Version: 2.1.80
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

CONFIG_DIR = Path.cwd() / ".alonechat"
THEME_FILE = CONFIG_DIR / "theme.yaml"

AVAILABLE_THEMES = {
    "dark": {
        "name": "深色主题 / Dark Theme",
        "background": "#1a1a2e",
        "foreground": "#eaeaea",
        "primary": "#4a9eff",
    },
    "light": {
        "name": "浅色主题 / Light Theme",
        "background": "#ffffff",
        "foreground": "#333333",
        "primary": "#0066cc",
    },
    "monokai": {
        "name": "Monokai主题 / Monokai Theme",
        "background": "#272822",
        "foreground": "#f8f8f2",
        "primary": "#66d9ef",
    },
    "dracula": {
        "name": "Dracula主题 / Dracula Theme",
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "primary": "#bd93f9",
    },
    "nord": {
        "name": "Nord主题 / Nord Theme",
        "background": "#2e3440",
        "foreground": "#eceff4",
        "primary": "#88c0d0",
    },
}


def _load_theme_config() -> dict:
    """
    加载主题配置 / Load theme configuration
    """
    if not THEME_FILE.exists():
        return {"current": "dark"}
    try:
        with open(THEME_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"current": "dark"}
    except Exception:
        return {"current": "dark"}


def _save_theme_config(config: dict) -> bool:
    """
    保存主题配置 / Save theme configuration
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception:
        return False


def theme_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    切换主题 / Switch theme

    用法 / Usage:
        /theme                  显示当前主题 / Show current theme
        /theme list             列出可用主题 / List available themes
        /theme <name>           切换到指定主题 / Switch to specified theme
        /theme preview <name>   预览主题 / Preview theme
        /theme reset            重置为默认主题 / Reset to default theme

    可用主题 / Available themes:
        dark, light, monokai, dracula, nord
    """
    config = _load_theme_config()
    current = config.get("current", "dark")

    if not args or args[0] == "status":
        theme_info = AVAILABLE_THEMES.get(current, {})
        console.print(Panel(
            f"[bold]当前主题 / Current Theme[/bold]\n\n"
            f"名称 / Name: {current}\n"
            f"描述 / Description: {theme_info.get('name', '-')}\n"
            f"背景 / Background: {theme_info.get('background', '-')}\n"
            f"前景 / Foreground: {theme_info.get('foreground', '-')}\n"
            f"主色 / Primary: {theme_info.get('primary', '-')}",
            border_style="cyan",
        ))
        return

    if args[0] == "list":
        table = Table(show_header=True, title="可用主题 / Available Themes")
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description", style="green")
        table.add_column("背景 / BG", style="yellow")
        table.add_column("前景 / FG", style="yellow")
        table.add_column("当前 / Current", style="bold")

        for name, info in AVAILABLE_THEMES.items():
            is_current = " ← " if name == current else ""
            table.add_row(
                name,
                info["name"],
                info["background"],
                info["foreground"],
                is_current,
            )

        console.print(table)
        return

    if args[0] == "preview":
        if len(args) < 2 or args[1] not in AVAILABLE_THEMES:
            console.print("[red]请指定有效主题 / Please specify valid theme[/red]")
            return
        theme = AVAILABLE_THEMES[args[1]]
        console.print(Panel(
            f"[bold]主题预览 / Theme Preview: {args[1]}[/bold]\n\n"
            f"名称 / Name: {theme['name']}\n"
            f"背景 / Background: {theme['background']}\n"
            f"前景 / Foreground: {theme['foreground']}\n"
            f"主色 / Primary: {theme['primary']}",
            border_style="cyan",
        ))
        return

    if args[0] == "reset":
        config["current"] = "dark"
        _save_theme_config(config)
        obj["theme"] = "dark"
        console.print("[green]✓ 主题已重置为深色 / Theme reset to dark[/green]")
        return

    theme_name = args[0].lower()
    if theme_name not in AVAILABLE_THEMES:
        console.print(f"[red]未知主题 / Unknown theme: {theme_name}[/red]")
        console.print(f"[dim]可用主题 / Available: {', '.join(AVAILABLE_THEMES.keys())}[/dim]")
        return

    config["current"] = theme_name
    _save_theme_config(config)
    obj["theme"] = theme_name
    console.print(f"[green]✓ 主题已切换 / Theme switched: {theme_name}[/green]")
    console.print(f"[dim]{AVAILABLE_THEMES[theme_name]['name']}[/dim]")
