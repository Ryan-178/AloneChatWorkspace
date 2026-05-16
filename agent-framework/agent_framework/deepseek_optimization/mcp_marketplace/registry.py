
"""
MCP Server Registry - Manages registered MCP servers.
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime

from .types import MCPServer, ServerStatus, MCPServerConfig


class MCPServerRegistry:
    """Registry for managing MCP servers."""

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}

    def register_server(
        self,
        name: str,
        config: MCPServerConfig,
        description: str = "",
        version: str = "1.0.0",
        server_id: Optional[str] = None,
    ) -&gt; MCPServer:
        """
        Register a new MCP server.

        Args:
            name: Server name
            config: Server configuration
            description: Server description
            version: Server version
            server_id: Optional server ID (generated if not provided)

        Returns:
            Registered MCPServer instance
        """
        server_id = server_id or str(uuid.uuid4())

        server = MCPServer(
            id=server_id,
            name=name,
            description=description,
            version=version,
            config=config,
            status=ServerStatus.INACTIVE,
            tools=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._servers[server_id] = server
        return server

    def get_server(self, server_id: str) -&gt; Optional[MCPServer]:
        """Get a server by ID."""
        return self._servers.get(server_id)

    def get_all_servers(self) -&gt; List[MCPServer]:
        """Get all registered servers."""
        return list(self._servers.values())

    def update_server(
        self,
        server_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        config: Optional[MCPServerConfig] = None,
    ) -&gt; Optional[MCPServer]:
        """Update a server's information."""
        server = self._servers.get(server_id)
        if not server:
            return None

        if name is not None:
            server.name = name
        if description is not None:
            server.description = description
        if version is not None:
            server.version = version
        if config is not None:
            server.config = config

        server.updated_at = datetime.utcnow()
        return server

    def update_server_status(
        self,
        server_id: str,
        status: ServerStatus,
        error_message: Optional[str] = None,
    ) -&gt; Optional[MCPServer]:
        """Update a server's status."""
        server = self._servers.get(server_id)
        if not server:
            return None

        server.status = status
        server.error_message = error_message
        server.updated_at = datetime.utcnow()

        if status == ServerStatus.ACTIVE:
            server.last_connected_at = datetime.utcnow()

        return server

    def update_server_tools(
        self,
        server_id: str,
        tools: List,
    ) -&gt; Optional[MCPServer]:
        """Update a server's available tools."""
        server = self._servers.get(server_id)
        if not server:
            return None

        server.tools = tools
        server.updated_at = datetime.utcnow()
        return server

    def unregister_server(self, server_id: str) -&gt; bool:
        """Unregister a server."""
        if server_id in self._servers:
            del self._servers[server_id]
            return True
        return False

    def get_servers_by_status(self, status: ServerStatus) -&gt; List[MCPServer]:
        """Get all servers with a specific status."""
        return [
            server for server in self._servers.values()
            if server.status == status
        ]

