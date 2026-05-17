"""
/help 命令 - 显示帮助信息 / Show help information
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def help_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    显示帮助信息 / Show help information
    
    用法 / Usage: /help [command]
    """
    if args:
        command_name = args[0]
        command = registry.get(command_name)
        
        if command:
            console.print(Panel(
                f"[bold cyan]/{command.name}[/bold cyan]\n\n"
                f"{command.description}\n\n"
                f"[dim]别名 / Aliases: {', '.join(command.aliases) if command.aliases else '无 / None'}[/dim]\n"
                f"[dim]分类 / Category: {command.category}[/dim]",
                title=f"命令帮助 / Command Help: {command.name}",
                border_style="cyan"
            ))
        else:
            console.print(f"[red]未知命令 / Unknown command: {command_name}[/red]")
        return
    
    console.print("\n[bold cyan]Slash 命令 / Slash Commands[/bold cyan]\n")
    
    categories = registry.list_categories()
    
    for category in categories:
        commands = registry.list_commands(category)
        if commands:
            table = Table(title=f"{category}", show_header=True)
            table.add_column("命令 / Command", style="cyan")
            table.add_column("描述 / Description")
            table.add_column("别名 / Aliases", style="dim")
            
            for cmd in commands:
                aliases = ", ".join(f"/{a}" for a in cmd.aliases) if cmd.aliases else "-"
                table.add_row(f"/{cmd.name}", cmd.description, aliases)
            
            console.print(table)
            console.print()
    
    console.print(Panel(
        "[bold]提示 / Tips:[/bold]\n\n"
        "• 输入 /help <command> 查看命令详情 / Type /help <command> for command details\n"
        "• 输入 /status 查看当前状态 / Type /status for current status\n"
        "• 输入 /cost 查看使用统计 / Type /cost for usage statistics\n"
        "• 按 Ctrl+C 中断当前操作 / Press Ctrl+C to interrupt",
        border_style="dim"
    ))
