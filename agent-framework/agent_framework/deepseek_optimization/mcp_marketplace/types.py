
"""
Type definitions for DeepSeek MCP Marketplace.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
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


class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(default=None, description="Resource description")
    mime_type: Optional[str] = Field(default=None, description="MIME type")


class MCPResourceTemplate(BaseModel):
    """MCP resource template definition."""
    uri_template: str = Field(..., description="URI template pattern")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    mime_type: Optional[str] = Field(default=None, description="MIME type")


class TransportType(str, Enum):
    """MCP transport type enum."""
    STDIO = "stdio"
    SSE = "sse"


class OAuthConfig(BaseModel):
    """OAuth configuration for MCP server authentication."""
    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth client secret")
    authorization_url: Optional[str] = Field(default=None, description="OAuth authorization URL")
    token_url: Optional[str] = Field(default=None, description="OAuth token URL")
    scopes: List[str] = Field(default_factory=list, description="OAuth scopes")
    metadata_url: Optional[str] = Field(default=None, description="OAuth metadata URL (CIMD/SEP-991)")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    transport: TransportType = Field(default=TransportType.STDIO, description="Transport type")
    url: Optional[str] = Field(default=None, description="SSE endpoint URL (for SSE transport)")
    oauth: Optional[OAuthConfig] = Field(default=None, description="OAuth configuration")
    instructions: Optional[str] = Field(default=None, description="Server instructions")


class MCPServer(BaseModel):
    """MCP server definition."""
    id: str = Field(..., description="Unique server ID")
    name: str = Field(..., description="Server name")
    description: str = Field(default="", description="Server description")
    version: str = Field(default="1.0.0", description="Server version")
    config: MCPServerConfig = Field(..., description="Server configuration")
    status: ServerStatus = Field(default=ServerStatus.INACTIVE, description="Current status")
    tools: List[MCPTool] = Field(default_factory=list, description="Available tools")
    resources: List[MCPResource] = Field(default_factory=list, description="Available resources")
    resource_templates: List[MCPResourceTemplate] = Field(default_factory=list, description="Resource templates")
    instructions: Optional[str] = Field(default=None, description="Server instructions")
    error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_connected_at: Optional[datetime] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SamplingMessage(BaseModel):
    """Message for MCP sampling/createMessage."""
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: Any = Field(..., description="Message content")


class SamplingRequest(BaseModel):
    """Request for MCP sampling/createMessage."""
    messages: List[SamplingMessage] = Field(..., description="Conversation messages")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    include_context: Optional[str] = Field(default=None, description="Context inclusion strategy")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    stop_sequences: List[str] = Field(default_factory=list, description="Stop sequences")
    temperature: Optional[float] = Field(default=None, description="Temperature")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

