"""
MCP Configuration - Configuration management for MCP servers.
"""

import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from .types import MCPServerConfig, TransportType, OAuthConfig


class MCPServerDefinition(BaseModel):
    """Definition of an MCP server from configuration."""
    
    name: str = Field(..., description="Server name")
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    auto_start: bool = Field(default=False, description="Auto-start on initialization")
    description: str = Field(default="", description="Server description")
    version: str = Field(default="1.0.0", description="Server version")
    transport: str = Field(default="stdio", description="Transport type (stdio or sse)")
    url: Optional[str] = Field(default=None, description="SSE endpoint URL")
    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth client secret")
    oauth_metadata_url: Optional[str] = Field(default=None, description="OAuth metadata URL (CIMD/SEP-991)")
    instructions: Optional[str] = Field(default=None, description="Server instructions")


class MCPSettings(BaseModel):
    """MCP global settings."""
    
    enabled: bool = Field(default=True, description="Enable MCP functionality")
    servers: List[MCPServerDefinition] = Field(default_factory=list, description="Server definitions")
    default_timeout: int = Field(default=30, description="Default timeout for tool calls")
    max_concurrent_calls: int = Field(default=10, description="Maximum concurrent tool calls")
    auto_register_tools: bool = Field(default=True, description="Auto-register tools with tool registry")
    lazy_load_tools: bool = Field(default=False, description="Lazy-load tools when descriptions exceed 10% of context window")
    auto_lazy_load_threshold: float = Field(default=0.1, description="Fraction of context window that triggers lazy loading")


def discover_project_mcp_json() -> Optional[str]:
    """
    Discover .mcp.json in the current or parent directories (project scope).
    
    Returns:
        Path to .mcp.json file if found, None otherwise
    """
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        mcp_file = parent / ".mcp.json"
        if mcp_file.exists():
            return str(mcp_file)
    return None


def load_project_mcp_json(path: str) -> List[MCPServerDefinition]:
    """
    Load MCP server definitions from a project-scoped .mcp.json file.
    
    Args:
        path: Path to .mcp.json file
        
    Returns:
        List of MCPServerDefinition objects
    """
    import json
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    servers = []
    mcp_servers = data.get("mcpServers", {})
    
    for name, server_data in mcp_servers.items():
        server_def = MCPServerDefinition(
            name=name,
            command=server_data.get("command", ""),
            args=server_data.get("args", []),
            env=server_data.get("env", {}),
            cwd=server_data.get("cwd"),
            timeout=server_data.get("timeout", 30),
            auto_start=server_data.get("auto_start", False),
            description=server_data.get("description", ""),
            version=server_data.get("version", "1.0.0"),
            transport=server_data.get("transport", "stdio"),
            url=server_data.get("url"),
            client_id=server_data.get("client_id"),
            client_secret=server_data.get("client_secret"),
            oauth_metadata_url=server_data.get("oauth_metadata_url"),
            instructions=server_data.get("instructions"),
        )
        servers.append(server_def)
    
    return servers


