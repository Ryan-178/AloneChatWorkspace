"""
/copy 命令 - 复制最后响应到剪贴板 / Copy last response to clipboard

版本 / Version: 2.1.80
"""

import subprocess
import platform
from rich.console import Console

console = Console()


def _copy_to_clipboard(text: str) -> bool:
    """
    跨平台复制文本到剪贴板 / Cross-platform copy text to clipboard
    """
    system = platform.system()
    try:
        if system == "Windows":
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                shell=True,
            )
            process.communicate(text.encode("utf-16-le"))
            return process.returncode == 0
        elif system == "Darwin":
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
            )
            process.communicate(text.encode("utf-8"))
            return process.returncode == 0
        else:
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                    )
                    process.communicate(text.encode("utf-8"))
                    if process.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except Exception:
        return False


def copy_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    复制最后响应到剪贴板 / Copy last response to clipboard

    用法 / Usage:
        /copy           复制最后一条助手消息 / Copy last assistant message
        /copy N         复制倒数第N条助手消息 / Copy Nth-latest assistant message
    """
    if not session_manager:
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        return

    messages = session_manager.get_messages()
    if not messages:
        console.print("[yellow]当前会话没有消息 / No messages in session[/yellow]")
        return

    n = 1
    if args:
        try:
            n = int(args[0])
            if n < 1:
                raise ValueError
        except ValueError:
            console.print(f"[red]无效参数 / Invalid argument: {args[0]}[/red]")
            console.print("[dim]用法 / Usage: /copy [N] (N为正整数 / N is positive integer)[/dim]")
            return

    assistant_messages = [
        msg for msg in messages
        if msg.get("role") == "assistant" and msg.get("content")
    ]

    if not assistant_messages:
        console.print("[yellow]没有可复制的助手消息 / No assistant messages to copy[/yellow]")
        return

    if n > len(assistant_messages):
        console.print(f"[yellow]只有 {len(assistant_messages)} 条助手消息 / Only {len(assistant_messages)} assistant messages available[/yellow]")
        n = len(assistant_messages)

    target_message = assistant_messages[-n]
    content = target_message.get("content", "")

    if not content.strip():
        console.print("[yellow]目标消息为空 / Target message is empty[/yellow]")
        return

    if _copy_to_clipboard(content):
        preview = content[:80].replace("\n", " ")
        if len(content) > 80:
            preview += "..."
        console.print(f"[green]✓ 已复制到剪贴板 / Copied to clipboard[/green]")
        console.print(f"[dim]预览 / Preview: {preview}[/dim]")
        console.print(f"[dim]长度 / Length: {len(content)} 字符 / chars[/dim]")
    else:
        console.print("[red]复制失败，请检查系统剪贴板权限 / Copy failed, check clipboard permissions[/red]")
        console.print(f"\n[dim]消息内容 / Message content:[/dim]\n{content}")
