"""
/fork 和 /branch 命令 - 分叉对话 / Fork conversation

功能 / Features:
- /fork: 从当前点创建新分支 / Create new branch from current point
- /branch: 从指定点创建新分支 / Create new branch from specified point
- 保留原会话历史 / Preserve original session history

版本 / Version: 2.1.77
"""

from rich.console import Console
from rich.table import Table

console = Console()


def fork_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    分叉当前会话 / Fork current session
    
    用法 / Usage: 
        /fork [name]              从当前点创建新分支 / Create branch from current point
        /fork --at <index> [name] 从指定消息索引创建分支 / Create branch from specified index
    
    示例 / Examples:
        /fork                     创建分支，自动命名 / Create branch with auto name
        /fork "实验性修改"         创建分支并命名 / Create named branch
        /fork --at 5              从第5条消息处创建分支 / Create branch from message 5
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return
    
    current = session_manager.current_session
    messages = current.messages
    
    branch_point = None
    display_name = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--at" and i + 1 < len(args):
            try:
                branch_point = int(args[i + 1])
                i += 2
            except ValueError:
                console.print(f"[red]无效的索引 / Invalid index: {args[i + 1]}[/red]")
                return
        elif not arg.startswith("--"):
            display_name = arg
            i += 1
        else:
            i += 1
    
    if branch_point is not None and (branch_point < 0 or branch_point > len(messages)):
        console.print(f"[red]索引超出范围 / Index out of range: {branch_point} (0-{len(messages)})[/red]")
        return
    
    forked = session_manager.fork_session(branch_point, display_name)
    
    if forked:
        console.print(f"[green]✓ 会话已分叉 / Session forked[/green]")
        console.print(f"[dim]原会话 / Original: {current.get_name()} ({len(current.messages)} 条消息)[/dim]")
        console.print(f"[dim]新分支 / New branch: {forked.get_name()} ({len(forked.messages)} 条消息)[/dim]")
        console.print(f"[dim]父会话ID / Parent ID: {forked.parent_id}[/dim]")
    else:
        console.print("[red]分叉失败 / Fork failed[/red]")


def branch_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理会话分支 / Manage session branches
    
    用法 / Usage:
        /branch                   列出所有分支 / List all branches
        /branch new [name]        创建新分支 / Create new branch
        /branch switch <id>       切换到分支 / Switch to branch
        /branch delete <id>       删除分支 / Delete branch
    
    示例 / Examples:
        /branch                   列出分支 / List branches
        /branch new "修复方案A"   创建命名分支 / Create named branch
        /branch switch abc123     切换到分支 / Switch to branch
    """
    if not session_manager:
        console.print("[yellow]无会话管理器 / No session manager[/yellow]")
        return
    
    subcommand = args[0] if args else "list"
    
    if subcommand == "list":
        _list_branches(session_manager)
    elif subcommand == "new":
        name = args[1] if len(args) > 1 else None
        fork_command([name] if name else [], obj, session_manager, registry, **kwargs)
    elif subcommand == "switch":
        if len(args) < 2:
            console.print("[red]请指定会话ID / Please specify session ID[/red]")
            return
        session_id = args[1]
        session = session_manager.resume_session(session_id)
        if session:
            console.print(f"[green]✓ 已切换到会话 / Switched to session: {session.get_name()}[/green]")
        else:
            console.print(f"[red]未找到会话 / Session not found: {session_id}[/red]")
    elif subcommand == "delete":
        if len(args) < 2:
            console.print("[red]请指定会话ID / Please specify session ID[/red]")
            return
        session_id = args[1]
        if session_manager.delete_session(session_id):
            console.print(f"[green]✓ 已删除会话 / Session deleted: {session_id}[/green]")
        else:
            console.print(f"[red]删除失败 / Delete failed: {session_id}[/red]")
    else:
        console.print(f"[red]未知子命令 / Unknown subcommand: {subcommand}[/red]")
        console.print("[dim]可用子命令: list, new, switch, delete[/dim]")


def _list_branches(session_manager) -> None:
    """列出所有分支 / List all branches"""
    sessions = session_manager.list_sessions(limit=50)
    
    if not sessions:
        console.print("[yellow]暂无会话 / No sessions[/yellow]")
        return
    
    current_id = session_manager.current_session.id if session_manager.current_session else None
    
    table = Table(title="会话分支 / Session Branches")
    table.add_column("当前", style="cyan", width=4)
    table.add_column("名称", style="green")
    table.add_column("ID", style="dim")
    table.add_column("消息数", justify="right")
    table.add_column("父会话", style="dim")
    table.add_column("更新时间", style="dim")
    
    for session in sessions:
        is_current = "✓" if session.id == current_id else ""
        parent = session.parent_id[:8] if session.parent_id else "-"
        table.add_row(
            is_current,
            session.get_name(),
            session.id[:8],
            str(len(session.messages)),
            parent,
            session.updated_at[:16] if session.updated_at else "-",
        )
    
    console.print(table)
