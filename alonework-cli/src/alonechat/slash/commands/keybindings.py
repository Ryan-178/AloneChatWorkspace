"""
/keybindings 命令 - 自定义键盘快捷键 / Custom keyboard shortcuts

管理键盘快捷键绑定 / Manage keyboard shortcut bindings
版本 / Version: 2.1.18
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json

console = Console()

DEFAULT_BINDINGS = {
    "Ctrl+C": {"action": "interrupt", "description": "中断当前操作 / Interrupt current operation"},
    "Ctrl+D": {"action": "exit", "description": "退出程序 / Exit program"},
    "Ctrl+L": {"action": "clear_screen", "description": "清屏 / Clear screen"},
    "Ctrl+O": {"action": "toggle_thinking", "description": "切换思维块显示 / Toggle thinking block"},
    "Tab": {"action": "autocomplete", "description": "自动补全 / Auto-complete"},
    "Up": {"action": "history_prev", "description": "上一条历史 / Previous history"},
    "Down": {"action": "history_next", "description": "下一条历史 / Next history"},
    "Enter": {"action": "submit", "description": "提交输入 / Submit input"},
    "Shift+Enter": {"action": "newline", "description": "换行 / New line"},
}


def keybindings_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    自定义键盘快捷键 / Custom keyboard shortcuts
    
    用法 / Usage:
        /keybindings                 列出所有快捷键 / List all shortcuts
        /keybindings <key>           查看快捷键详情 / Show shortcut details
        /keybindings set <key> <action> 设置快捷键 / Set shortcut
        /keybindings reset           恢复默认 / Reset to defaults
        /keybindings export          导出配置 / Export config
    
    示例 / Examples:
        /keybindings                 查看所有绑定 / View all bindings
        /keybindings Ctrl+C          查看Ctrl+C详情 / View Ctrl+C details
        /keybindings reset           恢复默认 / Reset to defaults
    """
    config_dir = Path.home() / ".alonechat"
    config_dir.mkdir(parents=True, exist_ok=True)
    bindings_file = config_dir / "keybindings.json"
    
    def _load_bindings() -> dict:
        if bindings_file.exists():
            try:
                with open(bindings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return dict(DEFAULT_BINDINGS)
    
    def _save_bindings(bindings: dict) -> None:
        with open(bindings_file, "w", encoding="utf-8") as f:
            json.dump(bindings, f, ensure_ascii=False, indent=2)
    
    bindings = _load_bindings()
    
    if not args:
        table = Table(title="键盘快捷键 / Keyboard Shortcuts", show_header=True)
        table.add_column("快捷键 / Key", style="cyan")
        table.add_column("操作 / Action")
        table.add_column("描述 / Description")
        
        for key, info in bindings.items():
            is_default = key in DEFAULT_BINDINGS and DEFAULT_BINDINGS[key]["action"] == info["action"]
            key_style = "cyan" if is_default else "yellow"
            table.add_row(f"[{key_style}]{key}[/{key_style}]", info.get("action", "-"), info.get("description", ""))
        
        console.print(table)
        console.print(f"\n[dim]共 {len(bindings)} 个快捷键 / Total {len(bindings)} shortcuts[/dim]")
        console.print("[dim]自定义快捷键用黄色标记 / Custom bindings marked in yellow[/dim]")
        console.print("[dim]使用 /keybindings set <key> <action> 添加自定义绑定[/dim]")
        return
    
    if args[0] == "set" and len(args) >= 3:
        key = args[1]
        action = args[2]
        description = " ".join(args[3:]) if len(args) > 3 else Prompt.ask("[cyan]描述 / Description[/cyan]", default=action)
        
        bindings[key] = {
            "action": action,
            "description": description or action,
        }
        _save_bindings(bindings)
        console.print(f"[green]✓ 快捷键已设置 / Shortcut set: {key} -> {action}[/green]")
        return
    
    if args[0] == "reset":
        if Confirm.ask("确定恢复所有快捷键为默认值？ / Reset all shortcuts to defaults?"):
            _save_bindings(dict(DEFAULT_BINDINGS))
            console.print("[green]✓ 快捷键已恢复默认 / Shortcuts reset to defaults[/green]")
        return
    
    if args[0] == "export":
        export_data = {
            "version": "1.0",
            "bindings": bindings,
            "exported_at": __import__("datetime").datetime.now().isoformat(),
        }
        export_path = config_dir / "keybindings_export.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓ 快捷键配置已导出 / Bindings exported: {export_path}[/green]")
        return
    
    key = args[0]
    binding = bindings.get(key)
    
    if binding:
        is_default = key in DEFAULT_BINDINGS and DEFAULT_BINDINGS[key]["action"] == binding["action"]
        console.print(Panel(
            f"[bold cyan]{key}[/bold cyan]\n\n"
            f"[dim]操作 / Action: {binding['action']}[/dim]\n"
            f"[dim]描述 / Description: {binding.get('description', '-')}[/dim]\n"
            f"[dim]来源 / Source: {'默认 / Default' if is_default else '自定义 / Custom'}[/dim]",
            title="快捷键详情 / Shortcut Details",
            border_style="cyan"
        ))
    else:
        console.print(f"[yellow]快捷键未绑定 / Key not bound: {key}[/yellow]")
        console.print("[dim]使用 /keybindings set <key> <action> 添加绑定[/dim]")
