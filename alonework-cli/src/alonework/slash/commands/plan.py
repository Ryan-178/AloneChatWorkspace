"""
/plan å½ä»¤ - åå»ºæ§è¡è®¡å / Create execution plan

æ¯æå¯éæè¿°åæ?/ Supports optional description parameter
çæ¬ / Version: 2.1.72
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from datetime import datetime

console = Console()


def plan_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    åå»ºæ§è¡è®¡å / Create execution plan
    
    ç¨æ³ / Usage:
        /plan                    åå»ºæ°è®¡å?/ Create new plan
        /plan <description>      åå»ºå¸¦æè¿°çè®¡å / Create plan with description
        /plan list               ååºææè®¡å?/ List all plans
        /plan show <id>          æ¾ç¤ºè®¡åè¯¦æ / Show plan details
        /plan complete <id>      æ è®°è®¡åå®æ / Mark plan as complete
        /plan delete <id>        å é¤è®¡å / Delete plan
    
    ç¤ºä¾ / Examples:
        /plan fix auth bug       åå»ºä¿®å¤è®¤è¯Bugçè®¡å?/ Create plan to fix auth bug
        /plan "éææ°æ®åºå±"      åå»ºéæè®¡å / Create refactoring plan
        /plan list               ååºææè®¡å?/ List all plans
    """
    from alonework.slash.registry import SlashCommandRegistry
    
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
            "[cyan]è®¡åæè¿° / Plan description[/cyan]",
            default=""
        )
        if not description:
            console.print("[yellow]è®¡åæè¿°ä¸è½ä¸ºç©º / Plan description cannot be empty[/yellow]")
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
        
        console.print("\n[bold cyan]æ·»å æ§è¡æ­¥éª¤ / Add execution steps[/bold cyan]")
        console.print("[dim]è¾å¥ç©ºè¡ç»æ / Enter empty line to finish[/dim]\n")
        
        step_num = 1
        while True:
            step = Prompt.ask(f"  [cyan]æ­¥éª¤ {step_num} / Step {step_num}[/cyan]")
            if not step.strip():
                break
            plan["steps"].append({"number": step_num, "content": step, "completed": False})
            step_num += 1
        
        plans.append(plan)
        _save_plans(plans)
        
        console.print(f"\n[green]â?è®¡åå·²åå»?/ Plan created: {plan_id} - {description}[/green]")
        console.print(f"[dim]å?{len(plan['steps'])} ä¸ªæ­¥éª?/ Total {len(plan['steps'])} steps[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        if not plans:
            console.print("[yellow]ææ è®¡å / No plans[/yellow]")
            return
        
        table = Table(title="æ§è¡è®¡å / Execution Plans", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("æè¿° / Description")
        table.add_column("æ­¥éª¤æ?/ Steps", justify="right")
        table.add_column("è¿åº¦ / Progress", justify="right")
        table.add_column("ç¶æ?/ Status")
        table.add_column("åå»ºæ¶é´ / Created", style="dim")
        
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
            console.print(f"[red]è®¡åæªæ¾å?/ Plan not found: {plan_id}[/red]")
            return
        
        console.print(Panel(
            f"[bold cyan]{plan['id']}[/bold cyan]: {plan['description']}\n\n"
            f"[dim]ç¶æ?/ Status: {plan['status']}[/dim]\n"
            f"[dim]åå»ºæ¶é´ / Created: {plan.get('created_at', '')[:16]}[/dim]\n"
            f"[dim]æ´æ°æ¶é´ / Updated: {plan.get('updated_at', '')[:16]}[/dim]\n",
            title="è®¡åè¯¦æ / Plan Details",
            border_style="cyan"
        ))
        
        if plan["steps"]:
            step_table = Table(show_header=True)
            step_table.add_column("#", style="cyan", width=4)
            step_table.add_column("æ­¥éª¤ / Step")
            step_table.add_column("ç¶æ?/ Status", width=12)
            
            for step in plan["steps"]:
                status = "[green]â?å®æ[/green]" if step["completed"] else "[yellow]â?å¾å[/yellow]"
                step_table.add_row(str(step["number"]), step["content"], status)
            
            console.print(step_table)
        return
    
    if subcommand == "complete" and len(args) >= 2:
        plan_id = args[1]
        plan = next((p for p in plans if p["id"] == plan_id), None)
        
        if not plan:
            console.print(f"[red]è®¡åæªæ¾å?/ Plan not found: {plan_id}[/red]")
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
                    console.print(f"[green]â?æ­¥éª¤ {step_to_complete} å·²å®æ?/ Step {step_to_complete} completed[/green]")
                    break
            else:
                console.print(f"[red]æ­¥éª¤æªæ¾å?/ Step not found: {step_to_complete}[/red]")
                return
        else:
            plan["status"] = "completed"
            for step in plan["steps"]:
                step["completed"] = True
            console.print(f"[green]â?è®¡åå·²å®æ?/ Plan completed: {plan_id}[/green]")
        
        plan["updated_at"] = datetime.now().isoformat()
        _save_plans(plans)
        return
    
    if subcommand == "delete" and len(args) >= 2:
        plan_id = args[1]
        original_len = len(plans)
        plans = [p for p in plans if p["id"] != plan_id]
        
        if len(plans) < original_len:
            _save_plans(plans)
            console.print(f"[green]â?è®¡åå·²å é?/ Plan deleted: {plan_id}[/green]")
        else:
            console.print(f"[red]è®¡åæªæ¾å?/ Plan not found: {plan_id}[/red]")
        return
    
    if subcommand == "step" and len(args) >= 2:
        plan_id = args[1]
        plan = next((p for p in plans if p["id"] == plan_id), None)
        
        if not plan:
            console.print(f"[red]è®¡åæªæ¾å?/ Plan not found: {plan_id}[/red]")
            return
        
        step_num = len(plan["steps"]) + 1
        step_content = " ".join(args[2:]) if len(args) > 2 else Prompt.ask(f"[cyan]æ­¥éª¤åå®¹ / Step content[/cyan]")
        
        if step_content:
            plan["steps"].append({"number": step_num, "content": step_content, "completed": False})
            plan["updated_at"] = datetime.now().isoformat()
            _save_plans(plans)
            console.print(f"[green]â?æ­¥éª¤å·²æ·»å?/ Step added: {step_num}[/green]")
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
        
        console.print(f"\n[bold cyan]è®¡å / Plan: {plan_id} - {description}[/bold cyan]")
        console.print("[dim]æ·»å æ§è¡æ­¥éª¤ï¼è¾å¥ç©ºè¡ç»æ?/ Add steps, enter empty line to finish[/dim]\n")
        
        step_num = 1
        while True:
            step = Prompt.ask(f"  [cyan]æ­¥éª¤ {step_num} / Step {step_num}[/cyan]")
            if not step.strip():
                break
            plan["steps"].append({"number": step_num, "content": step, "completed": False})
            step_num += 1
        
        plans.append(plan)
        _save_plans(plans)
        
        console.print(f"\n[green]â?è®¡åå·²åå»?/ Plan created: {plan_id} - {description}[/green]")
        console.print(f"[dim]å?{len(plan['steps'])} ä¸ªæ­¥éª?/ Total {len(plan['steps'])} steps[/dim]")
        return
    
    console.print(f"[red]æªç¥å­å½ä»?/ Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]å¯ç¨å­å½ä»? list, show, complete, delete, step[/dim]")
