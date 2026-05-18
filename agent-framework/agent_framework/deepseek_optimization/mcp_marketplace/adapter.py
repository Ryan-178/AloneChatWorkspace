
"""
MCP Tool Adapter - Adapts MCP tools to BaseTool interface.
"""

import asyncio
import time
from typing import Any, Dict, Optional

from agent_framework.core.base_tool import BaseTool, ToolResult
from .types import MCPTool, MCPToolParameter
from .loader import MCPServerLoader


class MCPToolAdapter(BaseTool):
    """
    Adapter that wraps an MCP tool to work with the BaseTool interface.
    This allows MCP tools to be used seamlessly within the agent framework.
    """

    def __init__(
        self,
        mcp_tool: MCPTool,
        server_id: str,
        loader: MCPServerLoader,
        timeout: Optional[float] = None,
    ):
        self.mcp_tool = mcp_tool
        self.server_id = server_id
        self.loader = loader
        self.timeout = timeout or 30.0
        
        self.name = f"mcp_{server_id[:8]}_{mcp_tool.name}"
        self.description = f"[MCP:{server_id[:8]}] {mcp_tool.description}"
        self.parameters = self._convert_parameters()

    def _convert_parameters(self) -> Dict[str, Any]:
        """Convert MCP tool parameters to JSON Schema format."""
        properties = {}
        required = []
        
        for param_name, param in self.mcp_tool.parameters.items():
            prop = {
                "type": param.type,
                "description": param.description,
            }
            
            if param.default is not None:
                prop["default"] = param.default
            
            if param.enum:
                prop["enum"] = param.enum
            
            properties[param_name] = prop
            
            if param.required:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def execute(self, **kwargs: Any) -> Any:
        """
        Synchronous execution wrapper.
        Uses asyncio.run for synchronous interface compatibility.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.execute_async(**kwargs))
                return future.result(timeout=self.timeout)
        else:
            return asyncio.run(self.execute_async(**kwargs))

    async def execute_async(self, **kwargs: Any) -> Any:
        """
        Asynchronous execution of the MCP tool.
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.loader.call_tool(
                    self.server_id,
                    self.mcp_tool.name,
                    kwargs,
                ),
                timeout=self.timeout,
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "execution_time_ms": execution_time_ms,
                    }
                return {
                    "success": True,
                    "data": result.get("content", result),
                    "execution_time_ms": execution_time_ms,
                }
            
            return {
                "success": True,
                "data": result,
                "execution_time_ms": execution_time_ms,
            }
            
        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": f"Tool execution timed out after {self.timeout} seconds",
                "execution_time_ms": execution_time_ms,
            }
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
            }

    def get_mcp_info(self) -> Dict[str, Any]:
        """Get MCP-specific information about this tool."""
        return {
            "server_id": self.server_id,
            "original_name": self.mcp_tool.name,
            "adapter_name": self.name,
            "timeout": self.timeout,
        }


class MCPToolRegistry:
    """
    Registry for MCP tool adapters.
    Manages the mapping between adapter names and their MCP tool adapters.
    """

    def __init__(self):
        self._adapters: Dict[str, MCPToolAdapter] = {}
        self._server_tools: Dict[str, Dict[str, str]] = {}

    def register_adapter(self, adapter: MCPToolAdapter) -> None:
        """Register an MCP tool adapter."""
        self._adapters[adapter.name] = adapter
        
        if adapter.server_id not in self._server_tools:
            self._server_tools[adapter.server_id] = {}
        
        self._server_tools[adapter.server_id][adapter.mcp_tool.name] = adapter.name

    def unregister_adapter(self, name: str) -> None:
        """Unregister an MCP tool adapter."""
        adapter = self._adapters.pop(name, None)
        if adapter:
            server_tools = self._server_tools.get(adapter.server_id, {})
            server_tools.pop(adapter.mcp_tool.name, None)
            if not server_tools:
                self._server_tools.pop(adapter.server_id, None)

    def get_adapter(self, name: str) -> Optional[MCPToolAdapter]:
        """Get an adapter by name."""
        return self._adapters.get(name)

    def get_adapters_by_server(self, server_id: str) -> Dict[str, MCPToolAdapter]:
        """Get all adapters for a specific server."""
        server_tools = self._server_tools.get(server_id, {})
        return {
            original_name: self._adapters[adapter_name]
            for original_name, adapter_name in server_tools.items()
        }

    def unregister_server(self, server_id: str) -> None:
        """Unregister all adapters for a server."""
        server_tools = self._server_tools.pop(server_id, {})
        for adapter_name in server_tools.values():
            self._adapters.pop(adapter_name, None)

    def list_adapters(self) -> Dict[str, MCPToolAdapter]:
        """List all registered adapters."""
        return dict(self._adapters)

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_adapters": len(self._adapters),
            "servers_with_tools": len(self._server_tools),
            "tools_per_server": {
                server_id: len(tools)
                for server_id, tools in self._server_tools.items()
            },
        }
