"""
/export 命令 - 导出对话以便共享 / Export conversation for sharing

支持多种导出格式 / Supports multiple export formats
版本 / Version: 1.0.44
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json
from datetime import datetime

console = Console()


def export_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    导出对话以便共享 / Export conversation for sharing
    
    用法 / Usage:
        /export                   导出当前会话（交互式）/ Export current session (interactive)
        /export <format>          指定格式导出 / Export in specified format
        /export --output <path>   指定输出路径 / Specify output path
        /export list              列出可导出的会话 / List exportable sessions
    
    支持的格式 / Supported formats:
        markdown, md  - Markdown格式 / Markdown format
        json          - JSON格式 / JSON format
        text, txt     - 纯文本格式 / Plain text format
        html          - HTML格式 / HTML format
    
    示例 / Examples:
        /export                       交互式导出 / Interactive export
        /export markdown              导出为Markdown / Export as Markdown
        /export json                  导出为JSON / Export as JSON
        /export text --output chat.txt 导出到指定文件 / Export to specific file
        /export list                  列出会话 / List sessions
    """
    def _get_export_dir() -> Path:
        export_dir = Path.cwd() / ".alonechat" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir
    
    def _get_session_data() -> tuple[list[dict], dict, str]:
        if not session_manager or not session_manager.current_session:
            return [], {}, "no_session"
        
        session = session_manager.current_session
        messages = session_manager.get_messages()
        
        info = {
            "session_id": session.id,
            "display_name": session.get_name(),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(messages),
            "parent_id": session.parent_id,
        }
        
        return messages, info, "ok"
    
    def _export_markdown(messages: list[dict], info: dict) -> str:
        lines = []
        lines.append(f"# 对话导出 / Conversation Export\n")
        lines.append(f"**会话 / Session**: {info.get('display_name', info.get('session_id', '-'))}\n")
        lines.append(f"**日期 / Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"**消息数 / Messages**: {len(messages)}\n")
        lines.append("---\n")
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            role_label = {"user": "**You**", "assistant": "**AloneChat**", "system": "**System**"}.get(role, f"**{role}**")
            
            lines.append(f"### {role_label}")
            if timestamp:
                lines.append(f"*{timestamp[:19]}*\n")
            lines.append(f"{content}\n")
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def _export_json(messages: list[dict], info: dict) -> str:
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "session": info,
            "messages": messages,
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def _export_text(messages: list[dict], info: dict) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"对话导出 / Conversation Export")
        lines.append(f"会话: {info.get('display_name', info.get('session_id', '-'))}")
        lines.append(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"消息数: {len(messages)}")
        lines.append("=" * 60)
        lines.append("")
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            role_label = {"user": "You", "assistant": "AloneChat", "system": "System"}.get(role, role)
            
            lines.append(f"[{role_label}]")
            if timestamp:
                lines.append(f"({timestamp[:19]})")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_html(messages: list[dict], info: dict) -> str:
        msg_html = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            role_class = role if role in ("user", "assistant", "system") else "unknown"
            role_label = {"user": "You", "assistant": "AloneChat", "system": "System"}.get(role, role)
            
            msg_html += f"""
            <div class="message {role_class}">
                <div class="message-header">
                    <span class="role-badge {role_class}">{role_label}</span>
                    <span class="timestamp">{timestamp[:19] if timestamp else ''}</span>
                </div>
                <div class="message-content">{content}</div>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对话导出 / Conversation Export</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .header {{ text-align: center; padding: 20px; background: white; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .header h1 {{ color: #333; font-size: 24px; }}
        .header p {{ color: #666; margin-top: 8px; }}
        .message {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .message.user {{ border-left: 4px solid #4A90D9; }}
        .message.assistant {{ border-left: 4px solid #52C41A; }}
        .message.system {{ border-left: 4px solid #FAAD14; }}
        .message-header {{ display: flex; justify-content: space-between; margin-bottom: 8px; }}
        .role-badge {{ font-size: 12px; padding: 2px 8px; border-radius: 4px; }}
        .role-badge.user {{ background: #E6F7FF; color: #4A90D9; }}
        .role-badge.assistant {{ background: #F6FFED; color: #52C41A; }}
        .role-badge.system {{ background: #FFFBE6; color: #FAAD14; }}
        .timestamp {{ font-size: 12px; color: #999; }}
        .message-content {{ white-space: pre-wrap; line-height: 1.6; color: #333; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>对话导出 / Conversation Export</h1>
        <p>会话 / Session: {info.get('display_name', info.get('session_id', '-'))}</p>
        <p>日期 / Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p>消息数 / Messages: {len(messages)}</p>
    </div>
    {msg_html}
</body>
</html>"""
    
    export_formats = {
        "markdown": {"ext": ".md", "func": _export_markdown, "aliases": ["md"]},
        "json": {"ext": ".json", "func": _export_json, "aliases": []},
        "text": {"ext": ".txt", "func": _export_text, "aliases": ["txt"]},
        "html": {"ext": ".html", "func": _export_html, "aliases": []},
    }
    
    messages, info, status = _get_session_data()
    
    if status == "no_session":
        console.print("[yellow]无活动会话 / No active session[/yellow]")
        console.print("[dim]请先开始对话 / Please start a conversation first[/dim]")
        return
    
    if not messages:
        console.print("[yellow]当前会话没有消息 / Current session has no messages[/yellow]")
        return
    
    output_path = None
    clean_args = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            clean_args.append(arg)
            i += 1
    
    if not clean_args:
        if output_path:
            fmt = output_path.suffix.lstrip(".")
        else:
            fmt = Prompt.ask(
                "[cyan]导出格式 / Export format[/cyan]",
                choices=["markdown", "json", "text", "html"],
                default="markdown",
            )
    else:
        fmt = clean_args[0]
    
    fmt_key = None
    for key, fmt_info in export_formats.items():
        if fmt == key or fmt in fmt_info.get("aliases", []):
            fmt_key = key
            break
    
    if not fmt_key:
        console.print(f"[red]不支持的格式 / Unsupported format: {fmt}[/red]")
        console.print("[dim]支持的格式: " + ", ".join(export_formats.keys()) + "[/dim]")
        return
    
    fmt_info = export_formats[fmt_key]
    content = fmt_info["func"](messages, info)
    
    if not output_path:
        session_name = info.get("display_name", info.get("session_id", "chat"))[:20]
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in session_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}{fmt_info['ext']}"
        output_path = _get_export_dir() / filename
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    
    console.print(f"\n[green]✓ 对话已导出 / Conversation exported[/green]")
    console.print(f"[dim]文件 / File: {output_path}[/dim]")
    console.print(f"[dim]格式 / Format: {fmt_key}[/dim]")
    console.print(f"[dim]大小 / Size: {len(content):,} 字符 / chars[/dim]")
    console.print(f"[dim]消息数 / Messages: {len(messages)}[/dim]")
