"""
/model 命令 - 显示模型信息 / Show model info

固定使用 DeepSeek V4 Flash，不支持切换 / Fixed to DeepSeek V4 Flash, no switching
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
    显示当前模型信息 / Show current model info
    
    用法 / Usage: /model
    """
    table = Table(title="当前模型 / Current Model", show_header=True)
    table.add_column("属性 / Property", style="cyan")
    table.add_column("值 / Value")
    
    table.add_row("模型ID / Model ID", DEEPSEEK_MODEL)
    table.add_row("名称 / Name", MODEL_INFO["name"])
    table.add_row("提供商 / Provider", MODEL_INFO["provider"])
    table.add_row("上下文窗口 / Context Window", f"{MODEL_INFO['context']:,} tokens")
    table.add_row("思考强度 / Reasoning Effort", MODEL_INFO["reasoning_effort"])
    table.add_row("缓存命中率 / Cache Hit Rate", MODEL_INFO["cache_hit_rate"])
    
    console.print(table)
    console.print("\n[dim]本工具固定使用 DeepSeek V4 Flash 模型 / This tool is fixed to use DeepSeek V4 Flash[/dim]")
    console.print("[dim]思考强度已设为最高 (high) / Reasoning effort is set to maximum (high)[/dim]")
    console.print("[dim]上下文缓存自动启用 / Context caching is auto-enabled[/dim]")
