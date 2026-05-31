"""
/rename 命令 - 重命名当前会话 / Rename current session

版本 / Version: 2.1.80
"""

from rich.console import Console

console = Console()


def rename_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    重命名当前会话 / Rename current session

    用法 / Usage:
        /rename                 交互式重命名 / Interactive rename
        /rename <new_name>      设置新名称 / Set new name
        /rename --reset         重置为默认名称 / Reset to default name

    示例 / Examples:
        /rename 我的项目会话
        /rename My Project Session
        /rename --reset
    """
    if not session_manager:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return

    session = session_manager.current_session
    if not session:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return

    current_name = session.get_name() if hasattr(session, "get_name") else getattr(session, "display_name", "unnamed")

    if not args:
        console.print(f"[cyan]当前会话名称 / Current session name:[/cyan] {current_name}")
        console.print(f"[dim]会话ID / Session ID: {session.id}[/dim]")
        console.print("[dim]用法 / Usage: /rename <新名称 / new name>[/dim]")
        return

    if args[0] == "--reset":
        if hasattr(session, "display_name"):
            session.display_name = None
        console.print("[green]✓ 会话名称已重置 / Session name reset[/green]")
        return

    new_name = " ".join(args)

    if hasattr(session, "display_name"):
        session.display_name = new_name
    elif hasattr(session, "set_name"):
        session.set_name(new_name)

    console.print(f"[green]✓ 会话已重命名 / Session renamed[/green]")
    console.print(f"[dim]旧名称 / Old: {current_name}[/dim]")
    console.print(f"[dim]新名称 / New: {new_name}[/dim]")
