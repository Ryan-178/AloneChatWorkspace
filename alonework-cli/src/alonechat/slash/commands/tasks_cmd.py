"""
/tasks 命令 - 管理后台任务 / Manage background tasks

版本 / Version: 2.1.80
"""

import threading
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

_tasks_registry: dict = {}
_task_counter = 0


def _register_task(name: str, description: str) -> int:
    """
    注册后台任务 / Register background task
    """
    global _task_counter
    _task_counter += 1
    _tasks_registry[_task_counter] = {
        "id": _task_counter,
        "name": name,
        "description": description,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "thread": threading.current_thread().name,
    }
    return _task_counter


def _update_task_status(task_id: int, status: str) -> None:
    """
    更新任务状态 / Update task status
    """
    if task_id in _tasks_registry:
        _tasks_registry[task_id]["status"] = status
        _tasks_registry[task_id]["updated_at"] = datetime.now().isoformat()


def tasks_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理后台任务 / Manage background tasks

    用法 / Usage:
        /tasks                 列出所有任务 / List all tasks
        /tasks list            列出所有任务 / List all tasks
        /tasks status          任务状态概览 / Task status overview
        /tasks stop <id>       停止任务 / Stop task
        /tasks clean           清理已完成任务 / Clean completed tasks
        /tasks info <id>       任务详情 / Task details
    """
    if not args or args[0] == "list":
        if not _tasks_registry:
            console.print("[dim]没有后台任务 / No background tasks[/dim]")
            console.print("[dim]任务会在后台操作时自动创建 / Tasks are created during background operations[/dim]")
            return

        table = Table(show_header=True, title="后台任务 / Background Tasks")
        table.add_column("#", style="dim", width=4)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description", style="green")
        table.add_column("状态 / Status", style="yellow")
        table.add_column("线程 / Thread", style="dim")

        for task in _tasks_registry.values():
            status_style = {
                "running": "[green]运行中 / Running[/green]",
                "completed": "[dim]已完成 / Completed[/dim]",
                "failed": "[red]失败 / Failed[/red]",
                "stopped": "[yellow]已停止 / Stopped[/yellow]",
            }.get(task["status"], task["status"])

            table.add_row(
                str(task["id"]),
                task["name"],
                task.get("description", "")[:40],
                status_style,
                task.get("thread", "-"),
            )

        console.print(table)
        return

    action = args[0]

    if action == "status":
        running = sum(1 for t in _tasks_registry.values() if t["status"] == "running")
        completed = sum(1 for t in _tasks_registry.values() if t["status"] == "completed")
        failed = sum(1 for t in _tasks_registry.values() if t["status"] == "failed")
        stopped = sum(1 for t in _tasks_registry.values() if t["status"] == "stopped")

        console.print(Panel(
            f"[bold]任务状态 / Task Status[/bold]\n\n"
            f"运行中 / Running: [green]{running}[/green]\n"
            f"已完成 / Completed: [dim]{completed}[/dim]\n"
            f"失败 / Failed: [red]{failed}[/red]\n"
            f"已停止 / Stopped: [yellow]{stopped}[/yellow]\n"
            f"总计 / Total: {len(_tasks_registry)}",
            border_style="cyan",
        ))
        return

    if action == "stop":
        if len(args) < 2:
            console.print("[red]请指定任务ID / Please specify task ID[/red]")
            return
        try:
            task_id = int(args[1])
        except ValueError:
            console.print(f"[red]无效ID / Invalid ID: {args[1]}[/red]")
            return
        if task_id in _tasks_registry:
            _update_task_status(task_id, "stopped")
            console.print(f"[green]✓ 任务已停止 / Task stopped: #{task_id}[/green]")
        else:
            console.print(f"[red]未找到任务 / Task not found: #{task_id}[/red]")
        return

    if action == "clean":
        before = len(_tasks_registry)
        completed_ids = [
            tid for tid, t in _tasks_registry.items()
            if t["status"] in ("completed", "failed", "stopped")
        ]
        for tid in completed_ids:
            del _tasks_registry[tid]
        console.print(f"[green]✓ 已清理 {len(completed_ids)} 个任务 / Cleaned {len(completed_ids)} tasks[/green]")
        return

    if action == "info":
        if len(args) < 2:
            console.print("[red]请指定任务ID / Please specify task ID[/red]")
            return
        try:
            task_id = int(args[1])
        except ValueError:
            console.print(f"[red]无效ID / Invalid ID: {args[1]}[/red]")
            return
        if task_id in _tasks_registry:
            task = _tasks_registry[task_id]
            info = "\n".join(f"{k}: {v}" for k, v in task.items())
            console.print(Panel(info, title=f"任务详情 / Task #{task_id}", border_style="cyan"))
        else:
            console.print(f"[red]未找到任务 / Task not found: #{task_id}[/red]")
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: list, status, stop, clean, info[/dim]")
