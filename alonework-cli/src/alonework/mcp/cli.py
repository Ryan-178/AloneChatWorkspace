"""
MCP CLIå½ä»¤ / MCP CLI Commands

æä¾MCPç¸å³çå½ä»¤è¡æ¥å£ / Provides MCP-related CLI interface

åè½ / Features:
- list: ååºææMCPæå¡å?/ List all MCP servers
- add: æ·»å MCPæå¡å?/ Add MCP server
- remove: ç§»é¤MCPæå¡å?/ Remove MCP server
- enable/disable: å¯ç¨/ç¦ç¨ / Enable/Disable
- start/stop: å¯å¨/åæ­¢ / Start/Stop
- sse: éç½®SSEä¼ è¾ / Configure SSE transport
- oauth: éç½®OAuthå­æ® / Configure OAuth credentials
- resources: ååºæå¡å¨èµæº?/ List server resources
- project: é¡¹ç®ä½ç¨åéç½?/ Project scope config
- lazy-load: å»¶è¿å è½½éç½® / Lazy-load config
- instructions: è·åæå¡å¨æä»?/ Get server instructions
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
    éç½®MCPæå¡å?/ Configure MCP servers

    Model Context Protocol (MCP) åè®¸è¿æ¥å¤é¨å·¥å·åæå?    """
    pass


@mcp_command.command("list")
def mcp_list() -> None:
    """ååºææMCPæå¡å?/ List all MCP servers"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    servers = manager.list_servers()

    if not servers:
        console.print("[yellow]æªéç½®MCPæå¡å?/ No MCP servers configured[/yellow]")
        console.print("\n[dim]ä½¿ç¨ 'alonechat mcp add' æ·»å æå¡å?/ Use 'alonechat mcp add' to add server[/dim]")
        return

    table = Table(title="MCPæå¡å?/ MCP Servers", show_header=True)
    table.add_column("åç§° / Name", style="cyan")
    table.add_column("å½ä»¤ / Command")
    table.add_column("ä¼ è¾ / Transport")
    table.add_column("OAuth")
    table.add_column("ç¶æ?/ Status")

    for server in servers:
        status = "[green]å¯ç¨ / Enabled[/green]" if server.enabled else "[yellow]ç¦ç¨ / Disabled[/yellow]"
        transport = getattr(server, 'transport', 'stdio')
        oauth = "[green]â[/green]" if getattr(server, 'client_id', None) else "[dim]-[/dim]"
        table.add_row(server.name, server.command, transport, oauth, status)

    console.print(table)


@mcp_command.command("add")
@click.argument("name")
@click.argument("command")
@click.option("--args", "-a", multiple=True, help="æå¡å¨åæ?/ Server arguments")
@click.option("--env", "-e", multiple=True, help="ç¯å¢åé (KEY=VALUE) / Environment variables")
@click.option("--transport", "-t", type=click.Choice(["stdio", "sse"]), default="stdio", help="ä¼ è¾ç±»å / Transport type")
@click.option("--url", help="SSEç«¯ç¹URL / SSE endpoint URL (for SSE transport)")
@click.option("--client-id", help="OAuthå®¢æ·ç«¯ID / OAuth client ID")
@click.option("--client-secret", help="OAuthå®¢æ·ç«¯å¯é?/ OAuth client secret")
@click.option("--oauth-metadata-url", help="OAuthåæ°æ®URL (CIMD/SEP-991)")
@click.option("--instructions", help="æå¡å¨æä»?/ Server instructions")
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
    """æ·»å MCPæå¡å?/ Add MCP server"""
    from alonework.mcp.config import MCPConfigManager, MCPServerConfig

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
        features.append("SSEä¼ è¾ / SSE Transport")
    if client_id:
        features.append("OAuth")
    if instructions:
        features.append("æä»¤ / Instructions")

    feature_text = f" ({', '.join(features)})" if features else ""
    console.print(f"[green]â?å·²æ·»å MCPæå¡å?/ MCP server added: {name}{feature_text}[/green]")


@mcp_command.command("remove")
@click.argument("name")
def mcp_remove(name: str) -> None:
    """ç§»é¤MCPæå¡å?/ Remove MCP server"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()

    if manager.remove_server(name):
        console.print(f"[green]â?å·²ç§»é¤MCPæå¡å?/ MCP server removed: {name}[/green]")
    else:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")


