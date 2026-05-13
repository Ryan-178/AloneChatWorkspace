"""
Gateway核心模块 - Agent网关
龙虾的神经中枢，7×24小时稳定运行
"""
import time
import asyncio
import logging
import json
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse

from .types import (
    MsgContext,
    Session,
    SessionState,
    GatewayConfig,
    GatewayStatus,
    ChatType,
)
from .session import SessionManager
from .router import MessageRouter
from .agent import ReActAgent
from agent_framework.llm.litellm_provider import LiteLLMProvider
from agent_framework.core.base_llm import LLMConfig
from .agent import ReActAgent
from .tools import get_tool_registry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_gateway")


class AgentGateway:
    """Agent网关 - 核心调度中心"""
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.started_at = datetime.utcnow()
        
        # 核心组件
        self.session_manager = SessionManager(timeout_seconds=self.config.session_timeout)
        self.message_router = MessageRouter()
        self.tool_registry = get_tool_registry()
        
        # WebSocket连接管理
        self.active_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        
        # 会话 -> Agent映射
        self.session_agents: Dict[str, ReActAgent] = {}
        
        # 统计
        self.total_messages_processed = 0
        
        # FastAPI应用
        self.app = FastAPI(title="Agent Gateway", lifespan=self.lifespan)
        self._setup_routes()
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """生命周期管理"""
        logger.info(f"🚀 Agent Gateway starting on port {self.config.port}...")
        yield
        logger.info("🛑 Agent Gateway shutting down...")
        # 清理
        for websocket in self.active_connections.values():
            try:
                await websocket.close()
            except:
                pass
    
    def _setup_routes(self):
        """设置API路由"""
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            return self.get_status()
        
        # 状态检查
        @self.app.get("/status")
        async def get_status():
            """获取Gateway状态"""
            return self.get_status()
        
        # 统计信息
        @self.app.get("/stats")
        async def get_stats():
            """获取统计信息"""
            session_stats = self.session_manager.get_stats()
            router_stats = self.message_router.get_stats()
            return {
                "gateway": self.get_status().dict(),
                "sessions": session_stats,
                "router": router_stats,
                "tools": [t.name for t in self.tool_registry.get_all()],
            }
        
        # WebSocket端点
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket通信端点"""
            await websocket.accept()
            session_id = None
            
            try:
                # 接收初始化消息
                init_data = await websocket.receive_json()
                user_id = init_data.get("user_id", "anonymous")
                session_key = init_data.get("session_key", str(int(time.time())))
                
                # 获取或创建会话
                session = self.session_manager.get_or_create_session(
                    session_key=session_key,
                    user_id=user_id,
                    channel="websocket"
                )
                session_id = session.session_id
                
                # 为会话创建Agent
                if session_id not in self.session_agents:
                    self.session_agents[session_id] = ReActAgent()
                    logger.info(f"🦞 Created Agent for session: {session_id}")
                
                # 保存连接
                self.active_connections[session_id] = websocket
                logger.info(f"📡 WebSocket connected: session_id={session_id}, user_id={user_id}")
                
                # 发送欢迎消息
                await websocket.send_json({
                    "type": "connected",
                    "session_id": session_id,
                    "message": "Welcome to Agent Gateway! 🦞",
                    "available_tools": [t.name for t in self.tool_registry.get_all()],
                })
                
                # 消息处理循环
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(session_id, websocket, data)
                    
            except WebSocketDisconnect:
                logger.info(f"👋 WebSocket disconnected: session_id={session_id}")
            except Exception as e:
                logger.error(f"❌ WebSocket error: {e}", exc_info=True)
            finally:
                if session_id and session_id in self.active_connections:
                    del self.active_connections[session_id]
    
    async def _handle_websocket_message(self, session_id: str, websocket: WebSocket, data: Dict):
        """处理WebSocket消息"""
        try:
            msg_type = data.get("type", "message")
            
            if msg_type == "message":
                # 处理用户消息
                body = data.get("body", "")
                user_id = data.get("user_id", "anonymous")
                
                # 创建MsgContext
                msg = MsgContext(
                    body=body,
                    session_key=session_id,
                    sender_id=user_id,
                    provider="websocket",
                    chat_type=ChatType.DIRECT,
                )
                
                # 检查重复
                if self.message_router.is_duplicate(msg):
                    await websocket.send_json({
                        "type": "error",
                        "error": "Duplicate message"
                    })
                    return
                
                self.total_messages_processed += 1
                
                # 获取会话并获取车道
                session = self.session_manager.get_session(session_id)
                if not session:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Session not found"
                    })
                    return
                
                # 获取车道（避免并发冲突）
                if not self.session_manager.acquire_session_lane(session_id):
                    await websocket.send_json({
                        "type": "busy",
                        "message": "Agent is busy processing previous request"
                    })
                    return
                
                try:
                    # 处理消息 - 真正的Agent推理
                    await self._process_message_with_agent(msg, session, websocket)
                    
                finally:
                    # 释放车道
                    self.session_manager.release_session_lane(session_id)
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "reset":
                # 重置会话
                if session_id in self.session_agents:
                    self.session_agents[session_id].reset()
                await websocket.send_json({
                    "type": "info",
                    "message": "Session reset!"
                })
            
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
    
    async def _process_message_with_agent(self, msg: MsgContext, session: Session, websocket: WebSocket):
        """使用真正的Agent处理消息"""
        # 获取或创建Agent
        agent = self.session_agents.get(session.session_id)
        if not agent:
            agent = ReActAgent()
            self.session_agents[session.session_id] = agent
        
        # 流式运行Agent
        try:
            async for event in agent.run_stream(msg.body):
                event_type = event.get("type")
                
                if event_type == "thinking":
                    await websocket.send_json({
                        "type": "thinking",
                        "message": event.get("message", "Thinking..."),
                        "step": event.get("step", 1),
                        "trace_id": msg.trace_id,
                    })
                
                elif event_type == "content":
                    await websocket.send_json({
                        "type": "stream",
                        "content": event.get("content", ""),
                        "trace_id": msg.trace_id,
                    })
                
                elif event_type == "acting":
                    await websocket.send_json({
                        "type": "acting",
                        "message": event.get("message", "Executing tool..."),
                        "trace_id": msg.trace_id,
                    })
                
                elif event_type == "observation":
                    await websocket.send_json({
                        "type": "observation",
                        "tool": event.get("tool"),
                        "result": event.get("result"),
                        "trace_id": msg.trace_id,
                    })
                
                elif event_type == "finished":
                    await websocket.send_json({
                        "type": "final",
                        "content": event.get("final_answer", ""),
                        "total_tokens": event.get("total_tokens", 0),
                        "execution_time_ms": event.get("execution_time_ms", 0),
                        "trace_id": msg.trace_id,
                    })
                
                elif event_type == "error":
                    await websocket.send_json({
                        "type": "error",
                        "error": event.get("message", "Unknown error"),
                        "trace_id": msg.trace_id,
                    })
        
        except Exception as e:
            logger.error(f"❌ Agent error: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "trace_id": msg.trace_id,
            })
    
    def get_status(self) -> GatewayStatus:
        """获取Gateway状态"""
        uptime = (datetime.utcnow() - self.started_at).total_seconds()
        return GatewayStatus(
            status="healthy",
            uptime_seconds=uptime,
            active_sessions=len(self.active_connections),
            total_messages_processed=self.total_messages_processed,
            started_at=self.started_at
        )
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """向指定会话发送消息"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"❌ Failed to send message to session {session_id}: {e}")
    
    async def handle_message(self, msg: MsgContext) -> Dict[str, Any]:
        """处理消息的同步入口（供外部调用）"""
        self.total_messages_processed += 1
        
        session = self.session_manager.get_or_create_session(
            session_key=msg.session_key,
            user_id=msg.sender_id,
            channel=msg.provider
        )
        
        # 获取或创建Agent
        agent = self.session_agents.get(session.session_id)
        if not agent:
            agent = ReActAgent()
            self.session_agents[session.session_id] = agent
        
        # 运行Agent
        result = await agent.run(msg.body)
        
        return {
            "status": "processed" if result.success else "error",
            "session_id": session.session_id,
            "response": result.final_answer,
            "trace_id": msg.trace_id,
            "total_tokens": result.total_tokens,
            "execution_time_ms": result.execution_time_ms,
        }
    
    def run(self):
        """启动Gateway（使用uvicorn）"""
        import uvicorn
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )


# 便捷函数：创建并启动Gateway
def create_gateway(config: Optional[GatewayConfig] = None) -> AgentGateway:
    """创建Gateway实例"""
    return AgentGateway(config=config)
