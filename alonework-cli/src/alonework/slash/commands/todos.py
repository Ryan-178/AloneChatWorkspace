"""
/todos å½ä»¤ - ååºå½åå¾åäºé¡¹ / List current todos

ç®¡çå¾åäºé¡¹åè¡¨ / Manage todo list
çæ¬ / Version: 1.0.94
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json
from datetime import datetime

console = Console()


def todos_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ååºå½åå¾åäºé¡¹ / List current todos
    
    ç¨æ³ / Usage:
        /todos                  ååºææå¾å?/ List all todos
        /todos add <text>       æ·»å å¾å / Add todo
        /todos done <id>        æ è®°å®æ / Mark as done
        /todos delete <id>      å é¤å¾å / Delete todo
        /todos clear            æ¸é¤å·²å®æç / Clear completed
        /todos prioritize       è®¾ç½®ä¼åçº?/ Set priority
    
    ç¤ºä¾ / Examples:
        /todos                  æ¥çåè¡¨ / View list
        /todos add éæç»å½æ¨¡å  æ·»å å¾å / Add todo
        /todos done 1           æ è®°å®æ / Mark done
        /todos delete 2         å é¤ / Delete
    """
    todos_dir = Path.home() / ".alonechat" / "todos"
    todos_dir.mkdir(parents=True, exist_ok=True)
    todos_file = todos_dir / "todos.json"
    
    def _load_todos() -> list[dict]:
        if todos_file.exists():
            try:
                with open(todos_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_todos(todos: list[dict]) -> None:
        with open(todos_file, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
    
    todos = _load_todos()
    
    if not args:
        if not todos:
            console.print("[yellow]ææ å¾åäºé¡¹ / No todos[/yellow]")
            console.print("[dim]ä½¿ç¨ /todos add <text> æ·»å å¾å / Use /todos add <text> to add[/dim]")
            return
        
        active = [t for t in todos if not t.get("completed", False)]
        completed = [t for t in todos if t.get("completed", False)]
        
        if active:
            table = Table(title=f"å¾åäºé¡¹ / Todos ({len(active)} é¡¹å¾å?/ active)", show_header=True)
            table.add_column("ID", style="cyan", width=4)
            table.add_column("åå®¹ / Content")
            table.add_column("ä¼åçº?/ Priority", width=10)
            table.add_column("åå»ºæ¶é´ / Created", style="dim", width=12)
            
            for t in active:
                priority = t.get("priority", "medium")
                priority_styles = {"high": "[red]é«[/red]", "medium": "[yellow]ä¸­[/yellow]", "low": "[dim]ä½[/dim]"}
                created = t.get("created_at", "")[:10]
                table.add_row(str(t["id"]), t["content"], priority_styles.get(priority, priority), created)
            
            console.print(table)
        
        if completed:
            console.print(f"\n[dim]å·²å®æ?/ Completed: {len(completed)} é¡¹[/dim]")
        
        if completed and not active:
            console.print("[yellow]ææå¾åå·²å®æ / All todos completed[/yellow]")
        
        console.print(f"\n[dim]æ»è®¡ / Total: {len(todos)} é¡?(å·²å® / Done: {len(completed)})[/dim]")
        console.print("[dim]ä½¿ç¨ /todos add <text> æ·»å å¾å / Use /todos add <text> to add[/dim]")
        return
    
    subcommand = args[0]
    
    if subcommand == "add" and len(args) >= 2:
        content = " ".join(args[1:])
        
        priority = "medium"
        if len(args) >= 3:
            for p in args[1:]:
                if p in ("--high", "-h"):
                    priority = "high"
                    content = content.replace(p, "").strip()
                elif p in ("--low", "-l"):
                    priority = "low"
                    content = content.replace(p, "").strip()
                elif p in ("--medium", "-m"):
                    priority = "medium"
                    content = content.replace(p, "").strip()
        
        todo_id = max([t["id"] for t in todos], default=0) + 1
        todo = {
            "id": todo_id,
            "content": content,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        todos.append(todo)
        _save_todos(todos)
        
        console.print(f"[green]â?å·²æ·»å å¾å?/ Todo added [#{todo_id}]: {content}[/green]")
        return
    
    if subcommand == "done":
        if len(args) >= 2:
            try:
                todo_id = int(args[1])
            except ValueError:
                console.print("[red]æ æçID / Invalid ID[/red]")
                return
        else:
            console.print("[red]è¯·æå®å¾åID / Please specify todo ID[/red]")
            return
        
        for t in todos:
            if t["id"] == todo_id and not t.get("completed", False):
                t["completed"] = True
                t["completed_at"] = datetime.now().isoformat()
                _save_todos(todos)
                console.print(f"[green]â?å·²å®æ?/ Done: #{todo_id} - {t['content']}[/green]")
                return
        
        console.print(f"[red]å¾åæªæ¾å°æå·²å®æ?/ Todo not found or already done: #{todo_id}[/red]")
        return
    
    if subcommand == "delete":
        if len(args) >= 2:
            try:
                todo_id = int(args[1])
            except ValueError:
                console.print("[red]æ æçID / Invalid ID[/red]")
                return
        else:
            console.print("[red]è¯·æå®å¾åID / Please specify todo ID[/red]")
            return
        
        original_len = len(todos)
        todos = [t for t in todos if t["id"] != todo_id]
        
        if len(todos) < original_len:
            _save_todos(todos)
            console.print(f"[green]â?å·²å é?/ Deleted: #{todo_id}[/green]")
        else:
            console.print(f"[red]å¾åæªæ¾å?/ Todo not found: #{todo_id}[/red]")
        return
    
    if subcommand == "clear":
        completed = [t for t in todos if t.get("completed", False)]
        if not completed:
            console.print("[yellow]æ²¡æå·²å®æçå¾å / No completed todos[/yellow]")
            return
        
        if Confirm.ask(f"æ¸é¤ {len(completed)} ä¸ªå·²å®æçå¾åï¼ / Clear {len(completed)} completed todos?"):
            todos = [t for t in todos if not t.get("completed", False)]
            _save_todos(todos)
            console.print(f"[green]â?å·²æ¸é?{len(completed)} ä¸ªå·²å®æé¡?/ Cleared {len(completed)} completed items[/green]")
        return
    
    if subcommand == "prioritize" and len(args) >= 3:
        try:
            todo_id = int(args[1])
        except ValueError:
            console.print("[red]æ æçID / Invalid ID[/red]")
            return
        
        priority = args[2]
        if priority not in ("high", "medium", "low"):
            console.print("[red]æ æçä¼åçº§ / Invalid priority (high/medium/low)[/red]")
            return
        
        for t in todos:
            if t["id"] == todo_id:
                t["priority"] = priority
                _save_todos(todos)
                console.print(f"[green]â?ä¼åçº§å·²æ´æ° / Priority updated: #{todo_id} -> {priority}[/green]")
                return
        
        console.print(f"[red]å¾åæªæ¾å?/ Todo not found: #{todo_id}[/red]")
        return
    
    console.print(f"[red]æªç¥å­å½ä»?/ Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]å¯ç¨å­å½ä»? add, done, delete, clear, prioritize[/dim]")
