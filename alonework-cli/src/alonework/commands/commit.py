"""
commitå½ä»¤ - æºè½æäº¤ / commit command - Smart commit

æ¯æ / Supports:
- èªå¨çæcommitæ¶æ¯ / Auto generate commit message
- åæ´åæ / Change analysis
- æ¹éæäº¤ / Batch commit
- AIå¢å¼º / AI enhanced
"""

import click
from rich.console import Console
from rich.panel import Panel

from alonework.config import ConfigManager
from alonework.git import GitManager, SmartCommit

console = Console()


@click.command()
@click.option("--all", "-a", "commit_all", is_flag=True, help="æäº¤ææåæ?/ Commit all changes")
@click.option("--message", "-m", help="æäº¤æ¶æ¯ / Commit message")
@click.option("--type", "-t", "commit_type", help="æäº¤ç±»å / Commit type")
@click.option("--scope", "-s", help="åæ´èå´ / Change scope")
@click.option("--ai", is_flag=True, help="ä½¿ç¨AIçææäº¤æ¶æ¯ / Use AI to generate commit message")
@click.option("--push", "-p", is_flag=True, help="æäº¤åæ¨é?/ Push after commit")
@click.pass_obj
def commit_command(
    obj: dict,
    commit_all: bool,
    message: str | None,
    commit_type: str | None,
    scope: str | None,
    ai: bool,
    push: bool,
) -> None:
    """
    æºè½æäº¤ / Smart commit
    
    èªå¨çæcommitæ¶æ¯å¹¶æäº?/ Auto generate commit message and commit
    """
    console.print(Panel.fit(
        "[bold cyan]æºè½æäº¤ / Smart Commit[/bold cyan]\n\n"
        "åè½ / Features:\n"
        "â?èªå¨åæåæ´ / Auto analyze changes\n"
        "â?çæè§èæ¶æ¯ / Generate conventional message\n"
        "â?AIå¢å¼ºå»ºè®® / AI enhanced suggestion\n"
        "â?å®å¨åæ» / Safe rollback",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    git = GitManager()
    
    if not git.is_git_repo():
        console.print("[red]éè¯¯: å½åç®å½ä¸æ¯Gitä»åº / Error: Current directory is not a git repository[/red]")
        return
    
    if ai:
        smart_commit = SmartCommit(git, console)
        success = smart_commit.ai_enhanced_commit(config_manager)
        if success and push:
            branch = git.get_current_branch()
            if branch:
                push_success, msg = git.push(branch=branch, set_upstream=True)
                if push_success:
                    console.print(f"[green]â?{msg}[/green]")
                else:
                    console.print(f"[red]â?{msg}[/red]")
        return
    
    analysis = git.analyze_changes()
    
    if not analysis.get("has_changes"):
        console.print(f"[yellow]{analysis.get('summary', 'æ²¡ææ£æµå°åæ´ / No changes detected')}[/yellow]")
        return
    
    console.print(git.render_status())
    
    if message:
        suggested = analysis.get("suggested", {})
        if not commit_type:
            commit_type = suggested.get("type")
        if not scope:
            scope = suggested.get("scope")
        
        success, msg = git.commit(message, add_all=commit_all)
        
        if success:
            console.print(f"\n[green]â?{msg}[/green]")
            if push:
                branch = git.get_current_branch()
                if branch:
                    push_success, push_msg = git.push(branch=branch, set_upstream=True)
                    if push_success:
                        console.print(f"[green]â?{push_msg}[/green]")
                    else:
                        console.print(f"[red]â?{push_msg}[/red]")
        else:
            console.print(f"\n[red]â?{msg}[/red]")
        return
    
    smart_commit = SmartCommit(git, console)
    success = smart_commit.interactive_commit()
    
    if success and push:
        branch = git.get_current_branch()
        if branch:
            push_success, msg = git.push(branch=branch, set_upstream=True)
            if push_success:
                console.print(f"[green]â?{msg}[/green]")
            else:
                console.print(f"[red]â?{msg}[/red]")
