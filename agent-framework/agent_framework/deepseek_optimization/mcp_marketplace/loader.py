"""
MCP Server Loader - Manages loading and running MCP servers.
"""

import asyncio
from typing import Dict, Optional

from .types import MCPServer, ServerStatus
from .registry import MCPServerRegistry
from .client import MCPClient


class MCPServerLoader:
    """Loader for managing MCP server lifecycle."""

    def __init__(self, registry: MCPServerRegistry):
        self.registry = registry
        self._active_clients: Dict[str, MCPClient] = {}
        self._lock = asyncio.Lock()

    async def start_server(self, server_id: str) -> bool:
        """
        Start an MCP server.

        Args:
            server_id: ID of the server to start

        Returns:
            True if server started successfully
        """
        async with self._lock:
            server = self.registry.get_server(server_id)
            if not server:
                return False

            if server.status == ServerStatus.ACTIVE:
                return True

            if server_id in self._active_clients:
                return True

            self.registry.update_server_status(
                server_id,
                ServerStatus.STARTING,
            )

            try:
                client = MCPClient(server)
                success = await client.connect()

                if success:
                    tools = await client.list_tools()
                    self.registry.update_server_tools(server_id, tools)

                    try:
                        resources = await client.list_resources()
                        self.registry.update_server_resources(server_id, resources)
                    except Exception:
                        pass

                    try:
                        resource_templates = await client.list_resource_templates()
                        self.registry.update_server_resource_templates(server_id, resource_templates)
                    except Exception:
                        pass

                    self.registry.update_server_status(
                        server_id,
                        ServerStatus.ACTIVE,
                    )
                    self._active_clients[server_id] = client
                    return True
                else:
                    self.registry.update_server_status(
                        server_id,
                        ServerStatus.ERROR,
                        "Failed to connect",
                    )
                    return False
            except Exception as e:
                self.registry.update_server_status(
                    server_id,
                    ServerStatus.ERROR,
                    str(e),
                )
                return False

    async def stop_server(self, server_id: str) -> bool:
        """
        Stop an MCP server.

        Args:
            server_id: ID of the server to stop

        Returns:
            True if server stopped successfully
        """
        async with self._lock:
            server = self.registry.get_server(server_id)
            if not server:
                return False

            if server.status == ServerStatus.INACTIVE:
                return True

            client = self._active_clients.pop(server_id, None)
            if client:
                await client.disconnect()

            self.registry.update_server_status(
                server_id,
                ServerStatus.INACTIVE,
            )
            return True

    async def restart_server(self, server_id: str) -> bool:
        """
        Restart an MCP server.

        Args:
            server_id: ID of the server to restart

        Returns:
            True if server restarted successfully
        """
        await self.stop_server(server_id)
        return await self.start_server(server_id)

    def get_client(self, server_id: str) -> Optional[MCPClient]:
        """
        Get the active client for a server.

        Args:
            server_id: ID of the server

        Returns:
            MCPClient instance if server is active, None otherwise
        """
        return self._active_clients.get(server_id)

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """
        Call a tool on an active server.

        Args:
            server_id: ID of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        client = self.get_client(server_id)
        if not client:
            raise Exception(f"Server {server_id} is not active")

        return await client.call_tool(tool_name, arguments)

    async def load_server_resources(self, server_id: str) -> None:
        """
        Load resources from an active server.

        Args:
            server_id: ID of the server
        """
        client = self.get_client(server_id)
        if not client:
            return

        try:
            resources = await client.list_resources()
            self.registry.update_server_resources(server_id, resources)
        except Exception:
            pass

        try:
            templates = await client.list_resource_templates()
            self.registry.update_server_resource_templates(server_id, templates)
        except Exception:
            pass

    async def read_resource(self, server_id: str, uri: str) -> dict:
        """
        Read a resource from an active server.

        Args:
            server_id: ID of the server
            uri: Resource URI

        Returns:
            Resource content
        """
        client = self.get_client(server_id)
        if not client:
            raise Exception(f"Server {server_id} is not active")

        return await client.read_resource(uri)

    async def get_tool_descriptions_size(self, server_id: str) -> int:
        """
        Get total tool descriptions size for lazy-loading decision.

        Args:
            server_id: ID of the server

        Returns:
            Total character count
        """
        client = self.get_client(server_id)
        if not client:
            return 0

        return await client.get_tool_descriptions_size()

    async def shutdown_all(self):
        """Shutdown all active servers."""
        async with self._lock:
            for server_id in list(self._active_clients.keys()):
                await self.stop_server(server_id)