class MCPConfig:
    """
    Configuration manager for MCP servers.
    Supports loading from YAML files, .mcp.json project files, and environment variable substitution.
    """
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._settings: Optional[MCPSettings] = None
        self._raw_config: Dict[str, Any] = {}
        self._project_servers: List[MCPServerDefinition] = []
    
    def load_from_dict(self, config: Dict[str, Any]) -> MCPSettings:
        """
        Load configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            MCPSettings instance
        """
        self._raw_config = config
        processed_config = self._process_config(config)
        self._settings = MCPSettings(**processed_config)
        return self._settings
    
    def load_from_yaml(self, path: str) -> MCPSettings:
        """
        Load configuration from a YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            MCPSettings instance
        """
        import yaml
        
        with open(path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f) or {}
        
        self.config_path = path
        mcp_config = raw_config.get('mcp', {})
        return self.load_from_dict(mcp_config)
    
    def load_project_scope(self, project_dir: Optional[str] = None) -> List[MCPServerDefinition]:
        """
        Load project-scoped MCP server definitions from .mcp.json.
        
        Args:
            project_dir: Project directory to search from (defaults to cwd)
            
        Returns:
            List of MCPServerDefinition from project scope
        """
        search_dir = project_dir or str(Path.cwd())
        
        mcp_json_path = discover_project_mcp_json()
        if mcp_json_path:
            self._project_servers = load_project_mcp_json(mcp_json_path)
            return self._project_servers
        
        return []
    
    def merge_project_servers(self):
        """Merge project-scoped servers into settings."""
        if not self._project_servers:
            return
        
        existing_names = {s.name for s in self.settings.servers}
        for server in self._project_servers:
            if server.name not in existing_names:
                self.settings.servers.append(server)
    
    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process configuration, substituting environment variables."""
        return self._substitute_env_vars(config)
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in configuration values."""
        if isinstance(value, str):
            return self._substitute_env_var(value)
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        return value
    
    def _substitute_env_var(self, value: str) -> str:
        """Substitute environment variables in a string."""
        def replace(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name, '')
            return env_value
        
        return self.ENV_VAR_PATTERN.sub(replace, value)
    
    @property
    def settings(self) -> MCPSettings:
        """Get current settings."""
        if self._settings is None:
            self._settings = MCPSettings()
        return self._settings
    
    def get_server_configs(self) -> List[tuple]:
        """
        Get all server configurations.
        
        Returns:
            List of tuples (name, MCPServerConfig, auto_start, description, version)
        """
        result = []
        for server_def in self.settings.servers:
            transport_type = TransportType.SSE if server_def.transport == "sse" else TransportType.STDIO
            
            oauth_config = None
            if server_def.client_id or server_def.client_secret or server_def.oauth_metadata_url:
                oauth_config = OAuthConfig(
                    client_id=server_def.client_id,
                    client_secret=server_def.client_secret,
                    metadata_url=server_def.oauth_metadata_url,
                )
            
            config = MCPServerConfig(
                command=server_def.command,
                args=server_def.args,
                env=server_def.env,
                cwd=server_def.cwd,
                timeout=server_def.timeout,
                transport=transport_type,
                url=server_def.url,
                oauth=oauth_config,
                instructions=server_def.instructions,
            )
            result.append((
                server_def.name,
                config,
                server_def.auto_start,
                server_def.description,
                server_def.version,
            ))
        return result
    
    def get_server_config(self, name: str) -> Optional[tuple]:
        """
        Get a specific server configuration by name.
        
        Args:
            name: Server name
            
        Returns:
            Tuple (name, MCPServerConfig, auto_start, description, version) or None
        """
        for server_def in self.settings.servers:
            if server_def.name == name:
                transport_type = TransportType.SSE if server_def.transport == "sse" else TransportType.STDIO
                
                oauth_config = None
                if server_def.client_id or server_def.client_secret or server_def.oauth_metadata_url:
                    oauth_config = OAuthConfig(
                        client_id=server_def.client_id,
                        client_secret=server_def.client_secret,
                        metadata_url=server_def.oauth_metadata_url,
                    )
                
                config = MCPServerConfig(
                    command=server_def.command,
                    args=server_def.args,
                    env=server_def.env,
                    cwd=server_def.cwd,
                    timeout=server_def.timeout,
                    transport=transport_type,
                    url=server_def.url,
                    oauth=oauth_config,
                    instructions=server_def.instructions,
                )
                return (
                    server_def.name,
                    config,
                    server_def.auto_start,
                    server_def.description,
                    server_def.version,
                )
        return None
    
    def add_server(self, server_def: MCPServerDefinition) -> None:
        """Add a server definition to the configuration."""
        if self._settings is None:
            self._settings = MCPSettings()
        self._settings.servers.append(server_def)
    
    def remove_server(self, name: str) -> bool:
        """Remove a server definition by name."""
        if self._settings is None:
            return False
        
        for i, server in enumerate(self._settings.servers):
            if server.name == name:
                self._settings.servers.pop(i)
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary."""
        return self.settings.model_dump()
    
    def save_to_yaml(self, path: Optional[str] = None) -> None:
        """
        Save configuration to a YAML file.
        
        Args:
            path: Path to save to (uses config_path if not specified)
        """
        import yaml
        
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No path specified for saving configuration")
        
        config_dict = {'mcp': self.to_dict()}
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


def load_mcp_config(config_path: Optional[str] = None, load_project_scope: bool = True) -> MCPConfig:
    """
    Load MCP configuration from a file, optionally including project-scoped .mcp.json.
    
    Args:
        config_path: Path to configuration file
        load_project_scope: Whether to also load project-scoped .mcp.json
        
    Returns:
        MCPConfig instance
    """
    config = MCPConfig(config_path)
    
    if config_path and Path(config_path).exists():
        config.load_from_yaml(config_path)
    
    if load_project_scope:
        config.load_project_scope()
        config.merge_project_servers()
    
    return config


def create_default_mcp_config() -> MCPSettings:
    """Create default MCP settings."""
    return MCPSettings(
        enabled=True,
        servers=[],
        default_timeout=30,
        max_concurrent_calls=10,
        auto_register_tools=True,
        lazy_load_tools=False,
        auto_lazy_load_threshold=0.1,
    )
