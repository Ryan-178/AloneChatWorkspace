"""
Tests for MCP integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from agent_framework.deepseek_optimization.mcp_marketplace import (
    MCPServer,
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    ServerStatus,
    MCPServerRegistry,
    MCPToolAdapter,
    MCPToolRegistry,
    MCPManager,
)
from agent_framework.tools.registry import ToolRegistry


class TestMCPServerRegistry:
    """Tests for MCPServerRegistry."""

    def test_register_server(self):
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server = registry.register_server(
            name="test-server",
            config=config,
            description="Test server",
        )
        
        assert server.name == "test-server"
        assert server.status == ServerStatus.INACTIVE
        assert registry.get_server(server.id) == server

    def test_unregister_server(self):
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server = registry.register_server(name="test-server", config=config)
        assert registry.get_server(server.id) is not None
        
        success = registry.unregister_server(server.id)
        assert success is True
        assert registry.get_server(server.id) is None

    def test_update_server_status(self):
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server = registry.register_server(name="test-server", config=config)
        registry.update_server_status(server.id, ServerStatus.ACTIVE)
        
        updated = registry.get_server(server.id)
        assert updated.status == ServerStatus.ACTIVE
        assert updated.last_connected_at is not None

    def test_get_servers_by_status(self):
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server1 = registry.register_server(name="server1", config=config)
        server2 = registry.register_server(name="server2", config=config)
        
        registry.update_server_status(server1.id, ServerStatus.ACTIVE)
        
        active = registry.get_servers_by_status(ServerStatus.ACTIVE)
        inactive = registry.get_servers_by_status(ServerStatus.INACTIVE)
        
        assert len(active) == 1
        assert len(inactive) == 1


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter."""

    def test_adapter_creation(self):
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            parameters={
                "arg1": MCPToolParameter(
                    name="arg1",
                    type="string",
                    description="First argument",
                    required=True,
                ),
            },
        )
        
        loader = Mock()
        adapter = MCPToolAdapter(
            mcp_tool=tool,
            server_id="test-server-id",
            loader=loader,
        )
        
        assert "test_tool" in adapter.name
        assert adapter.description == "[MCP:test-ser] Test tool"
        assert "arg1" in adapter.parameters["properties"]
        assert "arg1" in adapter.parameters["required"]

    def test_parameter_conversion(self):
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            parameters={
                "required_arg": MCPToolParameter(
                    name="required_arg",
                    type="string",
                    description="Required",
                    required=True,
                ),
                "optional_arg": MCPToolParameter(
                    name="optional_arg",
                    type="integer",
                    description="Optional",
                    required=False,
                    default=42,
                ),
                "enum_arg": MCPToolParameter(
                    name="enum_arg",
                    type="string",
                    description="Enum",
                    required=False,
                    enum=["a", "b", "c"],
                ),
            },
        )
        
        loader = Mock()
        adapter = MCPToolAdapter(
            mcp_tool=tool,
            server_id="test-server-id",
            loader=loader,
        )
        
        params = adapter.parameters
        assert params["type"] == "object"
        assert "required_arg" in params["required"]
        assert "optional_arg" not in params["required"]
        assert params["properties"]["optional_arg"]["default"] == 42
        assert params["properties"]["enum_arg"]["enum"] == ["a", "b", "c"]


class TestMCPToolRegistry:
    """Tests for MCPToolRegistry."""

    def test_register_adapter(self):
        registry = MCPToolRegistry()
        tool = MCPTool(name="test_tool", description="Test", parameters={})
        loader = Mock()
        adapter = MCPToolAdapter(tool, "server-1", loader)
        
        registry.register_adapter(adapter)
        
        assert registry.get_adapter(adapter.name) == adapter
        assert len(registry.list_adapters()) == 1

    def test_unregister_adapter(self):
        registry = MCPToolRegistry()
        tool = MCPTool(name="test_tool", description="Test", parameters={})
        loader = Mock()
        adapter = MCPToolAdapter(tool, "server-1", loader)
        
        registry.register_adapter(adapter)
        registry.unregister_adapter(adapter.name)
        
        assert registry.get_adapter(adapter.name) is None

    def test_unregister_server(self):
        registry = MCPToolRegistry()
        loader = Mock()
        
        tool1 = MCPTool(name="tool1", description="Tool 1", parameters={})
        tool2 = MCPTool(name="tool2", description="Tool 2", parameters={})
        
        adapter1 = MCPToolAdapter(tool1, "server-1", loader)
        adapter2 = MCPToolAdapter(tool2, "server-1", loader)
        
        registry.register_adapter(adapter1)
        registry.register_adapter(adapter2)
        
        registry.unregister_server("server-1")
        
        assert len(registry.list_adapters()) == 0

    def test_get_stats(self):
        registry = MCPToolRegistry()
        loader = Mock()
        
        tool1 = MCPTool(name="tool1", description="Tool 1", parameters={})
        tool2 = MCPTool(name="tool2", description="Tool 2", parameters={})
        
        adapter1 = MCPToolAdapter(tool1, "server-1", loader)
        adapter2 = MCPToolAdapter(tool2, "server-2", loader)
        
        registry.register_adapter(adapter1)
        registry.register_adapter(adapter2)
        
        stats = registry.get_stats()
        
        assert stats["total_adapters"] == 2
        assert stats["servers_with_tools"] == 2


