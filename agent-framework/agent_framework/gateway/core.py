import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from .router import MessageRouter
from .tools import ToolExecutor

logger = logging.getLogger(__name__)


class GatewayCore:
    """
    Gateway Core - 网关核心
    处理WebSocket连接和消息路由
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 18789,
        auth_secret: Optional[str] = None,
        max_request_size: int = 1024 * 1024,  # 1MB 默认请求大小限制
    ):
        self.host = host
        self.port = port
        self.router = MessageRouter()
        self.tool_executor = ToolExecutor()
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.auth_secret = auth_secret
        self.max_request_size = max_request_size

    async def start(self):
        """启动网关服务器"""
        logger.info(f"Starting gateway server on {self.host}:{self.port}")
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
        ):
            await asyncio.Future()  # 永久运行

    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理新的WebSocket连接"""
        connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New connection from {connection_id}")

        self.connections[connection_id] = websocket
        self.sessions[connection_id] = {
            "connected_at": datetime.now(),
            "authenticated": False,
            "user_id": None,
            "session_id": None,
        }

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(connection_id, websocket, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._send_error(websocket, "Internal server error")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection {connection_id} closed")
        finally:
            del self.connections[connection_id]
            del self.sessions[connection_id]

    async def _authenticate(self, connection_id: str, data: Dict[str, Any]) -> bool:
        """
        验证连接身份。
        需要有效的 token 才能通过认证。
        """
        session = self.sessions[connection_id]

        # 如果已经认证，直接返回
        if session.get("authenticated"):
            return True

        # 获取认证 token
        token = data.get("token")
        if not token:
            logger.warning(f"Authentication failed for {connection_id}: missing token")
            return False

        # 验证 token（简化实现，实际应该使用 JWT 验证）
        if self.auth_secret:
            try:
                import jwt
                payload = jwt.decode(token, self.auth_secret, algorithms=["HS256"])
                session["user_id"] = payload.get("sub")
                session["session_id"] = data.get("session_id")
                session["authenticated"] = True
                logger.info(f"User {session['user_id']} authenticated on {connection_id}")
                return True
            except jwt.ExpiredSignatureError:
                logger.warning(f"Authentication failed for {connection_id}: token expired")
                return False
            except jwt.InvalidTokenError:
                logger.warning(f"Authentication failed for {connection_id}: invalid token")
                return False
        else:
            # 如果没有配置 auth_secret，拒绝所有连接（安全默认）
            logger.warning(f"Authentication failed for {connection_id}: auth_secret not configured")
            return False

    async def _process_message(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        data: Dict[str, Any],
    ):
        """处理消息"""
        msg_type = data.get("type", "unknown")

        # 处理连接消息 - 需要认证
        if msg_type == "connect":
            if not await self._authenticate(connection_id, data):
                await self._send_error(websocket, "Authentication failed", code=401)
                await websocket.close(code=4001, reason="Authentication failed")
                return

            await self._handle_connect(connection_id, websocket, data)
            return

        # 对于其他消息，必须先通过认证
        session = self.sessions.get(connection_id)
        if not session or not session.get("authenticated"):
            await self._send_error(websocket, "Not authenticated", code=401)
            return

        session["last_seen"] = datetime.now()

        # 处理不同类型的消息
        if msg_type == "message":
            await self._handle_message(connection_id, websocket, data)
        elif msg_type == "tool_call":
            await self._handle_tool_call(connection_id, websocket, data)
        elif msg_type == "heartbeat":
            await self._handle_heartbeat(connection_id, websocket)
        else:
            await self._send_error(websocket, f"Unknown message type: {msg_type}")

    async def _handle_connect(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        data: Dict[str, Any],
    ):
        """处理连接建立"""
        session = self.sessions[connection_id]
        session["session_id"] = data.get("session_id")
        session["user_id"] = data.get("user_id")

        await websocket.send(
            json.dumps(
                {
                    "type": "connected",
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    async def _handle_message(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        data: Dict[str, Any],
    ):
        """处理普通消息"""
        # 路由消息
        target = data.get("target")
        if target:
            await self.router.route_message(target, data)
        else:
            # 广播给所有连接
            for conn_id, conn in self.connections.items():
                if conn_id != connection_id:
                    try:
                        await conn.send(json.dumps(data))
                    except Exception as e:
                        logger.error(f"Error sending to {conn_id}: {e}")

    async def _handle_tool_call(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
        data: Dict[str, Any],
    ):
        """处理工具调用"""
        tool_name = data.get("tool")
        params = data.get("params", {})

        try:
            result = await self.tool_executor.execute(tool_name, params)
            await websocket.send(
                json.dumps(
                    {
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result,
                    }
                )
            )
        except Exception as e:
            await self._send_error(websocket, f"Tool execution failed: {str(e)}")

    async def _handle_heartbeat(
        self,
        connection_id: str,
        websocket: WebSocketServerProtocol,
    ):
        """处理心跳"""
        await websocket.send(json.dumps({"type": "pong"}))

    async def _send_error(
        self,
        websocket: WebSocketServerProtocol,
        message: str,
        code: int = 400,
    ):
        """发送错误响应"""
        await websocket.send(
            json.dumps({"type": "error", "message": message, "code": code})
        )

    def register_handler(self, msg_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[msg_type] = handler

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理HTTP请求"""
        # 检查请求体大小
        body = request.get("body", "")
        if isinstance(body, (str, bytes)) and len(body) > self.max_request_size:
            return {
                "status": 413,
                "body": json.dumps({"error": "Request body too large"}),
            }

        try:
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
        except json.JSONDecodeError:
            return {
                "status": 400,
                "body": json.dumps({"error": "Invalid JSON"}),
            }

        msg_type = data.get("type", "unknown")

        if msg_type in self.message_handlers:
            handler = self.message_handlers[msg_type]
            result = await handler(data)
            return {"status": 200, "body": json.dumps(result)}

        return {
            "status": 400,
            "body": json.dumps({"error": f"Unknown message type: {msg_type}"}),
        }
