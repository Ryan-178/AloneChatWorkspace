"""
MCP Client - Communication with MCP servers.
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional, Callable

from .types import (
    MCPServer, MCPTool, MCPToolParameter, ServerStatus,
    MCPResource, MCPResourceTemplate, SamplingRequest, SamplingMessage,
    TransportType,
)


class MCPClient:
    """Client for communicating with MCP servers."""

    def __init__(self, server: MCPServer):
        self.server = server
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0
        self._server_instructions: Optional[str] = None
        self._server_capabilities: Dict[str, Any] = {}
        self._protocol_version: Optional[str] = None
        self._initialized = False

        self._sse_session: Optional[Any] = None
        self._sse_response: Optional[Any] = None
        self._oauth_token: Optional[str] = None

        self._sampling_handler: Optional[Callable] = None

    def set_sampling_handler(self, handler: Callable):
        """Set a handler for sampling/createMessage requests from the server."""
        self._sampling_handler = handler

    def set_oauth_token(self, token: str):
        """Set OAuth token for authenticated requests."""
        self._oauth_token = token

    async def connect(self) -> bool:
        """
        Connect to the MCP server.

        Returns:
            True if connection successful
        """
        try:
            config = self.server.config

            if config.transport == TransportType.SSE:
                return await self._connect_sse()
            else:
                return await self._connect_stdio()
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False

    async def _connect_stdio(self) -> bool:
        """Connect via stdio transport."""
        config = self.server.config

        env = dict(subprocess.os.environ)
        env.update(config.env)

        self._process = await asyncio.create_subprocess_exec(
            config.command,
            *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=config.cwd,
            env=env,
        )

        self._reader = self._process.stdout
        self._writer = self._process.stdin

        await asyncio.sleep(0.5)

        return await self._initialize()

    async def _connect_sse(self) -> bool:
        """Connect via SSE transport."""
        import aiohttp

        url = self.server.config.url
        if not url:
            raise Exception("SSE transport requires a URL")

        self._sse_session = aiohttp.ClientSession()

        headers = {}
        if self._oauth_token:
            headers["Authorization"] = f"Bearer {self._oauth_token}"

        resp = await self._sse_session.get(url, headers=headers)
        if resp.status != 200:
            raise Exception(f"SSE connection failed: {resp.status}")

        self._sse_response = resp
        return await self._initialize()

    async def _initialize(self) -> bool:
        """Initialize the MCP session."""
        capabilities = {}

        if self._sampling_handler:
            capabilities["sampling"] = {}

        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": capabilities,
                "clientInfo": {
                    "name": "deepseek-mcp-marketplace",
                    "version": "1.0.0",
                },
            },
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            raise Exception(f"Initialization failed: {response['error']}")

        result = response.get("result", {})

        self._protocol_version = result.get("protocolVersion", "2024-11-05")
        self._server_capabilities = result.get("capabilities", {})
        self._server_instructions = result.get("instructions")
        self.server.instructions = self._server_instructions

        self._initialized = True

        return True

    async def list_tools(self) -> List[MCPTool]:
        """
        List all available tools from the server.

        Returns:
            List of MCPTool objects
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/list",
            "params": {},
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")

        tools_data = response.get("result", {}).get("tools", [])
        return [self._parse_tool(t) for t in tools_data]

    async def get_tool_descriptions_size(self) -> int:
        """
        Get the total size of all tool descriptions in characters.
        Used for lazy-loading decision (auto mode).

        Returns:
            Total character count of all tool descriptions combined
        """
        tools = await self.list_tools()
        total = 0
        for tool in tools:
            total += len(tool.description) if tool.description else 0
            for param in tool.parameters.values():
                total += len(param.description) if param.description else 0
        return total

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call a tool on the server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")

        return response.get("result", {})

    async def list_resources(self) -> List[MCPResource]:
        """
        List all available resources from the server.

        Returns:
            List of MCPResource objects
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "resources/list",
            "params": {},
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            return []

        resources_data = response.get("result", {}).get("resources", [])
        return [MCPResource(**r) for r in resources_data]

    async def list_resource_templates(self) -> List[MCPResourceTemplate]:
        """
        List all resource templates from the server.

        Returns:
            List of MCPResourceTemplate objects
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "resources/templates/list",
            "params": {},
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            return []

        templates_data = response.get("result", {}).get("resourceTemplates", [])
        return [MCPResourceTemplate(**t) for t in templates_data]

    async def read_resource(self, uri: str) -> Any:
        """
        Read a resource from the server.

        Args:
            uri: Resource URI to read

        Returns:
            Resource content
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "resources/read",
            "params": {
                "uri": uri,
            },
        }

        await self._send_request(request)
        response = await self._receive_response()

        if "error" in response:
            raise Exception(f"Failed to read resource: {response['error']}")

        return response.get("result", {})

    async def get_server_instructions(self) -> Optional[str]:
        """
        Get the server instructions if provided during initialization.

        Returns:
            Server instructions string or None
        """
        return self._server_instructions

    @property
    def server_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities from initialization."""
        return dict(self._server_capabilities)

    @property
    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized

    async def disconnect(self):
        """Disconnect from the server."""
        if self._writer:
            try:
                request = {
                    "jsonrpc": "2.0",
                    "method": "shutdown",
                    "params": {},
                }
                await self._send_request(request, wait_for_response=False)
            except:
                pass

            self._writer.close()
            await self._writer.wait_closed()

        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()

        if self._sse_session:
            await self._sse_session.close()
            self._sse_session = None

        self._initialized = False

    async def _send_request(
        self,
        request: Dict[str, Any],
        wait_for_response: bool = True,
    ):
        """Send a JSON-RPC request to the server."""
        if self.server.config.transport == TransportType.SSE:
            return await self._send_sse_request(request, wait_for_response)

        if not self._writer:
            raise Exception("Not connected")

        request_json = json.dumps(request) + "\n"
        self._writer.write(request_json.encode())
        await self._writer.drain()

    async def _send_sse_request(
        self,
        request: Dict[str, Any],
        wait_for_response: bool = True,
    ):
        """Send a JSON-RPC request via SSE transport."""
        if not self._sse_session:
            raise Exception("Not connected")

        async with self._sse_session.post(
            self.server.config.url,
            json=request,
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Request failed: {resp.status}")
            return await resp.json()

    async def _receive_response(self) -> Dict[str, Any]:
        """Receive a JSON-RPC response from the server."""
        if self.server.config.transport == TransportType.SSE:
            raise Exception("SSE responses are handled differently via response events")

        if not self._reader:
            raise Exception("Not connected")

        line = await self._reader.readline()
        if not line:
            raise Exception("Connection closed")

        return json.loads(line.decode())

    def _get_next_request_id(self) -> int:
        """Get the next request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_tool(self, tool_data: Dict[str, Any]) -> MCPTool:
        """Parse tool data from MCP response."""
        name = tool_data.get("name", "")
        description = tool_data.get("description", "")

        params = {}
        input_schema = tool_data.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for param_name, param_schema in properties.items():
            params[param_name] = MCPToolParameter(
                name=param_name,
                type=param_schema.get("type", "string"),
                description=param_schema.get("description", ""),
                required=param_name in required,
                default=param_schema.get("default"),
                enum=param_schema.get("enum"),
            )

        return MCPTool(
            name=name,
            description=description,
            parameters=params,
        )
