"""
/mcp 命令 - 管理MCP服务器 / Manage MCP servers
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def mcp_slash_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理MCP服务器 / Manage MCP servers
    
    用法 / Usage:
        /mcp              - 列出所有服务器 / List all servers
        /mcp add <name>   - 添加服务器 / Add server
        /mcp remove <name> - 移除服务器 / Remove server
    """
    from alonechat.mcp.config import MCPConfigManager
    
    manager = MCPConfigManager()
    
    if not args:
        servers = manager.list_servers()
        
        if not servers:
            console.print("[yellow]未配置MCP服务器 / No MCP servers configured[/yellow]")
            console.print("\n[dim]使用 'alonechat mcp add' 添加服务器 / Use 'alonechat mcp add' to add server[/dim]")
            return
        
        table = Table(title="MCP服务器 / MCP Servers", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("命令 / Command")
        table.add_column("状态 / Status")
        
        for server in servers:
            status = "[green]启用 / Enabled[/green]" if server.enabled else "[yellow]禁用 / Disabled[/yellow]"
            table.add_row(server.name, server.command, status)
        
        console.print(table)
        return
    
    subcommand = args[0]
    
    if subcommand == "list":
        servers = manager.list_servers()
        for server in servers:
            status = "启用" if server.enabled else "禁用"
            console.print(f"  [cyan]{server.name}[/cyan] - {server.command} ({status})")
        return
    
    if subcommand == "enable" and len(args) >= 2:
        name = args[1]
        if manager.enable_server(name):
            console.print(f"[green]✓ 已启用 / Enabled: {name}[/green]")
        else:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
        return
    
    if subcommand == "disable" and len(args) >= 2:
        name = args[1]
        if manager.disable_server(name):
            console.print(f"[green]✓ 已禁用 / Disabled: {name}[/green]")
        else:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
        return
    
    console.print(Panel(
        "[bold cyan]/mcp 命令帮助 / Command Help[/bold cyan]\n\n"
        "用法 / Usage:\n"
        "  /mcp              列出所有服务器 / List all servers\n"
        "  /mcp list         列出服务器详情 / List server details\n"
        "  /mcp enable <n>   启用服务器 / Enable server\n"
        "  /mcp disable <n>  禁用服务器 / Disable server\n\n"
        "[dim]使用 'alonechat mcp' 命令进行完整配置 / Use 'alonechat mcp' for full config[/dim]",
        border_style="cyan"
    ))
