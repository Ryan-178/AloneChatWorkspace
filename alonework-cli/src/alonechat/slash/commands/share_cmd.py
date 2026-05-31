"""
/share 命令 - 分享会话 / Share session

版本 / Version: 2.1.80
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

SHARE_DIR = Path.cwd() / ".alonechat" / "shared"


def share_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    分享会话 / Share session

    用法 / Usage:
        /share                  交互式分享 / Interactive share
        /share file             生成分享文件 / Generate share file
        /share clipboard        复制到剪贴板 / Copy to clipboard
        /share link             生成分享链接 / Generate share link
        /share list             列出已分享会话 / List shared sessions

    示例 / Examples:
        /share
        /share file
        /share clipboard
    """
    if not session_manager or not session_manager.current_session:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return

    session = session_manager.current_session
    messages = session_manager.get_messages()

    if not messages:
        console.print("[yellow]当前会话没有消息 / No messages in session[/yellow]")
        return

    if not args or args[0] == "file":
        SHARE_DIR.mkdir(parents=True, exist_ok=True)

        session_name = session.get_name() if hasattr(session, "get_name") else session.id[:12]
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in session_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shared_{safe_name}_{timestamp}.md"
        filepath = SHARE_DIR / filename

        lines = []
        lines.append(f"# 分享会话 / Shared Session\n")
        lines.append(f"**会话 / Session**: {session_name}\n")
        lines.append(f"**日期 / Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"**消息数 / Messages**: {len(messages)}\n")
        lines.append("---\n")

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            label = {"user": "**You**", "assistant": "**AloneChat**"}.get(role, f"**{role}**")
            lines.append(f"### {label}\n")
            lines.append(f"{content}\n")
            lines.append("---\n")

        content = "\n".join(lines)
        filepath.write_text(content, encoding="utf-8")

        console.print(f"[green]✓ 会话已导出为分享文件 / Session exported as share file[/green]")
        console.print(f"[dim]文件 / File: {filepath}[/dim]")
        console.print(f"[dim]大小 / Size: {len(content):,} 字符 / chars[/dim]")
        return

    if args[0] == "clipboard":
        from alonechat.slash.commands.copy import _copy_to_clipboard

        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            label = {"user": "You", "assistant": "AloneChat"}.get(role, role)
            lines.append(f"[{label}]")
            lines.append(content)
            lines.append("")

        text = "\n".join(lines)
        if _copy_to_clipboard(text):
            console.print(f"[green]✓ 会话已复制到剪贴板 / Session copied to clipboard[/green]")
            console.print(f"[dim]长度 / Length: {len(text)} 字符 / chars[/dim]")
        else:
            console.print("[red]复制失败 / Copy failed[/red]")
        return

    if args[0] == "link":
        session_data = json.dumps({
            "id": session.id,
            "name": session.get_name() if hasattr(session, "get_name") else "",
            "messages": len(messages),
        }, ensure_ascii=False)
        share_hash = hashlib.md5(session_data.encode()).hexdigest()[:8]
        console.print(Panel(
            f"[bold]分享链接 / Share Link[/bold]\n\n"
            f"会话ID / Session ID: {session.id}\n"
            f"分享码 / Share code: {share_hash}\n\n"
            f"[dim]注意: 分享链接功能需要服务端支持[/dim]\n"
            f"[dim]Note: Share link requires server support[/dim]",
            border_style="cyan",
        ))
        return

    if args[0] == "list":
        if not SHARE_DIR.exists():
            console.print("[dim]没有已分享的会话 / No shared sessions[/dim]")
            return
        files = sorted(SHARE_DIR.glob("shared_*.md"), reverse=True)
        if not files:
            console.print("[dim]没有已分享的会话 / No shared sessions[/dim]")
            return
        console.print("[bold cyan]已分享会话 / Shared Sessions[/bold cyan]\n")
        for f in files[:10]:
            size = f.stat().st_size
            console.print(f"  {f.name} ({size / 1024:.1f} KB)")
        return

    console.print(f"[red]未知操作 / Unknown action: {args[0]}[/red]")
    console.print("[dim]可用操作 / Available: file, clipboard, link, list[/dim]")
