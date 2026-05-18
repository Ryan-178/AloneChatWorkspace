"""
/debug 命令 - 排查当前会话故障 / Troubleshoot current session

让Claude帮助诊断会话中的问题 / Let Claude help diagnose session issues
版本 / Version: 2.1.30
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
    排查当前会话故障 / Troubleshoot current session
    
    用法 / Usage:
        /debug             显示完整诊断信息 / Show full diagnostic info
        /debug session     诊断会话问题 / Diagnose session issues
        /debug config      诊断配置问题 / Diagnose config issues
        /debug network     诊断网络连接 / Diagnose network connection
        /debug all         显示所有诊断信息 / Show all diagnostics
    
    示例 / Examples:
        /debug            查看诊断概要 / View diagnostic summary
        /debug session    查看会话诊断 / View session diagnostics
        /debug network    检查网络连接 / Check network connectivity
    """
    import platform
    from datetime import datetime
    
    subcommand = args[0] if args else "summary"
    
    if subcommand == "summary" or subcommand == "all":
        console.print("\n[bold cyan]调试诊断 / Debug Diagnostics[/bold cyan]\n")
        
        diag_table = Table(show_header=True)
        diag_table.add_column("检查项 / Check", style="cyan")
        diag_table.add_column("状态 / Status")
        diag_table.add_column("详情 / Details")
        
        checks = []
        
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_ok = sys.version_info >= (3, 10)
        checks.append(("Python版本 / Python version", python_ok, python_ver))
        
        platform_info = f"{platform.system()} {platform.release()}"
        checks.append(("操作系统 / OS", True, platform_info))
        
        alonechat_dir = Path.home() / ".alonechat"
        alonechat_ok = alonechat_dir.exists()
        checks.append(("配置目录 / Config dir", alonechat_ok, str(alonechat_dir)))
        
        session_dir = alonechat_dir / "sessions"
        session_dir_ok = session_dir.exists()
        checks.append(("会话目录 / Session dir", session_dir_ok, str(session_dir)))
        
        if session_manager:
            session_info = session_manager.get_session_info()
            has_session = session_info["has_session"]
            msg_count = session_info["message_count"]
            checks.append(("活动会话 / Active session", has_session, f"{msg_count} 条消息 / messages"))
        else:
            checks.append(("会话管理器 / Session manager", False, "不可用 / Unavailable"))
        
        config_manager = obj.get("config_manager")
        if config_manager:
            config_path = config_manager.config_path
            config_ok = config_path.exists()
            checks.append(("配置文件 / Config file", config_ok, str(config_path) if config_ok else "未找到 / Not found"))
        else:
            checks.append(("配置管理器 / Config manager", False, "不可用 / Unavailable"))
        
        if subcommand == "all":
            try:
                import httpx
                response = httpx.get("https://api.deepseek.com/v1/models", timeout=5)
                api_ok = response.status_code == 200
                checks.append(("API连接 / API connection", api_ok, f"状态码 / Status: {response.status_code}"))
            except Exception as e:
                checks.append(("API连接 / API connection", False, str(e)[:40]))
        
        for name, ok, details in checks:
            status = "[green]✓ OK[/green]" if ok else "[red]✗ 失败[/red]"
            diag_table.add_row(name, status, details)
        
        console.print(diag_table)
        
        all_ok = all(check[1] for check in checks)
        if all_ok:
            console.print("\n[green]✓ 所有检查通过 / All checks passed[/green]")
        else:
            console.print("\n[yellow]⚠ 部分检查未通过 / Some checks failed[/yellow]")
    
    if subcommand == "session":
        console.print("\n[bold cyan]会话诊断 / Session Diagnostics[/bold cyan]\n")
        
        if not session_manager:
            console.print("[yellow]会话管理器不可用 / Session manager not available[/yellow]")
            return
        
        session_info = session_manager.get_session_info()
        
        info_table = Table(show_header=False)
        info_table.add_column("项目 / Item", style="cyan")
        info_table.add_column("值 / Value", style="green")
        
        if session_info["has_session"]:
            info_table.add_row("会话ID / Session ID", session_info["id"])
            info_table.add_row("消息数 / Messages", str(session_info["message_count"]))
            info_table.add_row("创建时间 / Created", session_info.get("created_at", "-")[:19])
            info_table.add_row("更新时间 / Updated", session_info.get("updated_at", "-")[:19])
            info_table.add_row("工作目录 / CWD", str(session_info.get("cwd", "-")))
            
            messages = session_manager.get_messages()
            if messages:
                user_msgs = sum(1 for m in messages if m.get("role") == "user")
                assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")
                total_chars = sum(len(m.get("content", "")) for m in messages)
                info_table.add_row("用户消息 / User msgs", str(user_msgs))
                info_table.add_row("助手消息 / Assistant msgs", str(assistant_msgs))
                info_table.add_row("总字符数 / Total chars", f"{total_chars:,}")
                
                if session_manager.current_session:
                    session = session_manager.current_session
                    if session.parent_id:
                        info_table.add_row("父会话ID / Parent ID", session.parent_id[:12] + "...")
                    info_table.add_row("分支点 / Branch point", str(session.branch_point))
                    info_table.add_row("已压缩 / Compressed", "是 / Yes" if session.compressed else "否 / No")
        else:
            info_table.add_row("会话 / Session", "无活动会话 / No active session")
        
        console.print(info_table)
        
        if session_info["has_session"] and session_info["message_count"] > 0:
            messages = session_manager.get_messages()
            last_msg = messages[-1]
            console.print(f"\n[bold]最后一条消息 / Last message:[/bold]")
            console.print(f"  [dim]角色 / Role: {last_msg.get('role', 'unknown')}[/dim]")
            content_preview = last_msg.get("content", "")[:200]
            console.print(f"  [dim]内容预览 / Preview: {content_preview}...[/dim]" if len(last_msg.get("content", "")) > 200 else f"  [dim]内容 / Content: {content_preview}[/dim]")
    
    if subcommand == "config":
        console.print("\n[bold cyan]配置诊断 / Config Diagnostics[/bold cyan]\n")
        
        config_manager = obj.get("config_manager")
        if not config_manager:
            console.print("[yellow]配置管理器不可用 / Config manager not available[/yellow]")
            return
        
        config_path = config_manager.config_path
        console.print(f"[dim]配置文件 / Config path: {config_path}[/dim]")
        
        if config_path.exists():
            try:
                config = config_manager.load_config()
                config_table = Table(show_header=True)
                config_table.add_column("键 / Key", style="cyan")
                config_table.add_column("值 / Value", style="green")
                
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
                console.print(f"[red]配置文件解析失败 / Config parse failed: {e}[/red]")
        else:
            console.print("[yellow]配置文件不存在 / Config file not found[/yellow]")
            console.print("[dim]请运行 / Please run: alonechat init[/dim]")
    
    if subcommand == "network":
        console.print("\n[bold cyan]网络诊断 / Network Diagnostics[/bold cyan]\n")
        
        import httpx
        
        endpoints = [
            ("DeepSeek API", "https://api.deepseek.com/v1/models"),
            ("GitHub", "https://github.com"),
            ("PyPI", "https://pypi.org"),
        ]
        
        net_table = Table(show_header=True)
        net_table.add_column("目标 / Target", style="cyan")
        net_table.add_column("状态 / Status")
        net_table.add_column("延迟 / Latency")
        
        for name, url in endpoints:
            try:
                start = __import__("time").time()
                response = httpx.get(url, timeout=5)
                latency = (__import__("time").time() - start) * 1000
                ok = response.status_code < 500
                status = "[green]✓ 可达[/green]" if ok else f"[yellow]⚠ {response.status_code}[/yellow]"
                net_table.add_row(name, status, f"{latency:.0f}ms")
            except Exception as e:
                net_table.add_row(name, f"[red]✗ 失败[/red]", str(e)[:20])
        
        console.print(net_table)
        
        console.print("\n[dim]提示: 网络问题排查步骤 / Network troubleshooting steps:[/dim]")
        console.print("[dim]  1. 检查网络连接 / Check network connection[/dim]")
        console.print("[dim]  2. 检查代理设置 / Check proxy settings[/dim]")
        console.print("[dim]  3. 检查API密钥 / Check API key[/dim]")
        console.print("[dim]  4. 检查防火墙 / Check firewall[/dim]")
    
    if subcommand not in ("summary", "session", "config", "network", "all"):
        console.print(f"[red]未知诊断项 / Unknown diagnostic: {subcommand}[/red]")
        console.print("[dim]可用选项: session, config, network, all[/dim]")
    
    console.print()
