"""
/feedback 命令 - 发送反馈 / Send feedback

版本 / Version: 2.1.80
"""

import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

FEEDBACK_DIR = Path.cwd() / ".alonechat" / "feedback"


def _save_feedback(feedback_type: str, content: str, rating: int = 0) -> Path:
    """
    保存反馈 / Save feedback
    """
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"feedback_{timestamp}.json"
    filepath = FEEDBACK_DIR / filename

    data = {
        "type": feedback_type,
        "content": content,
        "rating": rating,
        "timestamp": datetime.now().isoformat(),
    }

    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath


def feedback_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    发送反馈 / Send feedback

    用法 / Usage:
        /feedback               交互式反馈 / Interactive feedback
        /feedback <message>     快速反馈 / Quick feedback
        /feedback bug <desc>    报告bug / Report bug
        /feedback feature <desc> 功能建议 / Feature request
        /feedback praise <msg>  好评 / Positive feedback
        /feedback list          查看历史反馈 / View feedback history
        /feedback rate <1-5>    评分 / Rate

    示例 / Examples:
        /feedback 挺好用的！
        /feedback bug 命令执行报错
        /feedback feature 希望支持多语言
        /feedback rate 5
    """
    if not args:
        console.print(Panel(
            "[bold]反馈系统 / Feedback System[/bold]\n\n"
            "类型 / Types:\n"
            "  bug      - 报告问题 / Report issue\n"
            "  feature  - 功能建议 / Feature request\n"
            "  praise   - 好评鼓励 / Positive feedback\n"
            "  other    - 其他反馈 / Other feedback\n\n"
            "用法 / Usage:\n"
            "  /feedback <消息 / message>      快速反馈 / Quick feedback\n"
            "  /feedback bug <描述 / desc>     报告bug / Report bug\n"
            "  /feedback feature <描述 / desc> 功能建议 / Feature request\n"
            "  /feedback list                  历史反馈 / History\n"
            "  /feedback rate <1-5>            评分 / Rate",
            border_style="cyan",
        ))
        return

    action = args[0]

    if action == "list":
        if not FEEDBACK_DIR.exists():
            console.print("[dim]没有反馈记录 / No feedback records[/dim]")
            return

        files = sorted(FEEDBACK_DIR.glob("feedback_*.json"), reverse=True)
        if not files:
            console.print("[dim]没有反馈记录 / No feedback records[/dim]")
            return

        console.print("[bold cyan]反馈历史 / Feedback History[/bold cyan]\n")
        for f in files[:10]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                fb_type = data.get("type", "other")
                content = data.get("content", "")[:50]
                rating = data.get("rating", 0)
                time_str = data.get("timestamp", "")[:16]
                rating_str = f" {'★' * rating}{'☆' * (5 - rating)}" if rating else ""
                console.print(f"  [{fb_type}] {time_str}{rating_str}")
                console.print(f"    {content}")
            except Exception:
                pass
        return

    if action == "rate":
        if len(args) < 2:
            console.print("[red]请指定评分(1-5) / Please specify rating(1-5)[/red]")
            return
        try:
            rating = int(args[1])
            if not 1 <= rating <= 5:
                raise ValueError
        except ValueError:
            console.print("[red]评分范围1-5 / Rating range: 1-5[/red]")
            return
        content = " ".join(args[2:]) if len(args) > 2 else ""
        filepath = _save_feedback("rating", content, rating)
        stars = "★" * rating + "☆" * (5 - rating)
        console.print(f"[green]✓ 感谢评分 / Thanks for rating: {stars}[/green]")
        console.print(f"[dim]已保存 / Saved: {filepath.name}[/dim]")
        return

    if action in ("bug", "feature", "praise"):
        content = " ".join(args[1:])
        if not content:
            console.print(f"[red]请描述详情 / Please describe details[/red]")
            return
        filepath = _save_feedback(action, content)
        type_labels = {
            "bug": "Bug报告 / Bug Report",
            "feature": "功能建议 / Feature Request",
            "praise": "好评 / Praise",
        }
        console.print(f"[green]✓ 反馈已提交 / Feedback submitted: {type_labels[action]}[/green]")
        console.print(f"[dim]{content[:80]}[/dim]")
        console.print(f"[dim]已保存 / Saved: {filepath.name}[/dim]")
        return

    content = " ".join(args)
    filepath = _save_feedback("general", content)
    console.print(f"[green]✓ 反馈已提交 / Feedback submitted[/green]")
    console.print(f"[dim]{content[:80]}[/dim]")
    console.print(f"[dim]已保存 / Saved: {filepath.name}[/dim]")
