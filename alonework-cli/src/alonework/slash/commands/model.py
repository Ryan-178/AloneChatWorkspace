"""
/model å½ä»¤ - æ¾ç¤ºæ¨¡åä¿¡æ¯ / Show model info

åºå®ä½¿ç¨ DeepSeek V4 Flashï¼ä¸æ¯æåæ¢ / Fixed to DeepSeek V4 Flash, no switching
"""

from rich.console import Console
from rich.table import Table

console = Console()

DEEPSEEK_MODEL = "deepseek-v4-flash"
MODEL_INFO = {
    "name": "DeepSeek V4 Flash",
    "provider": "DeepSeek",
    "context": 1000000,
    "reasoning_effort": "high",
    "cache_hit_rate": "99.91%",
}


def model_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æ¾ç¤ºå½åæ¨¡åä¿¡æ¯ / Show current model info
    
    ç¨æ³ / Usage: /model
    """
    table = Table(title="å½åæ¨¡å / Current Model", show_header=True)
    table.add_column("å±æ?/ Property", style="cyan")
    table.add_column("å?/ Value")
    
    table.add_row("æ¨¡åID / Model ID", DEEPSEEK_MODEL)
    table.add_row("åç§° / Name", MODEL_INFO["name"])
    table.add_row("æä¾å?/ Provider", MODEL_INFO["provider"])
    table.add_row("ä¸ä¸æçªå?/ Context Window", f"{MODEL_INFO['context']:,} tokens")
    table.add_row("æèå¼ºåº?/ Reasoning Effort", MODEL_INFO["reasoning_effort"])
    table.add_row("ç¼å­å½ä¸­ç?/ Cache Hit Rate", MODEL_INFO["cache_hit_rate"])
    
    console.print(table)
    console.print("\n[dim]æ¬å·¥å·åºå®ä½¿ç?DeepSeek V4 Flash æ¨¡å / This tool is fixed to use DeepSeek V4 Flash[/dim]")
    console.print("[dim]æèå¼ºåº¦å·²è®¾ä¸ºæé«?(high) / Reasoning effort is set to maximum (high)[/dim]")
    console.print("[dim]ä¸ä¸æç¼å­èªå¨å¯ç?/ Context caching is auto-enabled[/dim]")
