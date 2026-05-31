"""
/resume 命令 - 恢复之前的会话 / Resume previous session

版本 / Version: 2.1.80
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()


def resume_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    恢复之前的会话 / Resume previous session

    用法 / Usage:
        /resume                 交互式选择会话 / Interactive session picker
        /resume <session_id>    恢复指定会话 / Resume specific session
        /resume <title>         按标题恢复 / Resume by title
        /resume last            恢复最近会话 / Resume last session
        /resume list            列出可恢复的会话 / List resumable sessions

    示例 / Examples:
        /resume
        /resume abc123
        /resume last
    """
    if not session_manager:
        console.print("[yellow]会话管理器不可用 / Session manager not available[/yellow]")
        return

    if not args or args[0] == "list":
        sessions = session_manager.list_sessions(limit=20) if hasattr(session_manager, "list_sessions") else []

        if not sessions:
            console.print("[dim]没有可恢复的会话 / No resumable sessions[/dim]")
            return

        table = Table(show_header=True, title="可恢复的会话 / Resumable Sessions")
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan", max_width=12)
        table.add_column("名称 / Name", style="green")
        table.add_column("消息数 / Msgs", style="yellow")
        table.add_column("时间 / Time", style="dim")

        for i, session in enumerate(sessions, 1):
            sid = session.id[:12] + "..." if len(session.id) > 12 else session.id
            name = session.get_name() if hasattr(session, "get_name") else getattr(session, "display_name", "-")
            msg_count = len(session.messages) if hasattr(session, "messages") else "-"
            created = session.created_at[:16] if hasattr(session, "created_at") and session.created_at else "-"
            table.add_row(str(i), sid, name, str(msg_count), created)

        console.print(table)
        console.print("[dim]使用 /resume <ID> 或 /resume <#> 恢复会话 / Use /resume <ID> or /resume <#> to resume[/dim]")
        return

    if args[0] == "last":
        session = session_manager.continue_session() if hasattr(session_manager, "continue_session") else None
        if session:
            name = session.get_name() if hasattr(session, "get_name") else session.id
            console.print(f"[green]✓ 已恢复会话 / Session resumed: {name}[/green]")
        else:
            console.print("[yellow]没有可恢复的会话 / No session to resume[/yellow]")
        return

    target = args[0]

    if target.isdigit():
        sessions = session_manager.list_sessions(limit=20) if hasattr(session_manager, "list_sessions") else []
        idx = int(target) - 1
        if 0 <= idx < len(sessions):
            target = sessions[idx].id
        else:
            console.print(f"[red]无效序号 / Invalid index: {target}[/red]")
            return

    session = session_manager.resume_session(target) if hasattr(session_manager, "resume_session") else None
    if session:
        name = session.get_name() if hasattr(session, "get_name") else session.id
        console.print(f"[green]✓ 已恢复会话 / Session resumed: {name}[/green]")
    else:
        sessions = session_manager.list_sessions(limit=20) if hasattr(session_manager, "list_sessions") else []
        matches = [s for s in sessions if target.lower() in (s.get_name() if hasattr(s, "get_name") else "").lower()]
        if matches:
            session = session_manager.resume_session(matches[0].id) if hasattr(session_manager, "resume_session") else None
            if session:
                name = session.get_name() if hasattr(session, "get_name") else session.id
                console.print(f"[green]✓ 已恢复会话 / Session resumed: {name}[/green]")
                return
        console.print(f"[red]未找到会话 / Session not found: {target}[/red]")
