"""
/diff 命令 - 查看未提交的更改 / View uncommitted changes

版本 / Version: 2.1.80
"""

import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def _run_git(args: list[str], cwd: str = None) -> tuple[int, str]:
    """
    执行git命令 / Execute git command
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd or str(Path.cwd()),
            timeout=30,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return -1, "git not found"
    except subprocess.TimeoutExpired:
        return -2, "timeout"
    except Exception as e:
        return -3, str(e)


def _check_git_repo() -> bool:
    """
    检查是否在git仓库中 / Check if in git repository
    """
    code, _ = _run_git(["rev-parse", "--git-dir"])
    return code == 0


def _get_diff(staged: bool = False) -> str:
    """
    获取diff内容 / Get diff content
    """
    args = ["diff"]
    if staged:
        args.append("--staged")
    code, output = _run_git(args)
    if code != 0:
        return ""
    return output


def _get_diff_stat() -> str:
    """
    获取diff统计 / Get diff statistics
    """
    code, output = _run_git(["diff", "--stat"])
    if code != 0:
        return ""
    return output


def _get_changed_files(staged: bool = False) -> list[str]:
    """
    获取变更文件列表 / Get list of changed files
    """
    args = ["diff", "--name-only"]
    if staged:
        args.append("--staged")
    code, output = _run_git(args)
    if code != 0:
        return []
    return [f for f in output.split("\n") if f.strip()]


def diff_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    查看未提交的更改 / View uncommitted changes

    用法 / Usage:
        /diff               查看工作区更改 / View working directory changes
        /diff --staged      查看暂存区更改 / View staged changes
        /diff --stat        查看更改统计 / View change statistics
        /diff --turn        查看本轮对话的更改 / View current turn changes
        /diff <file>        查看特定文件的更改 / View specific file changes
    """
    if not _check_git_repo():
        console.print("[yellow]当前目录不是git仓库 / Not a git repository[/yellow]")
        console.print("[dim]请在git项目中使用此命令 / Use this command in a git project[/dim]")
        return

    staged = "--staged" in args
    stat_only = "--stat" in args
    turn_mode = "--turn" in args
    target_file = None

    clean_args = [a for a in args if a not in ("--staged", "--stat", "--turn")]
    if clean_args:
        target_file = clean_args[0]

    if turn_mode:
        if not session_manager or not session_manager.current_session:
            console.print("[yellow]无活动会话 / No active session[/yellow]")
            return

        messages = session_manager.get_messages()
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            console.print("[yellow]本轮没有用户输入 / No user input this turn[/yellow]")
            return

        console.print(Panel(
            "[bold cyan]本轮对话摘要 / Current Turn Summary[/bold cyan]",
            border_style="cyan",
        ))
        console.print(f"[dim]消息总数 / Total messages: {len(messages)}[/dim]")
        console.print(f"[dim]用户输入数 / User inputs: {len(user_messages)}[/dim]")
        last_user = user_messages[-1].get("content", "")[:100]
        console.print(f"[dim]最近输入 / Last input: {last_user}...[/dim]")
        return

    stage_label = "暂存区 / Staged" if staged else "工作区 / Working"
    console.print(f"\n[bold cyan]Git Diff ({stage_label})[/bold cyan]\n")

    if stat_only:
        stat = _get_diff_stat()
        if not stat:
            console.print("[green]没有更改 / No changes[/green]")
            return
        console.print(stat)
        return

    if target_file:
        args_list = ["diff", target_file]
        if staged:
            args_list.insert(1, "--staged")
        code, output = _run_git(args_list)
        if code != 0 or not output:
            console.print(f"[yellow]文件无更改或不存在 / No changes or file not found: {target_file}[/yellow]")
            return
        console.print(Syntax(output, "diff", theme="monokai", line_numbers=True))
        return

    changed_files = _get_changed_files(staged)
    if not changed_files:
        console.print("[green]没有更改 / No changes[/green]")
        return

    table = Table(show_header=True, title="变更文件 / Changed Files")
    table.add_column("文件 / File", style="cyan")
    table.add_column("状态 / Status", style="green")
    for f in changed_files:
        table.add_row(f, "M")
    console.print(table)

    diff_content = _get_diff(staged)
    if diff_content:
        console.print()
        console.print(Syntax(diff_content, "diff", theme="monokai", line_numbers=False))
