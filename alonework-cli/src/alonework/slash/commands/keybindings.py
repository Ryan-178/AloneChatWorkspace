"""
/keybindings å½ä»¤ - èªå®ä¹é®çå¿«æ·é® / Custom keyboard shortcuts

ç®¡çé®çå¿«æ·é®ç»å®?/ Manage keyboard shortcut bindings
çæ¬ / Version: 2.1.18
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json

console = Console()

DEFAULT_BINDINGS = {
    "Ctrl+C": {"action": "interrupt", "description": "ä¸­æ­å½åæä½ / Interrupt current operation"},
    "Ctrl+D": {"action": "exit", "description": "éåºç¨åº?/ Exit program"},
    "Ctrl+L": {"action": "clear_screen", "description": "æ¸å± / Clear screen"},
    "Ctrl+O": {"action": "toggle_thinking", "description": "åæ¢æç»´åæ¾ç¤?/ Toggle thinking block"},
    "Tab": {"action": "autocomplete", "description": "èªå¨è¡¥å¨ / Auto-complete"},
    "Up": {"action": "history_prev", "description": "ä¸ä¸æ¡åå?/ Previous history"},
    "Down": {"action": "history_next", "description": "ä¸ä¸æ¡åå?/ Next history"},
    "Enter": {"action": "submit", "description": "æäº¤è¾å¥ / Submit input"},
    "Shift+Enter": {"action": "newline", "description": "æ¢è¡ / New line"},
}


def keybindings_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    èªå®ä¹é®çå¿«æ·é® / Custom keyboard shortcuts
    
    ç¨æ³ / Usage:
        /keybindings                 ååºææå¿«æ·é® / List all shortcuts
        /keybindings <key>           æ¥çå¿«æ·é®è¯¦æ?/ Show shortcut details
        /keybindings set <key> <action> è®¾ç½®å¿«æ·é?/ Set shortcut
        /keybindings reset           æ¢å¤é»è®¤ / Reset to defaults
        /keybindings export          å¯¼åºéç½® / Export config
    
    ç¤ºä¾ / Examples:
        /keybindings                 æ¥çææç»å®?/ View all bindings
        /keybindings Ctrl+C          æ¥çCtrl+Cè¯¦æ / View Ctrl+C details
        /keybindings reset           æ¢å¤é»è®¤ / Reset to defaults
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
        table = Table(title="é®çå¿«æ·é?/ Keyboard Shortcuts", show_header=True)
        table.add_column("å¿«æ·é?/ Key", style="cyan")
        table.add_column("æä½ / Action")
        table.add_column("æè¿° / Description")
        
        for key, info in bindings.items():
            is_default = key in DEFAULT_BINDINGS and DEFAULT_BINDINGS[key]["action"] == info["action"]
            key_style = "cyan" if is_default else "yellow"
            table.add_row(f"[{key_style}]{key}[/{key_style}]", info.get("action", "-"), info.get("description", ""))
        
        console.print(table)
        console.print(f"\n[dim]å?{len(bindings)} ä¸ªå¿«æ·é® / Total {len(bindings)} shortcuts[/dim]")
        console.print("[dim]èªå®ä¹å¿«æ·é®ç¨é»è²æ è®?/ Custom bindings marked in yellow[/dim]")
        console.print("[dim]ä½¿ç¨ /keybindings set <key> <action> æ·»å èªå®ä¹ç»å®[/dim]")
        return
    
    if args[0] == "set" and len(args) >= 3:
        key = args[1]
        action = args[2]
        description = " ".join(args[3:]) if len(args) > 3 else Prompt.ask("[cyan]æè¿° / Description[/cyan]", default=action)
        
        bindings[key] = {
            "action": action,
            "description": description or action,
        }
        _save_bindings(bindings)
        console.print(f"[green]â?å¿«æ·é®å·²è®¾ç½® / Shortcut set: {key} -> {action}[/green]")
        return
    
    if args[0] == "reset":
        if Confirm.ask("ç¡®å®æ¢å¤ææå¿«æ·é®ä¸ºé»è®¤å¼ï¼ / Reset all shortcuts to defaults?"):
            _save_bindings(dict(DEFAULT_BINDINGS))
            console.print("[green]â?å¿«æ·é®å·²æ¢å¤é»è®¤ / Shortcuts reset to defaults[/green]")
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
        console.print(f"[green]â?å¿«æ·é®éç½®å·²å¯¼åº / Bindings exported: {export_path}[/green]")
        return
    
    key = args[0]
    binding = bindings.get(key)
    
    if binding:
        is_default = key in DEFAULT_BINDINGS and DEFAULT_BINDINGS[key]["action"] == binding["action"]
        console.print(Panel(
            f"[bold cyan]{key}[/bold cyan]\n\n"
            f"[dim]æä½ / Action: {binding['action']}[/dim]\n"
            f"[dim]æè¿° / Description: {binding.get('description', '-')}[/dim]\n"
            f"[dim]æ¥æº / Source: {'é»è®¤ / Default' if is_default else 'èªå®ä¹?/ Custom'}[/dim]",
            title="å¿«æ·é®è¯¦æ?/ Shortcut Details",
            border_style="cyan"
        ))
    else:
        console.print(f"[yellow]å¿«æ·é®æªç»å® / Key not bound: {key}[/yellow]")
        console.print("[dim]ä½¿ç¨ /keybindings set <key> <action> æ·»å ç»å®[/dim]")
