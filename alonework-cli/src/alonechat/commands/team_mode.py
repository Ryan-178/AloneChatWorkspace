"""
CLI Team模式 / CLI Team Mode

提供多Agent协作的CLI交互
Provides multi-agent collaboration CLI interaction
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout

console = Console()
logger = logging.getLogger(__name__)


class CLITeamMode:
    """
    CLI Team模式 / CLI Team Mode

    管理多Agent协作的CLI界面和交互
    Manages multi-agent collaboration CLI interface and interaction
    """

    def __init__(self):
        self._team_engine = None
        self._is_running = False
        self._current_task: Optional[str] = None

    async def initialize(self) -> bool:
        """
        初始化Team模式 / Initialize Team mode
        """
        try:
            from alonechat.orchestration.team_engine import TeamEngine

            self._team_engine = TeamEngine()
            await self._team_engine.initialize()
            return True
        except ImportError as e:
            console.print(f"[red]无法加载Team Engine: {e}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]初始化失败: {e}[/red]")
            return False

    async def run_team(
        self,
        task: str,
        workers: int = 3,
        verifiers: int = 1,
        interactive: bool = True,
    ) -> Dict[str, Any]:
        """
        运行Team任务 / Run Team task

        Args:
            task: 任务描述
            workers: Worker数量
            verifiers: Verifier数量
            interactive: 是否交互式

        Returns:
            执行结果
        """
        if not self._team_engine:
            await self.initialize()

        if not self._team_engine:
            raise RuntimeError("Team Engine未初始化")

        self._is_running = True
        self._current_task = task

        console.print(Panel(
            f"启动Team协作模式\n"
            f"任务: {task}\n"
            f"Workers: {workers}, Verifiers: {verifiers}",
            title="Team Mode",
            border_style="blue",
        ))

        if interactive:
            with Live(refresh_per_second=1) as live:
                async for status in self._run_with_status(task):
                    layout = self._create_status_layout(status)
                    live.update(layout)
        else:
            result = await self._team_engine.run(task)
            return result

        status = self._team_engine.get_status()
        self._is_running = False

        if status["phase"] == "done":
            console.print("\n[green bold]✓ Team执行完成[/green bold]")
        elif status["phase"] == "failed":
            console.print("\n[red bold]✗ Team执行失败[/red bold]")
            if status["errors"]:
                for error in status["errors"]:
                    console.print(f"  [red]- {error}[/red]")

        return status

    async def _run_with_status(self, task: str):
        """
        带状态的运行 / Run with status updates
        """
        yield {
            "phase": "initializing",
            "workers": {},
            "subtasks": [],
        }

        try:
            result = await asyncio.create_task(self._team_engine.run(task))

            while self._team_engine.is_running:
                status = self._team_engine.get_status()
                yield status
                await asyncio.sleep(0.5)

            yield status

        except Exception as e:
            yield {
                "phase": "failed",
                "error": str(e),
                "workers": {},
                "subtasks": [],
            }

    def _create_status_layout(self, status: Dict[str, Any]) -> Layout:
        """
        创建状态布局 / Create status layout
        """
        layout = Layout()

        header = Panel(
            f"[bold blue]Team Status[/bold blue]\n"
            f"阶段: {status.get('phase', 'unknown')}\n"
            f"运行中: {status.get('is_running', False)}",
            title="Header",
        )

        body_content = []

        worker_count = status.get("worker_count", 0)
        completed = status.get("completed_subtasks", 0)
        total = status.get("subtask_count", 0)

        progress_bar = ""
        if total > 0:
            pct = (completed / total) * 100
            filled = int(pct / 10)
            empty = 10 - filled
            progress_bar = f"[{'█' * filled}{'░' * empty}] {pct:.0f}%"

        body_content.append(f"\n[bold]进度:[/bold] {progress_bar}")
        body_content.append(f"[bold]子任务:[/bold] {completed}/{total}")

        errors = status.get("errors", [])
        if errors:
            body_content.append(f"\n[red bold]错误:[/red bold]")
            for error in errors[:3]:
                body_content.append(f"  [red]{error}[/red]")

        body = Panel(
            "\n".join(body_content),
            title="Status",
        )

        layout.split_column(
            Layout(header, size=8),
            Layout(body),
        )

        return layout

    async def abort(self) -> None:
        """
        中止执行 / Abort execution
        """
        if self._team_engine and self._team_engine.is_running:
            await self._team_engine.abort()
            self._is_running = False
            console.print("[yellow]已中止Team执行[/yellow]")

    def display_team_status(self, status: Dict[str, Any]) -> None:
        """
        显示Team状态 / Display Team status
        """
        table = Table(title="Team Status", show_header=True, header_style="bold")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")

        phase = status.get("phase", "unknown")
        phase_colors = {
            "planning": "purple",
            "dispatching": "blue",
            "executing": "cyan",
            "verifying": "yellow",
            "aggregating": "indigo",
            "done": "green",
            "failed": "red",
        }
        color = phase_colors.get(phase, "white")

        table.add_row("Team ID", str(status.get("team_id", "N/A"))[:12])
        table.add_row("阶段", f"[{color}]{phase}[/{color}]")
        table.add_row("运行中", "是" if status.get("is_running") else "否")
        table.add_row("Worker数", str(status.get("worker_count", 0)))
        table.add_row("Verifier数", str(status.get("verifier_count", 0)))
        table.add_row("已完成子任务", str(status.get("completed_subtasks", 0)))
        table.add_row("失败子任务", str(status.get("failed_subtasks", 0)))
        table.add_row("待处理子任务", str(status.get("pending_subtasks", 0)))

        elapsed = status.get("elapsed_seconds")
        if elapsed is not None:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            table.add_row("已用时间", f"{minutes}:{seconds:02d}")

        console.print(table)

        errors = status.get("errors", [])
        if errors:
            console.print("\n[red bold]错误:[/red bold]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")


def display_worker_list(workers: List[Dict[str, Any]]) -> None:
    """
    显示Worker列表 / Display Worker list
    """
    if not workers:
        console.print("[yellow]没有Worker[/yellow]")
        return

    table = Table(title="Workers", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("角色", style="green")
    table.add_column("状态", style="yellow")

    status_icons = {
        "pending": "[gray]等待[/gray]",
        "producing": "[blue]执行[/blue]",
        "verifying": "[yellow]验证[/yellow]",
        "done": "[green]完成[/green]",
        "retry": "[orange]重试[/orange]",
        "failed": "[red]失败[/red]",
    }

    for worker in workers:
        wid = worker.get("agent_id", "unknown")[:8]
        role = worker.get("role", "unknown")
        status = worker.get("status", "pending")
        icon = status_icons.get(status, status)

        table.add_row(wid, role, icon)

    console.print(table)


def display_subtask_table(subtasks: List[Dict[str, Any]]) -> None:
    """
    显示子任务表格 / Display subtask table
    """
    if not subtasks:
        console.print("[yellow]没有子任务[/yellow]")
        return

    table = Table(title="Subtasks", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("描述", style="green")
    table.add_column("分配给", style="yellow")
    table.add_column("状态", style="magenta")
    table.add_column("重试", width=6)

    status_colors = {
        "pending": "gray",
        "producing": "blue",
        "verifying": "yellow",
        "done": "green",
        "retry": "orange",
        "failed": "red",
    }

    for subtask in subtasks:
        sid = subtask.get("id", "unknown")[:8]
        desc = subtask.get("description", "")[:40]
        assigned = (subtask.get("assigned_to") or "unassigned")[:8]
        status = subtask.get("status", "pending")
        retries = subtask.get("retry_count", 0)
        color = status_colors.get(status, "white")

        table.add_row(sid, desc, assigned, f"[{color}]{status}[/{color}]", str(retries))

    console.print(table)


async def team_mode_command(
    task: str,
    workers: int = 3,
    verifiers: int = 1,
    watch: bool = False,
) -> None:
    """
    Team模式命令 / Team mode command
    """
    cli_team = CLITeamMode()

    if watch:
        await cli_team.run_team(task, workers=workers, verifiers=verifiers, interactive=True)
    else:
        result = await cli_team.run_team(task, workers=workers, verifiers=verifiers, interactive=False)
        cli_team.display_team_status(result)
