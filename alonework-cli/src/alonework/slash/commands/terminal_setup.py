"""
/terminal-setup å½ä»¤ - ç»ç«¯éç½® / Terminal setup

ç®¡çç»ç«¯æ¨¡æå¨éç½?/ Manage terminal emulator configurations
æ¯æ KittyãAlacrittyãZedãWarp / Supports Kitty, Alacritty, Zed, Warp
çæ¬ / Version: 2.0.74
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json
import shutil

console = Console()

TERMINAL_CONFIGS = {
    "kitty": {
        "name": "Kitty",
        "config_file": "kitty.conf",
        "config_dir": "~/.config/kitty/",
        "website": "https://sw.kovidgoyal.net/kitty/",
        "features": ["GPUå é?, "åå²çªæ ¼", "å¿«æ·é®ä¸°å¯?, "å¾åæ¾ç¤º"],
    },
    "alacritty": {
        "name": "Alacritty",
        "config_file": "alacritty.toml",
        "config_dir": "~/.config/alacritty/",
        "website": "https://alacritty.org/",
        "features": ["GPUå é?, "è·¨å¹³å?, "TOMLéç½®", "é«æ§è½"],
    },
    "zed": {
        "name": "Zed",
        "config_file": "settings.json",
        "config_dir": "~/.config/zed/",
        "website": "https://zed.dev/",
        "features": ["åç½®ç»ç«¯", "åç¨æ¯æ", "AIéæ", "Vimæ¨¡å¼"],
    },
    "warp": {
        "name": "Warp",
        "config_file": "warp.config",
        "config_dir": "~/.warp/",
        "website": "https://www.warp.dev/",
        "features": ["AIç»ç«¯", "åç¼è¾?, "å·¥ä½æµ?, "æºè½è¡¥å¨"],
    },
}


def terminal_setup_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ç»ç«¯éç½® / Terminal setup
    
    ç¨æ³ / Usage:
        /terminal-setup                  æ¾ç¤ºç»ç«¯éç½®æ¦è§ / Show terminal overview
        /terminal-setup <terminal>       éç½®æå®ç»ç«¯ / Configure specific terminal
        /terminal-setup list             ååºæææ¯æçç»ç«¯ / List supported terminals
        /terminal-setup detect           èªå¨æ£æµå·²å®è£çç»ç«?/ Auto-detect installed terminals
    
    ç¤ºä¾ / Examples:
        /terminal-setup                  æ¥çéç½® / View configuration
        /terminal-setup kitty            éç½®Kitty / Configure Kitty
        /terminal-setup detect           æ£æµç»ç«?/ Detect terminals
    """
    config_dir = Path.home() / ".alonechat" / "terminal"
    config_dir.mkdir(parents=True, exist_ok=True)
    settings_file = config_dir / "settings.json"
    
    def _load_settings() -> dict:
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"preferred_terminal": None, "configured_terminals": []}
    
    def _save_settings(settings: dict) -> None:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    
    def _detect_terminal(name: str) -> bool:
        return shutil.which(name) is not None
    
    settings = _load_settings()
    
    if not args:
        console.print("\n[bold cyan]ç»ç«¯éç½® / Terminal Setup[/bold cyan]\n")
        
        overview_table = Table(show_header=True)
        overview_table.add_column("ç»ç«¯ / Terminal", style="cyan")
        overview_table.add_column("ç¶æ?/ Status")
        overview_table.add_column("å·²éç½?/ Configured")
        overview_table.add_column("åè½ç¹æ?/ Features")
        
        for key, info in TERMINAL_CONFIGS.items():
            installed = _detect_terminal(key)
            installed_str = "[green]â?å·²å®è£[/green]" if installed else "[yellow]æªå®è£[/yellow]"
            configured = "æ?/ Yes" if key in settings.get("configured_terminals", []) else "å?/ No"
            features = ", ".join(info["features"])
            overview_table.add_row(info["name"], installed_str, configured, features)
        
        console.print(overview_table)
        
        preferred = settings.get("preferred_terminal")
        if preferred:
            console.print(f"\n[dim]é¦éç»ç«?/ Preferred: {preferred}[/dim]")
        console.print(f"\n[dim]ä½¿ç¨ /terminal-setup <name> éç½®ç»ç«¯ / Use /terminal-setup <name> to configure[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        table = Table(title="æ¯æçç»ç«?/ Supported Terminals", show_header=True)
        table.add_column("åç§° / Name", style="cyan")
        table.add_column("éç½®ç®å½ / Config Dir")
        table.add_column("éç½®æä»¶ / Config File")
        table.add_column("å®æ¹ç½ç« / Website", style="dim")
        
        for key, info in TERMINAL_CONFIGS.items():
            table.add_row(
                info["name"],
                info["config_dir"],
                info["config_file"],
                info["website"],
            )
        
        console.print(table)
        return
    
    if subcommand == "detect":
        console.print("[bold cyan]æ£æµå·²å®è£ç»ç«¯ / Detecting Installed Terminals[/bold cyan]\n")
        
        detected = []
        for key in TERMINAL_CONFIGS:
            installed = _detect_terminal(key)
            status = "[green]â?å·²å®è£[/green]" if installed else "[yellow]æªå®è£[/yellow]"
            console.print(f"  {TERMINAL_CONFIGS[key]['name']}: {status}")
            if installed:
                detected.append(key)
        
        if detected:
            console.print(f"\n[green]æ£æµå° {len(detected)} ä¸ªç»ç«?/ {len(detected)} terminal(s) detected[/green]")
            settings["configured_terminals"] = list(set(settings.get("configured_terminals", []) + detected))
            _save_settings(settings)
        else:
            console.print("\n[yellow]æªæ£æµå°æ¯æçç»ç«?/ No supported terminals detected[/yellow]")
        return
    
    terminal_key = subcommand.lower()
    if terminal_key not in TERMINAL_CONFIGS:
        console.print(f"[red]ä¸æ¯æçç»ç«¯ / Unsupported terminal: {terminal_key}[/red]")
        console.print("[dim]æ¯æçç»ç«? " + ", ".join(TERMINAL_CONFIGS.keys()) + "[/dim]")
        return
    
    info = TERMINAL_CONFIGS[terminal_key]
    installed = _detect_terminal(terminal_key)
    
    console.print(Panel(
        f"[bold cyan]{info['name']}[/bold cyan]\n\n"
        f"[dim]å®è£ç¶æ?/ Installed: {'[green]â[/green]' if installed else '[yellow]â[/yellow]'}[/dim]\n"
        f"[dim]éç½®ç®å½ / Config dir: {info['config_dir']}[/dim]\n"
        f"[dim]éç½®æä»¶ / Config file: {info['config_file']}[/dim]\n"
        f"[dim]å®æ¹ç½ç« / Website: {info['website']}[/dim]\n\n"
        f"[bold]åè½ç¹æ?/ Features:[/bold]\n"
        + "\n".join(f"  â?{f}" for f in info["features"]),
        title="ç»ç«¯è¯¦æ / Terminal Details",
        border_style="cyan"
    ))
    
    if not installed:
        console.print(f"\n[yellow]{info['name']} æªå®è£ï¼è¯·è®¿é®å®ç½ä¸è½?/ Not installed, visit website to download[/yellow]")
        return
    
    if Confirm.ask(f"\néç½® {info['name']} ä¸ºAloneChaté¦éç»ç«¯ï¼ / Set {info['name']} as preferred terminal?"):
        config_path = Path(info["config_dir"].replace("~", str(Path.home()))) / info["config_file"]
        
        alonechat_config = f"""
# AloneChat éæéç½® / AloneChat Integration
# ç?/terminal-setup å½ä»¤çæ / Generated by /terminal-setup command

# å­ä½è®¾ç½® / Font settings
font_family = "JetBrains Mono"
font_size = 13.0

# é¢è²æ¹æ¡ / Color scheme
# ééAloneChat UIé£æ ¼ / Adapted for AloneChat UI style
foreground = "#cdd6f4"
background = "#1e1e2e"
"""
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text(alonechat_config.strip(), encoding="utf-8")
            console.print(f"[green]â?å·²åå»ºéç½®æä»?/ Config created: {config_path}[/green]")
        else:
            console.print(f"[dim]éç½®æä»¶å·²å­å?/ Config already exists: {config_path}[/dim]")
        
        if terminal_key not in settings.get("configured_terminals", []):
            configured = settings.get("configured_terminals", [])
            configured.append(terminal_key)
            settings["configured_terminals"] = configured
        settings["preferred_terminal"] = info["name"]
        _save_settings(settings)
        
        console.print(f"[green]â?{info['name']} å·²è®¾ä¸ºé¦éç»ç«?/ Set as preferred terminal[/green]")
