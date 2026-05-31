"""
/session 命令 - 会话管理 / Session management

版本 / Version: 2.1.80
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def session_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    会话管理 / Session management

    用法 / Usage:
        /session                显示当前会话信息 / Show current session info
        /session list           列出所有会话 / List all sessions
        /session info           当前会话详情 / Current session details
        /session delete <id>    删除会话 / Delete session
        /session export         导出当前会话 / Export current session
        /session clean          清理旧会话 / Clean old sessions
        /session storage        存储统计 / Storage statistics
    """
    if not session_manager:
        console.print("[yellow]会话管理器不可用 / Session manager not available[/yellow]")
        return

    if not args or args[0] == "info":
        session = session_manager.current_session
        if not session:
            console.print("[dim]无活动会话 / No active session[/dim]")
            return

        messages = session_manager.get_messages()
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        name = session.get_name() if hasattr(session, "get_name") else getattr(session, "display_name", "-")
        total_chars = sum(len(m.get("content", "")) for m in messages)

        info_text = (
            f"[bold]会话信息 / Session Info[/bold]\n\n"
            f"名称 / Name: {name}\n"
            f"ID: {session.id}\n"
            f"消息总数 / Total messages: {len(messages)}\n"
            f"用户消息 / User messages: {len(user_msgs)}\n"
            f"助手消息 / Assistant messages: {len(assistant_msgs)}\n"
            f"总字符数 / Total chars: {total_chars:,}\n"
        )
        if hasattr(session, "created_at") and session.created_at:
            info_text += f"创建时间 / Created: {session.created_at}\n"
        if hasattr(session, "updated_at") and session.updated_at:
            info_text += f"更新时间 / Updated: {session.updated_at}\n"
        if hasattr(session, "parent_id") and session.parent_id:
            info_text += f"父会话 / Parent: {session.parent_id}\n"

        console.print(Panel(info_text, border_style="cyan"))
        return

    action = args[0]

    if action == "list":
        sessions = session_manager.list_sessions(limit=30) if hasattr(session_manager, "list_sessions") else []
        if not sessions:
            console.print("[dim]没有会话 / No sessions[/dim]")
            return

        table = Table(show_header=True, title="会话列表 / Session List")
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan", max_width=12)
        table.add_column("名称 / Name", style="green")
        table.add_column("消息数 / Msgs", style="yellow")
        table.add_column("创建时间 / Created", style="dim")

        for i, session in enumerate(sessions, 1):
            sid = session.id[:12] + "..." if len(session.id) > 12 else session.id
            name = session.get_name() if hasattr(session, "get_name") else getattr(session, "display_name", "-")
            msg_count = len(session.messages) if hasattr(session, "messages") else "-"
            created = session.created_at[:16] if hasattr(session, "created_at") and session.created_at else "-"
            is_current = " *" if session_manager.current_session and session.id == session_manager.current_session.id else ""
            table.add_row(str(i), sid, f"{name}{is_current}", str(msg_count), created)

        console.print(table)
        console.print("[dim]* 当前活动会话 / Current active session[/dim]")
        return

    if action == "delete":
        if len(args) < 2:
            console.print("[red]请指定会话ID / Please specify session ID[/red]")
            return
        target = args[1]
        if hasattr(session_manager, "delete_session"):
            result = session_manager.delete_session(target)
            if result:
                console.print(f"[green]✓ 会话已删除 / Session deleted: {target}[/green]")
            else:
                console.print(f"[red]删除失败 / Delete failed: {target}[/red]")
        else:
            console.print("[yellow]删除功能不可用 / Delete not available[/yellow]")
        return

    if action == "export":
        from alonechat.slash.commands.export import export_command
        export_command([], obj, session_manager, registry)
        return

    if action == "clean":
        sessions = session_manager.list_sessions(limit=100) if hasattr(session_manager, "list_sessions") else []
        console.print(f"[cyan]找到 {len(sessions)} 个会话 / Found {len(sessions)} sessions[/cyan]")
        console.print("[dim]清理功能暂未实现 / Clean feature not yet implemented[/dim]")
        return

    if action == "storage":
        sessions = session_manager.list_sessions(limit=1000) if hasattr(session_manager, "list_sessions") else []
        total_messages = sum(len(s.messages) if hasattr(s, "messages") else 0 for s in sessions)
        total_chars = 0
        for s in sessions:
            if hasattr(s, "messages"):
                total_chars += sum(len(m.get("content", "")) for m in s.messages)

        session_dir = Path.cwd() / ".alonechat" / "sessions"
        disk_usage = 0
        if session_dir.exists():
            for f in session_dir.rglob("*"):
                if f.is_file():
                    disk_usage += f.stat().st_size

        console.print(Panel(
            f"[bold]存储统计 / Storage Stats[/bold]\n\n"
            f"会话数 / Sessions: {len(sessions)}\n"
            f"消息总数 / Total messages: {total_messages}\n"
            f"总字符数 / Total chars: {total_chars:,}\n"
            f"磁盘占用 / Disk usage: {disk_usage / 1024:.1f} KB\n"
            f"存储路径 / Storage path: {session_dir}",
            border_style="cyan",
        ))
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: info, list, delete, export, clean, storage[/dim]")
