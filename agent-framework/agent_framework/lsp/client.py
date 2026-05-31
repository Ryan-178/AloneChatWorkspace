"""
LSP客户端基类 / LSP Client Base Class

基于asyncio的LSP 3.16协议实现
Asyncio-based LSP 3.16 protocol implementation
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .types import (
    Diagnostic,
    Position,
    Range,
    TextDocumentItem,
    TextDocumentIdentifier,
    VersionedTextDocumentIdentifier,
    TextDocumentContentChangeEvent,
    PublishDiagnosticsParams,
)

logger = logging.getLogger(__name__)


class LSPClient:
    """
    LSP客户端基类 / LSP Client Base Class

    实现LSP 3.16协议的基本通信
    Implements basic communication for LSP 3.16 protocol
    """

    def __init__(
        self,
        language: str,
        command: str,
        args: List[str] = None,
        cwd: Optional[str] = None,
    ):
        self.language = language
        self.command = command
        self.args = args or []
        self.cwd = cwd

        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._diagnostics_handler: Optional[Callable[[str, List[Diagnostic]], None]] = None
        self._initialized = False
        self._shutdown = False
        self._root_uri: Optional[str] = None

    async def start(self, root_path: Optional[str] = None) -> bool:
        """
        启动LSP服务器 / Start LSP server
        """
        if self._process is not None:
            return True

        try:
            cwd = self.cwd or root_path or str(Path.cwd())
            cmd = [self.command] + self.args

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            self._reader_task = asyncio.create_task(self._read_loop())

            if root_path:
                self._root_uri = Path(root_path).as_uri()

            await self._initialize()

            logger.info(f"LSP server started for {self.language}: {self.command}")
            return True

        except Exception as e:
            logger.error(f"Failed to start LSP server for {self.language}: {e}")
            return False

    async def stop(self) -> None:
        """
        停止LSP服务器 / Stop LSP server
        """
        if self._process is None:
            return

        try:
            if not self._shutdown:
                await self._shutdown_server()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")

        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            except Exception:
                pass

        self._process = None
        self._reader_task = None
        self._initialized = False
        self._shutdown = False
        logger.info(f"LSP server stopped for {self.language}")

    async def _initialize(self) -> Dict[str, Any]:
        """
        发送initialize请求 / Send initialize request
        """
        params: Dict[str, Any] = {
            "processId": None,
            "clientInfo": {
                "name": "AloneChat",
                "version": "0.2.3",
            },
            "capabilities": {
                "textDocument": {
                    "publishDiagnostics": {
                        "relatedInformation": True,
                        "tagSupport": {"valueSet": [1, 2]},
                    },
                    "synchronization": {
                        "dynamicRegistration": True,
                        "willSave": True,
                        "willSaveWaitUntil": True,
                        "didSave": True,
                    },
                },
            },
            "trace": "off",
        }

        if self._root_uri:
            params["rootUri"] = self._root_uri
            params["workspaceFolders"] = [
                {
                    "uri": self._root_uri,
                    "name": Path(self._root_uri).name,
                }
            ]

        result = await self._send_request("initialize", params)
        self._initialized = True

        await self._send_notification("initialized", {})

        return result

    async def _shutdown_server(self) -> None:
        """
        发送shutdown请求 / Send shutdown request
        """
        await self._send_request("shutdown", None)
        await self._send_notification("exit", None)
        self._shutdown = True

    async def did_open(
        self,
        file_path: str,
        language_id: str,
        version: int,
        content: str,
    ) -> None:
        """
        通知服务器文档已打开 / Notify server that document was opened
        """
        if not self._initialized:
            return

        uri = Path(file_path).as_uri()
        params = {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": version,
                "text": content,
            }
        }
        await self._send_notification("textDocument/didOpen", params)

    async def did_change(
        self,
        file_path: str,
        version: int,
        changes: List[TextDocumentContentChangeEvent],
    ) -> None:
        """
        通知服务器文档已变更 / Notify server that document was changed
        """
        if not self._initialized:
            return

        uri = Path(file_path).as_uri()
        content_changes = []
        for change in changes:
            change_dict: Dict[str, Any] = {"text": change.text}
            if change.range:
                change_dict["range"] = change.range.to_lsp()
            if change.range_length is not None:
                change_dict["rangeLength"] = change.range_length
            content_changes.append(change_dict)

        params = {
            "textDocument": {
                "uri": uri,
                "version": version,
            },
            "contentChanges": content_changes,
        }
        await self._send_notification("textDocument/didChange", params)

    async def did_close(self, file_path: str) -> None:
        """
        通知服务器文档已关闭 / Notify server that document was closed
        """
        if not self._initialized:
            return

        uri = Path(file_path).as_uri()
        params = {
            "textDocument": {"uri": uri}
        }
        await self._send_notification("textDocument/didClose", params)

    async def did_save(self, file_path: str, version: Optional[int] = None) -> None:
        """
        通知服务器文档已保存 / Notify server that document was saved
        """
        if not self._initialized:
            return

        uri = Path(file_path).as_uri()
        text_document: Dict[str, Any] = {"uri": uri}
        if version is not None:
            text_document["version"] = version

        params = {"textDocument": text_document}
        await self._send_notification("textDocument/didSave", params)

    def set_diagnostics_handler(
        self,
        handler: Callable[[str, List[Diagnostic]], None]
    ) -> None:
        """
        设置诊断结果处理器 / Set diagnostics handler
        """
        self._diagnostics_handler = handler

    async def _send_request(
        self,
        method: str,
        params: Optional[Any],
    ) -> Any:
        """
        发送请求并等待响应 / Send request and wait for response
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("LSP server not running")

        self._request_id += 1
        request_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        await self._write_message(message)

        return await future

    async def _send_notification(self, method: str, params: Optional[Any]) -> None:
        """
        发送通知 / Send notification
        """
        if self._process is None or self._process.stdin is None:
            return

        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            message["params"] = params

        await self._write_message(message)

    async def _write_message(self, message: Dict[str, Any]) -> None:
        """
        写入LSP消息 / Write LSP message
        """
        if self._process is None or self._process.stdin is None:
            return

        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"

        self._process.stdin.write(header.encode("utf-8"))
        self._process.stdin.write(content.encode("utf-8"))
        await self._process.stdin.drain()

    async def _read_loop(self) -> None:
        """
        读取响应循环 / Read response loop
        """
        if self._process is None or self._process.stdout is None:
            return

        buffer = b""
        while True:
            try:
                chunk = await self._process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk

                while b"\r\n\r\n" in buffer:
                    header_end = buffer.index(b"\r\n\r\n")
                    header = buffer[:header_end].decode("utf-8")
                    buffer = buffer[header_end + 4:]

                    content_length = 0
                    for line in header.split("\r\n"):
                        if line.startswith("Content-Length:"):
                            content_length = int(line.split(":")[1].strip())
                            break

                    if content_length > 0:
                        while len(buffer) < content_length:
                            more = await self._process.stdout.read(content_length - len(buffer))
                            if not more:
                                break
                            buffer += more

                        content = buffer[:content_length].decode("utf-8")
                        buffer = buffer[content_length:]

                        try:
                            message = json.loads(content)
                            await self._handle_message(message)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse LSP message: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                break

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息 / Handle received message
        """
        if "id" in message:
            request_id = message["id"]
            if request_id in self._pending_requests:
                future = self._pending_requests.pop(request_id)
                if "error" in message:
                    future.set_exception(Exception(message["error"]))
                else:
                    future.set_result(message.get("result"))

        elif "method" in message:
            method = message["method"]
            params = message.get("params", {})

            if method == "textDocument/publishDiagnostics":
                await self._handle_diagnostics(params)

    async def _handle_diagnostics(self, params: Dict[str, Any]) -> None:
        """
        处理诊断结果 / Handle diagnostics
        """
        diagnostics_params = PublishDiagnosticsParams.from_lsp(params)

        if self._diagnostics_handler:
            try:
                self._diagnostics_handler(
                    diagnostics_params.uri,
                    diagnostics_params.diagnostics,
                )
            except Exception as e:
                logger.error(f"Error in diagnostics handler: {e}")

    @property
    def is_running(self) -> bool:
        """检查服务器是否运行中 / Check if server is running"""
        return self._process is not None and self._initialized
