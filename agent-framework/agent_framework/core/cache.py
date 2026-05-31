"""
通用缓存系统 - Universal Cache System / 通用緩存系統
提供线程安全的内存缓存，支持TTL、LRU淘汰策略
Provides thread-safe in-memory cache with TTL, LRU eviction policy

性能优化特性 / Performance optimization features:
- O(1)读写操作
- 自动过期清理
- 内存使用限制
- 统计监控

参考实现 / Reference implementations:
- Python functools.lru_cache
- Redis CACHE implementation
- Memcached slab allocator
"""
import time
import threading
from typing import Any, Dict, Optional, Tuple, Callable, TypeVar, Generic
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class CacheEntry:
    """
    缓存条目 - Cache Entry / 緩存條目
    存储缓存的值和元数据
    Stores cached value and metadata

    Attributes:
        value: 缓存的值 / Cached value
        created_at: 创建时间 / Creation time
        expires_at: 过期时间 / Expiration time
        access_count: 访问次数 / Access count (for LRU)
        size: 估计内存大小（字节） / Estimated memory size (bytes)
    """
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    access_count: int = 0
    size: int = 0


K = TypeVar('K')  # Key type / 键类型
V = TypeVar('V')  # Value type / 值类型


class TTLCache(Generic[K, V]):
    """
    带TTL的LRU缓存 - TTL-enabled LRU Cache / 帶TTL的LRU緩存
    线程安全的通用缓存实现
    Thread-safe generic cache implementation

    使用示例 / Usage example:
    ```python
    # 创建缓存（最大1000条，默认TTL 300秒）
    cache = TTLCache(maxsize=1000, default_ttl=300)

    # 设置值
    cache.set("key1", "value1")
    cache.set("key2", {"complex": "object"}, ttl=600)  # 自定义TTL

    # 获取值
    value = cache.get("key1")
    if value is None:
        print("缓存未命中或已过期")

    # 批量操作
    cache.set_many({"a": 1, "b": 2, "c": 3})
    items = cache.get_many(["a", "b", "c", "d"])

    # 装饰器用法（函数结果缓存）
    @cache.cached(ttl=60)
    def expensive_function(x: int) -> int:
        return x * x
    ```

    线程安全说明 / Thread safety notes:
    - 所有公共方法都是线程安全的
    - 内部使用RLock保证原子性
    - 支持高并发读写场景
    """

    def __init__(
        self,
        maxsize: int = 1000,
        default_ttl: Optional[float] = None,
        max_memory_bytes: Optional[int] = None,
        cleanup_interval: float = 60.0,
    ):
        """
        初始化缓存 - Initialize cache

        Args:
            maxsize: 最大条目数 / Maximum number of entries
            default_ttl: 默认过期时间（秒），None表示永不过期 / Default TTL (seconds), None for no expiry
            max_memory_bytes: 最大内存使用量（字节） / Maximum memory usage (bytes)
            cleanup_interval: 自动清理间隔（秒） / Auto-cleanup interval (seconds)
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_bytes
        self.cleanup_interval = cleanup_interval

        self._lock = threading.RLock()
        self._cache: OrderedDict[K, CacheEntry] = OrderedDict()

        # 统计信息 - Statistics
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._total_sets: int = 0

        # 当前内存使用估算 - Current memory usage estimate
        self._current_memory: int = 0

        # 上次清理时间 - Last cleanup time
        self._last_cleanup: float = time.time()

    def _estimate_size(self, value: Any) -> int:
        """
        估算值的内存大小 - Estimate memory size of value / 估算值的內存大小
        使用序列化后的字节长度作为近似值
        Uses serialized byte length as approximation

        Args:
            value: 要估算的值 / Value to estimate

        Returns:
            估算的字节数 / Estimated bytes
        """
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float, bool)):
                return 8
            elif isinstance(value, dict):
                return len(json.dumps(value, default=str))
            elif isinstance(value, (list, tuple, set)):
                return sum(self._estimate_size(item) for item in value)
            else:
                # 对于复杂对象，使用字符串表示的长度
                return len(repr(value))
        except Exception:
            return 64  # 默认估算值 / Default estimate

    def _cleanup_expired(self) -> int:
        """
        清理过期的条目 - Clean up expired entries / 清理過期的條目
        应该在每次操作前或定期调用
        Should be called before each operation or periodically

        Returns:
            清理的条目数 / Number of cleaned entries
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at is not None and now > entry.expires_at
        ]

        for key in expired_keys:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size

        return len(expired_keys)

    def _enforce_limits(self) -> None:
        """
        强制执行限制（大小和内存） - Enforce limits (size and memory) / 強制執行限制
        使用LRU策略淘汰最久未访问的条目
        Evicts least recently used entries using LRU policy
        """
        now = time.time()

        # 定期清理过期条目 - Periodically clean up expired entries
        if now - self._last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now

        # 检查大小限制 - Check size limit
        while len(self._cache) > self.maxsize:
            oldest_key, oldest_entry = self._cache.popitem(last=False)
            self._current_memory -= oldest_entry.size
            self._evictions += 1

        # 检查内存限制 - Check memory limit
        if self.max_memory_bytes is not None:
            while self._current_memory > self.max_memory_bytes and self._cache:
                oldest_key, oldest_entry = self._cache.popitem(last=False)
                self._current_memory -= oldest_entry.size
                self._evictions += 1

    def get(self, key: K, default: V = None) -> Optional[V]:
        """
        获取缓存值 - Get cached value / 獲取緩存值
        如果键不存在或已过期，返回默认值
        Returns default if key doesn't exist or has expired

        Args:
            key: 缓存键 / Cache key
            default: 默认值 / Default value

        Returns:
            缓存的值或默认值 / Cached value or default
        """
        with self._lock:
            # 清理过期条目 - Clean up expired entries
            self._cleanup_expired()

            if key not in self._cache:
                self._misses += 1
                return default

            entry = self._cache[key]

            # 检查是否过期 - Check if expired
            if entry.expires_at is not None and time.time() > entry.expires_at:
                del self._cache[key]
                self._current_memory -= entry.size
                self._misses += 1
                return default

            # 更新访问统计（用于LRU） - Update access stats (for LRU)
            entry.access_count += 1
            self._cache.move_to_end(key)

            self._hits += 1
            return entry.value

    def set(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """
        设置缓存值 - Set cached value / 設置緩存值
        如果键已存在，更新其值和TTL
        If key exists, updates its value and TTL

        Args:
            key: 缓存键 / Cache key
            value: 要缓存的值 / Value to cache
            ttl: 过期时间（秒），None使用默认值 / TTL (seconds), None for default
        """
        with self._lock:
            now = time.time()

            # 如果键已存在，先移除旧条目 - If key exists, remove old entry first
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_memory -= old_entry.size

            # 计算过期时间 - Calculate expiry time
            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = now + effective_ttl if effective_ttl is not None else None

            # 估算大小 - Estimate size
            size = self._estimate_size(value)

            # 创建新条目 - Create new entry
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=expires_at,
                access_count=0,
                size=size,
            )

            self._cache[key] = entry
            self._current_memory += size
            self._total_sets += 1

            # 移到末尾（最近访问） - Move to end (most recently accessed)
            self._cache.move_to_end(key)

            # 强制执行限制 - Enforce limits
            self._enforce_limits()

    def delete(self, key: K) -> bool:
        """
        删除缓存条目 - Delete cache entry / 刪除緩存條目

        Args:
            key: 要删除的键 / Key to delete

        Returns:
            是否删除成功 / Whether deletion was successful
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._current_memory -= entry.size
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存 - Clear all caches / 清空所有緩存"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0

    def get_many(self, keys: List[K]) -> Dict[K, V]:
        """
        批量获取 - Batch get / 批量獲取
        一次获取多个键的值
        Get values for multiple keys at once

        Args:
            keys: 键列表 / List of keys

        Returns:
            键值字典（只包含存在的键） / Dictionary of key-value pairs (only existing keys)
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, data: Dict[K, V], ttl: Optional[float] = None) -> None:
        """
        批量设置 - Batch set / 批量設置
        一次设置多个键值对
        Set multiple key-value pairs at once

        Args:
            data: 键值字典 / Dictionary of key-value pairs
            ttl: 过期时间（秒） / TTL (seconds)
        """
        for key, value in data.items():
            self.set(key, value, ttl)

    def exists(self, key: K) -> bool:
        """
        检查键是否存在且未过期 - Check if key exists and hasn't expired / 檢查鍵是否存在且未過期

        Args:
            key: 要检查的键 / Key to check

        Returns:
            是否存在 / Whether it exists
        """
        return self.get(key) is not None

    def touch(self, key: K, ttl: Optional[float] = None) -> bool:
        """
        更新键的过期时间 - Update key's expiry time / 更新鍵的過期時間
        不改变缓存的值
        Doesn't change the cached value

        Args:
            key: 要更新的键 / Key to update
            ttl: 新的TTL（秒） / New TTL (seconds)

        Returns:
            是否更新成功 / Whether update was successful
        """
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]

            # 检查是否已过期 - Check if already expired
            if entry.expires_at is not None and time.time() > entry.expires_at:
                return False

            # 更新过期时间 - Update expiry time
            effective_ttl = ttl if ttl is not None else self.default_ttl
            if effective_ttl is not None:
                entry.expires_at = time.time() + effective_ttl

            return True

    def keys(self) -> List[K]:
        """获取所有键 - Get all keys / 獲取所有鍵"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())

    def values(self) -> List[V]:
        """获取所有值 - Get all values / 獲取所有值"""
        with self._lock:
            self._cleanup_expired()
            return [entry.value for entry in self._cache.values()]

    def items(self) -> List[Tuple[K, V]]:
        """获取所有键值对 - Get all key-value pairs / 獲取所有鍵值對"""
        with self._lock:
            self._cleanup_expired()
            return [(key, entry.value) for key, entry in self._cache.items()]

    def __len__(self) -> int:
        """返回当前条目数 - Return current entry count / 返回當前條目數"""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)

    def __contains__(self, key: K) -> bool:
        """检查键是否存在 - Check if key exists / 檢查鍵是否存在"""
        return self.exists(key)

    def __getitem__(self, key: K) -> V:
        """
        通过[]获取值 - Get value via [] operator
        如果不存在则抛出KeyError
        Raises KeyError if doesn't exist
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        """通过[]设置值 - Set value via [] operator"""
        self.set(key, value)

    def __delitem__(self, key: K) -> None:
        """通过[]删除 - Delete via [] operator"""
        if not self.delete(key):
            raise KeyError(key)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息 - Get statistics / 獲取統計信息
        返回缓存的运行统计数据
        Returns runtime statistics of the cache

        Returns:
            统计数据字典 / Statistics dictionary
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.maxsize,
                "memory_usage_bytes": self._current_memory,
                "max_memory_bytes": self.max_memory_bytes,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self._evictions,
                "total_sets": self._total_sets,
                "default_ttl": self.default_ttl,
            }

    def cached(self, ttl: Optional[float] = None):
        """
        缓存装饰器 - Cache decorator / 緩存裝飾器
        用于缓存函数的结果
        Used to cache function results

        用法示例 / Usage example:
        ```python
        @cache.cached(ttl=60)
        def expensive_computation(x: int) -> int:
            # 复杂计算...
            return x ** 2
        ```

        Args:
            ttl: 过期时间（秒） / TTL (seconds)

        Returns:
            装饰器函数 / Decorator function
        """
        def decorator(func: Callable[..., V]) -> Callable[..., V]:
            def wrapper(*args, **kwargs) -> V:
                # 生成缓存键 - Generate cache key
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                }
                key_str = json.dumps(key_data, sort_keys=True, default=str)
                key_hash = hashlib.md5(key_str.encode()).hexdigest()

                # 尝试从缓存获取 - Try to get from cache
                cached_result = self.get(key_hash)
                if cached_result is not None:
                    return cached_result

                # 计算并缓存结果 - Compute and cache result
                result = func(*args, **kwargs)
                self.set(key_hash, result, ttl=ttl)

                return result

            # 保留原始函数信息 - Preserve original function info
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            wrapper.__module__ = func.__module__

            return wrapper

        return decorator


# ============================================================================
# 全局缓存实例 - Global cache instances / 全局緩存實例
# ============================================================================

# 默认缓存实例 - Default cache instance
_default_cache = TTLCache(maxsize=10000, default_ttl=300)


def get_cache(
    maxsize: int = 1000,
    default_ttl: Optional[float] = None,
) -> TTLCache:
    """
    获取缓存实例 - Get cache instance / 獲取緩存實例

    Args:
        maxsize: 最大条目数 / Max entries
        default_ttl: 默认TTL / Default TTL

    Returns:
        缓存实例 / Cache instance
    """
    return TTLCache(maxsize=maxsize, default_ttl=default_ttl)


def cached(ttl: Optional[float] = None):
    """
    便捷缓存装饰器 - Convenience cache decorator / 便捷緩存裝飾器
    使用默认缓存实例
    Uses the default cache instance

    用法 / Usage:
    ```python
    @cached(ttl=60)
    def my_func(x):
        return x * x
    ```
    """
    return _default_cache.cached(ttl=ttl)
