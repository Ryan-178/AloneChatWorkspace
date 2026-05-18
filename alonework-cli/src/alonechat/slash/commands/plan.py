"""
/plan 命令 - 创建执行计划 / Create execution plan

支持可选描述参数 / Supports optional description parameter
版本 / Version: 2.1.72
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from datetime import datetime

console = Console()


def plan_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    创建执行计划 / Create execution plan
    
    用法 / Usage:
        /plan                    创建新计划 / Create new plan
        /plan <description>      创建带描述的计划 / Create plan with description
        /plan list               列出所有计划 / List all plans
        /plan show <id>          显示计划详情 / Show plan details
        /plan complete <id>      标记计划完成 / Mark plan as complete
        /plan delete <id>        删除计划 / Delete plan
    
    示例 / Examples:
        /plan fix auth bug       创建修复认证Bug的计划 / Create plan to fix auth bug
        /plan "重构数据库层"      创建重构计划 / Create refactoring plan
        /plan list               列出所有计划 / List all plans
    """
    from alonechat.slash.registry import SlashCommandRegistry
    
    from pathlib import Path
    import json
    
    plans_dir = Path.home() / ".alonechat" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plans_file = plans_dir / "plans.json"
    
    def _load_plans() -> list[dict]:
        if plans_file.exists():
            try:
                with open(plans_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_plans(plans: list[dict]) -> None:
        with open(plans_file, "w", encoding="utf-8") as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)
    
    def _generate_plan_id(plans: list[dict]) -> str:
        return f"PLAN-{len(plans) + 1:03d}"
    
    plans = _load_plans()
    
    if not args:
        description = Prompt.ask(
            "[cyan]计划描述 / Plan description[/cyan]",
            default=""
        )
        if not description:
            console.print("[yellow]计划描述不能为空 / Plan description cannot be empty[/yellow]")
            return
        
        plan_id = _generate_plan_id(plans)
        now = datetime.now().isoformat()
        
        plan = {
            "id": plan_id,
            "description": description,
            "status": "active",
            "steps": [],
            "created_at": now,
            "updated_at": now,
        }
        
        console.print("\n[bold cyan]添加执行步骤 / Add execution steps[/bold cyan]")
        console.print("[dim]输入空行结束 / Enter empty line to finish[/dim]\n")
        
        step_num = 1
        while True:
            step = Prompt.ask(f"  [cyan]步骤 {step_num} / Step {step_num}[/cyan]")
            if not step.strip():
                break
            plan["steps"].append({"number": step_num, "content": step, "completed": False})
            step_num += 1
        
        plans.append(plan)
        _save_plans(plans)
        
        console.print(f"\n[green]✓ 计划已创建 / Plan created: {plan_id} - {description}[/green]")
        console.print(f"[dim]共 {len(plan['steps'])} 个步骤 / Total {len(plan['steps'])} steps[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        if not plans:
            console.print("[yellow]暂无计划 / No plans[/yellow]")
            return
        
        table = Table(title="执行计划 / Execution Plans", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("描述 / Description")
        table.add_column("步骤数 / Steps", justify="right")
        table.add_column("进度 / Progress", justify="right")
        table.add_column("状态 / Status")
        table.add_column("创建时间 / Created", style="dim")
        
        for plan in plans:
            total = len(plan["steps"])
            completed = sum(1 for s in plan["steps"] if s["completed"])
            progress = f"{completed}/{total}" if total > 0 else "0/0"
            status_style = "green" if plan["status"] == "completed" else "yellow"
            created = plan.get("created_at", "")[:10]
            table.add_row(
                plan["id"],
                plan["description"][:40],
                str(total),
                progress,
                f"[{status_style}]{plan['status']}[/{status_style}]",
                created,
            )
        
        console.print(table)
        return
    
    if subcommand == "show" and len(args) >= 2:
        plan_id = args[1]
        plan = next((p for p in plans if p["id"] == plan_id), None)
        
        if not plan:
            console.print(f"[red]计划未找到 / Plan not found: {plan_id}[/red]")
            return
        
        console.print(Panel(
            f"[bold cyan]{plan['id']}[/bold cyan]: {plan['description']}\n\n"
            f"[dim]状态 / Status: {plan['status']}[/dim]\n"
            f"[dim]创建时间 / Created: {plan.get('created_at', '')[:16]}[/dim]\n"
            f"[dim]更新时间 / Updated: {plan.get('updated_at', '')[:16]}[/dim]\n",
            title="计划详情 / Plan Details",
            border_style="cyan"
        ))
        
        if plan["steps"]:
            step_table = Table(show_header=True)
            step_table.add_column("#", style="cyan", width=4)
            step_table.add_column("步骤 / Step")
            step_table.add_column("状态 / Status", width=12)
            
            for step in plan["steps"]:
                status = "[green]✓ 完成[/green]" if step["completed"] else "[yellow]◻ 待办[/yellow]"
                step_table.add_row(str(step["number"]), step["content"], status)
            
            console.print(step_table)
        return
    
    if subcommand == "complete" and len(args) >= 2:
        plan_id = args[1]
        plan = next((p for p in plans if p["id"] == plan_id), None)
        
        if not plan:
            console.print(f"[red]计划未找到 / Plan not found: {plan_id}[/red]")
            return
        
        step_to_complete = None
        if len(args) >= 3:
            try:
                step_to_complete = int(args[2])
            except ValueError:
                pass
        
        if step_to_complete is not None:
            for step in plan["steps"]:
                if step["number"] == step_to_complete:
                    step["completed"] = True
                    console.print(f"[green]✓ 步骤 {step_to_complete} 已完成 / Step {step_to_complete} completed[/green]")
                    break
            else:
                console.print(f"[red]步骤未找到 / Step not found: {step_to_complete}[/red]")
                return
        else:
            plan["status"] = "completed"
            for step in plan["steps"]:
                step["completed"] = True
            console.print(f"[green]✓ 计划已完成 / Plan completed: {plan_id}[/green]")
        
        plan["updated_at"] = datetime.now().isoformat()
        _save_plans(plans)
        return
    
    if subcommand == "delete" and len(args) >= 2:
        plan_id = args[1]
        original_len = len(plans)
        plans = [p for p in plans if p["id"] != plan_id]
        
        if len(plans) < original_len:
            _save_plans(plans)
            console.print(f"[green]✓ 计划已删除 / Plan deleted: {plan_id}[/green]")
        else:
            console.print(f"[red]计划未找到 / Plan not found: {plan_id}[/red]")
        return
    
    if subcommand == "step" and len(args) >= 2:
        plan_id = args[1]
        plan = next((p for p in plans if p["id"] == plan_id), None)
        
        if not plan:
            console.print(f"[red]计划未找到 / Plan not found: {plan_id}[/red]")
            return
        
        step_num = len(plan["steps"]) + 1
        step_content = " ".join(args[2:]) if len(args) > 2 else Prompt.ask(f"[cyan]步骤内容 / Step content[/cyan]")
        
        if step_content:
            plan["steps"].append({"number": step_num, "content": step_content, "completed": False})
            plan["updated_at"] = datetime.now().isoformat()
            _save_plans(plans)
            console.print(f"[green]✓ 步骤已添加 / Step added: {step_num}[/green]")
        return
    
    if not subcommand.startswith("--"):
        description = " ".join(args)
        plan_id = _generate_plan_id(plans)
        now = datetime.now().isoformat()
        
        plan = {
            "id": plan_id,
            "description": description,
            "status": "active",
            "steps": [],
            "created_at": now,
            "updated_at": now,
        }
        
        console.print(f"\n[bold cyan]计划 / Plan: {plan_id} - {description}[/bold cyan]")
        console.print("[dim]添加执行步骤，输入空行结束 / Add steps, enter empty line to finish[/dim]\n")
        
        step_num = 1
        while True:
            step = Prompt.ask(f"  [cyan]步骤 {step_num} / Step {step_num}[/cyan]")
            if not step.strip():
                break
            plan["steps"].append({"number": step_num, "content": step, "completed": False})
            step_num += 1
        
        plans.append(plan)
        _save_plans(plans)
        
        console.print(f"\n[green]✓ 计划已创建 / Plan created: {plan_id} - {description}[/green]")
        console.print(f"[dim]共 {len(plan['steps'])} 个步骤 / Total {len(plan['steps'])} steps[/dim]")
        return
    
    console.print(f"[red]未知子命令 / Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]可用子命令: list, show, complete, delete, step[/dim]")
