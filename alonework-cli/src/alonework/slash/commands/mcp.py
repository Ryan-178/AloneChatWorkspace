"""
/mcp å½ä»¤ - ç®¡çMCPæå¡å?/ Manage MCP servers

æ¯æ / Supports:
- /mcp - ååºæææå¡å¨ / List all servers
- /mcp list - ååºæå¡å¨è¯¦æ?/ List server details
- /mcp add <name> <cmd> - æ·»å æå¡å?/ Add server
- /mcp remove <name> - ç§»é¤æå¡å?/ Remove server
- /mcp enable <name> - å¯ç¨æå¡å?/ Enable server
- /mcp disable <name> - ç¦ç¨æå¡å?/ Disable server
- /mcp info <name> - æ¾ç¤ºæå¡å¨è¯¦æ?/ Show server details
- /mcp oauth <name> --client-id <id> [--client-secret <secret>] - éç½®OAuth
- /mcp sse <name> <url> - éç½®SSEä¼ è¾
- /mcp resources [name] - ååºèµæº / List resources
- /mcp project - é¡¹ç®ä½ç¨åéç½?/ Project scope
- /mcp instructions <name> - è·åæå¡å¨æä»?/ Get instructions
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def mcp_slash_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ç®¡çMCPæå¡å?/ Manage MCP servers

    ç¨æ³ / Usage:
        /mcp                      - ååºæææå¡å¨ / List all servers
        /mcp list                 - ååºæå¡å¨è¯¦æ?/ List server details
        /mcp add <name> <cmd>     - æ·»å æå¡å?/ Add server
        /mcp remove <name>        - ç§»é¤æå¡å?/ Remove server
        /mcp enable <name>        - å¯ç¨æå¡å?/ Enable server
        /mcp disable <name>       - ç¦ç¨æå¡å?/ Disable server
        /mcp info <name>          - æ¾ç¤ºæå¡å¨è¯¦æ?/ Show server details
        /mcp oauth <name> <id>    - éç½®OAuth / Configure OAuth
        /mcp sse <name> <url>     - éç½®SSEä¼ è¾ / Configure SSE transport
        /mcp resources [name]     - ååºèµæº / List resources
        /mcp project              - é¡¹ç®ä½ç¨å?/ Project scope
        /mcp instructions <name>  - è·åæå¡å¨æä»?/ Get instructions
    """
    from alonework.mcp.config import MCPConfigManager, MCPServerConfig

    manager = MCPConfigManager()

    if not args:
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
            status = "[green]å¯ç¨[/green]" if server.enabled else "[yellow]ç¦ç¨[/yellow]"
            transport = getattr(server, 'transport', 'stdio')
            oauth = "[green]â[/green]" if getattr(server, 'client_id', None) else "[dim]-[/dim]"
            table.add_row(server.name, server.command, transport, oauth, status)

        console.print(table)
        return

    subcommand = args[0].lower()

    if subcommand == "list":
        servers = manager.list_servers()
        for server in servers:
            transport = getattr(server, 'transport', 'stdio')
            oauth = " OAuth" if getattr(server, 'client_id', None) else ""
            status = "å¯ç¨" if server.enabled else "ç¦ç¨"
            console.print(f"  [cyan]{server.name}[/cyan] - {server.command} ({transport}{oauth}, {status})")
        return

    if subcommand == "info" and len(args) >= 2:
        name = args[1]
        server = manager.get_server(name)
        if not server:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
            return

        info = f"[bold cyan]æå¡å¨ä¿¡æ?/ Server Info: {name}[/bold cyan]\n\n"
        info += f"å½ä»¤ / Command: {server.command}\n"
        info += f"åæ° / Args: {' '.join(server.args) if server.args else '(æ?/ none)'}\n"
        info += f"ä¼ è¾ / Transport: {getattr(server, 'transport', 'stdio')}\n"
        info += f"URL: {getattr(server, 'url', 'N/A')}\n"

        if server.client_id:
            info += f"OAuth Client ID: {server.client_id}\n"
        if server.oauth_metadata_url:
            info += f"OAuthåæ°æ®URL / Metadata URL: {server.oauth_metadata_url}\n"
        if server.instructions:
            info += f"æä»¤ / Instructions: {server.instructions[:200]}...\n"

        info += f"ç¶æ?/ Status: {'å¯ç¨ / Enabled' if server.enabled else 'ç¦ç¨ / Disabled'}"
        console.print(Panel(info, border_style="cyan"))
        return

    if subcommand == "enable" and len(args) >= 2:
        name = args[1]
        if manager.enable_server(name):
            console.print(f"[green]â?å·²å¯ç?/ Enabled: {name}[/green]")
        else:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
        return

    if subcommand == "disable" and len(args) >= 2:
        name = args[1]
        if manager.disable_server(name):
            console.print(f"[green]â?å·²ç¦ç?/ Disabled: {name}[/green]")
        else:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
        return

    if subcommand == "remove" and len(args) >= 2:
        name = args[1]
        if manager.remove_server(name):
            console.print(f"[green]â?å·²ç§»é?/ Removed: {name}[/green]")
        else:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
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
        console.print(f"[green]â?å·²æ·»å?/ Added: {name} ({command})[/green]")
        return

    if subcommand == "oauth" and len(args) >= 3:
        name = args[1]
        client_id = args[2]
        server = manager.get_server(name)
        if server:
            server.client_id = client_id
            manager.update_server(server)
            console.print(f"[green]â?å·²éç½®OAuth / OAuth configured: {name}[/green]")
        else:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
        return

    if subcommand == "sse" and len(args) >= 3:
        name = args[1]
        url = args[2]
        server = manager.get_server(name)
        if server:
            server.transport = "sse"
            server.url = url
            manager.update_server(server)
            console.print(f"[green]â?å·²éç½®SSEä¼ è¾ / SSE configured: {name}[/green]")
            console.print(f"[dim]   URL: {url}[/dim]")
        else:
            console.print(f"[red]æªæ¾å?/ Not found: {name}[/red]")
        return

    if subcommand == "resources":
        console.print("[yellow]èµæºéè¦å¨æå¡å¨å¯å¨åæ¥ç / Resources available after server start[/yellow]")
        return

    if subcommand == "project":
        from agent_framework.deepseek_optimization.mcp_marketplace.config import discover_project_mcp_json
        path = discover_project_mcp_json()
        if path:
            console.print(f"[green]â?åç°é¡¹ç®ä½ç¨åMCPéç½® / Project-scoped MCP config: {path}[/green]")
        else:
            console.print("[yellow]æªæ¾å?mcp.json / No .mcp.json found[/yellow]")
        return

    if subcommand == "instructions" and len(args) >= 2:
        name = args[1]
        server = manager.get_server(name)
        if server and server.instructions:
            console.print(Panel(
                server.instructions,
                title=f"[bold cyan]{name} æä»¤ / Instructions[/bold cyan]",
                border_style="cyan"
            ))
        else:
            console.print(f"[yellow]æ æä»?/ No instructions for: {name}[/yellow]")
        return

    console.print(Panel(
        "[bold cyan]/mcp å½ä»¤å¸®å© / Command Help[/bold cyan]\n\n"
        "ç¨æ³ / Usage:\n"
        "  /mcp                            ååºæææå¡å¨ / List all servers\n"
        "  /mcp list                       ååºæå¡å¨è¯¦æ?/ List server details\n"
        "  /mcp add <åç§°> <å½ä»¤> [åæ°...]  æ·»å æå¡å?/ Add server\n"
        "  /mcp remove <åç§°>              ç§»é¤æå¡å?/ Remove server\n"
        "  /mcp enable <åç§°>              å¯ç¨æå¡å?/ Enable server\n"
        "  /mcp disable <åç§°>             ç¦ç¨æå¡å?/ Disable server\n"
        "  /mcp info <åç§°>                æ¾ç¤ºæå¡å¨è¯¦æ?/ Show server details\n"
        "  /mcp oauth <åç§°> <client-id>   éç½®OAuth / Configure OAuth\n"
        "  /mcp sse <åç§°> <url>           éç½®SSEä¼ è¾ / Configure SSE transport\n"
        "  /mcp resources [åç§°]           ååºèµæº / List resources\n"
        "  /mcp project                    é¡¹ç®ä½ç¨å?/ Project scope\n"
        "  /mcp instructions <åç§°>        è·åæå¡å¨æä»?/ Get instructions\n\n"
        "[dim]ä½¿ç¨ 'alonechat mcp' å½ä»¤è¿è¡å®æ´éç½® / Use 'alonechat mcp' for full config[/dim]",
        border_style="cyan"
    ))
