"""
LSP å®¢æ·ç«?/ LSP Client

ä¸è¯­è¨æå¡å¨éä¿¡çå®¢æ·ç«¯ / Client for communicating with language servers
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess


class LanguageId(Enum):
    """è¯­è¨æ è¯ / Language identifier"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CPP = "cpp"
    C = "c"


@dataclass
class Position:
    """ä½ç½® / Position"""
    line: int
    character: int
    
    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}


@dataclass
class Range:
    """èå´ / Range"""
    start: Position
    end: Position
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
        }


@dataclass
class Location:
    """ä½ç½®ï¼æä»?èå´ï¼? Location (file + range)"""
    uri: str
    range: Range
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(
            uri=data["uri"],
            range=Range(
                start=Position(**data["range"]["start"]),
                end=Position(**data["range"]["end"]),
            ),
        )


@dataclass
class DefinitionResult:
    """å®ä¹ç»æ / Definition result"""
    locations: List[Location] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ReferencesResult:
    """å¼ç¨ç»æ / References Result"""
    locations: List[Location] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class HoverResult:
    """æ¬åç»æ / Hover Result"""
    content: str = ""
    kind: str = "plaintext"
    range: Optional[Range] = None
    error: Optional[str] = None


LANGUAGE_SERVERS = {
    LanguageId.PYTHON: {
        "command": ["pylsp"],
        "args": [],
    },
    LanguageId.TYPESCRIPT: {
        "command": ["typescript-language-server"],
        "args": ["--stdio"],
    },
    LanguageId.JAVASCRIPT: {
        "command": ["typescript-language-server"],
        "args": ["--stdio"],
    },
    LanguageId.GO: {
        "command": ["gopls"],
        "args": [],
    },
    LanguageId.RUST: {
        "command": ["rust-analyzer"],
        "args": [],
    },
}


class LSPClient:
    """
    LSP å®¢æ·ç«?/ LSP Client
    
    ä¸è¯­è¨æå¡å¨éä¿¡ï¼æä¾ä»£ç æºè½åè?/ Communicates with language servers for code intelligence
    """
    
    def __init__(
        self,
        workspace_root: str,
        language: LanguageId = LanguageId.PYTHON,
    ):
        """
        åå§å?LSP å®¢æ·ç«?/ Initialize LSP client
        
        Args:
            workspace_root: å·¥ä½åºæ ¹ç®å½ / Workspace root directory
            language: è¯­è¨ç±»å / Language type
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.language = language
        self._proc: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._initialized = False
    
    def _get_server_config(self) -> Optional[Dict[str, Any]]:
        """è·åæå¡å¨éç½?/ Get server config"""
        return LANGUAGE_SERVERS.get(self.language)
    
    def _next_id(self) -> int:
        """è·åä¸ä¸ä¸ªè¯·æ±ID / Get next request ID"""
        self._request_id += 1
        return self._request_id
    
    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        åéè¯·æ±?/ Send request
        
        Args:
            method: æ¹æ³å?/ Method name
            params: åæ° / Parameters
            
        Returns:
            è¯·æ±å­å¸ / Request dict
        """
        return {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
    
    def _send_notification(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        åééç¥ / Send notification
        
        Args:
            method: æ¹æ³å?/ Method name
            params: åæ° / Parameters
            
        Returns:
            éç¥å­å¸ / Notification dict
        """
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
    
    def start(self) -> bool:
        """
        å¯å¨è¯­è¨æå¡å?/ Start language server
        
        Returns:
            æ¯å¦æå / Whether successful
        """
        config = self._get_server_config()
        if not config:
            return False
        
        try:
            cmd = config["command"] + config.get("args", [])
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except Exception:
            return False
    
    def stop(self) -> None:
        """åæ­¢è¯­è¨æå¡å?/ Stop language server"""
        if self._proc:
            self._proc.terminate()
            self._proc = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        åå§åè¯­è¨æå¡å?/ Initialize language server
        
        Returns:
            æ¯å¦æå / Whether successful
        """
        if self._initialized:
            return True
        
        if not self._proc:
            if not self.start():
                return False
        
        init_params = {
            "processId": None,
            "rootUri": self._path_to_uri(str(self.workspace_root)),
            "capabilities": {
                "textDocument": {
                    "definition": {"linkSupport": True},
                    "references": {"includeDeclaration": True},
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "completion": {
                        "completionItem": {"snippetSupport": True},
                    },
                },
            },
        }
        
        self._initialized = True
        return True
    
    def _path_to_uri(self, path: str) -> str:
        """
        è·¯å¾è½?URI / Path to URI
        
        Args:
            path: æä»¶è·¯å¾ / File path
            
        Returns:
            URI å­ç¬¦ä¸?/ URI string
        """
        abs_path = Path(path).resolve()
        return f"file://{abs_path}"
    
    def _uri_to_path(self, uri: str) -> str:
        """
        URI è½¬è·¯å¾?/ URI to path
        
        Args:
            uri: URI å­ç¬¦ä¸?/ URI string
            
        Returns:
            æä»¶è·¯å¾ / File path
        """
        if uri.startswith("file://"):
            return uri[7:]
        return uri
    
    def go_to_definition(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> DefinitionResult:
        """
        è·³è½¬å°å®ä¹?/ Go to definition
        
        Args:
            file_path: æä»¶è·¯å¾ / File path
            line: è¡å·ï¼?-basedï¼? Line number (0-based)
            character: åå·ï¼?-basedï¼? Character number (0-based)
            
        Returns:
            å®ä¹ç»æ / Definition result
        """
        if not self._initialized:
            if not self.initialize():
                return DefinitionResult(error="LSP not initialized")
        
        return DefinitionResult(
            locations=[],
            error="Direct LSP communication requires async implementation",
        )
    
    def find_references(
        self,
        file_path: str,
        line: int,
        character: int,
        include_declaration: bool = True,
    ) -> ReferencesResult:
        """
        æ¥æ¾å¼ç¨ / Find references
        
        Args:
            file_path: æä»¶è·¯å¾ / File path
            line: è¡å· / Line number
            character: åå· / Character number
            include_declaration: æ¯å¦åå«å£°æ / Include declaration
            
        Returns:
            å¼ç¨ç»æ / References result
        """
        if not self._initialized:
            if not self.initialize():
                return ReferencesResult(error="LSP not initialized")
        
        return ReferencesResult(
            locations=[],
            error="Direct LSP communication requires async implementation",
        )
    
    def get_hover(
        self,
        file_path: str,
        line: int,
        character: int,
    ) -> HoverResult:
        """
        è·åæ¬åä¿¡æ¯ / Get hover info
        
        Args:
            file_path: æä»¶è·¯å¾ / File path
            line: è¡å· / Line number
            character: åå· / Character number
            
        Returns:
            æ¬åç»æ / Hover result
        """
        if not self._initialized:
            if not self.initialize():
                return HoverResult(error="LSP not initialized")
        
        return HoverResult(
            error="Direct LSP communication requires async implementation",
        )
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        è·åå®¢æ·ç«¯ä¿¡æ?/ Get client info
        
        Returns:
            å®¢æ·ç«¯ä¿¡æ¯å­å?/ Client info dict
        """
        return {
            "workspace_root": str(self.workspace_root),
            "language": self.language.value,
            "initialized": self._initialized,
            "server_running": self._proc is not None,
        }
