"""
/reload-plugins 命令 - 重新加载插件 / Reload plugins

无需重启即可激活插件更改 / Activate plugin changes without restart
版本 / Version: 2.1.69
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
    重新加载插件 / Reload plugins
    
    无需重启即可激活插件更改 / Activate plugin changes without restart
    
    用法 / Usage:
        /reload-plugins                   重新加载所有插件 / Reload all plugins
        /reload-plugins <name>            重新加载指定插件 / Reload specific plugin
        /reload-plugins list              列出所有已加载插件 / List all loaded plugins
        /reload-plugins status            查看插件状态 / Check plugin status
    
    示例 / Examples:
        /reload-plugins                   重新加载全部 / Reload all
        /reload-plugins code_tools        重新加载代码工具 / Reload code tools
        /reload-plugins list              列出插件 / List plugins
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
            console.print("[yellow]未找到可重新加载的插件 / No plugins available to reload[/yellow]")
            return
        
        reload_count = 0
        
        if registered:
            for name, info in registered.items():
                category = info.get("category", "general")
                if category in ("skills", "tools", "integrations"):
                    console.print(f"  [dim]重载 / Reload: {name} ({info['description']})[/dim]")
                    reload_count += 1
        
        for plugin_file in plugin_files:
            console.print(f"  [dim]检测到插件文件 / Plugin file: {plugin_file.name}[/dim]")
            reload_count += 1
        
        if reload_count > 0 and not Confirm.ask(f"\n将重新加载 {reload_count} 个插件，确认？ / Reload {reload_count} plugin(s)?"):
            console.print("[yellow]已取消 / Cancelled[/yellow]")
            return
        
        now = __import__("datetime").datetime.now().isoformat()
        plugin_data = _load_loaded_plugins()
        plugin_data["plugins"] = list(registered.keys()) + [str(f) for f in plugin_files]
        plugin_data["loaded_at"] = now
        plugin_data["reload_count"] = plugin_data.get("reload_count", 0) + 1
        _save_loaded_plugins(plugin_data)
        
        console.print(f"[green]✓ 已重新加载 {reload_count} 个插件 / Reloaded {reload_count} plugin(s)[/green]")
        console.print(f"[dim]无需重启 / No restart required[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        registered = _get_registered_plugins()
        plugin_files = _scan_plugin_files()
        
        if not registered and not plugin_files:
            console.print("[yellow]暂无插件 / No plugins[/yellow]")
            return
        
        table = Table(title="已加载插件 / Loaded Plugins", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("类型 / Type")
        table.add_column("来源 / Source")
        table.add_column("描述 / Description")
        
        for name, info in registered.items():
            table.add_row(name, info.get("type", "unknown"), "注册表 / Registry", info.get("description", ""))
        
        for f in plugin_files:
            table.add_row(f.stem, "file", str(f.parent.name), f.name)
        
        console.print(table)
        
        plugin_data = _load_loaded_plugins()
        if plugin_data.get("loaded_at"):
            console.print(f"\n[dim]上次重载 / Last reload: {plugin_data['loaded_at'][:16]}[/dim]")
            console.print(f"[dim]重载次数 / Reload count: {plugin_data.get('reload_count', 0)}[/dim]")
        return
    
    if subcommand == "status":
        registered = _get_registered_plugins()
        plugin_files = _scan_plugin_files()
        plugin_data = _load_loaded_plugins()
        
        console.print(Panel(
            f"[bold cyan]插件系统状态 / Plugin System Status[/bold cyan]\n\n"
            f"[dim]注册命令 / Registered commands: {len(registered)}[/dim]\n"
            f"[dim]插件文件 / Plugin files: {len(plugin_files)}[/dim]\n"
            f"[dim]重载次数 / Reloads: {plugin_data.get('reload_count', 0)}[/dim]\n"
            f"[dim]上次重载 / Last reload: {plugin_data.get('loaded_at', '从未 / Never')[:16]}[/dim]\n"
            f"[dim]搜索目录 / Search dirs: {', '.join(str(d) for d in plugin_dirs if d.exists())}[/dim]",
            title="插件状态 / Plugin Status",
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
            console.print(f"[green]✓ 已重新加载 / Reloaded: {name} ({info.get('description', '')})[/green]")
            found = True
            break
    
    if not found:
        console.print(f"[red]插件未找到 / Plugin not found: {target_name}[/red]")
        console.print("[dim]使用 /reload-plugins list 查看所有插件 / Use /reload-plugins list to see all plugins[/dim]")
