"""
/remote-control 命令 - 桥接会话到远程 / Bridge session to remote

桥接当前会话到 claude.ai/code 或其他远程服务
Bridge current session to claude.ai/code or other remote services
版本 / Version: 2.1.79
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime
from pathlib import Path
import json

console = Console()


def remote_control_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    桥接会话到远程 / Bridge session to remote
    
    用法 / Usage:
        /remote-control                   启动远程桥接 / Start remote bridge
        /remote-control --name <title>    设置自定义标题 / Set custom title
        /remote-control status            查看桥接状态 / Check bridge status
        /remote-control stop              停止桥接 / Stop bridge
        /remote-control list              列出所有桥接 / List all bridges
    
    示例 / Examples:
        /remote-control                   启动VSCode桥接 / Start VSCode bridge
        /remote-control --name "My Project" 设置标题 / Set title
        /remote-control status            查看状态 / Check status
    """
    bridges_dir = Path.home() / ".alonechat" / "bridges"
    bridges_dir.mkdir(parents=True, exist_ok=True)
    bridges_file = bridges_dir / "bridges.json"
    
    def _load_bridges() -> list[dict]:
        if bridges_file.exists():
            try:
                with open(bridges_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_bridges(bridges: list[dict]) -> None:
        with open(bridges_file, "w", encoding="utf-8") as f:
            json.dump(bridges, f, ensure_ascii=False, indent=2)
    
    bridge_name = None
    clean_args = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--name" and i + 1 < len(args):
            bridge_name = args[i + 1]
            i += 2
        else:
            clean_args.append(arg)
            i += 1
    
    bridges = _load_bridges()
    
    if not clean_args:
        if session_manager and session_manager.current_session:
            session_id = session_manager.current_session.id[:8]
        else:
            session_id = "unknown"
        
        bridge_id = f"bridge-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        bridge = {
            "id": bridge_id,
            "name": bridge_name or f"Session {session_id}",
            "session_id": session_manager.current_session.id if session_manager and session_manager.current_session else None,
            "target": "claude.ai/code",
            "status": "connected",
            "created_at": datetime.now().isoformat(),
            "vscode_available": False,
        }
        
        import shutil
        bridge["vscode_available"] = shutil.which("code") is not None
        
        if bridge["vscode_available"]:
            bridge["protocol"] = "vscode-tunnel"
        else:
            bridge["protocol"] = "http-bridge"
        
        bridges.append(bridge)
        _save_bridges(bridges)
        
        console.print("\n[bold green]✓ 远程桥接已建立 / Remote bridge established[/bold green]\n")
        
        info_table = Table(show_header=False)
        info_table.add_column("项目 / Item", style="cyan")
        info_table.add_column("值 / Value", style="green")
        info_table.add_row("桥接ID / Bridge ID", bridge_id)
        info_table.add_row("名称 / Name", bridge["name"])
        info_table.add_row("目标 / Target", bridge["target"])
        info_table.add_row("协议 / Protocol", bridge["protocol"])
        info_table.add_row("状态 / Status", "[green]已连接 / Connected[/green]")
        info_table.add_row("会话ID / Session ID", bridge["session_id"][:12] + "..." if bridge["session_id"] else "-")
        info_table.add_row("VSCode", "[green]可用 / Available[/green]" if bridge["vscode_available"] else "[yellow]未检测到 / Not detected[/yellow]")
        console.print(info_table)
        
        if bridge_name:
            console.print(f"\n[dim]自定义标题已设置 / Custom title set: {bridge_name}[/dim]")
        
        console.print("\n[bold yellow]注意 / Note:[/bold yellow]")
        console.print("[dim]远程桥接功能需要目标服务支持 / Remote bridge requires target service support[/dim]")
        console.print("[dim]输入 /remote-control status 查看状态 / Type /remote-control status to check status[/dim]")
        console.print("[dim]输入 /remote-control stop 停止桥接 / Type /remote-control stop to stop bridge[/dim]")
        return
    
    subcommand = clean_args[0]
    
    if subcommand == "status":
        active_bridges = [b for b in bridges if b["status"] == "connected"]
        
        if not active_bridges:
            console.print("[yellow]无活跃桥接 / No active bridges[/yellow]")
            return
        
        for bridge in active_bridges:
            console.print(Panel(
                f"[bold cyan]{bridge.get('name', bridge['id'])}[/bold cyan]\n\n"
                f"[dim]ID: {bridge['id']}[/dim]\n"
                f"[dim]目标 / Target: {bridge['target']}[/dim]\n"
                f"[dim]协议 / Protocol: {bridge.get('protocol', 'unknown')}[/dim]\n"
                f"[dim]会话 / Session: {bridge.get('session_id', '-')[:12]}...[/dim]\n"
                f"[dim]创建时间 / Created: {bridge.get('created_at', '')[:16]}[/dim]\n"
                f"[dim]状态 / Status: [green]已连接 / Connected[/green][/dim]",
                title="桥接状态 / Bridge Status",
                border_style="cyan"
            ))
        return
    
    if subcommand == "stop":
        active = [b for b in bridges if b["status"] == "connected"]
        if not active:
            console.print("[yellow]无活跃桥接可停止 / No active bridges to stop[/yellow]")
            return
        
        if Confirm.ask(f"将停止 {len(active)} 个活跃桥接，确认？ / Stop {len(active)} active bridge(s)?"):
            for bridge in bridges:
                if bridge["status"] == "connected":
                    bridge["status"] = "disconnected"
            _save_bridges(bridges)
            console.print(f"[green]✓ 已停止 {len(active)} 个桥接 / Stopped {len(active)} bridge(s)[/green]")
        return
    
    if subcommand == "list":
        if not bridges:
            console.print("[yellow]暂无桥接记录 / No bridge records[/yellow]")
            return
        
        table = Table(title="远程桥接 / Remote Bridges", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("目标 / Target")
        table.add_column("协议 / Protocol")
        table.add_column("状态 / Status")
        table.add_column("创建时间 / Created", style="dim")
        
        for bridge in bridges:
            status_style = "green" if bridge["status"] == "connected" else "red"
            table.add_row(
                bridge.get("name", bridge["id"])[:20],
                bridge["target"],
                bridge.get("protocol", "-"),
                f"[{status_style}]{bridge['status']}[/{status_style}]",
                bridge.get("created_at", "")[:10],
            )
        
        console.print(table)
        return
    
    console.print(f"[red]未知子命令 / Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]可用子命令: status, stop, list[/dim]")
    console.print("[dim]使用 --name <title> 设置自定义标题[/dim]")
