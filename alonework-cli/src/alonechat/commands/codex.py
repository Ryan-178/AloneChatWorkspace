"""
Codex CLI 桥接命令
Bridge commands between alonework-cli and Codex engine.

Usage:
    alonechat codex exec "创建一个Python Web服务器"
    alonechat codex review
    alonechat codex mode code
    alonechat codex status
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()


def _get_codex_bridge(working_dir: str = ".", mode: str = "code"):
    """获取 CodexBridge 实例"""
    try:
        from alonechat.code.codex_bridge import CodexBridge, CodexBridgeConfig, CodexProvider
        from alonechat.core.types import AgentMode

        config = CodexBridgeConfig(
            provider=CodexProvider.DEEPSEEK,
            model="deepseek-chat",
            working_directory=os.path.abspath(working_dir),
        )
        return CodexBridge(config)
    except ImportError as e:
        console.print(f"[red]无法导入 alonechat: {e}[/red]")
        console.print("[dim]请确保 alonechat 已安装: pip install -e alonechat[/dim]")
        return None


def _get_dual_mode_manager():
    """获取 DualModeManager 实例"""
    try:
        from alonechat.core.dual_mode_manager import DualModeManager
        return DualModeManager.get_instance()
    except ImportError:
        return None


def _display_execution_result(result, verbose: bool = False):
    """显示执行结果"""
    if result.success:
        if result.output:
            console.print(Panel(
                Markdown(result.output) if any(c in result.output for c in ["#", "*", "`", "-"]) else result.output,
                title="[green]执行结果[/green]",
                border_style="green",
            ))
        if result.tool_calls and verbose:
            table = Table(title="工具调用记录")
            table.add_column("工具", style="cyan")
            table.add_column("状态", style="green")
            table.add_column("输出", max_width=60)
            for tc in result.tool_calls:
                status = "[green]✓[/green]" if tc.get("success") else "[red]✗[/red]"
                table.add_row(
                    tc.get("tool", "?"),
                    status,
                    (tc.get("output", "")[:80] + "...") if len(tc.get("output", "")) > 80 else tc.get("output", ""),
                )
            console.print(table)
        console.print(f"[dim]耗时: {result.duration_ms:.0f}ms[/dim]")
    else:
        console.print(Panel(
            result.error or "未知错误",
            title="[red]执行失败[/red]",
            border_style="red",
        ))


@click.group()
@click.pass_context
def codex(ctx):
    """Codex 代码执行引擎命令

    集成 Codex 架构的代码生成、调试、重构能力。
    支持 Work (MTC) 和 CODE 双模式切换。
    """
    ctx.ensure_object(dict)


@codex.command("exec")
@click.argument("prompt")
@click.option("--cwd", "-c", default=".", help="工作目录")
@click.option("--model", "-m", default=None, help="模型名称")
@click.option("--stream", "-s", is_flag=True, help="流式输出")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.pass_obj
def exec_command(obj: dict, prompt: str, cwd: str, model: str, stream: bool, verbose: bool):
    """执行编码任务

    使用 Codex 引擎执行代码生成、调试、重构等任务。

    示例:
        alonechat codex exec "创建一个FastAPI服务器"
        alonechat codex exec "修复main.py中的bug" --verbose
        alonechat codex exec "重构utils模块" --cwd ./myproject
    """
    console.print(Panel.fit(
        f"[bold cyan]Codex 执行引擎[/bold cyan]\n\n"
        f"任务: {prompt}\n"
        f"目录: {os.path.abspath(cwd)}\n"
        f"模型: {model or '默认'}",
        border_style="cyan",
    ))

    bridge = _get_codex_bridge(cwd)
    if not bridge:
        return

    async def _run():
        if stream:
            console.print("\n[bold]执行中...[/bold]\n")
            async for event in bridge.exec_stream(prompt, cwd=cwd, model=model):
                if event.type == "message":
                    console.print(event.content)
                elif event.type == "tool_call":
                    console.print(f"[dim]调用工具: {event.content}[/dim]")
                elif event.type == "error":
                    console.print(f"[red]错误: {event.content}[/red]")
                elif event.type == "completed":
                    console.print(f"\n[dim]完成，耗时: {event.metadata.get('duration_ms', 0):.0f}ms[/dim]")
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("执行中...", total=None)
                result = await bridge.exec(prompt, cwd=cwd, model=model)
                progress.update(task, completed=True)

            _display_execution_result(result, verbose)

    asyncio.run(_run())


@codex.command("review")
@click.option("--cwd", "-c", default=".", help="工作目录")
@click.option("--target", "-t", default=None, help="审查目标（文件/目录）")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.pass_obj
def review_command(obj: dict, cwd: str, target: str, verbose: bool):
    """代码审查

    使用 Codex 引擎进行代码审查。

    示例:
        alonechat codex review
        alonechat codex review --target src/main.py
        alonechat codex review --cwd ./myproject
    """
    console.print(Panel.fit(
        f"[bold cyan]代码审查[/bold cyan]\n\n"
        f"目录: {os.path.abspath(cwd)}\n"
        f"目标: {target or '全部变更'}",
        border_style="cyan",
    ))

    bridge = _get_codex_bridge(cwd)
    if not bridge:
        return

    async def _run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("审查中...", total=None)
            result = await bridge.review(cwd=cwd, target=target)
            progress.update(task, completed=True)

        _display_execution_result(result, verbose)

    asyncio.run(_run())


@codex.command("mode")
@click.argument("mode_name", type=click.Choice(["work", "code", "auto", "mtc"], case_sensitive=False))
@click.option("--session", "-s", default="default", help="会话 ID")
@click.pass_obj
def mode_command(obj: dict, mode_name: str, session: str):
    """切换 Agent 模式

    WORK: 办公模式（文档、数据、调研）
    CODE: 编码模式（代码生成、调试、重构）
    AUTO: 自动检测

    示例:
        alonechat codex mode code
        alonechat codex mode work
        alonechat codex mode auto
    """
    from alonechat.core.types import AgentMode

    manager = _get_dual_mode_manager()
    if not manager:
        console.print("[red]无法初始化 DualModeManager[/red]")
        return

    async def _run():
        if mode_name == "auto":
            console.print("[yellow]自动模式检测需要提供任务描述[/yellow]")
            return

        if mode_name == "mtc":
            console.print("[yellow]已过时选项 / Deprecated choice: 使用 work 替换 mtc[/yellow]")
            target_mode = AgentMode.WORK
        elif mode_name == "work":
            target_mode = AgentMode.WORK
        else:
            target_mode = AgentMode.CODE

        success = await manager.switch_mode(session, target_mode)

        if success:
            state = manager.get_session_state(session)
            icon = "🔧" if state.mode == AgentMode.CODE else "📋"
            color = "green" if state.mode == AgentMode.CODE else "blue"
            console.print(Panel.fit(
                f"{icon} 已切换到 [bold {color}]{state.mode.value.upper()}[/bold {color}] 模式\n\n"
                f"切换次数: {state.switch_count}\n"
                f"会话: {session}",
                border_style=color,
            ))
        else:
            console.print("[red]模式切换失败[/red]")

    asyncio.run(_run())


@codex.command("status")
@click.option("--session", "-s", default="default", help="会话 ID")
@click.pass_obj
def status_command(obj: dict, session: str):
    """显示 Codex 引擎状态

    显示当前模式、工具链、执行历史等信息。
    """
    manager = _get_dual_mode_manager()

    table = Table(title="Codex 引擎状态")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="green")

    table.add_row("引擎", "纯 Python (Codex 架构)")
    table.add_row("工作目录", os.path.abspath("."))

    if manager:
        summary = manager.get_session_summary(session)
        table.add_row("当前模式", summary.get("current_mode", "未设置").upper())
        table.add_row("切换次数", str(summary.get("switch_count", 0)))
        mode_config = summary.get("mode_config", {})
        table.add_row("模型", mode_config.get("model", "未设置"))
        table.add_row("使用 CodexBridge", "是" if mode_config.get("use_codex_bridge") else "否")

    console.print(table)


@codex.command("tools")
@click.pass_obj
def tools_command(obj: dict):
    """列出可用工具

    显示 Codex 引擎支持的所有工具。
    """
    from alonechat.code.code_engine import TOOL_DEFINITIONS

    table = Table(title="可用工具")
    table.add_column("工具名", style="cyan")
    table.add_column("描述", style="green")
    table.add_column("参数", style="dim")

    for name, defn in TOOL_DEFINITIONS.items():
        params = defn.get("parameters", {}).get("properties", {})
        param_str = ", ".join(params.keys())
        table.add_row(name, defn.get("description", ""), param_str)

    console.print(table)


@codex.command("shell")
@click.argument("command", nargs=-1, required=True)
@click.option("--cwd", "-c", default=".", help="工作目录")
@click.option("--timeout", "-t", default=30, help="超时秒数")
@click.pass_obj
def shell_command(obj: dict, command: tuple, cwd: str, timeout: int):
    """执行 Shell 命令

    通过 Codex 的 Shell 工具执行命令。

    示例:
        alonechat codex shell ls -la
        alonechat codex shell python --version
        alonechat codex shell git status --cwd ./myproject
    """
    from alonechat.code.shell_tool import ShellTool, ShellConfig

    cmd_str = " ".join(command)
    console.print(f"[dim]$ {cmd_str}[/dim]")

    shell = ShellTool(ShellConfig(timeout_ms=timeout * 1000))

    async def _run():
        result = await shell.execute(cmd_str, cwd=os.path.abspath(cwd))

        if result.stdout:
            console.print(result.stdout, end="")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]", end="")

        if not result.success:
            console.print(f"\n[red]退出码: {result.exit_code}[/red]")
        console.print(f"[dim]耗时: {result.duration_ms:.0f}ms ({shell.shell_type.value})[/dim]")

    asyncio.run(_run())


@codex.command("patch")
@click.argument("patch_file", type=click.Path(exists=True))
@click.option("--cwd", "-c", default=".", help="工作目录")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际应用")
@click.pass_obj
def patch_command(obj: dict, patch_file: str, cwd: str, dry_run: bool):
    """应用补丁文件

    使用 Codex 的 ApplyPatch 工具应用 unified diff 补丁。

    示例:
        alonechat codex patch changes.diff
        alonechat codex patch changes.diff --dry-run
    """
    from alonechat.code.apply_patch import ApplyPatchTool

    patch_text = Path(patch_file).read_text(encoding="utf-8")
    patcher = ApplyPatchTool(workdir=os.path.abspath(cwd), dry_run=dry_run)

    if dry_run:
        preview = patcher.preview(patch_text)
        console.print(Panel(
            f"文件数: {preview['file_count']}\n"
            + "\n".join(f"  - {c['path']} ({c['type']})" for c in preview["changes"]),
            title="[yellow]补丁预览 (dry-run)[/yellow]",
            border_style="yellow",
        ))
    else:
        result = patcher.apply(patch_text)
        if result.success:
            console.print(Panel(
                f"{result.details}\n"
                + "\n".join(f"  ✓ {f}" for f in result.applied_files),
                title="[green]补丁已应用[/green]",
                border_style="green",
            ))
        else:
            console.print(Panel(
                "\n".join(f"  ✗ {e}" for e in result.errors),
                title="[red]补丁应用失败[/red]",
                border_style="red",
            ))
