import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from config import get_settings

settings = get_settings()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_groups: Dict[str, Set[str]] = {}
        self.redis_client = None
        self.pubsub = None

    async def connect_redis(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe("chat_messages", "online_status")
        asyncio.create_task(self._redis_listener())

    async def disconnect_redis(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

    async def _redis_listener(self):
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    channel = message["channel"].decode("utf-8")
                    if channel == "chat_messages":
                        await self._handle_chat_message(data)
                    elif channel == "online_status":
                        await self._handle_online_status(data)
                except Exception:
                    pass

    async def _handle_chat_message(self, data: dict):
        recipient_id = data.get("recipient_id")
        group_id = data.get("group_id")
        if recipient_id and recipient_id in self.active_connections:
            await self.active_connections[recipient_id].send_json(data)
        elif group_id:
            for user_id in self.user_groups.get(group_id, set()):
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_json(data)

    async def _handle_online_status(self, data: dict):
        user_id = data.get("user_id")
        status = data.get("status")
        for uid, ws in self.active_connections.items():
            if uid != user_id:
                try:
                    await ws.send_json({
                        "type": "online_status",
                        "payload": {"user_id": user_id, "status": status}
                    })
                except Exception:
                    pass

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self._broadcast_online_status(user_id, "online")

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        for group_id, members in self.user_groups.items():
            members.discard(user_id)
        await self._broadcast_online_status(user_id, "offline")

    async def _broadcast_online_status(self, user_id: str, status: str):
        if self.redis_client:
            await self.redis_client.publish("online_status", json.dumps({
                "user_id": user_id,
                "status": status
            }))

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_group(self, message: dict, group_id: str):
        if self.redis_client:
            await self.redis_client.publish("chat_messages", json.dumps({
                **message,
                "group_id": group_id
            }))

    async def send_message(self, message: dict, recipient_id: str):
        if self.redis_client:
            await self.redis_client.publish("chat_messages", json.dumps({
                **message,
                "recipient_id": recipient_id
            }))

    def join_group(self, user_id: str, group_id: str):
        if group_id not in self.user_groups:
            self.user_groups[group_id] = set()
        self.user_groups[group_id].add(user_id)

    def leave_group(self, user_id: str, group_id: str):
        if group_id in self.user_groups:
            self.user_groups[group_id].discard(user_id)

    async def handle_agent_message(self, user_id: str, content: str, session_id: str):
        try:
            from agent_service import run_agent_task
            from database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                answer = await run_agent_task(db, session_id, content)

            await self.send_personal_message({
                "type": "agent_response",
                "payload": {
                    "sender_id": "__agent__",
                    "content": answer,
                    "session_id": session_id,
                }
            }, user_id)
        except Exception as e:
            await self.send_personal_message({
                "type": "agent_response",
                "payload": {
                    "sender_id": "__agent__",
                    "content": f"Error: {str(e)}",
                    "session_id": session_id,
                }
            }, user_id)

    async def handle_agent_stream(self, user_id: str, content: str, session_id: str):
        try:
            from agent_service import run_agent_task_stream
            from database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                async for event in run_agent_task_stream(db, session_id, content):
                    await self.send_personal_message({
                        "type": "agent_stream",
                        "payload": {
                            "event": event.get("event"),
                            "content": event.get("content"),
                            "session_id": session_id,
                        }
                    }, user_id)
        except Exception as e:
            await self.send_personal_message({
                "type": "agent_stream",
                "payload": {
                    "event": "error",
                    "content": str(e),
                    "session_id": session_id,
                }
            }, user_id)


manager = ConnectionManager()