@mcp_command.command("enable")
@click.argument("name")
def mcp_enable(name: str) -> None:
    """å¯ç¨MCPæå¡å?/ Enable MCP server"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()

    if manager.enable_server(name):
        console.print(f"[green]â?å·²å¯ç¨MCPæå¡å?/ MCP server enabled: {name}[/green]")
    else:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")


@mcp_command.command("disable")
@click.argument("name")
def mcp_disable(name: str) -> None:
    """ç¦ç¨MCPæå¡å?/ Disable MCP server"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()

    if manager.disable_server(name):
        console.print(f"[green]â?å·²ç¦ç¨MCPæå¡å?/ MCP server disabled: {name}[/green]")
    else:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")


@mcp_command.command("start")
@click.argument("name")
def mcp_start(name: str) -> None:
    """å¯å¨MCPæå¡å?/ Start MCP server"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    console.print(f"[green]â?MCPæå¡å¨å¯å¨è¯·æ±å·²åé?/ MCP server start requested: {name}[/green]")
    console.print("[dim]MCPæå¡å¨å°å¨LLMä¼è¯ä¸­èªå¨å¯å?/ MCP servers auto-start in LLM sessions[/dim]")


@mcp_command.command("stop")
@click.argument("name")
def mcp_stop(name: str) -> None:
    """åæ­¢MCPæå¡å?/ Stop MCP server"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()

    if manager.disable_server(name):
        console.print(f"[green]â?MCPæå¡å¨å·²åæ­¢ / MCP server stopped: {name}[/green]")
    else:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")


@mcp_command.command("sse")
@click.argument("name")
@click.argument("url")
def mcp_sse(name: str, url: str) -> None:
    """
    ä¸ºæå¡å¨éç½®SSEä¼ è¾ / Configure SSE transport for a server

    SSEä¼ è¾åè®¸éè¿HTTPè¿æ¥å°MCPæå¡å?/ SSE transport enables HTTP-based MCP connections
    """
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    server.transport = "sse"
    server.url = url
    manager.update_server(server)

    console.print(f"[green]â?å·²éç½®SSEä¼ è¾ / SSE transport configured: {name}[/green]")
    console.print(f"[dim]   URL: {url}[/dim]")


@mcp_command.command("oauth")
@click.argument("name")
@click.option("--client-id", required=True, help="OAuthå®¢æ·ç«¯ID / OAuth client ID")
@click.option("--client-secret", help="OAuthå®¢æ·ç«¯å¯é?/ OAuth client secret")
@click.option("--metadata-url", help="OAuthåæ°æ®URL (CIMD/SEP-991)")
def mcp_oauth(name: str, client_id: str, client_secret: str | None, metadata_url: str | None) -> None:
    """
    éç½®OAuthå­æ® / Configure OAuth credentials

    ä¸ºä¸æ¯æå¨ææ³¨åçæå¡å¨ï¼å¦Slackï¼æä¾é¢éç½®å­æ®
    """
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    server.client_id = client_id
    server.client_secret = client_secret
    server.oauth_metadata_url = metadata_url
    manager.update_server(server)

    console.print(f"[green]â?å·²éç½®OAuthå­æ® / OAuth credentials configured: {name}[/green]")
    console.print(f"[dim]   Client ID: {client_id}[/dim]")
    if metadata_url:
        console.print(f"[dim]   åæ°æ®URL / Metadata URL: {metadata_url}[/dim]")
    if client_secret:
        console.print("[dim]   å®¢æ·ç«¯å¯é¥å·²è®¾ç½® / Client secret set[/dim]")


@mcp_command.command("resources")
@click.argument("name", required=False)
def mcp_resources(name: str | None) -> None:
    """ååºMCPæå¡å¨èµæº?/ List MCP server resources"""
    console.print("[yellow]èµæºåè¡¨ä»å¨æå¡å¨å¯å¨åå¯ç¨ / Resources available after server start[/yellow]")
    console.print("[dim]å¯å¨æå¡å¨åä½¿ç¨ /mcp resources <name> æ¥ç / Start server then use /mcp resources <name>[/dim]")


