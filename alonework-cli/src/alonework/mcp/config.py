"""
MCPéç½®ç®¡ç / MCP Configuration Management

ç®¡çMCPæå¡å¨éç½?/ Manages MCP server configurations

æ¯æ / Supports:
- åºæ¬éç½® / Basic config (command, args, env)
- SSEä¼ è¾ / SSE transport (transport, url)
- OAuthå­æ® / OAuth credentials (client_id, client_secret, oauth_metadata_url)
- æå¡å¨æä»?/ Server instructions
- å»¶è¿å è½½ / Lazy loading
- é¡¹ç®ä½ç¨å?/ Project scope (.mcp.json)
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class MCPServerConfig:
    """MCPæå¡å¨éç½?/ MCP server configuration"""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    transport: str = "stdio"
    url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    oauth_metadata_url: Optional[str] = None
    instructions: Optional[str] = None
    lazy_load_enabled: bool = False
    lazy_load_threshold: float = 0.1

    def to_dict(self) -> dict:
        """è½¬æ¢ä¸ºå­å?/ Convert to dict"""
        result = {
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
            "transport": self.transport,
        }
        if self.url:
            result["url"] = self.url
        if self.client_id:
            result["client_id"] = self.client_id
        if self.client_secret:
            result["client_secret"] = self.client_secret
        if self.oauth_metadata_url:
            result["oauth_metadata_url"] = self.oauth_metadata_url
        if self.instructions:
            result["instructions"] = self.instructions
        if self.lazy_load_enabled:
            result["lazy_load_enabled"] = True
            result["lazy_load_threshold"] = self.lazy_load_threshold
        return result

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "MCPServerConfig":
        """ä»å­å¸åå»?/ Create from dict"""
        return cls(
            name=name,
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            enabled=data.get("enabled", True),
            transport=data.get("transport", "stdio"),
            url=data.get("url"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            oauth_metadata_url=data.get("oauth_metadata_url"),
            instructions=data.get("instructions"),
            lazy_load_enabled=data.get("lazy_load_enabled", False),
            lazy_load_threshold=data.get("lazy_load_threshold", 0.1),
        )


class MCPConfigManager:
    """MCPéç½®ç®¡çå?/ MCP configuration manager"""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".alonechat"
        self.config_dir = config_dir
        self.config_file = config_dir / "mcp.json"

        self._servers: dict[str, MCPServerConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """å è½½éç½® / Load config"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                servers = data.get("mcpServers", {})
                for name, server_data in servers.items():
                    self._servers[name] = MCPServerConfig.from_dict(name, server_data)

            except Exception:
                pass

    def _save_config(self) -> None:
        """ä¿å­éç½® / Save config"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        servers = {
            name: server.to_dict()
            for name, server in self._servers.items()
        }

        data = {"mcpServers": servers}

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_server(self, server: MCPServerConfig) -> None:
        """æ·»å æå¡å?/ Add server"""
        self._servers[server.name] = server
        self._save_config()

    def update_server(self, server: MCPServerConfig) -> None:
        """æ´æ°æå¡å¨éç½?/ Update server config"""
        if server.name in self._servers:
            self._servers[server.name] = server
            self._save_config()

    def remove_server(self, name: str) -> bool:
        """ç§»é¤æå¡å?/ Remove server"""
        if name in self._servers:
            del self._servers[name]
            self._save_config()
            return True
        return False

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """è·åæå¡å¨éç½?/ Get server config"""
        return self._servers.get(name)

    def list_servers(self) -> list[MCPServerConfig]:
        """ååºæææå¡å¨ / List all servers"""
        return list(self._servers.values())

    def enable_server(self, name: str) -> bool:
        """å¯ç¨æå¡å?/ Enable server"""
        server = self.get_server(name)
        if server:
            server.enabled = True
            self._save_config()
            return True
        return False

    def disable_server(self, name: str) -> bool:
        """ç¦ç¨æå¡å?/ Disable server"""
        server = self.get_server(name)
        if server:
            server.enabled = False
            self._save_config()
            return True
        return False
