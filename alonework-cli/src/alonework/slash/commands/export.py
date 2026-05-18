"""
/export å½ä»¤ - å¯¼åºå¯¹è¯ä»¥ä¾¿å±äº« / Export conversation for sharing

æ¯æå¤ç§å¯¼åºæ ¼å¼ / Supports multiple export formats
çæ¬ / Version: 1.0.44
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
    å¯¼åºå¯¹è¯ä»¥ä¾¿å±äº« / Export conversation for sharing
    
    ç¨æ³ / Usage:
        /export                   å¯¼åºå½åä¼è¯ï¼äº¤äºå¼ï¼? Export current session (interactive)
        /export <format>          æå®æ ¼å¼å¯¼åº / Export in specified format
        /export --output <path>   æå®è¾åºè·¯å¾ / Specify output path
        /export list              ååºå¯å¯¼åºçä¼è¯ / List exportable sessions
    
    æ¯æçæ ¼å¼?/ Supported formats:
        markdown, md  - Markdownæ ¼å¼ / Markdown format
        json          - JSONæ ¼å¼ / JSON format
        text, txt     - çº¯ææ¬æ ¼å¼?/ Plain text format
        html          - HTMLæ ¼å¼ / HTML format
    
    ç¤ºä¾ / Examples:
        /export                       äº¤äºå¼å¯¼å?/ Interactive export
        /export markdown              å¯¼åºä¸ºMarkdown / Export as Markdown
        /export json                  å¯¼åºä¸ºJSON / Export as JSON
        /export text --output chat.txt å¯¼åºå°æå®æä»?/ Export to specific file
        /export list                  ååºä¼è¯ / List sessions
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
        lines.append(f"# å¯¹è¯å¯¼åº / Conversation Export\n")
        lines.append(f"**ä¼è¯ / Session**: {info.get('display_name', info.get('session_id', '-'))}\n")
        lines.append(f"**æ¥æ / Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        lines.append(f"**æ¶æ¯æ?/ Messages**: {len(messages)}\n")
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
        lines.append(f"å¯¹è¯å¯¼åº / Conversation Export")
        lines.append(f"ä¼è¯: {info.get('display_name', info.get('session_id', '-'))}")
        lines.append(f"æ¥æ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"æ¶æ¯æ? {len(messages)}")
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
    <title>å¯¹è¯å¯¼åº / Conversation Export</title>
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
        <h1>å¯¹è¯å¯¼åº / Conversation Export</h1>
        <p>ä¼è¯ / Session: {info.get('display_name', info.get('session_id', '-'))}</p>
        <p>æ¥æ / Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p>æ¶æ¯æ?/ Messages: {len(messages)}</p>
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
        console.print("[yellow]æ æ´»å¨ä¼è¯?/ No active session[/yellow]")
        console.print("[dim]è¯·åå¼å§å¯¹è¯?/ Please start a conversation first[/dim]")
        return
    
    if not messages:
        console.print("[yellow]å½åä¼è¯æ²¡ææ¶æ¯ / Current session has no messages[/yellow]")
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
                "[cyan]å¯¼åºæ ¼å¼ / Export format[/cyan]",
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
        console.print(f"[red]ä¸æ¯æçæ ¼å¼ / Unsupported format: {fmt}[/red]")
        console.print("[dim]æ¯æçæ ¼å¼? " + ", ".join(export_formats.keys()) + "[/dim]")
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
    
    console.print(f"\n[green]â?å¯¹è¯å·²å¯¼å?/ Conversation exported[/green]")
    console.print(f"[dim]æä»¶ / File: {output_path}[/dim]")
    console.print(f"[dim]æ ¼å¼ / Format: {fmt_key}[/dim]")
    console.print(f"[dim]å¤§å° / Size: {len(content):,} å­ç¬¦ / chars[/dim]")
    console.print(f"[dim]æ¶æ¯æ?/ Messages: {len(messages)}[/dim]")
