"""
DeepSeek专用Cache管理
配合DeepSeek KV Cache的前缀匹配机制
"""
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class PrefixCacheEntry:
    """前缀缓存条目 - 配合DeepSeek KV Cache"""
    prefix_messages: List[Dict[str, Any]]
    prefix_length: int  # 前缀消息数量
    prefix_tokens: int  # 前缀token数（估算）
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class DeepSeekCacheManager:
    """
    DeepSeek专用Cache管理器
    配合DeepSeek的前缀匹配KV Cache机制
    """

    def __init__(
        self,
        max_prefixes: int = 100,
        min_prefix_tokens: int = 64,  # DeepSeek以64token为存储单元
    ):
        self.max_prefixes = max_prefixes
        self.min_prefix_tokens = min_prefix_tokens
        self._prefix_cache: OrderedDict = OrderedDict()
        self._stats = {
            "total_requests": 0,
            "prefix_hits": 0,
            "tokens_saved": 0,
        }

    def _compute_prefix_hash(self, messages: List[Dict[str, Any]], prefix_length: int) -> str:
        """计算前缀消息的哈希值"""
        prefix_content = str(messages[:prefix_length])
        return hashlib.sha256(prefix_content.encode("utf-8")).hexdigest()

    def find_matching_prefix(
        self,
        messages: List[Dict[str, Any]],
    ) -> Tuple[Optional[int], Optional[PrefixCacheEntry]]:
        """
        查找匹配的前缀 - 配合DeepSeek前缀匹配机制
        
        返回: (匹配的前缀长度, 缓存条目)
        """
        if not messages:
            return None, None

        # 从最长可能的前缀开始匹配
        for prefix_len in range(len(messages), 0, -1):
            cache_key = self._compute_prefix_hash(messages, prefix_len)
            
            if cache_key in self._prefix_cache:
                entry = self._prefix_cache[cache_key]
                entry.access_count += 1
                entry.last_accessed = time.time()
                
                # 移到LRU队列前面
                self._prefix_cache.move_to_end(cache_key)
                
                return prefix_len, entry

        return None, None

    def cache_prefix(
        self,
        messages: List[Dict[str, Any]],
        prefix_length: int,
        estimated_tokens: int,
    ):
        """
        缓存前缀 - 配合DeepSeek KV Cache
        
        注意：DeepSeek只缓存64token以上的内容
        """
        if prefix_length == 0:
            return
            
        if estimated_tokens < self.min_prefix_tokens:
            return  # 不足64tokens不缓存，符合DeepSeek机制

        cache_key = self._compute_prefix_hash(messages, prefix_length)

        if cache_key in self._prefix_cache:
            # 更新已有的缓存条目
            entry = self._prefix_cache[cache_key]
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._prefix_cache.move_to_end(cache_key)
        else:
            # 创建新的缓存条目
            entry = PrefixCacheEntry(
                prefix_messages=messages[:prefix_length],
                prefix_length=prefix_length,
                prefix_tokens=estimated_tokens,
            )
            self._prefix_cache[cache_key] = entry

            # LRU淘汰
            if len(self._prefix_cache) > self.max_prefixes:
                self._prefix_cache.popitem(last=False)

    def optimize_for_deepseek(
        self,
        messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        为DeepSeek优化消息排列，最大化KV Cache命中
        
        返回: (优化后的消息, 优化信息)
        """
        self._stats["total_requests"] += 1
        
        optimization_info = {
            "original_length": len(messages),
            "prefix_hit": False,
            "prefix_length": 0,
        }

        # 查找前缀匹配
        prefix_len, entry = self.find_matching_prefix(messages)
        
        if entry is not None:
            optimization_info["prefix_hit"] = True
            optimization_info["prefix_length"] = prefix_len
            self._stats["prefix_hits"] += 1
            self._stats["tokens_saved"] += entry.prefix_tokens

            # 对于DeepSeek，我们不需要修改消息，它会自动处理
            # 但我们记录统计信息以便优化
            return messages, optimization_info

        # 如果没有命中，我们可以尝试常见的前缀模式优化
        # 比如保持系统消息在前，示例消息在前等
        
        return messages, optimization_info

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        hit_rate = self._stats["prefix_hits"] / max(self._stats["total_requests"], 1)
        
        return {
            "total_requests": self._stats["total_requests"],
            "prefix_hits": self._stats["prefix_hits"],
            "hit_rate": hit_rate,
            "tokens_saved": self._stats["tokens_saved"],
            "cached_prefixes": len(self._prefix_cache),
            "min_prefix_tokens": self.min_prefix_tokens,
        }

    def clear(self):
        """清空缓存"""
        self._prefix_cache.clear()
        self._stats = {
            "total_requests": 0,
            "prefix_hits": 0,
            "tokens_saved": 0,
        }
