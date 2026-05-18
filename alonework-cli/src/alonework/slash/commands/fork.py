"""
/fork å?/branch å½ä»¤ - ååå¯¹è¯ / Fork conversation

åè½ / Features:
- /fork: ä»å½åç¹åå»ºæ°åæ?/ Create new branch from current point
- /branch: ä»æå®ç¹åå»ºæ°åæ?/ Create new branch from specified point
- ä¿çåä¼è¯åå?/ Preserve original session history

çæ¬ / Version: 2.1.77
"""

from rich.console import Console
from rich.table import Table

console = Console()


def fork_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ååå½åä¼è¯ / Fork current session
    
    ç¨æ³ / Usage: 
        /fork [name]              ä»å½åç¹åå»ºæ°åæ?/ Create branch from current point
        /fork --at <index> [name] ä»æå®æ¶æ¯ç´¢å¼åå»ºåæ?/ Create branch from specified index
    
    ç¤ºä¾ / Examples:
        /fork                     åå»ºåæ¯ï¼èªå¨å½å?/ Create branch with auto name
        /fork "å®éªæ§ä¿®æ?         åå»ºåæ¯å¹¶å½å?/ Create named branch
        /fork --at 5              ä»ç¬¬5æ¡æ¶æ¯å¤åå»ºåæ¯ / Create branch from message 5
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")
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
                console.print(f"[red]æ æçç´¢å¼?/ Invalid index: {args[i + 1]}[/red]")
                return
        elif not arg.startswith("--"):
            display_name = arg
            i += 1
        else:
            i += 1
    
    if branch_point is not None and (branch_point < 0 or branch_point > len(messages)):
        console.print(f"[red]ç´¢å¼è¶åºèå´ / Index out of range: {branch_point} (0-{len(messages)})[/red]")
        return
    
    forked = session_manager.fork_session(branch_point, display_name)
    
    if forked:
        console.print(f"[green]â?ä¼è¯å·²åå?/ Session forked[/green]")
        console.print(f"[dim]åä¼è¯?/ Original: {current.get_name()} ({len(current.messages)} æ¡æ¶æ?[/dim]")
        console.print(f"[dim]æ°åæ?/ New branch: {forked.get_name()} ({len(forked.messages)} æ¡æ¶æ?[/dim]")
        console.print(f"[dim]ç¶ä¼è¯ID / Parent ID: {forked.parent_id}[/dim]")
    else:
        console.print("[red]ååå¤±è´¥ / Fork failed[/red]")


def branch_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ç®¡çä¼è¯åæ¯ / Manage session branches
    
    ç¨æ³ / Usage:
        /branch                   ååºææåæ?/ List all branches
        /branch new [name]        åå»ºæ°åæ?/ Create new branch
        /branch switch <id>       åæ¢å°åæ?/ Switch to branch
        /branch delete <id>       å é¤åæ¯ / Delete branch
    
    ç¤ºä¾ / Examples:
        /branch                   ååºåæ¯ / List branches
        /branch new "ä¿®å¤æ¹æ¡A"   åå»ºå½ååæ¯ / Create named branch
        /branch switch abc123     åæ¢å°åæ?/ Switch to branch
    """
    if not session_manager:
        console.print("[yellow]æ ä¼è¯ç®¡çå¨ / No session manager[/yellow]")
        return
    
    subcommand = args[0] if args else "list"
    
    if subcommand == "list":
        _list_branches(session_manager)
    elif subcommand == "new":
        name = args[1] if len(args) > 1 else None
        fork_command([name] if name else [], obj, session_manager, registry, **kwargs)
    elif subcommand == "switch":
        if len(args) < 2:
            console.print("[red]è¯·æå®ä¼è¯ID / Please specify session ID[/red]")
            return
        session_id = args[1]
        session = session_manager.resume_session(session_id)
        if session:
            console.print(f"[green]â?å·²åæ¢å°ä¼è¯ / Switched to session: {session.get_name()}[/green]")
        else:
            console.print(f"[red]æªæ¾å°ä¼è¯?/ Session not found: {session_id}[/red]")
    elif subcommand == "delete":
        if len(args) < 2:
            console.print("[red]è¯·æå®ä¼è¯ID / Please specify session ID[/red]")
            return
        session_id = args[1]
        if session_manager.delete_session(session_id):
            console.print(f"[green]â?å·²å é¤ä¼è¯?/ Session deleted: {session_id}[/green]")
        else:
            console.print(f"[red]å é¤å¤±è´¥ / Delete failed: {session_id}[/red]")
    else:
        console.print(f"[red]æªç¥å­å½ä»?/ Unknown subcommand: {subcommand}[/red]")
        console.print("[dim]å¯ç¨å­å½ä»? list, new, switch, delete[/dim]")


def _list_branches(session_manager) -> None:
    """ååºææåæ?/ List all branches"""
    sessions = session_manager.list_sessions(limit=50)
    
    if not sessions:
        console.print("[yellow]ææ ä¼è¯ / No sessions[/yellow]")
        return
    
    current_id = session_manager.current_session.id if session_manager.current_session else None
    
    table = Table(title="ä¼è¯åæ¯ / Session Branches")
    table.add_column("å½å", style="cyan", width=4)
    table.add_column("åç§°", style="green")
    table.add_column("ID", style="dim")
    table.add_column("æ¶æ¯æ?, justify="right")
    table.add_column("ç¶ä¼è¯?, style="dim")
    table.add_column("æ´æ°æ¶é´", style="dim")
    
    for session in sessions:
        is_current = "â? if session.id == current_id else ""
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
