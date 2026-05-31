"""
LSP服务器管理器 / LSP Server Manager

管理多个语言服务器实例
Manages multiple language server instances
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .client import LSPClient
from .types import Diagnostic

logger = logging.getLogger(__name__)


class LSPManager:
    """
    LSP服务器管理器 / LSP Server Manager

    管理多个语言服务器，提供统一的诊断接口
    Manages multiple language servers, provides unified diagnostic interface
    """

    LANGUAGE_MAP = {
        ".py": "python",
        ".pyw": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".lua": "lua",
        ".vim": "vim",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
    }

    def __init__(self, config_path: Optional[str] = None):
        self._clients: Dict[str, LSPClient] = {}
        self._config: Dict[str, Any] = {}
        self._diagnostics_cache: Dict[str, List[Diagnostic]] = {}
        self._diagnostics_handlers: List[Callable[[str, str, List[Diagnostic]], None]] = []
        self._root_path: Optional[str] = None
        self._enabled = True
        self._debounce_ms = 500
        self._max_diagnostics = 100

        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: str) -> None:
        """
        加载配置文件 / Load configuration file
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    lsp_config = config.get("lsp", {})
                    self._enabled = lsp_config.get("enabled", True)
                    self._debounce_ms = lsp_config.get("diagnostics", {}).get("debounce_ms", 500)
                    self._max_diagnostics = lsp_config.get("diagnostics", {}).get("max_diagnostics", 100)
                    self._config = lsp_config.get("servers", {})
        except Exception as e:
            logger.warning(f"Failed to load LSP config: {e}")

    def get_language(self, file_path: str) -> Optional[str]:
        """
        根据文件扩展名获取语言类型 / Get language type from file extension
        """
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAP.get(ext)

    async def get_client(self, language: str) -> Optional[LSPClient]:
        """
        获取或创建语言服务器客户端 / Get or create language server client
        """
        if not self._enabled:
            return None

        if language in self._clients:
            return self._clients[language]

        server_config = self._config.get(language, {})
        if not server_config:
            default_configs = self._get_default_server_configs()
            server_config = default_configs.get(language, {})

        if not server_config:
            logger.debug(f"No LSP server configured for language: {language}")
            return None

        command = server_config.get("command")
        if not command:
            return None

        args = server_config.get("args", [])

        client = LSPClient(
            language=language,
            command=command,
            args=args,
        )

        client.set_diagnostics_handler(
            lambda uri, diagnostics: self._on_diagnostics(language, uri, diagnostics)
        )

        if self._root_path:
            success = await client.start(self._root_path)
            if not success:
                logger.warning(f"Failed to start LSP server for {language}")
                return None

        self._clients[language] = client
        return client

    def _get_default_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取默认服务器配置 / Get default server configurations
        """
        return {
            "python": {
                "command": "pyright-langserver",
                "args": ["--stdio"],
            },
            "typescript": {
                "command": "typescript-language-server",
                "args": ["--stdio"],
            },
            "javascript": {
                "command": "typescript-language-server",
                "args": ["--stdio"],
            },
            "go": {
                "command": "gopls",
                "args": [],
            },
            "rust": {
                "command": "rust-analyzer",
                "args": [],
            },
        }

    async def start(self, root_path: str) -> None:
        """
        启动管理器 / Start manager
        """
        self._root_path = root_path
        logger.info(f"LSP manager started with root path: {root_path}")

    async def stop(self) -> None:
        """
        停止所有服务器 / Stop all servers
        """
        for language, client in self._clients.items():
            try:
                await client.stop()
            except Exception as e:
                logger.warning(f"Error stopping LSP server for {language}: {e}")

        self._clients.clear()
        self._diagnostics_cache.clear()
        logger.info("LSP manager stopped")

    async def open_document(
        self,
        file_path: str,
        content: str,
        version: int = 1,
    ) -> None:
        """
        打开文档 / Open document
        """
        language = self.get_language(file_path)
        if not language:
            return

        client = await self.get_client(language)
        if not client:
            return

        await client.did_open(file_path, language, version, content)

    async def change_document(
        self,
        file_path: str,
        version: int,
        new_content: str,
        old_content: Optional[str] = None,
    ) -> None:
        """
        文档变更 / Document changed
        """
        language = self.get_language(file_path)
        if not language:
            return

        client = await self.get_client(language)
        if not client:
            return

        from .types import TextDocumentContentChangeEvent

        change = TextDocumentContentChangeEvent(text=new_content)
        await client.did_change(file_path, version, [change])

    async def close_document(self, file_path: str) -> None:
        """
        关闭文档 / Close document
        """
        language = self.get_language(file_path)
        if not language:
            return

        client = self._clients.get(language)
        if client:
            await client.did_close(file_path)

        uri = Path(file_path).as_uri()
        if uri in self._diagnostics_cache:
            del self._diagnostics_cache[uri]

    async def save_document(self, file_path: str, version: Optional[int] = None) -> None:
        """
        保存文档 / Save document
        """
        language = self.get_language(file_path)
        if not language:
            return

        client = self._clients.get(language)
        if client:
            await client.did_save(file_path, version)

    def get_diagnostics(self, file_path: str) -> List[Diagnostic]:
        """
        获取文档的诊断结果 / Get diagnostics for document
        """
        uri = Path(file_path).as_uri()
        return self._diagnostics_cache.get(uri, [])

    def get_all_diagnostics(self) -> Dict[str, List[Diagnostic]]:
        """
        获取所有诊断结果 / Get all diagnostics
        """
        return self._diagnostics_cache.copy()

    def get_diagnostics_summary(self) -> Dict[str, int]:
        """
        获取诊断统计 / Get diagnostics summary
        """
        errors = 0
        warnings = 0
        info = 0
        hints = 0

        for diagnostics in self._diagnostics_cache.values():
            for d in diagnostics:
                if d.is_error():
                    errors += 1
                elif d.is_warning():
                    warnings += 1
                elif d.severity.value == 3:
                    info += 1
                else:
                    hints += 1

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "hints": hints,
            "total": errors + warnings + info + hints,
        }

    def add_diagnostics_handler(
        self,
        handler: Callable[[str, str, List[Diagnostic]], None]
    ) -> None:
        """
        添加诊断处理器 / Add diagnostics handler
        """
        self._diagnostics_handlers.append(handler)

    def remove_diagnostics_handler(
        self,
        handler: Callable[[str, str, List[Diagnostic]], None]
    ) -> None:
        """
        移除诊断处理器 / Remove diagnostics handler
        """
        if handler in self._diagnostics_handlers:
            self._diagnostics_handlers.remove(handler)

    def _on_diagnostics(
        self,
        language: str,
        uri: str,
        diagnostics: List[Diagnostic],
    ) -> None:
        """
        处理诊断结果回调 / Handle diagnostics callback
        """
        limited_diagnostics = diagnostics[:self._max_diagnostics]
        self._diagnostics_cache[uri] = limited_diagnostics

        for handler in self._diagnostics_handlers:
            try:
                handler(language, uri, limited_diagnostics)
            except Exception as e:
                logger.error(f"Error in diagnostics handler: {e}")

    @property
    def is_enabled(self) -> bool:
        """检查LSP是否启用 / Check if LSP is enabled"""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """设置LSP启用状态 / Set LSP enabled state"""
        self._enabled = enabled

    @property
    def active_languages(self) -> List[str]:
        """获取活跃的语言服务器列表 / Get list of active language servers"""
        return list(self._clients.keys())
