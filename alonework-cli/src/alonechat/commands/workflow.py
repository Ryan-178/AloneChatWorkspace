"""
workflow命令组 - 工作流编排

提供工作流管理、执行、监控等功能：
- workflow list: 列出工作流
- workflow create: 创建工作流
- workflow run: 执行工作流
- workflow status: 查看执行状态
- workflow plan: 任务规划
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from alonechat.orchestration.workflow import (
    Workflow,
    WorkflowEngine,
    WorkflowContext,
    Node,
    NodeType,
)
from alonechat.orchestration.planner import TaskPlanner, DecompositionStrategy
from alonechat.orchestration.executor import WorkflowExecutor, ExecutionConfig
from alonechat.agents.supervisor import Task

console = Console()


def get_workflow_dir() -> Path:
    workflow_dir = Path.home() / ".alonechat" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    return workflow_dir


@click.group(name="workflow")
def workflow_commands():
    """工作流编排命令 / Workflow orchestration commands"""
    pass


@workflow_commands.command(name="list")
@click.option("--detail", is_flag=True, help="显示详细信息 / Show details")
@click.pass_context
def list_workflows(
    ctx: click.Context,
    detail: bool,
) -> None:
    """列出所有工作流 / List all workflows"""
    engine = WorkflowEngine()
    workflow_dir = get_workflow_dir()
    
    for file in workflow_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                workflow = Workflow.from_dict(data)
                engine.register_workflow(workflow)
        except Exception:
            continue
    
    workflows = engine.list_workflows()
    
    if not workflows:
        console.print("[yellow]没有工作流 / No workflows[/yellow]")
        return
    
    if detail:
        for wf in workflows:
            workflow = engine.get_workflow(wf["id"])
            if workflow:
                console.print(Panel(
                    f"[bold cyan]{workflow.name}[/bold cyan]\n"
                    f"ID: {workflow.id}\n"
                    f"描述: {workflow.description}\n"
                    f"节点数: {len(workflow.nodes)}\n"
                    f"边数: {len(workflow.edges)}",
                    border_style="cyan",
                ))
    else:
        table = Table(title="工作流列表 / Workflow List")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("名称", style="green")
        table.add_column("描述", style="dim")
        table.add_column("节点数", style="yellow", justify="right")
        
        for wf in workflows:
            workflow = engine.get_workflow(wf["id"])
            if workflow:
                table.add_row(
                    workflow.id[:12],
                    workflow.name,
                    workflow.description[:40] if workflow.description else "",
                    str(len(workflow.nodes)),
                )
        
        console.print(table)


@workflow_commands.command(name="create")
@click.argument("name")
@click.option("--description", "-d", default="", help="工作流描述 / Workflow description")
@click.option("--from-file", help="从文件导入 / Import from file")
@click.option("--preset", type=click.Choice(["code_review", "data_pipeline", "research"]), help="使用预设模板 / Use preset template")
@click.pass_context
def create_workflow(
    ctx: click.Context,
    name: str,
    description: str,
    from_file: Optional[str],
    preset: Optional[str],
) -> None:
    """创建新工作流 / Create new workflow"""
    console.print(f"[bold cyan]创建工作流: {name}[/bold cyan]")
    
    if from_file:
        try:
            with open(from_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                workflow = Workflow.from_dict(data)
                workflow.name = name
                if description:
                    workflow.description = description
        except Exception as e:
            console.print(f"[red]导入失败 / Import failed: {e}[/red]")
            return
    
    elif preset:
        workflow = _create_preset_workflow(name, description, preset)
    
    else:
        workflow = Workflow(
            id="",
            name=name,
            description=description,
        )
        
        start_node = Node(
            id="start",
            name="开始",
            node_type=NodeType.START,
        )
        end_node = Node(
            id="end",
            name="结束",
            node_type=NodeType.END,
        )
        
        workflow.add_node(start_node).add_node(end_node)
        workflow.add_edge("start", "end")
    
    workflow_dir = get_workflow_dir()
    file_path = workflow_dir / f"{workflow.id}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workflow.to_dict(), f, ensure_ascii=False, indent=2)
        
        console.print(f"[green]工作流已创建 / Workflow created: {file_path}[/green]")
        console.print(f"[dim]ID: {workflow.id}[/dim]")
        
    except Exception as e:
        console.print(f"[red]创建失败 / Creation failed: {e}[/red]")


def _create_preset_workflow(
    name: str,
    description: str,
    preset: str,
) -> Workflow:
    workflow = Workflow(
        id="",
        name=name,
        description=description,
    )
    
    start = Node(id="start", name="开始", node_type=NodeType.START)
    workflow.add_node(start)
    
    if preset == "code_review":
        analyze = Node(
            id="analyze",
            name="分析代码",
            node_type=NodeType.ACTION,
            config={"agent": "code_agent", "action": "analyze"},
        )
        review = Node(
            id="review",
            name="审查代码",
            node_type=NodeType.ACTION,
            config={"agent": "code_agent", "action": "review"},
        )
        report = Node(
            id="report",
            name="生成报告",
            node_type=NodeType.ACTION,
            config={"agent": "code_agent", "action": "report"},
        )
        
        workflow.add_node(analyze).add_node(review).add_node(report)
        workflow.add_edge("start", "analyze")
        workflow.add_edge("analyze", "review")
        workflow.add_edge("review", "report")
    
    elif preset == "data_pipeline":
        extract = Node(
            id="extract",
            name="提取数据",
            node_type=NodeType.ACTION,
            config={"agent": "data_agent", "action": "extract"},
        )
        transform = Node(
            id="transform",
            name="转换数据",
            node_type=NodeType.ACTION,
            config={"agent": "data_agent", "action": "transform"},
        )
        load = Node(
            id="load",
            name="加载数据",
            node_type=NodeType.ACTION,
            config={"agent": "data_agent", "action": "load"},
        )
        validate = Node(
            id="validate",
            name="验证数据",
            node_type=NodeType.ACTION,
            config={"agent": "test_agent", "action": "validate"},
        )
        
        workflow.add_node(extract).add_node(transform).add_node(load).add_node(validate)
        workflow.add_edge("start", "extract")
        workflow.add_edge("extract", "transform")
        workflow.add_edge("transform", "load")
        workflow.add_edge("load", "validate")
    
    elif preset == "research":
        search = Node(
            id="search",
            name="搜索信息",
            node_type=NodeType.ACTION,
            config={"agent": "research_agent", "action": "search"},
        )
        collect = Node(
            id="collect",
            name="收集资料",
            node_type=NodeType.ACTION,
            config={"agent": "research_agent", "action": "collect"},
        )
        analyze = Node(
            id="analyze",
            name="分析总结",
            node_type=NodeType.ACTION,
            config={"agent": "research_agent", "action": "analyze"},
        )
        
        workflow.add_node(search).add_node(collect).add_node(analyze)
        workflow.add_edge("start", "search")
        workflow.add_edge("search", "collect")
        workflow.add_edge("collect", "analyze")
    
    end = Node(id="end", name="结束", node_type=NodeType.END)
    workflow.add_node(end)
    
    last_node = [n for n in workflow.nodes.values() if n.node_type == NodeType.ACTION][-1]
    workflow.add_edge(last_node.id, "end")
    
    return workflow


@workflow_commands.command(name="run")
@click.argument("workflow_id")
@click.option("--var", "variables", multiple=True, help="设置变量 key=value / Set variable")
@click.option("--async", "async_mode", is_flag=True, help="异步执行 / Async execution")
@click.option("--timeout", type=float, default=3600, help="超时时间(秒) / Timeout in seconds")
@click.pass_context
def run_workflow(
    ctx: click.Context,
    workflow_id: str,
    variables: tuple,
    async_mode: bool,
    timeout: float,
) -> None:
    """执行工作流 / Execute workflow"""
    console.print(f"[bold cyan]执行工作流: {workflow_id}[/bold cyan]")
    
    engine = WorkflowEngine()
    workflow_dir = get_workflow_dir()
    
    workflow_file = workflow_dir / f"{workflow_id}.json"
    if not workflow_file.exists():
        for file in workflow_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id", "").startswith(workflow_id):
                        workflow_file = file
                        break
            except Exception:
                continue
    
    if not workflow_file.exists():
        console.print(f"[red]工作流未找到 / Workflow not found: {workflow_id}[/red]")
        return
    
    try:
        with open(workflow_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            workflow = Workflow.from_dict(data)
            engine.register_workflow(workflow)
    except Exception as e:
        console.print(f"[red]加载工作流失败 / Failed to load workflow: {e}[/red]")
        return
    
    initial_vars = {}
    for var in variables:
        if "=" in var:
            key, value = var.split("=", 1)
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
            initial_vars[key] = value
    
    import asyncio
    
    async def _execute():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("执行工作流... / Executing workflow...", total=None)
            
            result = await engine.execute(
                workflow.id,
                initial_variables=initial_vars,
            )
            
            progress.update(task, completed=True)
            
            return result
    
    try:
        result = asyncio.run(_execute())
        
        console.print(f"\n[bold]执行结果 / Execution Result:[/bold]")
        console.print(f"状态: {result.status.value}")
        console.print(f"执行时间: {result.execution_time:.2f}s")
        
        if result.output:
            console.print(f"输出:")
            console.print(json.dumps(result.output, ensure_ascii=False, indent=2))
        
        if result.context and result.context.errors:
            console.print("[red]错误:[/red]")
            for error in result.context.errors:
                console.print(f"  - {error}")
        
    except Exception as e:
        console.print(f"[red]执行失败 / Execution failed: {e}[/red]")


@workflow_commands.command(name="status")
@click.argument("execution_id", required=False)
@click.pass_context
def workflow_status(
    ctx: click.Context,
    execution_id: Optional[str],
) -> None:
    """查看工作流执行状态 / View workflow execution status"""
    console.print("[bold cyan]工作流执行状态 / Workflow Execution Status[/bold cyan]")
    
    if execution_id:
        console.print(f"[dim]执行ID: {execution_id}[/dim]")
    else:
        console.print("[dim]显示最近执行 / Showing recent executions[/dim]")


@workflow_commands.command(name="plan")
@click.argument("task_description")
@click.option("--strategy", type=click.Choice(["sequential", "parallel", "hierarchical", "conditional", "adaptive"]), default="adaptive")
@click.option("--output", "-o", help="输出文件 / Output file")
@click.pass_context
def plan_task(
    ctx: click.Context,
    task_description: str,
    strategy: str,
    output: Optional[str],
) -> None:
    """规划任务 / Plan task"""
    console.print(f"[bold cyan]规划任务: {task_description}[/bold cyan]")
    
    planner = TaskPlanner()
    
    task = Task(
        id="",
        name=task_description,
        description=task_description,
        priority=0,
        metadata={"complexity": 2.0},
    )
    
    strategy_enum = DecompositionStrategy(strategy)
    result = planner.plan(task, strategy=strategy_enum)
    
    if not result.success or not result.plan:
        console.print(f"[red]规划失败 / Planning failed: {result.reasoning}[/red]")
        return
    
    plan = result.plan
    
    console.print(f"\n[bold]执行计划 / Execution Plan:[/bold]")
    console.print(f"名称: {plan.name}")
    console.print(f"策略: {plan.strategy.value}")
    console.print(f"步骤数: {len(plan.steps)}")
    
    table = Table(title="计划步骤 / Plan Steps")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("依赖", style="yellow")
    table.add_column("Agent", style="magenta")
    table.add_column("工作量", style="blue", justify="right")
    
    for step in plan.steps:
        table.add_row(
            step.id,
            step.name,
            ", ".join(step.dependencies) or "无",
            step.assigned_agent or "未分配",
            f"{step.estimated_effort:.1f}",
        )
    
    console.print(table)
    
    effort = planner.estimate_effort(plan)
    console.print(f"\n[dim]预计总工作量 / Estimated effort: {effort:.1f}[/dim]")
    console.print(f"[dim]规划置信度 / Planning confidence: {result.confidence:.2f}[/dim]")
    
    if output:
        try:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)
            console.print(f"[green]计划已保存 / Plan saved: {output}[/green]")
        except Exception as e:
            console.print(f"[red]保存失败 / Save failed: {e}[/red]")


@workflow_commands.command(name="delete")
@click.argument("workflow_id")
@click.confirmation_option(prompt="确定要删除此工作流吗? / Are you sure?")
@click.pass_context
def delete_workflow(
    ctx: click.Context,
    workflow_id: str,
) -> None:
    """删除工作流 / Delete workflow"""
    workflow_dir = get_workflow_dir()
    
    workflow_file = workflow_dir / f"{workflow_id}.json"
    if not workflow_file.exists():
        for file in workflow_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id", "").startswith(workflow_id):
                        workflow_file = file
                        break
            except Exception:
                continue
    
    if not workflow_file.exists():
        console.print(f"[red]工作流未找到 / Workflow not found: {workflow_id}[/red]")
        return
    
    try:
        workflow_file.unlink()
        console.print(f"[green]工作流已删除 / Workflow deleted: {workflow_id}[/green]")
    except Exception as e:
        console.print(f"[red]删除失败 / Delete failed: {e}[/red]")
