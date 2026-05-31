"""
WebSocket流式输出 - 实时推送任务进度、Agent思考过程、产出物更新
"""
import asyncio
import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    type: str = Field(..., description="消息类型")
    content: Any = Field(..., description="消息内容")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self._connections: List[WebSocket] = []
        self._subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        """建立连接"""
        await websocket.accept()
        self._connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """断开连接"""
        if websocket in self._connections:
            self._connections.remove(websocket)
        
        for subscribers in self._subscriptions.values():
            if websocket in subscribers:
                subscribers.remove(websocket)
    
    def subscribe(self, websocket: WebSocket, channel: str) -> None:
        """订阅频道"""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = set()
        self._subscriptions[channel].add(websocket)
    
    def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        """取消订阅"""
        if channel in self._subscriptions and websocket in self._subscriptions[channel]:
            self._subscriptions[channel].remove(websocket)
    
    async def send_personal(self, websocket: WebSocket, message: WebSocketMessage) -> None:
        """发送个人消息"""
        try:
            await websocket.send_json(message.model_dump())
        except Exception:
            pass
    
    async def broadcast(self, message: WebSocketMessage) -> None:
        """广播消息"""
        for connection in self._connections:
            try:
                await connection.send_json(message.model_dump())
            except Exception:
                pass
    
    async def broadcast_to_channel(self, channel: str, message: WebSocketMessage) -> None:
        """向频道广播"""
        if channel not in self._subscriptions:
            return
        
        for connection in self._subscriptions[channel]:
            try:
                await connection.send_json(message.model_dump())
            except Exception:
                pass
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self._connections)


manager = ConnectionManager()


async def push_task_progress(
    task_id: str,
    status: str,
    progress: float,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """推送任务进度"""
    msg = WebSocketMessage(
        type="task_progress",
        content={
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
        },
        metadata=metadata or {},
    )
    
    await manager.broadcast_to_channel(f"task:{task_id}", msg)
    await manager.broadcast_to_channel("tasks", msg)


async def push_agent_thinking(
    session_id: str,
    event_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """推送Agent思考过程"""
    msg = WebSocketMessage(
        type="agent_thinking",
        content={
            "session_id": session_id,
            "event_type": event_type,
            "content": content,
        },
        metadata=metadata or {},
    )
    
    await manager.broadcast_to_channel(f"session:{session_id}", msg)


async def push_artifact_update(
    artifact_id: str,
    action: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """推送产出物更新"""
    msg = WebSocketMessage(
        type="artifact_update",
        content={
            "artifact_id": artifact_id,
            "action": action,
        },
        metadata=metadata or {},
    )
    
    await manager.broadcast_to_channel(f"artifact:{artifact_id}", msg)
    await manager.broadcast_to_channel("artifacts", msg)


async def push_mode_switch(
    previous_mode: str,
    new_mode: str,
    session_id: Optional[str] = None,
) -> None:
    """推送模式切换"""
    msg = WebSocketMessage(
        type="mode_switch",
        content={
            "previous_mode": previous_mode,
            "new_mode": new_mode,
            "session_id": session_id,
        },
    )
    
    await manager.broadcast(msg)


async def push_skill_execution(
    skill_name: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
) -> None:
    """推送Skill执行状态"""
    msg = WebSocketMessage(
        type="skill_execution",
        content={
            "skill_name": skill_name,
            "status": status,
            "result": result,
        },
    )
    
    await manager.broadcast_to_channel(f"skill:{skill_name}", msg)


async def push_error(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """推送错误"""
    msg = WebSocketMessage(
        type="error",
        content={
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
        },
    )
    
    await manager.broadcast(msg)


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                params = message.get("params", {})
                
                if action == "subscribe":
                    channel = params.get("channel")
                    if channel:
                        manager.subscribe(websocket, channel)
                        await manager.send_personal(
                            websocket,
                            WebSocketMessage(
                                type="subscribed",
                                content={"channel": channel},
                            ),
                        )
                
                elif action == "unsubscribe":
                    channel = params.get("channel")
                    if channel:
                        manager.unsubscribe(websocket, channel)
                        await manager.send_personal(
                            websocket,
                            WebSocketMessage(
                                type="unsubscribed",
                                content={"channel": channel},
                            ),
                        )
                
                elif action == "ping":
                    await manager.send_personal(
                        websocket,
                        WebSocketMessage(
                            type="pong",
                            content={"timestamp": datetime.utcnow().isoformat()},
                        ),
                    )
                
                else:
                    await manager.send_personal(
                        websocket,
                        WebSocketMessage(
                            type="error",
                            content={"message": f"未知操作: {action}"},
                        ),
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal(
                    websocket,
                    WebSocketMessage(
                        type="error",
                        content={"message": "无效的JSON格式"},
                    ),
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def heartbeat_task():
    """心跳任务"""
    while True:
        await asyncio.sleep(30)
        
        msg = WebSocketMessage(
            type="heartbeat",
            content={
                "timestamp": datetime.utcnow().isoformat(),
                "connections": manager.get_connection_count(),
            },
        )
        
        await manager.broadcast(msg)
