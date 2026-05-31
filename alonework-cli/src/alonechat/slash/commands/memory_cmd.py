"""
/memory 命令 - 编辑记忆文件 / Edit memory files

版本 / Version: 2.1.80

套用agent-framework的记忆系统 / Uses agent-framework's memory system
"""

from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

MEMORY_DIR = Path.cwd() / ".alonechat" / "memory"
MEMORY_FILE = MEMORY_DIR / "memories.md"


def _ensure_memory_dir() -> Path:
    """
    确保记忆目录存在 / Ensure memory directory exists
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR


def _load_memories() -> list[dict]:
    """
    加载记忆列表 / Load memories list
    """
    _ensure_memory_dir()
    memories_file = MEMORY_DIR / "memories.yaml"
    if not memories_file.exists():
        return []
    try:
        import yaml
        with open(memories_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("memories", []) if data else []
    except Exception:
        return []


def _save_memories(memories: list[dict]) -> bool:
    """
    保存记忆列表 / Save memories list
    """
    _ensure_memory_dir()
    memories_file = MEMORY_DIR / "memories.yaml"
    try:
        import yaml
        with open(memories_file, "w", encoding="utf-8") as f:
            yaml.dump({"memories": memories}, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        console.print(f"[red]保存失败 / Save failed: {e}[/red]")
        return False


def _load_memory_md() -> str:
    """
    加载记忆Markdown文件 / Load memory Markdown file
    """
    if not MEMORY_FILE.exists():
        return ""
    return MEMORY_FILE.read_text(encoding="utf-8")


def _save_memory_md(content: str) -> bool:
    """
    保存记忆Markdown文件 / Save memory Markdown file
    """
    try:
        _ensure_memory_dir()
        MEMORY_FILE.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        console.print(f"[red]保存失败 / Save failed: {e}[/red]")
        return False


def memory_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    编辑记忆文件 / Edit memory files

    用法 / Usage:
        /memory                 显示所有记忆 / Show all memories
        /memory show            显示所有记忆 / Show all memories
        /memory add <content>   添加记忆 / Add memory
        /memory remove <id>     删除记忆 / Remove memory
        /memory edit            编辑记忆文件 / Edit memory file
        /memory clear           清空所有记忆 / Clear all memories
        /memory search <query>  搜索记忆 / Search memories
        /memory stats           记忆统计 / Memory statistics

    记忆文件位置 / Memory file location:
        .alonechat/memory/memories.md
        .alonechat/memory/memories.yaml
    """
    if not args or args[0] == "show":
        memories = _load_memories()
        md_content = _load_memory_md()

        if not memories and not md_content:
            console.print("[dim]记忆为空 / Memory is empty[/dim]")
            console.print("[dim]使用 /memory add <内容> 添加记忆 / Use /memory add <content> to add[/dim]")
            console.print(f"[dim]记忆目录 / Memory dir: {MEMORY_DIR}[/dim]")
            return

        if memories:
            table = Table(show_header=True, title="记忆列表 / Memory List")
            table.add_column("#", style="dim", width=4)
            table.add_column("内容 / Content", style="cyan")
            table.add_column("时间 / Time", style="green")
            table.add_column("标签 / Tags", style="yellow")
            for i, mem in enumerate(memories, 1):
                content = mem.get("content", "")[:60]
                if len(mem.get("content", "")) > 60:
                    content += "..."
                time_str = mem.get("created_at", "")[:16]
                tags = ", ".join(mem.get("tags", []))
                table.add_row(str(i), content, time_str, tags)
            console.print(table)

        if md_content:
            console.print(Panel(md_content, title="记忆文件 / Memory File", border_style="cyan"))
        return

    action = args[0]

    if action == "add":
        if len(args) < 2:
            console.print("[red]请指定记忆内容 / Please specify memory content[/red]")
            console.print("[dim]用法 / Usage: /memory add <内容 / content>[/dim]")
            return
        content = " ".join(args[1:])
        memories = _load_memories()
        new_memory = {
            "id": len(memories) + 1,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "tags": [],
        }
        memories.append(new_memory)
        if _save_memories(memories):
            console.print(f"[green]✓ 记忆已添加 / Memory added[/green]")
            console.print(f"[dim]{content[:80]}[/dim]")
        return

    if action == "remove":
        if len(args) < 2:
            console.print("[red]请指定记忆ID / Please specify memory ID[/red]")
            return
        try:
            mem_id = int(args[1])
        except ValueError:
            console.print(f"[red]无效ID / Invalid ID: {args[1]}[/red]")
            return
        memories = _load_memories()
        original_len = len(memories)
        memories = [m for m in memories if m.get("id") != mem_id]
        if len(memories) < original_len:
            _save_memories(memories)
            console.print(f"[green]✓ 记忆已删除 / Memory removed: #{mem_id}[/green]")
        else:
            console.print(f"[yellow]未找到记忆 / Memory not found: #{mem_id}[/yellow]")
        return

    if action == "edit":
        console.print(f"[cyan]记忆文件路径 / Memory file path:[/cyan]")
        console.print(f"  YAML: {MEMORY_DIR / 'memories.yaml'}")
        console.print(f"  MD:   {MEMORY_FILE}")
        console.print("[dim]请使用编辑器打开文件进行编辑 / Please open file in editor to edit[/dim]")
        return

    if action == "clear":
        if Confirm.ask("[yellow]确定清空所有记忆？ / Clear all memories?[/yellow]"):
            _save_memories([])
            _save_memory_md("")
            console.print("[green]✓ 所有记忆已清空 / All memories cleared[/green]")
        return

    if action == "search":
        query = " ".join(args[1:]).lower() if len(args) > 1 else ""
        if not query:
            console.print("[red]请指定搜索词 / Please specify search query[/red]")
            return
        memories = _load_memories()
        matches = [m for m in memories if query in m.get("content", "").lower()]
        if matches:
            table = Table(show_header=True, title=f"搜索结果 / Search: '{query}'")
            table.add_column("#", style="dim", width=4)
            table.add_column("内容 / Content", style="cyan")
            table.add_column("时间 / Time", style="green")
            for i, mem in enumerate(matches, 1):
                table.add_row(str(i), mem.get("content", "")[:60], mem.get("created_at", "")[:16])
            console.print(table)
        else:
            console.print(f"[yellow]未找到匹配记忆 / No matching memories: {query}[/yellow]")
        return

    if action == "stats":
        memories = _load_memories()
        md_content = _load_memory_md()
        md_size = len(md_content) if md_content else 0

        console.print(Panel(
            f"[bold]记忆统计 / Memory Stats[/bold]\n"
            f"结构化记忆 / Structured: {len(memories)} 条 / entries\n"
            f"Markdown大小 / MD size: {md_size} 字符 / chars\n"
            f"记忆目录 / Dir: {MEMORY_DIR}",
            border_style="cyan",
        ))
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: show, add, remove, edit, clear, search, stats[/dim]")