@mcp_command.command("project")
def mcp_project() -> None:
    """ç®¡çé¡¹ç®ä½ç¨åMCPéç½® / Manage project-scoped MCP config"""
    from agent_framework.deepseek_optimization.mcp_marketplace.config import discover_project_mcp_json, load_project_mcp_json

    path = discover_project_mcp_json()

    if path:
        console.print(f"[green]â?åç°é¡¹ç®ä½ç¨åMCPéç½®æä»¶ / Project-scoped MCP config found[/green]")
        console.print(f"[dim]   è·¯å¾ / Path: {path}[/dim]")

        servers = load_project_mcp_json(path)
        if servers:
            table = Table(title="é¡¹ç®MCPæå¡å?/ Project MCP Servers", show_header=True)
            table.add_column("åç§° / Name", style="cyan")
            table.add_column("å½ä»¤ / Command")
            table.add_column("ä¼ è¾ / Transport")

            for server in servers:
                transport = getattr(server, 'transport', 'stdio')
                table.add_row(server.name, server.command, transport)

            console.print(table)
        else:
            console.print("[yellow]æªæ¾å°MCPæå¡å¨å®ä¹?/ No MCP server definitions found[/yellow]")
    else:
        console.print("[yellow]æªæ¾å?mcp.jsonæä»¶ / No .mcp.json found[/yellow]")
        console.print("[dim]å¨é¡¹ç®æ ¹ç®å½åå»º.mcp.jsonæ·»å  / Create .mcp.json in project root[/dim]")


@mcp_command.command("lazy-load")
@click.argument("name")
@click.option("--enable/--disable", default=True, help="å¯ç¨/ç¦ç¨å»¶è¿å è½½ / Enable/Disable lazy loading")
@click.option("--threshold", type=float, default=0.1, help="è§¦åéå?(0.0-1.0) / Trigger threshold")
def mcp_lazy_load(name: str, enable: bool, threshold: float) -> None:
    """
    éç½®MCPå·¥å·å»¶è¿å è½½ / Configure MCP tool lazy loading

    å½å·¥å·æè¿°è¶è¿ä¸ä¸æçªå£çéå¼æ¶èªå¨å»¶è¿å è½½
    """
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    server.lazy_load_enabled = enable
    server.lazy_load_threshold = threshold
    manager.update_server(server)

    status = "[green]å·²å¯ç¨[/green]" if enable else "[yellow]å·²ç¦ç¨[/yellow]"
    console.print(f"[green]â?å»¶è¿å è½½éç½®å·²æ´æ?/ Lazy-load config updated: {name}[/green]")
    console.print(f"[dim]   ç¶æ?/ Status: {status}[/dim]")
    console.print(f"[dim]   éå?/ Threshold: {threshold:.0%}[/dim]")


@mcp_command.command("instructions")
@click.argument("name")
def mcp_instructions(name: str) -> None:
    """è·åMCPæå¡å¨æä»?/ Get MCP server instructions"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    if server.instructions:
        console.print(Panel(
            server.instructions,
            title=f"[bold cyan]{name} æå¡å¨æä»?/ Server Instructions[/bold cyan]",
            border_style="cyan"
        ))
    else:
        console.print(f"[yellow]æå¡å¨æªæä¾æä»¤ / Server has no instructions: {name}[/yellow]")
        console.print("[dim]æä»¤å¨æå¡å¨åå§åæ¶æä¾ / Instructions are provided during server initialization[/dim]")


@mcp_command.command("info")
@click.argument("name")
def mcp_info(name: str) -> None:
    """æ¾ç¤ºMCPæå¡å¨è¯¦ç»ä¿¡æ?/ Show detailed MCP server info"""
    from alonework.mcp.config import MCPConfigManager

    manager = MCPConfigManager()
    server = manager.get_server(name)

    if not server:
        console.print(f"[red]æªæ¾å°MCPæå¡å?/ MCP server not found: {name}[/red]")
        return

    info = f"""[bold cyan]æå¡å¨ä¿¡æ?/ Server Info: {name}[/bold cyan]

[bold]åç§° / Name:[/bold] {server.name}
[bold]å½ä»¤ / Command:[/bold] {server.command}
[bold]åæ° / Args:[/bold] {' '.join(server.args) if server.args else '(æ?/ none)'}
[bold]ä¼ è¾ç±»å / Transport:[/bold] {getattr(server, 'transport', 'stdio')}
[bold]URL:[/bold] {getattr(server, 'url', '(æ?/ none)')}
[bold]ç¶æ?/ Status:[/bold] {"[green]å¯ç¨[/green]" if server.enabled else "[yellow]ç¦ç¨[/yellow]"}
"""

    if server.client_id:
        info += f"\n[bold]OAuth Client ID:[/bold] {server.client_id}"
    if server.oauth_metadata_url:
        info += f"\n[bold]OAuthåæ°æ®URL:[/bold] {server.oauth_metadata_url}"
    if server.instructions:
        info += f"\n[bold]æä»¤:[/bold] {server.instructions[:200]}..."

    console.print(Panel(info, border_style="cyan"))
