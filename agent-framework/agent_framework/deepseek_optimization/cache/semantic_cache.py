"""
Semantic Cache
基于语义相似度的缓存层
"""
import hashlib
import xxhash
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
import time


@dataclass
class CachedItem:
    """缓存条目"""
    key: str
    value: Any
    hash_key: str
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0


class SemanticCache:
    """
    语义缓存层
    支持精确匹配和近似相似度匹配
    """

    def __init__(
        self,
        max_size: int = 10000,
        similarity_threshold: float = 0.95,
        ttl_seconds: float = 86400 * 7,
    ):
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._hash_map: Dict[str, CachedItem] = {}

    def _compute_hash(self, text: str) -> str:
        """计算内容哈希"""
        return xxhash.xxh64(text.encode("utf-8")).hexdigest()

    def _compute_fingerprint(self, text: str) -> str:
        """计算语义指纹"""
        # 归一化处理
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def put(self, key: str, value: Any, text: str = "") -> bool:
        """添加缓存"""
        cache_key = self._compute_hash(key)
        fingerprint = self._compute_fingerprint(text or key)
        item = CachedItem(
            key=key,
            value=value,
            hash_key=cache_key,
        )
        # 估算大小
        try:
            import json
            item.size_bytes = len(json.dumps(value, default=str))
        except Exception:
            item.size_bytes = 100
        self._cache[cache_key] = item
        self._hash_map[fingerprint] = item

        if len(self._cache) > self.max_size:
            self._evict_oldest()

        return True

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        cache_key = self._compute_hash(key)
        if cache_key in self._cache:
            item = self._cache[cache_key]

            # 检查TTL
            if time.time() - item.created_at > self.ttl_seconds:
                del self._cache[cache_key]
                if item.hash_key in self._hash_map:
                    del self._hash_map[item.hash_key]
                return None

            item.access_count += 1
            item.last_accessed = time.time()
            return item.value
        return None

    def find_similar(
        self, text: str, threshold: Optional[float] = None
    ) -> Tuple[Optional[Any], float]:
        """查找相似项（简化版）"""
        target_threshold = threshold or self.similarity_threshold
        fingerprint = self._compute_fingerprint(text)

        # 精确指纹匹配
        if fingerprint in self._hash_map:
            item = self._hash_map[fingerprint]
            return item.value, 1.0

        return None, 0.0

    def _evict_oldest(self):
        """淘汰最旧的条目"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            item = self._cache.popitem(last=False)
            if item[1].hash_key in self._hash_map:
                if self._hash_map[item[1].hash_key] == item[1]:
                    del self._hash_map[item[1].hash_key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hash_map.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return self._compute_hash(key) in self._cache
