"""
Gateway核心数据模型
参考OpenClaw设计，生产级Agent网关
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


def generate_trace_id() -> str:
    """生成链路追踪ID"""
    return str(uuid.uuid4())


class SessionState(str, Enum):
    """会话状态"""
    IDLE = "idle"          # 空闲
    RUNNING = "running"    # 运行中
    PAUSED = "paused"      # 暂停
    ERROR = "error"        # 错误
    FINISHED = "finished"  # 完成


class ChatType(str, Enum):
    """聊天类型"""
    DIRECT = "direct"  # 单聊
    GROUP = "group"    # 群聊


class MsgContext(BaseModel):
    """消息上下文 - 统一消息格式"""
    body: str = Field(..., description="消息主体内容")
    session_key: str = Field(..., description="会话唯一标识")
    provider: str = Field(default="chat_app", description="渠道标识")
    chat_type: ChatType = Field(default=ChatType.DIRECT, description="聊天类型")
    sender_id: str = Field(..., description="发送者ID")
    originating_channel: str = Field(default="chat_app", description="原始渠道")
    message_sid: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息唯一ID")
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp(), description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    trace_id: str = Field(default_factory=generate_trace_id, description="链路追踪ID")
    
    class Config:
        extra = "allow"


class Session(BaseModel):
    """会话对象"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    channel: str = Field(default="chat_app", description="渠道")
    state: SessionState = Field(default=SessionState.IDLE, description="会话状态")
    agent_config: Dict[str, Any] = Field(default_factory=dict, description="Agent配置")
    memory_context: Dict[str, Any] = Field(default_factory=dict, description="记忆上下文")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def touch(self):
        """更新时间戳"""
        self.updated_at = datetime.utcnow()
    
    class Config:
        extra = "allow"


class GatewayConfig(BaseModel):
    """Gateway配置"""
    # 服务配置
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=18789, description="监听端口（向OpenClaw致敬）")
    debug: bool = Field(default=False, description="调试模式")
    
    # 会话配置
    session_timeout: int = Field(default=3600, description="会话超时秒数")
    max_concurrent_sessions: int = Field(default=1000, description="最大并发会话数")
    
    # LLM配置
    default_model: str = Field(default="gpt-4o", description="默认模型")
    
    # 存储配置
    sqlite_path: str = Field(default="./data/gateway.db", description="SQLite路径")
    redis_url: Optional[str] = Field(default=None, description="Redis URL")
    
    class Config:
        extra = "allow"


class GatewayStatus(BaseModel):
    """Gateway状态"""
    status: str = Field(default="healthy", description="服务状态")
    uptime_seconds: float = Field(default=0.0, description="运行秒数")
    active_sessions: int = Field(default=0, description="活跃会话数")
    total_messages_processed: int = Field(default=0, description="处理消息总数")
    started_at: datetime = Field(default_factory=datetime.utcnow)
