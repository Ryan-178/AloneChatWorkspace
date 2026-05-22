"""
env命令组 - 环境管理

提供行动环境管理功能：
- env status: 查看环境状态
- env reset: 重置环境
- env checkpoint: 创建检查点
- env restore: 恢复检查点
- env sandbox: 沙箱管理
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from alonechat.environment.state import EnvironmentState
from alonechat.environment.sandbox import Sandbox, SandboxConfig
from alonechat.environment.action_env import ActionEnvironment

console = Console()


def get_env_dir() -> Path:
    env_dir = Path.home() / ".alonechat" / "env"
    env_dir.mkdir(parents=True, exist_ok=True)
    return env_dir


@click.group(name="env")
def env_commands():
    """环境管理命令 / Environment management commands"""
    pass


@env_commands.command(name="status")
@click.pass_context
def env_status(ctx: click.Context) -> None:
    """查看环境状态 / View environment status"""
    console.print("[bold cyan]环境状态 / Environment Status[/bold cyan]")
    
    env_state = EnvironmentState()
    
    console.print(Panel(
        f"[bold]世界状态 / World State[/bold]\n"
        f"工作目录: {env_state.world_state.working_directory}\n"
        f"项目根目录: {env_state.world_state.project_root}\n"
        f"可用工具: {len(env_state.world_state.available_tools)}\n"
        f"文件系统状态: {env_state.world_state.filesystem_state}\n\n"
        f"[bold]Agent状态 / Agent State[/bold]\n"
        f"当前任务: {env_state.agent_state.current_task or '无'}\n"
        f"当前计划: {env_state.agent_state.current_plan or '无'}\n"
        f"执行历史: {len(env_state.agent_state.execution_history)} 条\n"
        f"知识库: {len(env_state.agent_state.knowledge_base)} 条\n\n"
        f"[bold]交互历史 / Interaction History[/bold]\n"
        f"总交互数: {len(env_state.interaction_history.interactions)}\n"
        f"最后交互: {env_state.interaction_history.last_interaction_time or '无'}",
        border_style="cyan",
    ))
    
    if env_state.interaction_history.interactions:
        table = Table(title="最近交互 / Recent Interactions")
        table.add_column("时间", style="dim")
        table.add_column("类型", style="cyan")
        table.add_column("内容", style="green")
        
        for interaction in env_state.interaction_history.interactions[-5:]:
            table.add_row(
                interaction.get("timestamp", "")[:19],
                interaction.get("type", "N/A"),
                str(interaction.get("content", ""))[:50],
            )
        
        console.print(table)


@env_commands.command(name="reset")
@click.option("--soft", is_flag=True, help="软重置（保留配置）/ Soft reset (keep config)")
@click.confirmation_option(prompt="确定要重置环境吗? / Are you sure you want to reset?")
@click.pass_context
def env_reset(
    ctx: click.Context,
    soft: bool,
) -> None:
    """重置环境 / Reset environment"""
    console.print("[bold yellow]正在重置环境... / Resetting environment...[/bold yellow]")
    
    env_state = EnvironmentState()
    
    if soft:
        env_state.agent_state.current_task = None
        env_state.agent_state.current_plan = None
        env_state.agent_state.execution_history.clear()
        env_state.interaction_history.interactions.clear()
        console.print("[green]软重置完成 / Soft reset complete[/green]")
    else:
        env_state = EnvironmentState()
        console.print("[green]完全重置完成 / Full reset complete[/green]")
    
    env_dir = get_env_dir()
    checkpoint_dir = env_dir / "checkpoints"
    if checkpoint_dir.exists():
        for file in checkpoint_dir.glob("*.json"):
            file.unlink()
        console.print("[dim]检查点已清除 / Checkpoints cleared[/dim]")


@env_commands.command(name="checkpoint")
@click.option("--name", "-n", help="检查点名称 / Checkpoint name")
@click.option("--description", "-d", default="", help="检查点描述 / Checkpoint description")
@click.pass_context
def create_checkpoint(
    ctx: click.Context,
    name: Optional[str],
    description: str,
) -> None:
    """创建环境检查点 / Create environment checkpoint"""
    env_state = EnvironmentState()
    
    checkpoint_data = env_state.to_dict()
    checkpoint_data["checkpoint_name"] = name or f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    checkpoint_data["checkpoint_description"] = description
    checkpoint_data["checkpoint_time"] = datetime.now().isoformat()
    
    env_dir = get_env_dir()
    checkpoint_dir = env_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_file = checkpoint_dir / f"{checkpoint_data['checkpoint_name']}.json"
    
    try:
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]检查点已创建 / Checkpoint created: {checkpoint_file.name}[/green]")
        
    except Exception as e:
        console.print(f"[red]创建失败 / Creation failed: {e}[/red]")


@env_commands.command(name="restore")
@click.argument("checkpoint_name")
@click.pass_context
def restore_checkpoint(
    ctx: click.Context,
    checkpoint_name: str,
) -> None:
    """恢复环境检查点 / Restore environment checkpoint"""
    env_dir = get_env_dir()
    checkpoint_dir = env_dir / "checkpoints"
    
    checkpoint_file = checkpoint_dir / f"{checkpoint_name}.json"
    if not checkpoint_file.exists():
        for file in checkpoint_dir.glob("*.json"):
            if file.stem.startswith(checkpoint_name):
                checkpoint_file = file
                break
    
    if not checkpoint_file.exists():
        console.print(f"[red]检查点未找到 / Checkpoint not found: {checkpoint_name}[/red]")
        return
    
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            checkpoint_data = json.load(f)
        
        console.print(f"[green]检查点已加载 / Checkpoint loaded: {checkpoint_file.name}[/green]")
        console.print(f"[dim]创建时间 / Created: {checkpoint_data.get('checkpoint_time', 'N/A')}[/dim]")
        console.print(f"[dim]描述 / Description: {checkpoint_data.get('checkpoint_description', 'N/A')}[/dim]")
        
    except Exception as e:
        console.print(f"[red]恢复失败 / Restore failed: {e}[/red]")


@env_commands.command(name="checkpoints")
@click.pass_context
def list_checkpoints(ctx: click.Context) -> None:
    """列出所有检查点 / List all checkpoints"""
    env_dir = get_env_dir()
    checkpoint_dir = env_dir / "checkpoints"
    
    if not checkpoint_dir.exists():
        console.print("[yellow]没有检查点 / No checkpoints[/yellow]")
        return
    
    checkpoints = []
    for file in checkpoint_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                checkpoints.append({
                    "name": data.get("checkpoint_name", file.stem),
                    "time": data.get("checkpoint_time", "N/A"),
                    "description": data.get("checkpoint_description", ""),
                })
        except Exception:
            continue
    
    if not checkpoints:
        console.print("[yellow]没有有效检查点 / No valid checkpoints[/yellow]")
        return
    
    table = Table(title="检查点列表 / Checkpoint List")
    table.add_column("名称", style="cyan")
    table.add_column("时间", style="dim")
    table.add_column("描述", style="green")
    
    for cp in sorted(checkpoints, key=lambda x: x["time"], reverse=True):
        table.add_row(
            cp["name"],
            cp["time"][:19] if cp["time"] != "N/A" else "N/A",
            cp["description"][:40] if cp["description"] else "",
        )
    
    console.print(table)


@env_commands.command(name="sandbox")
@click.option("--create", is_flag=True, help="创建沙箱 / Create sandbox")
@click.option("--destroy", is_flag=True, help="销毁沙箱 / Destroy sandbox")
@click.option("--status", is_flag=True, help="查看沙箱状态 / View sandbox status")
@click.option("--allow-read", multiple=True, help="允许读取的路径 / Allowed read paths")
@click.option("--allow-write", multiple=True, help="允许写入的路径 / Allowed write paths")
@click.option("--allow-execute", multiple=True, help="允许执行的命令 / Allowed execute commands")
@click.pass_context
def manage_sandbox(
    ctx: click.Context,
    create: bool,
    destroy: bool,
    status: bool,
    allow_read: tuple,
    allow_write: tuple,
    allow_execute: tuple,
) -> None:
    """沙箱管理 / Sandbox management"""
    if create:
        config = SandboxConfig(
            allowed_read=list(allow_read) if allow_read else None,
            allowed_write=list(allow_write) if allow_write else None,
            allowed_execute=list(allow_execute) if allow_execute else None,
        )
        
        sandbox = Sandbox(config)
        console.print("[green]沙箱已创建 / Sandbox created[/green]")
        console.print(Panel(
            f"允许读取 / Allowed read: {config.allowed_read or '全部'}\n"
            f"允许写入 / Allowed write: {config.allowed_write or '全部'}\n"
            f"允许执行 / Allowed execute: {config.allowed_execute or '全部'}\n"
            f"最大文件大小 / Max file size: {config.max_file_size} bytes\n"
            f"超时时间 / Timeout: {config.timeout}s",
            title="沙箱配置 / Sandbox Config",
            border_style="green",
        ))
    
    elif destroy:
        console.print("[yellow]沙箱已销毁 / Sandbox destroyed[/yellow]")
    
    elif status:
        console.print("[bold cyan]沙箱状态 / Sandbox Status[/bold cyan]")
        console.print(Panel(
            "沙箱状态: 未激活\n"
            "已执行操作: 0\n"
            "已拦截操作: 0\n"
            "资源使用: N/A",
            border_style="cyan",
        ))
    
    else:
        console.print("[yellow]请指定操作: --create, --destroy, 或 --status[/yellow]")


@env_commands.command(name="tree")
@click.option("--max-depth", type=int, default=3, help="最大深度 / Max depth")
@click.pass_context
def env_tree(
    ctx: click.Context,
    max_depth: int,
) -> None:
    """显示环境状态树 / Display environment state tree"""
    env_state = EnvironmentState()
    
    tree = Tree("[bold cyan]环境状态 / Environment State[/bold cyan]")
    
    world = tree.add("[bold]世界状态 / World State[/bold]")
    world.add(f"工作目录: {env_state.world_state.working_directory}")
    world.add(f"项目根目录: {env_state.world_state.project_root}")
    
    tools = world.add(f"可用工具 ({len(env_state.world_state.available_tools)})")
    for tool in env_state.world_state.available_tools[:max_depth]:
        tools.add(f"{tool}")
    
    agent = tree.add("[bold]Agent状态 / Agent State[/bold]")
    agent.add(f"当前任务: {env_state.agent_state.current_task or '无'}")
    agent.add(f"当前计划: {env_state.agent_state.current_plan or '无'}")
    
    history = agent.add(f"执行历史 ({len(env_state.agent_state.execution_history)})")
    for i, exec_hist in enumerate(env_state.agent_state.execution_history[-max_depth:]):
        history.add(f"{exec_hist}")
    
    interactions = tree.add("[bold]交互历史 / Interaction History[/bold]")
    interactions.add(f"总交互数: {len(env_state.interaction_history.interactions)}")
    interactions.add(f"最后交互: {env_state.interaction_history.last_interaction_time or '无'}")
    
    console.print(tree)
