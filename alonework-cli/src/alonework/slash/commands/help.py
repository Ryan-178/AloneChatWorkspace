"""
/help å½ä»¤ - æ¾ç¤ºå¸®å©ä¿¡æ¯ / Show help information
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def help_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æ¾ç¤ºå¸®å©ä¿¡æ¯ / Show help information
    
    ç¨æ³ / Usage: /help [command]
    """
    if args:
        command_name = args[0]
        command = registry.get(command_name)
        
        if command:
            console.print(Panel(
                f"[bold cyan]/{command.name}[/bold cyan]\n\n"
                f"{command.description}\n\n"
                f"[dim]å«å / Aliases: {', '.join(command.aliases) if command.aliases else 'æ?/ None'}[/dim]\n"
                f"[dim]åç±» / Category: {command.category}[/dim]",
                title=f"å½ä»¤å¸®å© / Command Help: {command.name}",
                border_style="cyan"
            ))
        else:
            console.print(f"[red]æªç¥å½ä»¤ / Unknown command: {command_name}[/red]")
        return
    
    console.print("\n[bold cyan]Slash å½ä»¤ / Slash Commands[/bold cyan]\n")
    
    categories = registry.list_categories()
    
    for category in categories:
        commands = registry.list_commands(category)
        if commands:
            table = Table(title=f"{category}", show_header=True)
            table.add_column("å½ä»¤ / Command", style="cyan")
            table.add_column("æè¿° / Description")
            table.add_column("å«å / Aliases", style="dim")
            
            for cmd in commands:
                aliases = ", ".join(f"/{a}" for a in cmd.aliases) if cmd.aliases else "-"
                table.add_row(f"/{cmd.name}", cmd.description, aliases)
            
            console.print(table)
            console.print()
    
    console.print(Panel(
        "[bold]æç¤º / Tips:[/bold]\n\n"
        "â?è¾å¥ /help <command> æ¥çå½ä»¤è¯¦æ / Type /help <command> for command details\n"
        "â?è¾å¥ /status æ¥çå½åç¶æ?/ Type /status for current status\n"
        "â?è¾å¥ /cost æ¥çä½¿ç¨ç»è®¡ / Type /cost for usage statistics\n"
        "â?æ?Ctrl+C ä¸­æ­å½åæä½ / Press Ctrl+C to interrupt",
        border_style="dim"
    ))
