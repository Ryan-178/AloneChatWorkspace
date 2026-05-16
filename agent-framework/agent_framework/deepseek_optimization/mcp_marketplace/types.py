
"""
Type definitions for DeepSeek MCP Marketplace.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ServerStatus(str, Enum):
    """MCP server status enum."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class MCPToolParameter(BaseModel):
    """MCP tool parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, etc.)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    enum: Optional[List[Any]] = Field(default=None, description="Allowed values")


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, MCPToolParameter] = Field(
        default_factory=dict,
        description="Tool parameters"
    )


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class MCPServer(BaseModel):
    """MCP server definition."""
    id: str = Field(..., description="Unique server ID")
    name: str = Field(..., description="Server name")
    description: str = Field(default="", description="Server description")
    version: str = Field(default="1.0.0", description="Server version")
    config: MCPServerConfig = Field(..., description="Server configuration")
    status: ServerStatus = Field(default=ServerStatus.INACTIVE, description="Current status")
    tools: List[MCPTool] = Field(default_factory=list, description="Available tools")
    error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_connected_at: Optional[datetime] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

