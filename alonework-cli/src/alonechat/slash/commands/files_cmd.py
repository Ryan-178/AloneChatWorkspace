"""
/files 命令 - 列出当前上下文中的文件 / List files in context

版本 / Version: 2.1.80
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _scan_project_files(root: Path = None, max_depth: int = 3) -> list[dict]:
    """
    扫描项目文件 / Scan project files
    """
    root = root or Path.cwd()
    files = []
    ignore_dirs = {
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        ".idea", ".vscode", "dist", "build", ".alonechat",
        ".mypy_cache", ".pytest_cache", ".tox", ".eggs",
    }
    ignore_exts = {".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe"}

    def _walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith(".") and item.name not in (".env",):
                    continue
                if item.is_dir():
                    if item.name not in ignore_dirs:
                        _walk(item, depth + 1)
                elif item.is_file():
                    if item.suffix not in ignore_exts:
                        rel_path = item.relative_to(root)
                        files.append({
                            "path": str(rel_path),
                            "size": item.stat().st_size,
                            "ext": item.suffix,
                        })
        except PermissionError:
            pass

    _walk(root, 0)
    return files


def files_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    列出当前上下文中的文件 / List files in context

    用法 / Usage:
        /files                 列出所有文件 / List all files
        /files list            列出所有文件 / List all files
        /files add <path>      添加文件到上下文 / Add file to context
        /files remove <path>   从上下文移除文件 / Remove file from context
        /files stats           文件统计 / File statistics
        /files search <query>  搜索文件 / Search files
    """
    ctx_files = obj.get("context_files", [])

    if not args or args[0] == "list":
        if ctx_files:
            table = Table(show_header=True, title="上下文文件 / Context Files")
            table.add_column("#", style="dim", width=4)
            table.add_column("文件 / File", style="cyan")
            table.add_column("大小 / Size", style="green")
            table.add_column("类型 / Type", style="yellow")
            for i, f in enumerate(ctx_files, 1):
                path = Path(f) if isinstance(f, str) else f
                size = path.stat().st_size if path.exists() else 0
                size_str = _format_size(size)
                table.add_row(str(i), str(path), size_str, path.suffix or "unknown")
            console.print(table)
        else:
            console.print("[dim]上下文文件列表为空，扫描项目文件...[/dim]")
            console.print("[dim]Context files empty, scanning project files...[/dim]\n")
            project_files = _scan_project_files()
            if project_files:
                table = Table(show_header=True, title="项目文件 / Project Files")
                table.add_column("#", style="dim", width=4)
                table.add_column("文件 / File", style="cyan")
                table.add_column("大小 / Size", style="green")
                table.add_column("类型 / Type", style="yellow")
                for i, f in enumerate(project_files[:50], 1):
                    table.add_row(str(i), f["path"], _format_size(f["size"]), f["ext"])
                if len(project_files) > 50:
                    table.add_row("...", f"还有 {len(project_files) - 50} 个文件 / {len(project_files) - 50} more files", "", "")
                console.print(table)
            else:
                console.print("[yellow]未找到项目文件 / No project files found[/yellow]")
        return

    action = args[0]

    if action == "add":
        if len(args) < 2:
            console.print("[red]请指定文件路径 / Please specify file path[/red]")
            console.print("[dim]用法 / Usage: /files add <path>[/dim]")
            return
        file_path = Path(args[1])
        if not file_path.exists():
            console.print(f"[red]文件不存在 / File not found: {file_path}[/red]")
            return
        if str(file_path) not in [str(f) for f in ctx_files]:
            ctx_files.append(str(file_path))
            obj["context_files"] = ctx_files
            console.print(f"[green]✓ 已添加 / Added: {file_path}[/green]")
        else:
            console.print(f"[yellow]文件已在上下文中 / File already in context: {file_path}[/yellow]")
        return

    if action == "remove":
        if len(args) < 2:
            console.print("[red]请指定文件路径 / Please specify file path[/red]")
            return
        target = args[1]
        original_len = len(ctx_files)
        ctx_files = [f for f in ctx_files if str(f) != target]
        if len(ctx_files) < original_len:
            obj["context_files"] = ctx_files
            console.print(f"[green]✓ 已移除 / Removed: {target}[/green]")
        else:
            console.print(f"[yellow]文件不在上下文中 / File not in context: {target}[/yellow]")
        return

    if action == "stats":
        project_files = _scan_project_files()
        if not project_files:
            console.print("[yellow]未找到文件 / No files found[/yellow]")
            return

        ext_counts = {}
        total_size = 0
        for f in project_files:
            ext = f["ext"] or "no ext"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            total_size += f["size"]

        console.print(Panel(
            f"[bold]项目文件统计 / Project File Stats[/bold]\n"
            f"文件总数 / Total files: {len(project_files)}\n"
            f"总大小 / Total size: {_format_size(total_size)}\n"
            f"上下文文件 / Context files: {len(ctx_files)}",
            border_style="cyan",
        ))

        table = Table(show_header=True, title="按类型统计 / By Type")
        table.add_column("类型 / Type", style="cyan")
        table.add_column("数量 / Count", style="green")
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])[:15]:
            table.add_row(ext, str(count))
        console.print(table)
        return

    if action == "search":
        query = " ".join(args[1:]).lower() if len(args) > 1 else ""
        if not query:
            console.print("[red]请指定搜索词 / Please specify search query[/red]")
            return
        project_files = _scan_project_files()
        matches = [f for f in project_files if query in f["path"].lower()]
        if matches:
            table = Table(show_header=True, title=f"搜索结果 / Search Results: '{query}'")
            table.add_column("文件 / File", style="cyan")
            table.add_column("大小 / Size", style="green")
            for f in matches[:30]:
                table.add_row(f["path"], _format_size(f["size"]))
            console.print(table)
        else:
            console.print(f"[yellow]未找到匹配文件 / No matching files: {query}[/yellow]")
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: list, add, remove, stats, search[/dim]")


def _format_size(size: int) -> str:
    """
    格式化文件大小 / Format file size
    """
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
