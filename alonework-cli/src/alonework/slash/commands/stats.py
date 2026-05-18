"""
/stats 鍛戒护 - 鏄剧ず浣跨敤缁熻 / Show usage statistics

鏀寔鏃ユ湡鑼冨洿杩囨护 / Supports date range filtering:
- /stats 7d    - 杩囧幓7澶?/ Past 7 days
- /stats 30d   - 杩囧幓30澶?/ Past 30 days
- /stats all   - 鍏ㄩ儴鏃堕棿 / All time
"""

from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _parse_date_range(args: list) -> tuple[str, datetime | None]:
    """瑙ｆ瀽鏃ユ湡鑼冨洿鍙傛暟 / Parse date range argument"""
    if not args:
        return "7d", datetime.now(timezone.utc) - timedelta(days=7)

    arg = args[0].lower()

    if arg in ("7d", "7", "week"):
        return "7d", datetime.now(timezone.utc) - timedelta(days=7)
    elif arg in ("30d", "30", "month"):
        return "30d", datetime.now(timezone.utc) - timedelta(days=30)
    elif arg in ("all", "a", "鍏ㄩ儴"):
        return "all", None
    else:
        console.print(f"[yellow]鏈煡鑼冨洿 / Unknown range: {arg}锛屼娇鐢ㄩ粯璁?澶?/ using default 7 days[/yellow]")
        return "7d", datetime.now(timezone.utc) - timedelta(days=7)


def _estimate_tokens(text: str) -> int:
    """浼扮畻token鏁?/ Estimate token count"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def _format_timedelta(delta: timedelta) -> str:
    """鏍煎紡鍖栨椂闂村樊 / Format time delta"""
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days}澶?{hours}灏忔椂"
    return f"{hours}灏忔椂"


def stats_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    鏄剧ず浣跨敤缁熻 / Show usage statistics

    鐢ㄦ硶 / Usage: /stats [7d|30d|all]
    绀轰緥 / Examples:
      /stats       - 杩囧幓7澶?/ Past 7 days
      /stats 30d   - 杩囧幓30澶?/ Past 30 days
      /stats all   - 鍏ㄩ儴鏃堕棿 / All time
    """
    range_name, since = _parse_date_range(args)
    range_labels = {
        "7d": "杩囧幓 7 澶?/ Past 7 days",
        "30d": "杩囧幓 30 澶?/ Past 30 days",
        "all": "鍏ㄩ儴鏃堕棿 / All time",
    }

    console.print(f"\n[bold cyan]浣跨敤缁熻 / Usage Statistics ({range_labels.get(range_name, range_name)})[/bold cyan]\n")

    total_input = 0
    total_output = 0
    total_tokens = 0
    session_count = 0
    total_messages = 0
    messages_by_date: dict[str, int] = {}

    if session_manager:
        sessions = session_manager.list_sessions(limit=1000)
        filtered_sessions = []

        for session in sessions:
            try:
                session_time = datetime.fromisoformat(session.updated_at)
                if session_time.tzinfo is None:
                    session_time = session_time.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                session_time = datetime.now(timezone.utc)

            if since is None or session_time >= since:
                filtered_sessions.append(session)

                session_msg_count = len(session.messages)
                total_messages += session_msg_count

                for msg in session.messages:
                    content = msg.get("content", "")
                    tokens = _estimate_tokens(content)
                    if msg.get("role") == "user":
                        total_input += tokens
                    else:
                        total_output += tokens
                    total_tokens += tokens

                try:
                    date_key = session_time.strftime("%Y-%m-%d")
                    messages_by_date[date_key] = messages_by_date.get(date_key, 0) + session_msg_count
                except (ValueError, AttributeError):
                    pass

        session_count = len(filtered_sessions)
    else:
        console.print("[yellow]鏃犱細璇濈鐞嗗櫒锛屾棤娉曡幏鍙栫粺璁?/ No session manager available[/yellow]")
        return

    summary = Table(show_header=True)
    summary.add_column("鎸囨爣 / Metric", style="cyan")
    summary.add_column("鍊?/ Value", style="green")

    summary.add_row("浼氳瘽鏁?/ Sessions", str(session_count))
    summary.add_row("娑堟伅鏁?/ Messages", str(total_messages))
    summary.add_row("杈撳叆Token / Input tokens", f"{total_input:,}")
    summary.add_row("杈撳嚭Token / Output tokens", f"{total_output:,}")
    summary.add_row("鎬昏Token / Total tokens", f"{total_tokens:,}")

    estimated_cost = total_input * 0.000001 + total_output * 0.000002
    summary.add_row("浼扮畻鎴愭湰 / Estimated cost", f"${estimated_cost:.4f}")

    if range_name != "all":
        if range_name == "7d":
            avg_daily_tokens = total_tokens / 7
            avg_daily_cost = estimated_cost / 7
        else:
            avg_daily_tokens = total_tokens / 30
            avg_daily_cost = estimated_cost / 30
        summary.add_row("鏃ュ潎Token / Avg daily tokens", f"{int(avg_daily_tokens):,}")
        summary.add_row("鏃ュ潎鎴愭湰 / Avg daily cost", f"${avg_daily_cost:.4f}")

    console.print(summary)

    if messages_by_date:
        console.print("\n[bold]姣忔棩娑堟伅瓒嬪娍 / Daily Message Trend[/bold]\n")
        daily_table = Table(show_header=True)
        daily_table.add_column("鏃ユ湡 / Date", style="cyan")
        daily_table.add_column("娑堟伅鏁?/ Messages", style="green")

        sorted_dates = sorted(messages_by_date.keys(), reverse=True)
        for date in sorted_dates[:14]:
            daily_table.add_row(date, str(messages_by_date[date]))

        console.print(daily_table)

    console.print()
