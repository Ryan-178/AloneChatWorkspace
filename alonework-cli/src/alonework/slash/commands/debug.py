"""
/debug å½ä»¤ - ææ¥å½åä¼è¯æé / Troubleshoot current session

è®©Claudeå¸®å©è¯æ­ä¼è¯ä¸­çé®é¢ / Let Claude help diagnose session issues
çæ¬ / Version: 2.1.30
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path
import sys
import os
import json

console = Console()


def debug_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ææ¥å½åä¼è¯æé / Troubleshoot current session
    
    ç¨æ³ / Usage:
        /debug             æ¾ç¤ºå®æ´è¯æ­ä¿¡æ¯ / Show full diagnostic info
        /debug session     è¯æ­ä¼è¯é®é¢ / Diagnose session issues
        /debug config      è¯æ­éç½®é®é¢ / Diagnose config issues
        /debug network     è¯æ­ç½ç»è¿æ¥ / Diagnose network connection
        /debug all         æ¾ç¤ºææè¯æ­ä¿¡æ?/ Show all diagnostics
    
    ç¤ºä¾ / Examples:
        /debug            æ¥çè¯æ­æ¦è¦ / View diagnostic summary
        /debug session    æ¥çä¼è¯è¯æ­ / View session diagnostics
        /debug network    æ£æ¥ç½ç»è¿æ?/ Check network connectivity
    """
    import platform
    from datetime import datetime
    
    subcommand = args[0] if args else "summary"
    
    if subcommand == "summary" or subcommand == "all":
        console.print("\n[bold cyan]è°è¯è¯æ­ / Debug Diagnostics[/bold cyan]\n")
        
        diag_table = Table(show_header=True)
        diag_table.add_column("æ£æ¥é¡¹ / Check", style="cyan")
        diag_table.add_column("ç¶æ?/ Status")
        diag_table.add_column("è¯¦æ / Details")
        
        checks = []
        
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 10)
        checks.append(("Pythonçæ¬ / Python version", python_ok, python_ver))
        
        platform_info = f"{platform.system()} {platform.release()}"
        checks.append(("æä½ç³»ç» / OS", True, platform_info))
        
        alonechat_dir = Path.home() / ".alonechat"
        alonechat_ok = alonechat_dir.exists()
        checks.append(("éç½®ç®å½ / Config dir", alonechat_ok, str(alonechat_dir)))
        
        session_dir = alonechat_dir / "sessions"
        session_dir_ok = session_dir.exists()
        checks.append(("ä¼è¯ç®å½ / Session dir", session_dir_ok, str(session_dir)))
        
        if session_manager:
            session_info = session_manager.get_session_info()
            has_session = session_info["has_session"]
            msg_count = session_info["message_count"]
            checks.append(("æ´»å¨ä¼è¯ / Active session", has_session, f"{msg_count} æ¡æ¶æ?/ messages"))
        else:
            checks.append(("ä¼è¯ç®¡çå?/ Session manager", False, "ä¸å¯ç?/ Unavailable"))
        
        config_manager = obj.get("config_manager")
        if config_manager:
            config_path = config_manager.config_path
            config_ok = config_path.exists()
            checks.append(("éç½®æä»¶ / Config file", config_ok, str(config_path) if config_ok else "æªæ¾å?/ Not found"))
        else:
            checks.append(("éç½®ç®¡çå?/ Config manager", False, "ä¸å¯ç?/ Unavailable"))
        
        if subcommand == "all":
            try:
                import httpx
                response = httpx.get("https://api.deepseek.com/v1/models", timeout=5)
                api_ok = response.status_code == 200
                checks.append(("APIè¿æ¥ / API connection", api_ok, f"ç¶æç  / Status: {response.status_code}"))
            except Exception as e:
                checks.append(("APIè¿æ¥ / API connection", False, str(e)[:40]))
        
        for name, ok, details in checks:
            status = "[green]â?OK[/green]" if ok else "[red]â?å¤±è´¥[/red]"
            diag_table.add_row(name, status, details)
        
        console.print(diag_table)
        
        all_ok = all(check[1] for check in checks)
        if all_ok:
            console.print("\n[green]â?æææ£æ¥éè¿ / All checks passed[/green]")
        else:
            console.print("\n[yellow]â?é¨åæ£æ¥æªéè¿ / Some checks failed[/yellow]")
    
    if subcommand == "session":
        console.print("\n[bold cyan]ä¼è¯è¯æ­ / Session Diagnostics[/bold cyan]\n")
        
        if not session_manager:
            console.print("[yellow]ä¼è¯ç®¡çå¨ä¸å¯ç¨ / Session manager not available[/yellow]")
            return
        
        session_info = session_manager.get_session_info()
        
        info_table = Table(show_header=False)
        info_table.add_column("é¡¹ç® / Item", style="cyan")
        info_table.add_column("å?/ Value", style="green")
        
        if session_info["has_session"]:
            info_table.add_row("ä¼è¯ID / Session ID", session_info["id"])
            info_table.add_row("æ¶æ¯æ?/ Messages", str(session_info["message_count"]))
            info_table.add_row("åå»ºæ¶é´ / Created", session_info.get("created_at", "-")[:19])
            info_table.add_row("æ´æ°æ¶é´ / Updated", session_info.get("updated_at", "-")[:19])
            info_table.add_row("å·¥ä½ç®å½ / CWD", str(session_info.get("cwd", "-")))
            
            messages = session_manager.get_messages()
            if messages:
                user_msgs = sum(1 for m in messages if m.get("role") == "user")
                assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")
                total_chars = sum(len(m.get("content", "")) for m in messages)
                info_table.add_row("ç¨æ·æ¶æ¯ / User msgs", str(user_msgs))
                info_table.add_row("å©ææ¶æ¯ / Assistant msgs", str(assistant_msgs))
                info_table.add_row("æ»å­ç¬¦æ° / Total chars", f"{total_chars:,}")
                
                if session_manager.current_session:
                    session = session_manager.current_session
                    if session.parent_id:
                        info_table.add_row("ç¶ä¼è¯ID / Parent ID", session.parent_id[:12] + "...")
                    info_table.add_row("åæ¯ç?/ Branch point", str(session.branch_point))
                    info_table.add_row("å·²åç¼?/ Compressed", "æ?/ Yes" if session.compressed else "å?/ No")
        else:
            info_table.add_row("ä¼è¯ / Session", "æ æ´»å¨ä¼è¯?/ No active session")
        
        console.print(info_table)
        
        if session_info["has_session"] and session_info["message_count"] > 0:
            messages = session_manager.get_messages()
            last_msg = messages[-1]
            console.print(f"\n[bold]æåä¸æ¡æ¶æ?/ Last message:[/bold]")
            console.print(f"  [dim]è§è² / Role: {last_msg.get('role', 'unknown')}[/dim]")
            content_preview = last_msg.get("content", "")[:200]
            console.print(f"  [dim]åå®¹é¢è§ / Preview: {content_preview}...[/dim]" if len(last_msg.get("content", "")) > 200 else f"  [dim]åå®¹ / Content: {content_preview}[/dim]")
    
    if subcommand == "config":
        console.print("\n[bold cyan]éç½®è¯æ­ / Config Diagnostics[/bold cyan]\n")
        
        config_manager = obj.get("config_manager")
        if not config_manager:
            console.print("[yellow]éç½®ç®¡çå¨ä¸å¯ç¨ / Config manager not available[/yellow]")
            return
        
        config_path = config_manager.config_path
        console.print(f"[dim]éç½®æä»¶ / Config path: {config_path}[/dim]")
        
        if config_path.exists():
            try:
                config = config_manager.load_config()
                config_table = Table(show_header=True)
                config_table.add_column("é?/ Key", style="cyan")
                config_table.add_column("å?/ Value", style="green")
                
                def _add_rows(data: dict, prefix: str = ""):
                    for key, value in data.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            _add_rows(value, full_key)
                        else:
                            val_str = str(value)
                            if len(val_str) > 60:
                                val_str = val_str[:57] + "..."
                            config_table.add_row(full_key, val_str)
                
                _add_rows(config)
                console.print(config_table)
            except Exception as e:
                console.print(f"[red]éç½®æä»¶è§£æå¤±è´¥ / Config parse failed: {e}[/red]")
        else:
            console.print("[yellow]éç½®æä»¶ä¸å­å?/ Config file not found[/yellow]")
            console.print("[dim]è¯·è¿è¡?/ Please run: alonechat init[/dim]")
    
    if subcommand == "network":
        console.print("\n[bold cyan]ç½ç»è¯æ­ / Network Diagnostics[/bold cyan]\n")
        
        import httpx
        
        endpoints = [
            ("DeepSeek API", "https://api.deepseek.com/v1/models"),
            ("GitHub", "https://github.com"),
            ("PyPI", "https://pypi.org"),
        ]
        
        net_table = Table(show_header=True)
        net_table.add_column("ç®æ  / Target", style="cyan")
        net_table.add_column("ç¶æ?/ Status")
        net_table.add_column("å»¶è¿ / Latency")
        
        for name, url in endpoints:
            try:
                start = __import__("time").time()
                response = httpx.get(url, timeout=5)
                latency = (__import__("time").time() - start) * 1000
                ok = response.status_code < 500
                status = "[green]â?å¯è¾¾[/green]" if ok else f"[yellow]â?{response.status_code}[/yellow]"
                net_table.add_row(name, status, f"{latency:.0f}ms")
            except Exception as e:
                net_table.add_row(name, f"[red]â?å¤±è´¥[/red]", str(e)[:20])
        
        console.print(net_table)
        
        console.print("\n[dim]æç¤º: ç½ç»é®é¢ææ¥æ­¥éª¤ / Network troubleshooting steps:[/dim]")
        console.print("[dim]  1. æ£æ¥ç½ç»è¿æ?/ Check network connection[/dim]")
        console.print("[dim]  2. æ£æ¥ä»£çè®¾ç½?/ Check proxy settings[/dim]")
        console.print("[dim]  3. æ£æ¥APIå¯é¥ / Check API key[/dim]")
        console.print("[dim]  4. æ£æ¥é²ç«å¢ / Check firewall[/dim]")
    
    if subcommand not in ("summary", "session", "config", "network", "all"):
        console.print(f"[red]æªç¥è¯æ­é¡?/ Unknown diagnostic: {subcommand}[/red]")
        console.print("[dim]å¯ç¨éé¡¹: session, config, network, all[/dim]")
    
    console.print()
