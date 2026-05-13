"""
消息路由模块 - Message Router
实现消息去重、路由分发
"""
import time
import re
from typing import Optional, Dict, Callable, Any, List, Tuple
from collections import deque
from dataclasses import dataclass
from .types import MsgContext, ChatType


@dataclass
class RouteEntry:
    """路由条目"""
    pattern: str
    handler: Callable
    priority: int = 0
    chat_type: Optional[ChatType] = None


class MessageRouter:
    """消息路由器"""
    
    def __init__(self, max_recent_messages: int = 1000, dedup_window_seconds: int = 60):
        self.max_recent = max_recent_messages
        self.dedup_window = dedup_window_seconds
        
        # 最近消息记录：message_sid -> timestamp
        self.recent_messages: Dict[str, float] = {}
        
        # 消息ID队列，用于FIFO淘汰
        self.message_queue = deque(maxlen=max_recent_messages)
        
        # 路由处理器列表，支持优先级
        self.routes: List[RouteEntry] = []
        
        # 统计
        self.total_processed = 0
        self.total_deduped = 0
        self.total_routed = 0
    
    def is_duplicate(self, msg: MsgContext) -> bool:
        """检查消息是否重复"""
        now = time.time()
        message_sid = msg.message_sid
        
        # 清理过期消息记录
        self._cleanup_old_messages(now)
        
        # 检查是否已处理过
        if message_sid in self.recent_messages:
            self.total_deduped += 1
            return True
        
        # 记录新消息
        self.recent_messages[message_sid] = now
        self.message_queue.append(message_sid)
        self.total_processed += 1
        return False
    
    def _cleanup_old_messages(self, now: float):
        """清理过期的消息记录"""
        cutoff = now - self.dedup_window
        expired_sids = []
        for sid, ts in list(self.recent_messages.items()):
            if ts < cutoff:
                expired_sids.append(sid)
        
        for sid in expired_sids:
            self.recent_messages.pop(sid, None)
    
    def register_route(
        self, 
        pattern: str, 
        handler: Callable, 
        priority: int = 0,
        chat_type: Optional[ChatType] = None
    ):
        """
        注册路由
        
        Args:
            pattern: 正则表达式模式或关键词
            handler: 处理器函数
            priority: 优先级，数字越大优先级越高
            chat_type: 可选，限制特定聊天类型
        """
        # 按优先级插入到正确位置
        entry = RouteEntry(pattern=pattern, handler=handler, priority=priority, chat_type=chat_type)
        
        # 找到插入位置，保持按优先级降序排列
        insert_idx = len(self.routes)
        for i, existing in enumerate(self.routes):
            if priority > existing.priority:
                insert_idx = i
                break
        
        self.routes.insert(insert_idx, entry)
    
    def unregister_route(self, pattern: str):
        """取消注册路由"""
        self.routes = [r for r in self.routes if r.pattern != pattern]
    
    def route(self, msg: MsgContext) -> Optional[Callable]:
        """
        路由消息到对应的处理器
        
        Returns:
            匹配的处理器，如果没有匹配则返回None
        """
        for entry in self.routes:
            # 检查聊天类型是否匹配
            if entry.chat_type is not None and msg.chat_type != entry.chat_type:
                continue
            
            # 尝试匹配模式
            if self._match_pattern(msg.body, entry.pattern):
                self.total_routed += 1
                return entry.handler
        
        return None
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """
        匹配模式
        
        支持：
        - 精确匹配（以^开头和$结尾）
        - 正则表达式匹配
        - 关键词包含匹配
        """
        # 检查是否是正则表达式
        if pattern.startswith('^') and pattern.endswith('$'):
            try:
                return bool(re.match(pattern, text, re.IGNORECASE))
            except re.error:
                pass
        
        # 尝试正则表达式匹配
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        except re.error:
            pass
        
        # 回退到关键词包含匹配
        return pattern.lower() in text.lower()
    
    def list_routes(self) -> List[Dict[str, Any]]:
        """列出所有注册的路由"""
        return [
            {
                "pattern": r.pattern,
                "priority": r.priority,
                "chat_type": r.chat_type.value if r.chat_type else None,
                "handler_name": r.handler.__name__ if hasattr(r.handler, "__name__") else str(r.handler)
            }
            for r in self.routes
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_processed": self.total_processed,
            "total_deduped": self.total_deduped,
            "total_routed": self.total_routed,
            "recent_message_count": len(self.recent_messages),
            "route_count": len(self.routes),
            "routes": self.list_routes(),
        }
