"""
/terminal-setup 命令 - 终端配置 / Terminal setup

管理终端模拟器配置 / Manage terminal emulator configurations
支持 Kitty、Alacritty、Zed、Warp / Supports Kitty, Alacritty, Zed, Warp
版本 / Version: 2.0.74
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
        "features": ["GPU加速", "分割窗格", "快捷键丰富", "图像显示"],
    },
    "alacritty": {
        "name": "Alacritty",
        "config_file": "alacritty.toml",
        "config_dir": "~/.config/alacritty/",
        "website": "https://alacritty.org/",
        "features": ["GPU加速", "跨平台", "TOML配置", "高性能"],
    },
    "zed": {
        "name": "Zed",
        "config_file": "settings.json",
        "config_dir": "~/.config/zed/",
        "website": "https://zed.dev/",
        "features": ["内置终端", "协程支持", "AI集成", "Vim模式"],
    },
    "warp": {
        "name": "Warp",
        "config_file": "warp.config",
        "config_dir": "~/.warp/",
        "website": "https://www.warp.dev/",
        "features": ["AI终端", "块编辑", "工作流", "智能补全"],
    },
}


def terminal_setup_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    终端配置 / Terminal setup
    
    用法 / Usage:
        /terminal-setup                  显示终端配置概览 / Show terminal overview
        /terminal-setup <terminal>       配置指定终端 / Configure specific terminal
        /terminal-setup list             列出所有支持的终端 / List supported terminals
        /terminal-setup detect           自动检测已安装的终端 / Auto-detect installed terminals
    
    示例 / Examples:
        /terminal-setup                  查看配置 / View configuration
        /terminal-setup kitty            配置Kitty / Configure Kitty
        /terminal-setup detect           检测终端 / Detect terminals
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
        console.print("\n[bold cyan]终端配置 / Terminal Setup[/bold cyan]\n")
        
        overview_table = Table(show_header=True)
        overview_table.add_column("终端 / Terminal", style="cyan")
        overview_table.add_column("状态 / Status")
        overview_table.add_column("已配置 / Configured")
        overview_table.add_column("功能特性 / Features")
        
        for key, info in TERMINAL_CONFIGS.items():
            installed = _detect_terminal(key)
            installed_str = "[green]✓ 已安装[/green]" if installed else "[yellow]未安装[/yellow]"
            configured = "是 / Yes" if key in settings.get("configured_terminals", []) else "否 / No"
            features = ", ".join(info["features"])
            overview_table.add_row(info["name"], installed_str, configured, features)
        
        console.print(overview_table)
        
        preferred = settings.get("preferred_terminal")
        if preferred:
            console.print(f"\n[dim]首选终端 / Preferred: {preferred}[/dim]")
        console.print(f"\n[dim]使用 /terminal-setup <name> 配置终端 / Use /terminal-setup <name> to configure[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        table = Table(title="支持的终端 / Supported Terminals", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("配置目录 / Config Dir")
        table.add_column("配置文件 / Config File")
        table.add_column("官方网站 / Website", style="dim")
        
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
        console.print("[bold cyan]检测已安装终端 / Detecting Installed Terminals[/bold cyan]\n")
        
        detected = []
        for key in TERMINAL_CONFIGS:
            installed = _detect_terminal(key)
            status = "[green]✓ 已安装[/green]" if installed else "[yellow]未安装[/yellow]"
            console.print(f"  {TERMINAL_CONFIGS[key]['name']}: {status}")
            if installed:
                detected.append(key)
        
        if detected:
            console.print(f"\n[green]检测到 {len(detected)} 个终端 / {len(detected)} terminal(s) detected[/green]")
            settings["configured_terminals"] = list(set(settings.get("configured_terminals", []) + detected))
            _save_settings(settings)
        else:
            console.print("\n[yellow]未检测到支持的终端 / No supported terminals detected[/yellow]")
        return
    
    terminal_key = subcommand.lower()
    if terminal_key not in TERMINAL_CONFIGS:
        console.print(f"[red]不支持的终端 / Unsupported terminal: {terminal_key}[/red]")
        console.print("[dim]支持的终端: " + ", ".join(TERMINAL_CONFIGS.keys()) + "[/dim]")
        return
    
    info = TERMINAL_CONFIGS[terminal_key]
    installed = _detect_terminal(terminal_key)
    
    console.print(Panel(
        f"[bold cyan]{info['name']}[/bold cyan]\n\n"
        f"[dim]安装状态 / Installed: {'[green]✓[/green]' if installed else '[yellow]✗[/yellow]'}[/dim]\n"
        f"[dim]配置目录 / Config dir: {info['config_dir']}[/dim]\n"
        f"[dim]配置文件 / Config file: {info['config_file']}[/dim]\n"
        f"[dim]官方网站 / Website: {info['website']}[/dim]\n\n"
        f"[bold]功能特性 / Features:[/bold]\n"
        + "\n".join(f"  • {f}" for f in info["features"]),
        title="终端详情 / Terminal Details",
        border_style="cyan"
    ))
    
    if not installed:
        console.print(f"\n[yellow]{info['name']} 未安装，请访问官网下载 / Not installed, visit website to download[/yellow]")
        return
    
    if Confirm.ask(f"\n配置 {info['name']} 为AloneChat首选终端？ / Set {info['name']} as preferred terminal?"):
        config_path = Path(info["config_dir"].replace("~", str(Path.home()))) / info["config_file"]
        
        alonechat_config = f"""
# AloneChat 集成配置 / AloneChat Integration
# 由 /terminal-setup 命令生成 / Generated by /terminal-setup command

# 字体设置 / Font settings
font_family = "JetBrains Mono"
font_size = 13.0

# 颜色方案 / Color scheme
# 适配AloneChat UI风格 / Adapted for AloneChat UI style
foreground = "#cdd6f4"
background = "#1e1e2e"
"""
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text(alonechat_config.strip(), encoding="utf-8")
            console.print(f"[green]✓ 已创建配置文件 / Config created: {config_path}[/green]")
        else:
            console.print(f"[dim]配置文件已存在 / Config already exists: {config_path}[/dim]")
        
        if terminal_key not in settings.get("configured_terminals", []):
            configured = settings.get("configured_terminals", [])
            configured.append(terminal_key)
            settings["configured_terminals"] = configured
        settings["preferred_terminal"] = info["name"]
        _save_settings(settings)
        
        console.print(f"[green]✓ {info['name']} 已设为首选终端 / Set as preferred terminal[/green]")
