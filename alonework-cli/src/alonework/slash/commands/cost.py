"""
/cost 鍛戒护 - 鏄剧ずtoken浣跨敤缁熻 / Show token usage statistics
"""

from rich.console import Console
from rich.table import Table
from pathlib import Path
import json

console = Console()


def cost_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    鏄剧ずtoken浣跨敤缁熻 / Show token usage statistics
    
    鐢ㄦ硶 / Usage: /cost
    """
    total_input = 0
    total_output = 0
    total_tokens = 0
    session_count = 0
    
    if session_manager:
        sessions = session_manager.list_sessions(limit=100)
        session_count = len(sessions)
        
        for session in sessions:
            for msg in session.messages:
                content = msg.get("content", "")
                tokens = len(content) // 4
                
                if msg.get("role") == "user":
                    total_input += tokens
                else:
                    total_output += tokens
                total_tokens += tokens
    
    console.print("\n[bold cyan]Token 浣跨敤缁熻 / Token Usage Statistics[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("鎸囨爣 / Metric", style="cyan")
    table.add_column("鍊?/ Value", style="green")
    
    table.add_row("浼氳瘽鏁?/ Sessions", str(session_count))
    table.add_row("杈撳叆tokens / Input tokens", f"{total_input:,}")
    table.add_row("杈撳嚭tokens / Output tokens", f"{total_output:,}")
    table.add_row("鎬昏tokens / Total tokens", f"{total_tokens:,}")
    
    estimated_cost = (total_input * 0.000001 + total_output * 0.000002)
    table.add_row("浼扮畻鎴愭湰 / Estimated cost", f"${estimated_cost:.4f}")
    
    console.print(table)
    console.print()
