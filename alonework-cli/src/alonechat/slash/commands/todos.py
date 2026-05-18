"""
/todos 命令 - 列出当前待办事项 / List current todos

管理待办事项列表 / Manage todo list
版本 / Version: 1.0.94
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
    列出当前待办事项 / List current todos
    
    用法 / Usage:
        /todos                  列出所有待办 / List all todos
        /todos add <text>       添加待办 / Add todo
        /todos done <id>        标记完成 / Mark as done
        /todos delete <id>      删除待办 / Delete todo
        /todos clear            清除已完成的 / Clear completed
        /todos prioritize       设置优先级 / Set priority
    
    示例 / Examples:
        /todos                  查看列表 / View list
        /todos add 重构登录模块  添加待办 / Add todo
        /todos done 1           标记完成 / Mark done
        /todos delete 2         删除 / Delete
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
            console.print("[yellow]暂无待办事项 / No todos[/yellow]")
            console.print("[dim]使用 /todos add <text> 添加待办 / Use /todos add <text> to add[/dim]")
            return
        
        active = [t for t in todos if not t.get("completed", False)]
        completed = [t for t in todos if t.get("completed", False)]
        
        if active:
            table = Table(title=f"待办事项 / Todos ({len(active)} 项待办 / active)", show_header=True)
            table.add_column("ID", style="cyan", width=4)
            table.add_column("内容 / Content")
            table.add_column("优先级 / Priority", width=10)
            table.add_column("创建时间 / Created", style="dim", width=12)
            
            for t in active:
                priority = t.get("priority", "medium")
                priority_styles = {"high": "[red]高[/red]", "medium": "[yellow]中[/yellow]", "low": "[dim]低[/dim]"}
                created = t.get("created_at", "")[:10]
                table.add_row(str(t["id"]), t["content"], priority_styles.get(priority, priority), created)
            
            console.print(table)
        
        if completed:
            console.print(f"\n[dim]已完成 / Completed: {len(completed)} 项[/dim]")
        
        if completed and not active:
            console.print("[yellow]所有待办已完成 / All todos completed[/yellow]")
        
        console.print(f"\n[dim]总计 / Total: {len(todos)} 项 (已完 / Done: {len(completed)})[/dim]")
        console.print("[dim]使用 /todos add <text> 添加待办 / Use /todos add <text> to add[/dim]")
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
        
        console.print(f"[green]✓ 已添加待办 / Todo added [#{todo_id}]: {content}[/green]")
        return
    
    if subcommand == "done":
        if len(args) >= 2:
            try:
                todo_id = int(args[1])
            except ValueError:
                console.print("[red]无效的ID / Invalid ID[/red]")
                return
        else:
            console.print("[red]请指定待办ID / Please specify todo ID[/red]")
            return
        
        for t in todos:
            if t["id"] == todo_id and not t.get("completed", False):
                t["completed"] = True
                t["completed_at"] = datetime.now().isoformat()
                _save_todos(todos)
                console.print(f"[green]✓ 已完成 / Done: #{todo_id} - {t['content']}[/green]")
                return
        
        console.print(f"[red]待办未找到或已完成 / Todo not found or already done: #{todo_id}[/red]")
        return
    
    if subcommand == "delete":
        if len(args) >= 2:
            try:
                todo_id = int(args[1])
            except ValueError:
                console.print("[red]无效的ID / Invalid ID[/red]")
                return
        else:
            console.print("[red]请指定待办ID / Please specify todo ID[/red]")
            return
        
        original_len = len(todos)
        todos = [t for t in todos if t["id"] != todo_id]
        
        if len(todos) < original_len:
            _save_todos(todos)
            console.print(f"[green]✓ 已删除 / Deleted: #{todo_id}[/green]")
        else:
            console.print(f"[red]待办未找到 / Todo not found: #{todo_id}[/red]")
        return
    
    if subcommand == "clear":
        completed = [t for t in todos if t.get("completed", False)]
        if not completed:
            console.print("[yellow]没有已完成的待办 / No completed todos[/yellow]")
            return
        
        if Confirm.ask(f"清除 {len(completed)} 个已完成的待办？ / Clear {len(completed)} completed todos?"):
            todos = [t for t in todos if not t.get("completed", False)]
            _save_todos(todos)
            console.print(f"[green]✓ 已清除 {len(completed)} 个已完成项 / Cleared {len(completed)} completed items[/green]")
        return
    
    if subcommand == "prioritize" and len(args) >= 3:
        try:
            todo_id = int(args[1])
        except ValueError:
            console.print("[red]无效的ID / Invalid ID[/red]")
            return
        
        priority = args[2]
        if priority not in ("high", "medium", "low"):
            console.print("[red]无效的优先级 / Invalid priority (high/medium/low)[/red]")
            return
        
        for t in todos:
            if t["id"] == todo_id:
                t["priority"] = priority
                _save_todos(todos)
                console.print(f"[green]✓ 优先级已更新 / Priority updated: #{todo_id} -> {priority}[/green]")
                return
        
        console.print(f"[red]待办未找到 / Todo not found: #{todo_id}[/red]")
        return
    
    console.print(f"[red]未知子命令 / Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]可用子命令: add, done, delete, clear, prioritize[/dim]")
