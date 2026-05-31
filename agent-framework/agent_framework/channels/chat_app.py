"""
聊天应用通道适配器 - Chat App Channel Adapter
集成项目自带的聊天应用
"""
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseChannel, ChannelMessage, ChannelUser, MessageType


class ChatAppChannel(BaseChannel):
    """聊天应用通道适配器"""
    
    def __init__(self, channel_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(channel_id, config)
        self._users: Dict[str, ChannelUser] = {}
        self._messages: Dict[str, ChannelMessage] = {}
        self._websocket_clients: Dict[str, Any] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        """连接到聊天应用"""
        self._log_info("Connecting to Chat App...")
        
        # 初始化一些示例用户
        self._users = {
            "user_1": ChannelUser(
                user_id="user_1",
                username="alice",
                display_name="Alice",
                metadata={"role": "admin"}
            ),
            "user_2": ChannelUser(
                user_id="user_2",
                username="bob",
                display_name="Bob",
                metadata={"role": "user"}
            )
        }
        
        # 启动消息处理worker
        self._worker_task = asyncio.create_task(self._message_worker())
        
        self._log_info("Connected to Chat App")
    
    async def disconnect(self):
        """断开连接"""
        self._log_info("Disconnecting from Chat App...")
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        self._websocket_clients.clear()
        self._log_info("Disconnected from Chat App")
    
    async def send_message(
        self,
        content: str,
        user_id: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """发送消息到聊天应用"""
        message_id = str(uuid.uuid4())
        
        system_user = ChannelUser(
            user_id="system",
            username="agent_system",
            display_name="Agent System"
        )
        
        message = ChannelMessage(
            message_id=message_id,
            channel_id=self.channel_id,
            user=system_user,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
            attachments=attachments or [],
            metadata=metadata or {}
        )
        
        self._messages[message_id] = message
        
        # 发送到连接的WebSocket客户端
        await self._broadcast_to_websockets(message)
        
        self._log_info(f"Sent message: {message_id}")
        return message_id
    
    async def send_reply(
        self,
        reply_to: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """回复消息"""
        message_id = str(uuid.uuid4())
        
        system_user = ChannelUser(
            user_id="system",
            username="agent_system",
            display_name="Agent System"
        )
        
        message = ChannelMessage(
            message_id=message_id,
            channel_id=self.channel_id,
            user=system_user,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
            attachments=attachments or [],
            metadata=metadata or {},
            reply_to=reply_to
        )
        
        self._messages[message_id] = message
        await self._broadcast_to_websockets(message)
        
        self._log_info(f"Sent reply to {reply_to}: {message_id}")
        return message_id
    
    async def get_user(self, user_id: str) -> Optional[ChannelUser]:
        """获取用户信息"""
        return self._users.get(user_id)
    
    async def _message_worker(self):
        """消息处理worker"""
        self._log_info("Message worker started")
        
        try:
            while True:
                message = await self._message_queue.get()
                try:
                    await self._dispatch_message(message)
                finally:
                    self._message_queue.task_done()
        except asyncio.CancelledError:
            self._log_info("Message worker stopped")
    
    async def _broadcast_to_websockets(self, message: ChannelMessage):
        """广播消息到WebSocket客户端"""
        for client_id, client in self._websocket_clients.items():
            try:
                if hasattr(client, 'send_json'):
                    await client.send_json({
                        "message_id": message.message_id,
                        "channel_id": message.channel_id,
                        "user": {
                            "user_id": message.user.user_id,
                            "username": message.user.username,
                            "display_name": message.user.display_name
                        },
                        "content": message.content,
                        "message_type": message.message_type,
                        "timestamp": message.timestamp.isoformat(),
                        "attachments": message.attachments,
                        "metadata": message.metadata,
                        "reply_to": message.reply_to
                    })
            except Exception as e:
                self._log_error(f"Failed to send to client {client_id}: {e}")
    
    async def receive_from_chat_app(
        self,
        user_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从聊天应用接收消息（供聊天应用后端调用）"""
        message_id = str(uuid.uuid4())
        
        user = await self.get_user(user_id)
        if not user:
            user = ChannelUser(
                user_id=user_id,
                username=user_id,
                display_name=user_id
            )
            self._users[user_id] = user
        
        message = ChannelMessage(
            message_id=message_id,
            channel_id=self.channel_id,
            user=user,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
            attachments=attachments or [],
            metadata=metadata or {}
        )
        
        self._messages[message_id] = message
        
        # 放入队列处理
        await self._message_queue.put(message)
        
        self._log_info(f"Received message from {user_id}: {message_id}")
        return message_id
    
    async def register_websocket(self, client_id: str, websocket: Any):
        """注册WebSocket客户端"""
        self._websocket_clients[client_id] = websocket
        self._log_info(f"WebSocket client registered: {client_id}")
    
    async def unregister_websocket(self, client_id: str):
        """注销WebSocket客户端"""
        if client_id in self._websocket_clients:
            del self._websocket_clients[client_id]
            self._log_info(f"WebSocket client unregistered: {client_id}")
    
    def get_message_history(self, limit: int = 50) -> List[ChannelMessage]:
        """获取消息历史"""
        sorted_messages = sorted(
            self._messages.values(),
            key=lambda m: m.timestamp,
            reverse=True
        )
        return sorted_messages[:limit]
