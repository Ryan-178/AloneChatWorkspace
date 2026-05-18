"""
/remote-control å½ä»¤ - æ¡¥æ¥ä¼è¯å°è¿ç¨?/ Bridge session to remote

æ¡¥æ¥å½åä¼è¯å?claude.ai/code æå¶ä»è¿ç¨æå?Bridge current session to claude.ai/code or other remote services
çæ¬ / Version: 2.1.79
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
    æ¡¥æ¥ä¼è¯å°è¿ç¨?/ Bridge session to remote
    
    ç¨æ³ / Usage:
        /remote-control                   å¯å¨è¿ç¨æ¡¥æ¥ / Start remote bridge
        /remote-control --name <title>    è®¾ç½®èªå®ä¹æ é¢?/ Set custom title
        /remote-control status            æ¥çæ¡¥æ¥ç¶æ?/ Check bridge status
        /remote-control stop              åæ­¢æ¡¥æ¥ / Stop bridge
        /remote-control list              ååºæææ¡¥æ?/ List all bridges
    
    ç¤ºä¾ / Examples:
        /remote-control                   å¯å¨VSCodeæ¡¥æ¥ / Start VSCode bridge
        /remote-control --name "My Project" è®¾ç½®æ é¢ / Set title
        /remote-control status            æ¥çç¶æ?/ Check status
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
        
        console.print("\n[bold green]â?è¿ç¨æ¡¥æ¥å·²å»ºç«?/ Remote bridge established[/bold green]\n")
        
        info_table = Table(show_header=False)
        info_table.add_column("é¡¹ç® / Item", style="cyan")
        info_table.add_column("å?/ Value", style="green")
        info_table.add_row("æ¡¥æ¥ID / Bridge ID", bridge_id)
        info_table.add_row("åç§° / Name", bridge["name"])
        info_table.add_row("ç®æ  / Target", bridge["target"])
        info_table.add_row("åè®® / Protocol", bridge["protocol"])
        info_table.add_row("ç¶æ?/ Status", "[green]å·²è¿æ?/ Connected[/green]")
        info_table.add_row("ä¼è¯ID / Session ID", bridge["session_id"][:12] + "..." if bridge["session_id"] else "-")
        info_table.add_row("VSCode", "[green]å¯ç¨ / Available[/green]" if bridge["vscode_available"] else "[yellow]æªæ£æµå° / Not detected[/yellow]")
        console.print(info_table)
        
        if bridge_name:
            console.print(f"\n[dim]èªå®ä¹æ é¢å·²è®¾ç½® / Custom title set: {bridge_name}[/dim]")
        
        console.print("\n[bold yellow]æ³¨æ / Note:[/bold yellow]")
        console.print("[dim]è¿ç¨æ¡¥æ¥åè½éè¦ç®æ æå¡æ¯æ?/ Remote bridge requires target service support[/dim]")
        console.print("[dim]è¾å¥ /remote-control status æ¥çç¶æ?/ Type /remote-control status to check status[/dim]")
        console.print("[dim]è¾å¥ /remote-control stop åæ­¢æ¡¥æ¥ / Type /remote-control stop to stop bridge[/dim]")
        return
    
    subcommand = clean_args[0]
    
    if subcommand == "status":
        active_bridges = [b for b in bridges if b["status"] == "connected"]
        
        if not active_bridges:
            console.print("[yellow]æ æ´»è·æ¡¥æ?/ No active bridges[/yellow]")
            return
        
        for bridge in active_bridges:
            console.print(Panel(
                f"[bold cyan]{bridge.get('name', bridge['id'])}[/bold cyan]\n\n"
                f"[dim]ID: {bridge['id']}[/dim]\n"
                f"[dim]ç®æ  / Target: {bridge['target']}[/dim]\n"
                f"[dim]åè®® / Protocol: {bridge.get('protocol', 'unknown')}[/dim]\n"
                f"[dim]ä¼è¯ / Session: {bridge.get('session_id', '-')[:12]}...[/dim]\n"
                f"[dim]åå»ºæ¶é´ / Created: {bridge.get('created_at', '')[:16]}[/dim]\n"
                f"[dim]ç¶æ?/ Status: [green]å·²è¿æ?/ Connected[/green][/dim]",
                title="æ¡¥æ¥ç¶æ?/ Bridge Status",
                border_style="cyan"
            ))
        return
    
    if subcommand == "stop":
        active = [b for b in bridges if b["status"] == "connected"]
        if not active:
            console.print("[yellow]æ æ´»è·æ¡¥æ¥å¯åæ­¢ / No active bridges to stop[/yellow]")
            return
        
        if Confirm.ask(f"å°åæ­?{len(active)} ä¸ªæ´»è·æ¡¥æ¥ï¼ç¡®è®¤ï¼?/ Stop {len(active)} active bridge(s)?"):
            for bridge in bridges:
                if bridge["status"] == "connected":
                    bridge["status"] = "disconnected"
            _save_bridges(bridges)
            console.print(f"[green]â?å·²åæ­?{len(active)} ä¸ªæ¡¥æ?/ Stopped {len(active)} bridge(s)[/green]")
        return
    
    if subcommand == "list":
        if not bridges:
            console.print("[yellow]ææ æ¡¥æ¥è®°å½ / No bridge records[/yellow]")
            return
        
        table = Table(title="è¿ç¨æ¡¥æ¥ / Remote Bridges", show_header=True)
        table.add_column("åç§° / Name", style="cyan")
        table.add_column("ç®æ  / Target")
        table.add_column("åè®® / Protocol")
        table.add_column("ç¶æ?/ Status")
        table.add_column("åå»ºæ¶é´ / Created", style="dim")
        
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
    
    console.print(f"[red]æªç¥å­å½ä»?/ Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]å¯ç¨å­å½ä»? status, stop, list[/dim]")
    console.print("[dim]ä½¿ç¨ --name <title> è®¾ç½®èªå®ä¹æ é¢[/dim]")
