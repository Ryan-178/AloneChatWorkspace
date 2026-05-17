"""
/model 命令 - 切换模型 / Switch model
"""

from rich.console import Console
from rich.table import Table

console = Console()

AVAILABLE_MODELS = {
    "deepseek-v4-flash": {
        "name": "DeepSeek V4 Flash",
        "provider": "deepseek",
        "context": 1000000,
    },
    "deepseek-v3": {
        "name": "DeepSeek V3",
        "provider": "deepseek",
        "context": 64000,
    },
}


def model_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    切换模型 / Switch model
    
    用法 / Usage: /model [model-name]
    """
    if not args:
        current_model = obj.get("model_name", "deepseek-v4-flash")
        
        table = Table(title="可用模型 / Available Models", show_header=True)
        table.add_column("模型 / Model", style="cyan")
        table.add_column("名称 / Name")
        table.add_column("上下文 / Context")
        table.add_column("状态 / Status")
        
        for model_id, info in AVAILABLE_MODELS.items():
            status = "[green]当前 / Current[/green]" if model_id == current_model else ""
            table.add_row(
                model_id,
                info["name"],
                f"{info['context']:,}",
                status
            )
        
        console.print(table)
        console.print("\n[dim]使用 /model <model-id> 切换模型 / Use /model <model-id> to switch[/dim]")
        return
    
    model_name = args[0]
    
    if model_name not in AVAILABLE_MODELS:
        console.print(f"[red]未知模型 / Unknown model: {model_name}[/red]")
        console.print(f"[dim]可用模型 / Available models: {', '.join(AVAILABLE_MODELS.keys())}[/dim]")
        return
    
    obj["model_name"] = model_name
    info = AVAILABLE_MODELS[model_name]
    
    console.print(f"[green]✓ 已切换模型 / Switched to model: {info['name']}[/green]")
    console.print(f"[dim]上下文窗口 / Context window: {info['context']:,} tokens[/dim]")
