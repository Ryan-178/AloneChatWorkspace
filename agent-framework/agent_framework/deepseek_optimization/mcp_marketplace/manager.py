"""
MCP Manager - Unified management of MCP servers and tools.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from .types import MCPServer, MCPServerConfig, ServerStatus, MCPTool, MCPResource
from .registry import MCPServerRegistry
from .loader import MCPServerLoader
from .adapter import MCPToolAdapter, MCPToolRegistry


class MCPManager:
    """
    Central manager for MCP servers and tools.
    Provides a unified interface for:
    - Registering and managing MCP servers
    - Auto-registering MCP tools with the tool registry
    - Tool invocation and lifecycle management
    - Resource listing and @-mention support
    - Lazy tool loading for context window optimization
    - OAuth token management
    """

    def __init__(
        self,
        tool_registry: Optional[Any] = None,
        auto_register_tools: bool = True,
        default_timeout: float = 30.0,
        lazy_load_threshold: float = 0.1,
    ):
        self.registry = MCPServerRegistry()
        self.loader = MCPServerLoader(self.registry)
        self.tool_registry = tool_registry
        self.adapter_registry = MCPToolRegistry()
        self.auto_register_tools = auto_register_tools
        self.default_timeout = default_timeout
        self.lazy_load_threshold = lazy_load_threshold

        self._call_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        self._semaphore = asyncio.Semaphore(10)

    async def register_server(
        self,
        name: str,
        config: MCPServerConfig,
        description: str = "",
        version: str = "1.0.0",
        auto_start: bool = False,
    ) -> MCPServer:
        """
        Register a new MCP server.

        Args:
            name: Server name
            config: Server configuration
            description: Server description
            version: Server version
            auto_start: Whether to start the server immediately

        Returns:
            Registered MCPServer instance
        """
        server = self.registry.register_server(
            name=name,
            config=config,
            description=description,
            version=version,
        )

        if auto_start:
            await self.start_server(server.id)

        return server

    async def start_server(
        self,
        server_id: str,
        register_tools: Optional[bool] = None,
    ) -> bool:
        """
        Start an MCP server and optionally register its tools.

        Args:
            server_id: ID of the server to start
            register_tools: Override auto_register_tools setting

        Returns:
            True if server started successfully
        """
        success = await self.loader.start_server(server_id)

        if not success:
            return False

        should_register = register_tools if register_tools is not None else self.auto_register_tools
        if should_register:
            await self._register_server_tools(server_id)

        return True

    async def check_and_lazy_load_tools(self, server_id: str, context_window_size: int = 100000) -> bool:
        """
        Check if tool descriptions exceed the threshold and lazy-load if needed.
        Auto mode: when tool descriptions exceed 10% of context window, defer loading.

        Args:
            server_id: ID of the server
            context_window_size: Estimated context window size in characters

        Returns:
            True if tools were lazy-loaded (deferred), False if loaded normally
        """
        try:
            desc_size = await self.loader.get_tool_descriptions_size(server_id)
            threshold = int(context_window_size * self.lazy_load_threshold)

            if desc_size > threshold:
                server = self.registry.get_server(server_id)
                if server:
                    tool_summaries = []
                    for tool in server.tools:
                        short_desc = tool.description[:100] if tool.description else ""
                        tool_summaries.append(f"{tool.name}: {short_desc}...")
                    return True
            return False
        except Exception:
            return False

    async def stop_server(self, server_id: str) -> bool:
        """
        Stop an MCP server and unregister its tools.

        Args:
            server_id: ID of the server to stop

        Returns:
            True if server stopped successfully
        """
        self._unregister_server_tools(server_id)
        return await self.loader.stop_server(server_id)

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

    async def _register_server_tools(self, server_id: str) -> None:
        """Register all tools from a server to the tool registry."""
        server = self.registry.get_server(server_id)
        if not server or not server.tools:
            return

        for tool in server.tools:
            adapter = MCPToolAdapter(
                mcp_tool=tool,
                server_id=server_id,
                loader=self.loader,
                timeout=self.default_timeout,
            )

            self.adapter_registry.register_adapter(adapter)

            if self.tool_registry:
                try:
                    self.tool_registry.register(adapter)
                except ValueError:
                    pass

    def _unregister_server_tools(self, server_id: str) -> None:
        """Unregister all tools from a server."""
        adapters = self.adapter_registry.get_adapters_by_server(server_id)

        for adapter in adapters.values():
            if self.tool_registry:
                self.tool_registry.unregister(adapter.name)

        self.adapter_registry.unregister_server(server_id)

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool on an MCP server.

        Args:
            server_id: ID of the server
            tool_name: Name of the tool
            arguments: Tool arguments
            timeout: Optional timeout override

        Returns:
            Tool result
        """
        async with self._semaphore:
            start_time = datetime.utcnow()

            try:
                effective_timeout = timeout or self.default_timeout
                result = await asyncio.wait_for(
                    self.loader.call_tool(server_id, tool_name, arguments),
                    timeout=effective_timeout,
                )

                execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                call_record = {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "success": True,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": start_time.isoformat(),
                }
                self._add_to_history(call_record)

                return {
                    "success": True,
                    "result": result,
                    "execution_time_ms": execution_time_ms,
                }

            except asyncio.TimeoutError:
                execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                error_msg = f"Tool call timed out after {timeout or self.default_timeout} seconds"

                call_record = {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "error": error_msg,
                    "success": False,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": start_time.isoformat(),
                }
                self._add_to_history(call_record)

                return {
                    "success": False,
                    "error": error_msg,
                    "execution_time_ms": execution_time_ms,
                }

            except Exception as e:
                execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                call_record = {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "error": str(e),
                    "success": False,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": start_time.isoformat(),
                }
                self._add_to_history(call_record)

                return {
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms,
                }

    async def read_resource(self, server_id: str, uri: str) -> dict:
        """
        Read a resource from an MCP server.

        Args:
            server_id: ID of the server
            uri: Resource URI

        Returns:
            Resource content
        """
        return await self.loader.read_resource(server_id, uri)

    def search_resources(self, query: str) -> List[tuple]:
        """
        Search resources across all servers for @-mention support.

        Args:
            query: Search string

        Returns:
            List of tuples (server_name, resource)
        """
        return self.registry.search_resources(query)

    def get_server_resources(self, server_id: str) -> List[MCPResource]:
        """Get resources provided by a server."""
        server = self.registry.get_server(server_id)
        return server.resources if server else []

    def get_server_instructions(self, server_id: str) -> Optional[str]:
        """Get instructions from a server."""
        server = self.registry.get_server(server_id)
        return server.instructions if server else None

    def _add_to_history(self, record: Dict[str, Any]) -> None:
        """Add a call record to history."""
        self._call_history.append(record)
        if len(self._call_history) > self._max_history:
            self._call_history = self._call_history[-self._max_history:]

    def get_call_history(
        self,
        server_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get tool call history.

        Args:
            server_id: Filter by server ID
            tool_name: Filter by tool name
            limit: Maximum number of records to return

        Returns:
            List of call records
        """
        history = self._call_history

        if server_id:
            history = [h for h in history if h.get("server_id") == server_id]

        if tool_name:
            history = [h for h in history if h.get("tool_name") == tool_name]

        return history[-limit:]

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self.registry.get_server(server_id)

    def get_all_servers(self) -> List[MCPServer]:
        """Get all registered servers."""
        return self.registry.get_all_servers()

    def get_active_servers(self) -> List[MCPServer]:
        """Get all active servers."""
        return self.registry.get_servers_by_status(ServerStatus.ACTIVE)

    def get_server_tools(self, server_id: str) -> List[MCPTool]:
        """Get tools provided by a server."""
        server = self.registry.get_server(server_id)
        return server.tools if server else []

    def get_all_tools(self) -> Dict[str, List[MCPTool]]:
        """Get all tools grouped by server."""
        result = {}
        for server in self.get_active_servers():
            if server.tools:
                result[server.id] = server.tools
        return result

    def get_registered_adapters(self) -> Dict[str, MCPToolAdapter]:
        """Get all registered tool adapters."""
        return self.adapter_registry.list_adapters()

    async def unregister_server(self, server_id: str) -> bool:
        """
        Unregister a server completely.
        Stops the server if running and removes all tools.
        """
        server = self.registry.get_server(server_id)
        if not server:
            return False

        if server.status == ServerStatus.ACTIVE:
            await self.stop_server(server_id)

        return self.registry.unregister_server(server_id)

    async def shutdown(self) -> None:
        """Shutdown all servers and cleanup."""
        await self.loader.shutdown_all()
        self.adapter_registry = MCPToolRegistry()
        self._call_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        servers = self.get_all_servers()
        total_resources = sum(len(s.resources) for s in servers)

        return {
            "servers": {
                "total": len(servers),
                "active": len([s for s in servers if s.status == ServerStatus.ACTIVE]),
                "inactive": len([s for s in servers if s.status == ServerStatus.INACTIVE]),
                "error": len([s for s in servers if s.status == ServerStatus.ERROR]),
            },
            "tools": {
                "total_adapters": len(self.adapter_registry.list_adapters()),
                "adapters_per_server": self.adapter_registry.get_stats()["tools_per_server"],
            },
            "resources": {
                "total": total_resources,
            },
            "calls": {
                "total": len(self._call_history),
                "successful": len([c for c in self._call_history if c.get("success")]),
                "failed": len([c for c in self._call_history if not c.get("success")]),
            },
        }


_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


def init_mcp_manager(
    tool_registry: Optional[Any] = None,
    auto_register_tools: bool = True,
    default_timeout: float = 30.0,
    lazy_load_threshold: float = 0.1,
) -> MCPManager:
    """Initialize the global MCP manager."""
    global _mcp_manager
    _mcp_manager = MCPManager(
        tool_registry=tool_registry,
        auto_register_tools=auto_register_tools,
        default_timeout=default_timeout,
        lazy_load_threshold=lazy_load_threshold,
    )
    return _mcp_manager
