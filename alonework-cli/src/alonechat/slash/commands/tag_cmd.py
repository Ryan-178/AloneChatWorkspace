"""
/tag 命令 - 管理会话标签 / Manage session tags

版本 / Version: 2.1.80
"""

import yaml
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

TAGS_DIR = Path.cwd() / ".alonechat" / "tags"


def _load_tags() -> dict:
    """
    加载标签配置 / Load tags configuration
    """
    tags_file = TAGS_DIR / "tags.yaml"
    if not tags_file.exists():
        return {"tags": {}, "sessions": {}}
    try:
        with open(tags_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"tags": {}, "sessions": {}}
    except Exception:
        return {"tags": {}, "sessions": {}}


def _save_tags(data: dict) -> bool:
    """
    保存标签配置 / Save tags configuration
    """
    try:
        TAGS_DIR.mkdir(parents=True, exist_ok=True)
        tags_file = TAGS_DIR / "tags.yaml"
        with open(tags_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception:
        return False


def tag_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理会话标签 / Manage session tags

    用法 / Usage:
        /tag                       列出所有标签 / List all tags
        /tag list                  列出所有标签 / List all tags
        /tag add <tag_name>        为当前会话添加标签 / Add tag to current session
        /tag remove <tag_name>     移除当前会话标签 / Remove tag from current session
        /tag show <tag_name>       显示标签下的会话 / Show sessions with tag
        /tag sessions              显示当前会话的标签 / Show current session tags
        /tag delete <tag_name>     删除标签 / Delete tag
        /tag stats                 标签统计 / Tag statistics
    """
    data = _load_tags()
    tags = data.get("tags", {})
    sessions = data.get("sessions", {})

    session_id = None
    if session_manager and session_manager.current_session:
        session_id = session_manager.current_session.id

    if not args or args[0] == "list":
        if not tags:
            console.print("[dim]没有标签 / No tags[/dim]")
            console.print("[dim]使用 /tag add <名称> 创建标签 / Use /tag add <name> to create[/dim]")
            return

        table = Table(show_header=True, title="标签列表 / Tag List")
        table.add_column("标签 / Tag", style="cyan")
        table.add_column("会话数 / Sessions", style="green")
        table.add_column("颜色 / Color", style="yellow")
        table.add_column("创建时间 / Created", style="dim")

        for tag_name, tag_info in tags.items():
            session_count = sum(
                1 for s_tags in sessions.values()
                if tag_name in (s_tags if isinstance(s_tags, list) else [])
            )
            table.add_row(
                tag_name,
                str(session_count),
                tag_info.get("color", "default"),
                tag_info.get("created_at", "")[:16],
            )

        console.print(table)
        return

    action = args[0]

    if action == "add":
        if len(args) < 2:
            console.print("[red]请指定标签名称 / Please specify tag name[/red]")
            return
        tag_name = args[1].lower()

        if tag_name not in tags:
            tags[tag_name] = {
                "created_at": datetime.now().isoformat(),
                "color": "cyan",
            }

        if session_id:
            if session_id not in sessions:
                sessions[session_id] = []
            if tag_name not in sessions[session_id]:
                sessions[session_id].append(tag_name)
                data["tags"] = tags
                data["sessions"] = sessions
                _save_tags(data)
                console.print(f"[green]✓ 标签已添加 / Tag added: {tag_name}[/green]")
            else:
                console.print(f"[yellow]标签已存在 / Tag already exists: {tag_name}[/yellow]")
        else:
            data["tags"] = tags
            _save_tags(data)
            console.print(f"[green]✓ 标签已创建 / Tag created: {tag_name}[/green]")
        return

    if action == "remove":
        if len(args) < 2:
            console.print("[red]请指定标签名称 / Please specify tag name[/red]")
            return
        tag_name = args[1].lower()
        if session_id and session_id in sessions:
            if tag_name in sessions[session_id]:
                sessions[session_id].remove(tag_name)
                data["sessions"] = sessions
                _save_tags(data)
                console.print(f"[green]✓ 标签已移除 / Tag removed: {tag_name}[/green]")
            else:
                console.print(f"[yellow]会话没有此标签 / Session doesn't have tag: {tag_name}[/yellow]")
        else:
            console.print("[yellow]无活动会话 / No active session[/yellow]")
        return

    if action == "show":
        if len(args) < 2:
            console.print("[red]请指定标签名称 / Please specify tag name[/red]")
            return
        tag_name = args[1].lower()
        tagged_sessions = [
            sid for sid, s_tags in sessions.items()
            if tag_name in (s_tags if isinstance(s_tags, list) else [])
        ]
        if tagged_sessions:
            console.print(f"[cyan]标签 '{tag_name}' 下的会话 / Sessions with tag '{tag_name}':[/cyan]")
            for sid in tagged_sessions:
                console.print(f"  - {sid}")
        else:
            console.print(f"[yellow]没有会话使用此标签 / No sessions with tag: {tag_name}[/yellow]")
        return

    if action == "sessions":
        if session_id and session_id in sessions:
            session_tags = sessions[session_id]
            if session_tags:
                console.print(f"[cyan]当前会话标签 / Current session tags:[/cyan] {', '.join(session_tags)}")
            else:
                console.print("[dim]当前会话没有标签 / Current session has no tags[/dim]")
        else:
            console.print("[dim]无活动会话 / No active session[/dim]")
        return

    if action == "delete":
        if len(args) < 2:
            console.print("[red]请指定标签名称 / Please specify tag name[/red]")
            return
        tag_name = args[1].lower()
        if tag_name in tags:
            del tags[tag_name]
            for sid in sessions:
                if tag_name in sessions[sid]:
                    sessions[sid].remove(tag_name)
            data["tags"] = tags
            data["sessions"] = sessions
            _save_tags(data)
            console.print(f"[green]✓ 标签已删除 / Tag deleted: {tag_name}[/green]")
        else:
            console.print(f"[yellow]标签不存在 / Tag not found: {tag_name}[/yellow]")
        return

    if action == "stats":
        total_tags = len(tags)
        total_sessions = len(sessions)
        tagged_sessions = sum(1 for s_tags in sessions.values() if s_tags)
        console.print(Panel(
            f"[bold]标签统计 / Tag Stats[/bold]\n\n"
            f"标签数 / Tags: {total_tags}\n"
            f"会话数 / Sessions: {total_sessions}\n"
            f"已标记会话 / Tagged: {tagged_sessions}\n"
            f"未标记会话 / Untagged: {total_sessions - tagged_sessions}",
            border_style="cyan",
        ))
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: list, add, remove, show, sessions, delete, stats[/dim]")


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
