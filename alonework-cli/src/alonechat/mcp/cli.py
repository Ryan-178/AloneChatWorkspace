"""
MCP CLI命令 / MCP CLI Commands

提供MCP相关的命令行接口 / Provides MCP-related CLI interface

功能 / Features:
- list: 列出所有MCP服务器 / List all MCP servers
- add: 添加MCP服务器 / Add MCP server
- remove: 移除MCP服务器 / Remove MCP server
- enable/disable: 启用/禁用 / Enable/Disable
- start/stop: 启动/停止 / Start/Stop
- sse: 配置SSE传输 / Configure SSE transport
- oauth: 配置OAuth凭据 / Configure OAuth credentials
- resources: 列出服务器资源 / List server resources
- project: 项目作用域配置 / Project scope config
- lazy-load: 延迟加载配置 / Lazy-load config
- instructions: 获取服务器指令 / Get server instructions
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

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
    table.add_column("传输 / Transport")
    table.add_column("OAuth")
    table.add_column("状态 / Status")

    for server in servers:
        status = "[green]启用 / Enabled[/green]" if server.enabled else "[yellow]禁用 / Disabled[/yellow]"
        transport = getattr(server, 'transport', 'stdio')
        oauth = "[green]✓[/green]" if getattr(server, 'client_id', None) else "[dim]-[/dim]"
        table.add_row(server.name, server.command, transport, oauth, status)

    console.print(table)


@mcp_command.command("add")
@click.argument("name")
@click.argument("command")
@click.option("--args", "-a", multiple=True, help="服务器参数 / Server arguments")
@click.option("--env", "-e", multiple=True, help="环境变量 (KEY=VALUE) / Environment variables")
@click.option("--transport", "-t", type=click.Choice(["stdio", "sse"]), default="stdio", help="传输类型 / Transport type")
@click.option("--url", help="SSE端点URL / SSE endpoint URL (for SSE transport)")
@click.option("--client-id", help="OAuth客户端ID / OAuth client ID")
@click.option("--client-secret", help="OAuth客户端密钥 / OAuth client secret")
@click.option("--oauth-metadata-url", help="OAuth元数据URL (CIMD/SEP-991)")
@click.option("--instructions", help="服务器指令 / Server instructions")
def mcp_add(
    name: str,
    command: str,
    args: tuple,
    env: tuple,
    transport: str,
    url: str | None,
    client_id: str | None,
    client_secret: str | None,
    oauth_metadata_url: str | None,
    instructions: str | None,
) -> None:
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
        transport=transport,
        url=url,
        client_id=client_id,
        client_secret=client_secret,
        oauth_metadata_url=oauth_metadata_url,
        instructions=instructions,
    )

    manager.add_server(server)

    features = []
    if transport == "sse":
        features.append("SSE传输 / SSE Transport")
    if client_id:
        features.append("OAuth")
    if instructions:
        features.append("指令 / Instructions")

    feature_text = f" ({', '.join(features)})" if features else ""
    console.print(f"[green]✓ 已添加MCP服务器 / MCP server added: {name}{feature_text}[/green]")


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


@mcp_command.command("start")
@click.argument("name")
def mcp_start(name: str) -> None:
    """启动MCP服务器 / Start MCP server"""
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    console.print(f"[green]✓ MCP服务器启动请求已发送 / MCP server start requested: {name}[/green]")
    console.print("[dim]MCP服务器将在LLM会话中自动启动 / MCP servers auto-start in LLM sessions[/dim]")


@mcp_command.command("stop")
@click.argument("name")
def mcp_stop(name: str) -> None:
    """停止MCP服务器 / Stop MCP server"""
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()

    if manager.disable_server(name):
        console.print(f"[green]✓ MCP服务器已停止 / MCP server stopped: {name}[/green]")
    else:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")


@mcp_command.command("sse")
@click.argument("name")
@click.argument("url")
def mcp_sse(name: str, url: str) -> None:
    """
    为服务器配置SSE传输 / Configure SSE transport for a server

    SSE传输允许通过HTTP连接到MCP服务器 / SSE transport enables HTTP-based MCP connections
    """
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    server.transport = "sse"
    server.url = url
    manager.update_server(server)

    console.print(f"[green]✓ 已配置SSE传输 / SSE transport configured: {name}[/green]")
    console.print(f"[dim]   URL: {url}[/dim]")


@mcp_command.command("oauth")
@click.argument("name")
@click.option("--client-id", required=True, help="OAuth客户端ID / OAuth client ID")
@click.option("--client-secret", help="OAuth客户端密钥 / OAuth client secret")
@click.option("--metadata-url", help="OAuth元数据URL (CIMD/SEP-991)")
def mcp_oauth(name: str, client_id: str, client_secret: str | None, metadata_url: str | None) -> None:
    """
    配置OAuth凭据 / Configure OAuth credentials

    为不支持动态注册的服务器（如Slack）提供预配置凭据
    """
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    server.client_id = client_id
    server.client_secret = client_secret
    server.oauth_metadata_url = metadata_url
    manager.update_server(server)

    console.print(f"[green]✓ 已配置OAuth凭据 / OAuth credentials configured: {name}[/green]")
    console.print(f"[dim]   Client ID: {client_id}[/dim]")
    if metadata_url:
        console.print(f"[dim]   元数据URL / Metadata URL: {metadata_url}[/dim]")
    if client_secret:
        console.print("[dim]   客户端密钥已设置 / Client secret set[/dim]")


@mcp_command.command("resources")
@click.argument("name", required=False)
def mcp_resources(name: str | None) -> None:
    """列出MCP服务器资源 / List MCP server resources"""
    console.print("[yellow]资源列表仅在服务器启动后可用 / Resources available after server start[/yellow]")
    console.print("[dim]启动服务器后使用 /mcp resources <name> 查看 / Start server then use /mcp resources <name>[/dim]")


@mcp_command.command("project")
def mcp_project() -> None:
    """管理项目作用域MCP配置 / Manage project-scoped MCP config"""
    from alonechat.deepseek_optimization.mcp_marketplace.config import discover_project_mcp_json, load_project_mcp_json

    path = discover_project_mcp_json()

    if path:
        console.print(f"[green]✓ 发现项目作用域MCP配置文件 / Project-scoped MCP config found[/green]")
        console.print(f"[dim]   路径 / Path: {path}[/dim]")

        servers = load_project_mcp_json(path)
        if servers:
            table = Table(title="项目MCP服务器 / Project MCP Servers", show_header=True)
            table.add_column("名称 / Name", style="cyan")
            table.add_column("命令 / Command")
            table.add_column("传输 / Transport")

            for server in servers:
                transport = getattr(server, 'transport', 'stdio')
                table.add_row(server.name, server.command, transport)

            console.print(table)
        else:
            console.print("[yellow]未找到MCP服务器定义 / No MCP server definitions found[/yellow]")
    else:
        console.print("[yellow]未找到.mcp.json文件 / No .mcp.json found[/yellow]")
        console.print("[dim]在项目根目录创建.mcp.json添加 / Create .mcp.json in project root[/dim]")


@mcp_command.command("lazy-load")
@click.argument("name")
@click.option("--enable/--disable", default=True, help="启用/禁用延迟加载 / Enable/Disable lazy loading")
@click.option("--threshold", type=float, default=0.1, help="触发阈值 (0.0-1.0) / Trigger threshold")
def mcp_lazy_load(name: str, enable: bool, threshold: float) -> None:
    """
    配置MCP工具延迟加载 / Configure MCP tool lazy loading

    当工具描述超过上下文窗口的阈值时自动延迟加载
    """
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    server.lazy_load_enabled = enable
    server.lazy_load_threshold = threshold
    manager.update_server(server)

    status = "[green]已启用[/green]" if enable else "[yellow]已禁用[/yellow]"
    console.print(f"[green]✓ 延迟加载配置已更新 / Lazy-load config updated: {name}[/green]")
    console.print(f"[dim]   状态 / Status: {status}[/dim]")
    console.print(f"[dim]   阈值 / Threshold: {threshold:.0%}[/dim]")


@mcp_command.command("instructions")
@click.argument("name")
def mcp_instructions(name: str) -> None:
    """获取MCP服务器指令 / Get MCP server instructions"""
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    if server.instructions:
        console.print(Panel(
            server.instructions,
            title=f"[bold cyan]{name} 服务器指令 / Server Instructions[/bold cyan]",
            border_style="cyan"
        ))
    else:
        console.print(f"[yellow]服务器未提供指令 / Server has no instructions: {name}[/yellow]")
        console.print("[dim]指令在服务器初始化时提供 / Instructions are provided during server initialization[/dim]")


@mcp_command.command("info")
@click.argument("name")
def mcp_info(name: str) -> None:
    """显示MCP服务器详细信息 / Show detailed MCP server info"""
    from alonechat.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]未找到MCP服务器 / MCP server not found: {name}[/red]")
        return

    info = f"""[bold cyan]服务器信息 / Server Info: {name}[/bold cyan]

[bold]名称 / Name:[/bold] {server.name}
[bold]命令 / Command:[/bold] {server.command}
[bold]参数 / Args:[/bold] {' '.join(server.args) if server.args else '(无 / none)'}
[bold]传输类型 / Transport:[/bold] {getattr(server, 'transport', 'stdio')}
[bold]URL:[/bold] {getattr(server, 'url', '(无 / none)')}
[bold]状态 / Status:[/bold] {"[green]启用[/green]" if server.enabled else "[yellow]禁用[/yellow]"}
"""

    if server.client_id:
        info += f"\n[bold]OAuth Client ID:[/bold] {server.client_id}"
    if server.oauth_metadata_url:
        info += f"\n[bold]OAuth元数据URL:[/bold] {server.oauth_metadata_url}"
    if server.instructions:
        info += f"\n[bold]指令:[/bold] {server.instructions[:200]}..."

    console.print(Panel(info, border_style="cyan"))