class TestMCPManager:
    """Tests for MCPManager."""

    @pytest.mark.asyncio
    async def test_register_server(self):
        manager = MCPManager()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server = await manager.register_server(
            name="test-server",
            config=config,
            description="Test server",
        )
        
        assert server.name == "test-server"
        assert manager.get_server(server.id) == server

    @pytest.mark.asyncio
    async def test_get_stats(self):
        manager = MCPManager()
        config = MCPServerConfig(command="test", args=[], env={})
        
        await manager.register_server(name="server1", config=config)
        await manager.register_server(name="server2", config=config)
        
        stats = manager.get_stats()
        
        assert stats["servers"]["total"] == 2
        assert stats["servers"]["inactive"] == 2

    @pytest.mark.asyncio
    async def test_call_history(self):
        manager = MCPManager()
        
        manager._call_history = [
            {"server_id": "s1", "tool_name": "t1", "success": True},
            {"server_id": "s1", "tool_name": "t2", "success": False},
            {"server_id": "s2", "tool_name": "t1", "success": True},
        ]
        
        history = manager.get_call_history()
        assert len(history) == 3
        
        history_s1 = manager.get_call_history(server_id="s1")
        assert len(history_s1) == 2
        
        history_t1 = manager.get_call_history(tool_name="t1")
        assert len(history_t1) == 2

    @pytest.mark.asyncio
    async def test_unregister_server(self):
        manager = MCPManager()
        config = MCPServerConfig(command="test", args=[], env={})
        
        server = await manager.register_server(name="test-server", config=config)
        success = await manager.unregister_server(server.id)
        
        assert success is True
        assert manager.get_server(server.id) is None


class TestMCPConfig:
    """Tests for MCP configuration."""

    def test_load_from_dict(self):
        from agent_framework.deepseek_optimization.mcp_marketplace.config import MCPConfig
        
        config = MCPConfig()
        settings = config.load_from_dict({
            "enabled": True,
            "servers": [
                {
                    "name": "test-server",
                    "command": "npx",
                    "args": ["-y", "test-package"],
                    "env": {"API_KEY": "test"},
                    "auto_start": True,
                }
            ],
            "default_timeout": 60,
        })
        
        assert settings.enabled is True
        assert len(settings.servers) == 1
        assert settings.servers[0].name == "test-server"
        assert settings.default_timeout == 60

    def test_env_var_substitution(self):
        import os
        from agent_framework.deepseek_optimization.mcp_marketplace.config import MCPConfig
        
        os.environ["TEST_API_KEY"] = "secret-key"
        
        config = MCPConfig()
        settings = config.load_from_dict({
            "servers": [
                {
                    "name": "test",
                    "command": "test",
                    "env": {"API_KEY": "${TEST_API_KEY}"},
                }
            ]
        })
        
        assert settings.servers[0].env["API_KEY"] == "secret-key"
        
        del os.environ["TEST_API_KEY"]

    def test_get_server_configs(self):
        from agent_framework.deepseek_optimization.mcp_marketplace.config import MCPConfig
        
        config = MCPConfig()
        config.load_from_dict({
            "servers": [
                {
                    "name": "server1",
                    "command": "cmd1",
                    "args": ["arg1"],
                    "timeout": 30,
                    "auto_start": True,
                    "description": "Server 1",
                    "version": "1.0.0",
                }
            ]
        })
        
        configs = config.get_server_configs()
        
        assert len(configs) == 1
        name, server_config, auto_start, desc, version = configs[0]
        assert name == "server1"
        assert server_config.command == "cmd1"
        assert auto_start is True
