"""
MCP CLI命令 / MCP CLI Commands

提供MCP相关的命令行接口 / Provides MCP-related CLI interface
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@click.group()
def mcp_command() -> None:
    """
    配置MCP服务器 / Configure MCP servers
    
    Model Context Protocol (MCP) 允许连接外部工具和服务
    """
    pass


@mcp_command.command("list")
def mcp_list() -> None:
    """列出所有MCP服务器 / List all MCP servers"""
    from alonechat.mcp.config import MCPConfigManager
    
    manager = MCPConfigManager()
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


@mcp_command.command("add")
@click.argument("name")
@click.argument("command")
@click.option("--args", "-a", multiple=True, help="服务器参数 / Server arguments")
@click.option("--env", "-e", multiple=True, help="环境变量 (KEY=VALUE) / Environment variables")
def mcp_add(name: str, command: str, args: tuple, env: tuple) -> None:
    """添加MCP服务器 / Add MCP server"""
    from alonechat.mcp.config import MCPConfigManager, MCPServerConfig
    
    manager = MCPConfigManager()
    
    env_dict = {}
    for e in env:
        if "=" in e:
            key, value = e.split("=", 1)
            env_dict[key] = value
    
    server = MCPServerConfig(
        name=name,
        command=command,
        args=list(args),
        env=env_dict,
        enabled=True,
    )
    
    manager.add_server(server)
    console.print(f"[green]✓ 已添加MCP服务器 / MCP server added: {name}[/green]")


@mcp_command.command("remove")
@click.argument("name")
def mcp_remove(name: str) -> None:
    """移除MCP服务器 / Remove MCP server"""
    from alonechat.mcp.config import MCPConfigManager
    
    manager = MCPConfigManager()
    
    if manager.remove_server(name):
        console.print(f"[green]✓ 已移除MCP服务器 / MCP server removed: {name}[/green]")
    else:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")


@mcp_command.command("enable")
@click.argument("name")
def mcp_enable(name: str) -> None:
    """启用MCP服务器 / Enable MCP server"""
    from alonechat.mcp.config import MCPConfigManager
    
    manager = MCPConfigManager()
    
    if manager.enable_server(name):
        console.print(f"[green]✓ 已启用MCP服务器 / MCP server enabled: {name}[/green]")
    else:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")


@mcp_command.command("disable")
@click.argument("name")
def mcp_disable(name: str) -> None:
    """禁用MCP服务器 / Disable MCP server"""
    from alonechat.mcp.config import MCPConfigManager
    
    manager = MCPConfigManager()
    
    if manager.disable_server(name):
        console.print(f"[green]✓ 已禁用MCP服务器 / MCP server disabled: {name}[/green]")
    else:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
