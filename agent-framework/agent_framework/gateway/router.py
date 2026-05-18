from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass


class RouterKeyType(Enum):
    """路由键类型"""
    USER = "user"
    SESSION = "session"
    TOPIC = "topic"
    AGENT = "agent"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "RouterKeyType":
        """从字符串获取枚举值，未知类型返回 UNKNOWN"""
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


@dataclass
class RouterKey:
    """路由键"""
    key_type: RouterKeyType
    key_id: str


class MessageRouter:
    """
    Message Router - 消息路由器
    负责消息的路由和分发
    """

    def __init__(self):
        self.routes: Dict[str, List[str]] = {}
        self.handlers: Dict[str, Any] = {}

    def register_route(self, key: RouterKey, handler: Any):
        """注册路由"""
        route_key = f"{key.key_type.value}:{key.key_id}"
        if route_key not in self.routes:
            self.routes[route_key] = []
        self.routes[route_key].append(handler)

    def route_message(self, target: str, message: Dict[str, Any]) -> bool:
        """路由消息到目标"""
        if target in self.routes:
            for handler in self.routes[target]:
                handler(message)
            return True
        return False

    def get_routes(self, key_type: Optional[RouterKeyType] = None) -> List[str]:
        """获取路由列表"""
        if key_type:
            return [
                k for k in self.routes.keys()
                if k.startswith(f"{key_type.value}:")
            ]
        return list(self.routes.keys())
