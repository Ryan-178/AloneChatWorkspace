"""
/config å½ä»¤ - æå¼éç½®çé¢ / Open config interface
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def config_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æå¼éç½®çé¢ / Open config interface
    
    ç¨æ³ / Usage: /config [key] [value]
    """
    config_manager = obj.get("config_manager")
    
    if not config_manager:
        console.print("[red]éç½®ç®¡çå¨ä¸å¯ç¨ / Config manager not available[/red]")
        return
    
    if not args:
        config = config_manager.load_config()
        
        table = Table(title="éç½® / Configuration", show_header=True)
        table.add_column("é?/ Key", style="cyan")
        table.add_column("å?/ Value", style="green")
        
        def add_rows(data: dict, prefix: str = ""):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    add_rows(value, full_key)
                else:
                    table.add_row(full_key, str(value))
        
        add_rows(config)
        console.print(table)
        return
    
    if len(args) == 1:
        key = args[0]
        config = config_manager.load_config()
        
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                console.print(f"[red]éç½®é®ä¸å­å¨ / Config key not found: {key}[/red]")
                return
        
        console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")
        return
    
    if len(args) >= 2:
        key = args[0]
        value_str = " ".join(args[1:])
        
        console.print(f"[yellow]è®¾ç½®éç½® / Setting config: {key} = {value_str}[/yellow]")
        console.print("[dim]æ³¨æ: ç´æ¥ä¿®æ¹éç½®åè½å¼åä¸­ / Note: Direct config modification is in development[/dim]")
        return
