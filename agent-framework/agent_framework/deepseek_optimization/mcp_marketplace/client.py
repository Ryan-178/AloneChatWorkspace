
"""
MCP Client - Communication with MCP servers.
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional

from .types import MCPServer, MCPTool, MCPToolParameter, ServerStatus


class MCPClient:
    """Client for communicating with MCP servers."""

    def __init__(self, server: MCPServer):
        self.server = server
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0

    async def connect(self) -&gt; bool:
        """
        Connect to the MCP server.

        Returns:
            True if connection successful
        """
        try:
            config = self.server.config

            # Start the MCP server process
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

            # Wait for initialization
            await asyncio.sleep(1)

            # Send initialize request
            await self._initialize()

            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False

    async def _initialize(self):
        """Initialize the MCP session."""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
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

    async def list_tools(self) -&gt; List[MCPTool]:
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

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -&gt; Dict[str, Any]:
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

    async def disconnect(self):
        """Disconnect from the server."""
        if self._writer:
            try:
                # Send shutdown notification
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

    async def _send_request(
        self,
        request: Dict[str, Any],
        wait_for_response: bool = True,
    ):
        """Send a JSON-RPC request to the server."""
        if not self._writer:
            raise Exception("Not connected")

        request_json = json.dumps(request) + "\n"
        self._writer.write(request_json.encode())
        await self._writer.drain()

    async def _receive_response(self) -&gt; Dict[str, Any]:
        """Receive a JSON-RPC response from the server."""
        if not self._reader:
            raise Exception("Not connected")

        line = await self._reader.readline()
        if not line:
            raise Exception("Connection closed")

        return json.loads(line.decode())

    def _get_next_request_id(self) -&gt; int:
        """Get the next request ID."""
        self._request_id += 1
        return self._request_id

    def _parse_tool(self, tool_data: Dict[str, Any]) -&gt; MCPTool:
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

