"""
MCP CLI模块 / MCP CLI Module

提供MCP相关的CLI命令 / Provides MCP-related CLI commands
"""

from alonechat.mcp.cli import mcp_command
from alonechat.mcp.config import MCPConfigManager

__all__ = ["mcp_command", "MCPConfigManager"]
