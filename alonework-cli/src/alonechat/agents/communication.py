"""
Agent通信模块 / Agent Communication Module

实现Agent间的消息传递和协调
Implements message passing and coordination between agents
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import asyncio


@dataclass
class Message:
    """
    消息定义 / Message Definition
    
    Agent间传递的消息
    Message passed between agents
    """
    message_id: str
    from_agent: str
    to_agent: str
    content: Any
    message_type: str = "info"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    read: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
            "read": self.read,
            "metadata": self.metadata,
        }
    
    def mark_read(self) -> None:
        """标记为已读 / Mark as read"""
        self.read = True


class MessageBus:
    """
    消息总线 / Message Bus
    
    管理Agent间的消息传递
    Manages message passing between agents
    """
    
    def __init__(self):
        """初始化消息总线 / Initialize message bus"""
        self._queues: dict[str, asyncio.Queue] = {}
        self._history: list[Message] = []
        self._subscribers: dict[str, list[str]] = {}
    
    def register_agent(self, agent_id: str) -> None:
        """
        注册Agent / Register agent
        
        Args:
            agent_id: Agent标识 / Agent identifier
        """
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        注销Agent / Unregister agent
        
        Args:
            agent_id: Agent标识 / Agent identifier
        """
        if agent_id in self._queues:
            del self._queues[agent_id]
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
    
    async def send(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        message_type: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        发送消息 / Send message
        
        Args:
            from_agent: 发送者 / Sender
            to_agent: 接收者 / Receiver
            content: 消息内容 / Message content
            message_type: 消息类型 / Message type
            metadata: 元数据 / Metadata
            
        Returns:
            消息ID / Message ID
        """
        message_id = str(uuid4())
        
        message = Message(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            message_type=message_type,
            metadata=metadata or {},
        )
        
        self._history.append(message)
        
        if len(self._history) > 10000:
            self._history = self._history[-5000:]
        
        if to_agent in self._queues:
            await self._queues[to_agent].put(message)
        
        if to_agent in self._subscribers:
            for subscriber in self._subscribers[to_agent]:
                if subscriber in self._queues:
                    await self._queues[subscriber].put(message)
        
        return message_id
    
    async def receive(
        self,
        agent_id: str,
        timeout: float | None = None,
    ) -> Message | None:
        """
        接收消息 / Receive message
        
        Args:
            agent_id: Agent标识 / Agent identifier
            timeout: 超时时间 / Timeout
            
        Returns:
            消息对象 / Message object
        """
        if agent_id not in self._queues:
            return None
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self._queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self._queues[agent_id].get()
            
            message.mark_read()
            return message
        except asyncio.TimeoutError:
            return None
    
    async def broadcast(
        self,
        from_agent: str,
        content: Any,
        message_type: str = "broadcast",
    ) -> list[str]:
        """
        广播消息 / Broadcast message
        
        Args:
            from_agent: 发送者 / Sender
            content: 消息内容 / Message content
            message_type: 消息类型 / Message type
            
        Returns:
            消息ID列表 / List of message IDs
        """
        message_ids = []
        
        for agent_id in self._queues:
            if agent_id != from_agent:
                message_id = await self.send(
                    from_agent=from_agent,
                    to_agent=agent_id,
                    content=content,
                    message_type=message_type,
                )
                message_ids.append(message_id)
        
        return message_ids
    
    def subscribe(
        self,
        subscriber_id: str,
        target_id: str,
    ) -> None:
        """
        订阅Agent消息 / Subscribe to agent messages
        
        Args:
            subscriber_id: 订阅者ID / Subscriber ID
            target_id: 目标Agent ID / Target agent ID
        """
        if target_id not in self._subscribers:
            self._subscribers[target_id] = []
        
        if subscriber_id not in self._subscribers[target_id]:
            self._subscribers[target_id].append(subscriber_id)
    
    def unsubscribe(
        self,
        subscriber_id: str,
        target_id: str,
    ) -> None:
        """
        取消订阅 / Unsubscribe
        
        Args:
            subscriber_id: 订阅者ID / Subscriber ID
            target_id: 目标Agent ID / Target agent ID
        """
        if target_id in self._subscribers:
            if subscriber_id in self._subscribers[target_id]:
                self._subscribers[target_id].remove(subscriber_id)
    
    def get_history(
        self,
        agent_id: str | None = None,
        message_type: str | None = None,
        limit: int = 100,
    ) -> list[Message]:
        """
        获取历史消息 / Get message history
        
        Args:
            agent_id: Agent标识（可选）/ Agent identifier (optional)
            message_type: 消息类型（可选）/ Message type (optional)
            limit: 数量限制 / Limit
            
        Returns:
            消息列表 / List of messages
        """
        messages = self._history
        
        if agent_id:
            messages = [
                m for m in messages
                if m.from_agent == agent_id or m.to_agent == agent_id
            ]
        
        if message_type:
            messages = [
                m for m in messages
                if m.message_type == message_type
            ]
        
        return messages[-limit:]
    
    def get_pending_count(self, agent_id: str) -> int:
        """
        获取待处理消息数量 / Get pending message count
        
        Args:
            agent_id: Agent标识 / Agent identifier
            
        Returns:
            待处理消息数量 / Pending message count
        """
        if agent_id not in self._queues:
            return 0
        return self._queues[agent_id].qsize()


class AgentCommunication:
    """
    Agent通信管理器 / Agent Communication Manager
    
    提供高级通信功能
    Provides high-level communication features
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        初始化通信管理器 / Initialize communication manager
        
        Args:
            message_bus: 消息总线 / Message bus
        """
        self.bus = message_bus
        self._shared_memory: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}
    
    async def request(
        self,
        from_agent: str,
        to_agent: str,
        request_type: str,
        params: dict[str, Any],
        timeout: float = 30.0,
    ) -> Any:
        """
        发送请求并等待响应 / Send request and wait for response
        
        Args:
            from_agent: 发送者 / Sender
            to_agent: 接收者 / Receiver
            request_type: 请求类型 / Request type
            params: 请求参数 / Request parameters
            timeout: 超时时间 / Timeout
            
        Returns:
            响应结果 / Response result
        """
        request_id = str(uuid4())
        
        await self.bus.send(
            from_agent=from_agent,
            to_agent=to_agent,
            content={
                "request_id": request_id,
                "request_type": request_type,
                "params": params,
            },
            message_type="request",
        )
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            message = await self.bus.receive(from_agent, timeout=0.1)
            
            if message and message.message_type == "response":
                content = message.content
                if isinstance(content, dict) and content.get("request_id") == request_id:
                    return content.get("result")
        
        return None
    
    async def respond(
        self,
        from_agent: str,
        to_agent: str,
        request_id: str,
        result: Any,
    ) -> str:
        """
        发送响应 / Send response
        
        Args:
            from_agent: 发送者 / Sender
            to_agent: 接收者 / Receiver
            request_id: 请求ID / Request ID
            result: 结果 / Result
            
        Returns:
            消息ID / Message ID
        """
        return await self.bus.send(
            from_agent=from_agent,
            to_agent=to_agent,
            content={
                "request_id": request_id,
                "result": result,
            },
            message_type="response",
        )
    
    def set_shared(
        self,
        key: str,
        value: Any,
        agent_id: str | None = None,
    ) -> None:
        """
        设置共享数据 / Set shared data
        
        Args:
            key: 键 / Key
            value: 值 / Value
            agent_id: Agent标识（可选）/ Agent identifier (optional)
        """
        full_key = f"{agent_id}:{key}" if agent_id else key
        self._shared_memory[full_key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "owner": agent_id,
        }
    
    def get_shared(
        self,
        key: str,
        agent_id: str | None = None,
        default: Any = None,
    ) -> Any:
        """
        获取共享数据 / Get shared data
        
        Args:
            key: 键 / Key
            agent_id: Agent标识（可选）/ Agent identifier (optional)
            default: 默认值 / Default value
            
        Returns:
            共享数据 / Shared data
        """
        full_key = f"{agent_id}:{key}" if agent_id else key
        data = self._shared_memory.get(full_key)
        return data["value"] if data else default
    
    async def with_lock(
        self,
        lock_name: str,
        agent_id: str,
        action: Any,
    ) -> Any:
        """
        使用锁执行操作 / Execute action with lock
        
        Args:
            lock_name: 锁名称 / Lock name
            agent_id: Agent标识 / Agent identifier
            action: 操作 / Action
            
        Returns:
            操作结果 / Action result
        """
        if lock_name not in self._locks:
            self._locks[lock_name] = asyncio.Lock()
        
        async with self._locks[lock_name]:
            if callable(action):
                if asyncio.iscoroutinefunction(action):
                    return await action()
                return action()
            return action
    
    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息 / Get statistics
        
        Returns:
            统计信息 / Statistics
        """
        return {
            "registered_agents": len(self.bus._queues),
            "message_history_count": len(self.bus._history),
            "shared_memory_count": len(self._shared_memory),
            "active_locks": len(self._locks),
        }
