"""
/mcp 命令 - 管理MCP服务器 / Manage MCP servers

支持 / Supports:
- /mcp - 列出所有服务器 / List all servers
- /mcp list - 列出服务器详情 / List server details
- /mcp add <name> <cmd> - 添加服务器 / Add server
- /mcp remove <name> - 移除服务器 / Remove server
- /mcp enable <name> - 启用服务器 / Enable server
- /mcp disable <name> - 禁用服务器 / Disable server
- /mcp info <name> - 显示服务器详情 / Show server details
- /mcp oauth <name> --client-id <id> [--client-secret <secret>] - 配置OAuth
- /mcp sse <name> <url> - 配置SSE传输
- /mcp resources [name] - 列出资源 / List resources
- /mcp project - 项目作用域配置 / Project scope
- /mcp instructions <name> - 获取服务器指令 / Get instructions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def mcp_slash_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理MCP服务器 / Manage MCP servers

    用法 / Usage:
        /mcp                      - 列出所有服务器 / List all servers
        /mcp list                 - 列出服务器详情 / List server details
        /mcp add <name> <cmd>     - 添加服务器 / Add server
        /mcp remove <name>        - 移除服务器 / Remove server
        /mcp enable <name>        - 启用服务器 / Enable server
        /mcp disable <name>       - 禁用服务器 / Disable server
        /mcp info <name>          - 显示服务器详情 / Show server details
        /mcp oauth <name> <id>    - 配置OAuth / Configure OAuth
        /mcp sse <name> <url>     - 配置SSE传输 / Configure SSE transport
        /mcp resources [name]     - 列出资源 / List resources
        /mcp project              - 项目作用域 / Project scope
        /mcp instructions <name>  - 获取服务器指令 / Get instructions
    """
    from alonechat.mcp.config import MCPConfigManager, MCPServerConfig

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
        table.add_column("传输 / Transport")
        table.add_column("OAuth")
        table.add_column("状态 / Status")

        for server in servers:
            status = "[green]启用[/green]" if server.enabled else "[yellow]禁用[/yellow]"
            transport = getattr(server, 'transport', 'stdio')
            oauth = "[green]✓[/green]" if getattr(server, 'client_id', None) else "[dim]-[/dim]"
            table.add_row(server.name, server.command, transport, oauth, status)

        console.print(table)
        return

    subcommand = args[0].lower()

    if subcommand == "list":
        servers = manager.list_servers()
        for server in servers:
            transport = getattr(server, 'transport', 'stdio')
            oauth = " OAuth" if getattr(server, 'client_id', None) else ""
            status = "启用" if server.enabled else "禁用"
            console.print(f"  [cyan]{server.name}[/cyan] - {server.command} ({transport}{oauth}, {status})")
        return

    if subcommand == "info" and len(args) >= 2:
        name = args[1]
        server = manager.get_server(name)
        if not server:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
            return

        info = f"[bold cyan]服务器信息 / Server Info: {name}[/bold cyan]\n\n"
        info += f"命令 / Command: {server.command}\n"
        info += f"参数 / Args: {' '.join(server.args) if server.args else '(无 / none)'}\n"
        info += f"传输 / Transport: {getattr(server, 'transport', 'stdio')}\n"
        info += f"URL: {getattr(server, 'url', 'N/A')}\n"

        if server.client_id:
            info += f"OAuth Client ID: {server.client_id}\n"
        if server.oauth_metadata_url:
            info += f"OAuth元数据URL / Metadata URL: {server.oauth_metadata_url}\n"
        if server.instructions:
            info += f"指令 / Instructions: {server.instructions[:200]}...\n"

        info += f"状态 / Status: {'启用 / Enabled' if server.enabled else '禁用 / Disabled'}"
        console.print(Panel(info, border_style="cyan"))
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

    if subcommand == "remove" and len(args) >= 2:
        name = args[1]
        if manager.remove_server(name):
            console.print(f"[green]✓ 已移除 / Removed: {name}[/green]")
        else:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
        return

    if subcommand == "add" and len(args) >= 3:
        name = args[1]
        command = args[2]
        server_args = args[3:]

        server = MCPServerConfig(
            name=name,
            command=command,
            args=list(server_args),
        )
        manager.add_server(server)
        console.print(f"[green]✓ 已添加 / Added: {name} ({command})[/green]")
        return

    if subcommand == "oauth" and len(args) >= 3:
        name = args[1]
        client_id = args[2]
        server = manager.get_server(name)
        if server:
            server.client_id = client_id
            manager.update_server(server)
            console.print(f"[green]✓ 已配置OAuth / OAuth configured: {name}[/green]")
        else:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
        return

    if subcommand == "sse" and len(args) >= 3:
        name = args[1]
        url = args[2]
        server = manager.get_server(name)
        if server:
            server.transport = "sse"
            server.url = url
            manager.update_server(server)
            console.print(f"[green]✓ 已配置SSE传输 / SSE configured: {name}[/green]")
            console.print(f"[dim]   URL: {url}[/dim]")
        else:
            console.print(f"[red]未找到 / Not found: {name}[/red]")
        return

    if subcommand == "resources":
        console.print("[yellow]资源需要在服务器启动后查看 / Resources available after server start[/yellow]")
        return

    if subcommand == "project":
        from agent_framework.deepseek_optimization.mcp_marketplace.config import discover_project_mcp_json
        path = discover_project_mcp_json()
        if path:
            console.print(f"[green]✓ 发现项目作用域MCP配置 / Project-scoped MCP config: {path}[/green]")
        else:
            console.print("[yellow]未找到.mcp.json / No .mcp.json found[/yellow]")
        return

    if subcommand == "instructions" and len(args) >= 2:
        name = args[1]
        server = manager.get_server(name)
        if server and server.instructions:
            console.print(Panel(
                server.instructions,
                title=f"[bold cyan]{name} 指令 / Instructions[/bold cyan]",
                border_style="cyan"
            ))
        else:
            console.print(f"[yellow]无指令 / No instructions for: {name}[/yellow]")
        return

    console.print(Panel(
        "[bold cyan]/mcp 命令帮助 / Command Help[/bold cyan]\n\n"
        "用法 / Usage:\n"
        "  /mcp                            列出所有服务器 / List all servers\n"
        "  /mcp list                       列出服务器详情 / List server details\n"
        "  /mcp add <名称> <命令> [参数...]  添加服务器 / Add server\n"
        "  /mcp remove <名称>              移除服务器 / Remove server\n"
        "  /mcp enable <名称>              启用服务器 / Enable server\n"
        "  /mcp disable <名称>             禁用服务器 / Disable server\n"
        "  /mcp info <名称>                显示服务器详情 / Show server details\n"
        "  /mcp oauth <名称> <client-id>   配置OAuth / Configure OAuth\n"
        "  /mcp sse <名称> <url>           配置SSE传输 / Configure SSE transport\n"
        "  /mcp resources [名称]           列出资源 / List resources\n"
        "  /mcp project                    项目作用域 / Project scope\n"
        "  /mcp instructions <名称>        获取服务器指令 / Get instructions\n\n"
        "[dim]使用 'alonechat mcp' 命令进行完整配置 / Use 'alonechat mcp' for full config[/dim]",
        border_style="cyan"
    ))
