"""
commit命令 - 智能提交 / commit command - Smart commit

支持 / Supports:
- 自动生成commit消息 / Auto generate commit message
- 变更分析 / Change analysis
- 批量提交 / Batch commit
- AI增强 / AI enhanced
"""

import click
from rich.console import Console
from rich.panel import Panel

from alonechat.config import ConfigManager
from alonechat.git import GitManager, SmartCommit

console = Console()


@click.command()
@click.option("--all", "-a", "commit_all", is_flag=True, help="提交所有变更 / Commit all changes")
@click.option("--message", "-m", help="提交消息 / Commit message")
@click.option("--type", "-t", "commit_type", help="提交类型 / Commit type")
@click.option("--scope", "-s", help="变更范围 / Change scope")
@click.option("--ai", is_flag=True, help="使用AI生成提交消息 / Use AI to generate commit message")
@click.option("--push", "-p", is_flag=True, help="提交后推送 / Push after commit")
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
    智能提交 / Smart commit
    
    自动生成commit消息并提交 / Auto generate commit message and commit
    """
    console.print(Panel.fit(
        "[bold cyan]智能提交 / Smart Commit[/bold cyan]\n\n"
        "功能 / Features:\n"
        "• 自动分析变更 / Auto analyze changes\n"
        "• 生成规范消息 / Generate conventional message\n"
        "• AI增强建议 / AI enhanced suggestion\n"
        "• 安全回滚 / Safe rollback",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    git = GitManager()
    
    if not git.is_git_repo():
        console.print("[red]错误: 当前目录不是Git仓库 / Error: Current directory is not a git repository[/red]")
        return
    
    if ai:
        smart_commit = SmartCommit(git, console)
        success = smart_commit.ai_enhanced_commit(config_manager)
        if success and push:
            branch = git.get_current_branch()
            if branch:
                push_success, msg = git.push(branch=branch, set_upstream=True)
                if push_success:
                    console.print(f"[green]✓ {msg}[/green]")
                else:
                    console.print(f"[red]✗ {msg}[/red]")
        return
    
    analysis = git.analyze_changes()
    
    if not analysis.get("has_changes"):
        console.print(f"[yellow]{analysis.get('summary', '没有检测到变更 / No changes detected')}[/yellow]")
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
            console.print(f"\n[green]✓ {msg}[/green]")
            if push:
                branch = git.get_current_branch()
                if branch:
                    push_success, push_msg = git.push(branch=branch, set_upstream=True)
                    if push_success:
                        console.print(f"[green]✓ {push_msg}[/green]")
                    else:
                        console.print(f"[red]✗ {push_msg}[/red]")
        else:
            console.print(f"\n[red]✗ {msg}[/red]")
        return
    
    smart_commit = SmartCommit(git, console)
    success = smart_commit.interactive_commit()
    
    if success and push:
        branch = git.get_current_branch()
        if branch:
            push_success, msg = git.push(branch=branch, set_upstream=True)
            if push_success:
                console.print(f"[green]✓ {msg}[/green]")
            else:
                console.print(f"[red]✗ {msg}[/red]")
