"""
通道适配器基类 - Base Channel Adapter
定义通道适配器的通用接口
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


@dataclass
class ChannelUser:
    """通道用户"""
    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelMessage:
    """通道消息"""
    message_id: str
    channel_id: str
    user: ChannelUser
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None


class BaseChannel(ABC):
    """通道适配器基类"""
    
    def __init__(self, channel_id: str, config: Optional[Dict[str, Any]] = None):
        self.channel_id = channel_id
        self.config = config or {}
        self._message_handlers: List[Callable[[ChannelMessage], Any]] = []
        self._running = False
    
    def add_message_handler(self, handler: Callable[[ChannelMessage], Any]):
        """添加消息处理器"""
        self._message_handlers.append(handler)
        return self
    
    def remove_message_handler(self, handler: Callable[[ChannelMessage], Any]):
        """移除消息处理器"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
        return self
    
    async def _dispatch_message(self, message: ChannelMessage):
        """分发消息到所有处理器"""
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self._log_error(f"Error in message handler: {e}")
    
    @abstractmethod
    async def connect(self):
        """连接到通道"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        content: str,
        user_id: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """发送消息"""
        pass
    
    @abstractmethod
    async def send_reply(
        self,
        reply_to: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """回复消息"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[ChannelUser]:
        """获取用户信息"""
        pass
    
    def _log_info(self, message: str):
        """记录信息日志"""
        print(f"[Channel {self.channel_id}] INFO: {message}")
    
    def _log_error(self, message: str):
        """记录错误日志"""
        print(f"[Channel {self.channel_id}] ERROR: {message}")
    
    async def start(self):
        """启动通道"""
        if self._running:
            return
        
        self._running = True
        await self.connect()
        self._log_info("Channel started")
    
    async def stop(self):
        """停止通道"""
        if not self._running:
            return
        
        self._running = False
        await self.disconnect()
        self._log_info("Channel stopped")
