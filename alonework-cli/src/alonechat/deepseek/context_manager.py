"""
上下文管理模块 / Context Management Module

提供 / Provides:
- 100万Token上下文 / 1M token context
- 上下文压缩 / Context compression
- 智能缓存 / Smart caching
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
import hashlib
import json

import yaml
from pathlib import Path


@dataclass
class Message:
    """消息数据类 / Message Data Class"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def estimate_tokens(self) -> int:
        """估算Token数 / Estimate token count"""
        if self.token_count > 0:
            return self.token_count
        
        chinese_chars = sum(1 for c in self.content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(self.content) - chinese_chars
        
        self.token_count = int(chinese_chars / 1.5 + other_chars / 4)
        return self.token_count


@dataclass
class ContextSnapshot:
    """上下文快照 / Context Snapshot"""
    messages: List[Message]
    total_tokens: int
    created_at: datetime
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "token_count": m.token_count,
                }
                for m in self.messages
            ],
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
        }


class ContextConfigLoader:
    """上下文配置加载器 / Context Config Loader"""
    
    _instance: Optional["ContextConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "configs" / "deepseek_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"deepseek": {"context": {"max_tokens": 1000000}}}
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def get_instance(cls) -> "ContextConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


context_config = ContextConfigLoader.get_instance()


class MegaContextManager:
    """
    超大上下文管理器 / Mega Context Manager
    
    支持DeepSeek V4的100万Token上下文 / Support DeepSeek V4's 1M token context
    """
    
    def __init__(self, max_tokens: Optional[int] = None):
        """
        初始化上下文管理器 / Initialize context manager
        
        Args:
            max_tokens: 最大Token数，默认从配置读取 / Max tokens, default from config
        """
        self._config = context_config.get("deepseek.context", {})
        self.max_tokens = max_tokens or self._config.get("max_tokens", 1000000)
        self.compression_threshold = self._config.get("compression_threshold", 800000)
        self.compression_ratio = self._config.get("compression_ratio", 0.3)
        
        self._messages: deque[Message] = deque()
        self._total_tokens = 0
        
        self._cache_enabled = self._config.get("cache_enabled", True)
        self._cache_ttl = self._config.get("cache_ttl", 3600)
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        
        self._snapshots: List[ContextSnapshot] = []
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        添加消息 / Add message
        
        Args:
            role: 角色 / Role
            content: 内容 / Content
            metadata: 元数据 / Metadata
            
        Returns:
            添加的消息 / Added message
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        message.estimate_tokens()
        
        while (
            self._total_tokens + message.token_count > self.max_tokens
            and self._messages
        ):
            removed = self._messages.popleft()
            self._total_tokens -= removed.token_count
        
        self._messages.append(message)
        self._total_tokens += message.token_count
        
        if self._total_tokens > self.compression_threshold:
            self._compress_context()
        
        return message
    
    def get_messages(self) -> List[Message]:
        """获取所有消息 / Get all messages"""
        return list(self._messages)
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """获取API格式的消息 / Get messages in API format"""
        return [
            {"role": m.role, "content": m.content}
            for m in self._messages
        ]
    
    def clear(self) -> None:
        """清空上下文 / Clear context"""
        self._messages.clear()
        self._total_tokens = 0
    
    def get_token_count(self) -> int:
        """获取当前Token数 / Get current token count"""
        return self._total_tokens
    
    def get_usage_ratio(self) -> float:
        """获取使用比例 / Get usage ratio"""
        return self._total_tokens / self.max_tokens
    
    def _compress_context(self) -> None:
        """压缩上下文 / Compress context"""
        if len(self._messages) < 4:
            return
        
        system_messages = [
            m for m in self._messages if m.role == "system"
        ]
        recent_messages = list(self._messages)[-2:]
        
        middle_messages = [
            m for m in self._messages
            if m not in system_messages and m not in recent_messages
        ]
        
        compress_count = int(len(middle_messages) * self.compression_ratio)
        
        if compress_count > 0:
            summary = self._create_summary(middle_messages[:compress_count])
            
            summary_message = Message(
                role="system",
                content=f"[上下文摘要 / Context Summary]\n{summary}",
            )
            summary_message.estimate_tokens()
            
            new_messages = deque()
            new_total = 0
            
            for m in system_messages:
                new_messages.append(m)
                new_total += m.token_count
            
            new_messages.append(summary_message)
            new_total += summary_message.token_count
            
            for m in middle_messages[compress_count:]:
                new_messages.append(m)
                new_total += m.token_count
            
            for m in recent_messages:
                new_messages.append(m)
                new_total += m.token_count
            
            self._messages = new_messages
            self._total_tokens = new_total
    
    def _create_summary(self, messages: List[Message]) -> str:
        """创建摘要 / Create summary"""
        if not messages:
            return ""
        
        summary_parts = []
        
        roles = {}
        for m in messages:
            roles[m.role] = roles.get(m.role, 0) + 1
        
        summary_parts.append(
            f"压缩了 {len(messages)} 条消息 (用户: {roles.get('user', 0)}, 助手: {roles.get('assistant', 0)})"
        )
        
        key_points = []
        for m in messages[-3:]:
            content = m.content[:100]
            if len(m.content) > 100:
                content += "..."
            key_points.append(f"- {m.role}: {content}")
        
        if key_points:
            summary_parts.append("关键内容:\n" + "\n".join(key_points))
        
        return "\n".join(summary_parts)
    
    def save_snapshot(self) -> ContextSnapshot:
        """保存快照 / Save snapshot"""
        content = json.dumps([
            {"role": m.role, "content": m.content}
            for m in self._messages
        ], ensure_ascii=False)
        
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        snapshot = ContextSnapshot(
            messages=list(self._messages),
            total_tokens=self._total_tokens,
            created_at=datetime.now(),
            checksum=checksum,
        )
        
        self._snapshots.append(snapshot)
        
        return snapshot
    
    def restore_snapshot(self, snapshot: ContextSnapshot) -> bool:
        """恢复快照 / Restore snapshot"""
        self._messages = deque(snapshot.messages)
        self._total_tokens = snapshot.total_tokens
        return True
    
    def get_cache_key(self, prompt: str) -> str:
        """获取缓存键 / Get cache key"""
        content = prompt + json.dumps([
            {"role": m.role, "content": m.content}
            for m in self._messages[-5:]
        ], ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """获取缓存 / Get cache"""
        if not self._cache_enabled:
            return None
        
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return value
            else:
                del self._cache[key]
        
        return None
    
    def set_cache(self, key: str, value: Any) -> None:
        """设置缓存 / Set cache"""
        if self._cache_enabled:
            self._cache[key] = (value, datetime.now())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息 / Get statistics"""
        return {
            "total_tokens": self._total_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": self.get_usage_ratio(),
            "message_count": len(self._messages),
            "cache_size": len(self._cache),
            "snapshot_count": len(self._snapshots),
        }
