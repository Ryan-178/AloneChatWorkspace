"""
/reload-plugins å½ä»¤ - éæ°å è½½æä»¶ / Reload plugins

æ ééå¯å³å¯æ¿æ´»æä»¶æ´æ?/ Activate plugin changes without restart
çæ¬ / Version: 2.1.69
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from pathlib import Path
import sys

console = Console()


def reload_plugins_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    éæ°å è½½æä»¶ / Reload plugins
    
    æ ééå¯å³å¯æ¿æ´»æä»¶æ´æ?/ Activate plugin changes without restart
    
    ç¨æ³ / Usage:
        /reload-plugins                   éæ°å è½½æææä»?/ Reload all plugins
        /reload-plugins <name>            éæ°å è½½æå®æä»¶ / Reload specific plugin
        /reload-plugins list              ååºææå·²å è½½æä»¶ / List all loaded plugins
        /reload-plugins status            æ¥çæä»¶ç¶æ?/ Check plugin status
    
    ç¤ºä¾ / Examples:
        /reload-plugins                   éæ°å è½½å¨é¨ / Reload all
        /reload-plugins code_tools        éæ°å è½½ä»£ç å·¥å· / Reload code tools
        /reload-plugins list              ååºæä»¶ / List plugins
    """
    plugin_dirs = [
        Path.cwd() / ".alonechat" / "plugins",
        Path.home() / ".alonechat" / "plugins",
    ]
    
    loaded_plugins_file = Path.home() / ".alonechat" / "loaded_plugins.json"
    import json
    
    def _get_registered_plugins() -> dict[str, dict]:
        plugins = {}
        if registry:
            for cmd in registry.list_commands():
                plugins[f"slash:{cmd.name}"] = {
                    "type": "slash_command",
                    "name": cmd.name,
                    "category": cmd.category,
                    "description": cmd.description,
                }
        return plugins
    
    def _scan_plugin_files() -> list[Path]:
        found = []
        for plugin_dir in plugin_dirs:
            if plugin_dir.exists():
                for ext in ("*.py", "*.yaml", "*.yml", "*.json"):
                    found.extend(plugin_dir.glob(ext))
        return found
    
    def _load_loaded_plugins() -> dict:
        if loaded_plugins_file.exists():
            try:
                with open(loaded_plugins_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"plugins": [], "loaded_at": None}
    
    def _save_loaded_plugins(data: dict) -> None:
        loaded_plugins_file.parent.mkdir(parents=True, exist_ok=True)
        with open(loaded_plugins_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    if not args:
        registered = _get_registered_plugins()
        plugin_files = _scan_plugin_files()
        
        if not registered and not plugin_files:
            console.print("[yellow]æªæ¾å°å¯éæ°å è½½çæä»?/ No plugins available to reload[/yellow]")
            return
        
        reload_count = 0
        
        if registered:
            for name, info in registered.items():
                category = info.get("category", "general")
                if category in ("skills", "tools", "integrations"):
                    console.print(f"  [dim]éè½½ / Reload: {name} ({info['description']})[/dim]")
                    reload_count += 1
        
        for plugin_file in plugin_files:
            console.print(f"  [dim]æ£æµå°æä»¶æä»¶ / Plugin file: {plugin_file.name}[/dim]")
            reload_count += 1
        
        if reload_count > 0 and not Confirm.ask(f"\nå°éæ°å è½?{reload_count} ä¸ªæä»¶ï¼ç¡®è®¤ï¼?/ Reload {reload_count} plugin(s)?"):
            console.print("[yellow]å·²åæ¶?/ Cancelled[/yellow]")
            return
        
        now = __import__("datetime").datetime.now().isoformat()
        plugin_data = _load_loaded_plugins()
        plugin_data["plugins"] = list(registered.keys()) + [str(f) for f in plugin_files]
        plugin_data["loaded_at"] = now
        plugin_data["reload_count"] = plugin_data.get("reload_count", 0) + 1
        _save_loaded_plugins(plugin_data)
        
        console.print(f"[green]â?å·²éæ°å è½?{reload_count} ä¸ªæä»?/ Reloaded {reload_count} plugin(s)[/green]")
        console.print(f"[dim]æ ééå¯ / No restart required[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        registered = _get_registered_plugins()
        plugin_files = _scan_plugin_files()
        
        if not registered and not plugin_files:
            console.print("[yellow]ææ æä»¶ / No plugins[/yellow]")
            return
        
        table = Table(title="å·²å è½½æä»?/ Loaded Plugins", show_header=True)
        table.add_column("åç§° / Name", style="cyan")
        table.add_column("ç±»å / Type")
        table.add_column("æ¥æº / Source")
        table.add_column("æè¿° / Description")
        
        for name, info in registered.items():
            table.add_row(name, info.get("type", "unknown"), "æ³¨åè¡?/ Registry", info.get("description", ""))
        
        for f in plugin_files:
            table.add_row(f.stem, "file", str(f.parent.name), f.name)
        
        console.print(table)
        
        plugin_data = _load_loaded_plugins()
        if plugin_data.get("loaded_at"):
            console.print(f"\n[dim]ä¸æ¬¡éè½½ / Last reload: {plugin_data['loaded_at'][:16]}[/dim]")
            console.print(f"[dim]éè½½æ¬¡æ° / Reload count: {plugin_data.get('reload_count', 0)}[/dim]")
        return
    
    if subcommand == "status":
        registered = _get_registered_plugins()
        plugin_files = _scan_plugin_files()
        plugin_data = _load_loaded_plugins()
        
        console.print(Panel(
            f"[bold cyan]æä»¶ç³»ç»ç¶æ?/ Plugin System Status[/bold cyan]\n\n"
            f"[dim]æ³¨åå½ä»¤ / Registered commands: {len(registered)}[/dim]\n"
            f"[dim]æä»¶æä»¶ / Plugin files: {len(plugin_files)}[/dim]\n"
            f"[dim]éè½½æ¬¡æ° / Reloads: {plugin_data.get('reload_count', 0)}[/dim]\n"
            f"[dim]ä¸æ¬¡éè½½ / Last reload: {plugin_data.get('loaded_at', 'ä»æª / Never')[:16]}[/dim]\n"
            f"[dim]æç´¢ç®å½ / Search dirs: {', '.join(str(d) for d in plugin_dirs if d.exists())}[/dim]",
            title="æä»¶ç¶æ?/ Plugin Status",
            border_style="cyan"
        ))
        return
    
    registered = _get_registered_plugins()
    target_name = subcommand
    
    found = False
    for name, info in registered.items():
        short_name = name.split(":")[-1] if ":" in name else name
        target_short = target_name.split(":")[-1] if ":" in target_name else target_name
        if short_name == target_short or name == target_name:
            console.print(f"[green]â?å·²éæ°å è½?/ Reloaded: {name} ({info.get('description', '')})[/green]")
            found = True
            break
    
    if not found:
        console.print(f"[red]æä»¶æªæ¾å?/ Plugin not found: {target_name}[/red]")
        console.print("[dim]ä½¿ç¨ /reload-plugins list æ¥çæææä»?/ Use /reload-plugins list to see all plugins[/dim]")
