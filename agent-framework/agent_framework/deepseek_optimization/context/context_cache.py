"""
Context Cache
上下文缓存 - LRU缓存和预热机制
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)


@dataclass
class CacheStats:
    total_entries: int = 0
    total_size_bytes: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class ContextCache:
    """
    上下文LRU缓存
    支持TTL、大小限制和预热
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 100.0,
        default_ttl_seconds: Optional[int] = 3600,
    ):
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl_seconds = default_ttl_seconds
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        
        self._preloaded_keys: set = set()
    
    def _generate_key(self, *args, **kwargs) -> str:
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _estimate_size(self, value: Any) -> int:
        if isinstance(value, (str, bytes)):
            return len(value)
        try:
            return len(json.dumps(value, default=str))
        except:
            return 100
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            self._stats.misses += 1
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired():
            self._remove(key)
            self._stats.misses += 1
            return None
        
        self._cache.move_to_end(key)
        entry.last_accessed = datetime.now()
        entry.access_count += 1
        self._stats.hits += 1
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        size = self._estimate_size(value)
        
        while (
            len(self._cache) >= self.max_size or
            self._stats.total_size_bytes + size > self.max_memory_bytes
        ):
            if not self._evict_oldest():
                break
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl_seconds or self.default_ttl_seconds,
            size_bytes=size,
        )
        
        if key in self._cache:
            self._stats.total_size_bytes -= self._cache[key].size_bytes
            del self._cache[key]
        
        self._cache[key] = entry
        self._stats.total_size_bytes += size
        self._stats.total_entries = len(self._cache)
        
        return True
    
    def _remove(self, key: str) -> bool:
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        self._stats.total_size_bytes -= entry.size_bytes
        del self._cache[key]
        self._stats.total_entries = len(self._cache)
        
        return True
    
    def _evict_oldest(self) -> bool:
        if not self._cache:
            return False
        
        oldest_key = next(iter(self._cache))
        self._remove(oldest_key)
        self._stats.evictions += 1
        
        return True
    
    def delete(self, key: str) -> bool:
        return self._remove(key)
    
    def clear(self):
        self._cache.clear()
        self._stats = CacheStats()
    
    def contains(self, key: str) -> bool:
        if key not in self._cache:
            return False
        return not self._cache[key].is_expired()
    
    def get_stats(self) -> CacheStats:
        return self._stats
    
    def warmup(
        self,
        items: List[Dict[str, Any]],
        key_func: Optional[Callable] = None,
    ) -> int:
        warmed = 0
        
        for item in items:
            if key_func:
                key = key_func(item)
            else:
                key = self._generate_key(item)
            
            if self.set(key, item):
                self._preloaded_keys.add(key)
                warmed += 1
        
        return warmed
    
    def get_preloaded(self, key: str) -> Optional[Any]:
        if key in self._preloaded_keys:
            return self.get(key)
        return None
    
    def invalidate_pattern(self, pattern: str) -> int:
        import fnmatch
        
        keys_to_remove = [
            key for key in self._cache
            if fnmatch.fnmatch(key, pattern)
        ]
        
        for key in keys_to_remove:
            self._remove(key)
            self._preloaded_keys.discard(key)
        
        return len(keys_to_remove)
    
    def cleanup_expired(self) -> int:
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)


class ContextPreloader:
    """
    上下文预加载器
    基于历史模式预加载相关内容
    """
    
    def __init__(
        self,
        cache: ContextCache,
        storage_root: Optional[Path] = None,
    ):
        self.cache = cache
        self.storage_root = storage_root or Path("./data/context_preload")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        self._preload_rules: List[Dict[str, Any]] = []
        self._access_patterns: Dict[str, int] = {}
    
    def add_preload_rule(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        loader: Callable[[], List[Any]],
        priority: int = 0,
    ):
        self._preload_rules.append({
            "name": name,
            "condition": condition,
            "loader": loader,
            "priority": priority,
        })
        self._preload_rules.sort(key=lambda r: r["priority"], reverse=True)
    
    def record_access(self, key: str):
        self._access_patterns[key] = self._access_patterns.get(key, 0) + 1
    
    def get_frequent_keys(self, top_n: int = 10) -> List[str]:
        sorted_keys = sorted(
            self._access_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [key for key, _ in sorted_keys[:top_n]]
    
    def preload_frequent(self, loader: Callable[[str], Any]) -> int:
        frequent_keys = self.get_frequent_keys()
        warmed = 0
        
        for key in frequent_keys:
            if not self.cache.contains(key):
                value = loader(key)
                if value is not None:
                    self.cache.set(key, value)
                    warmed += 1
        
        return warmed
    
    def preload_by_rules(self, context: Dict[str, Any]) -> int:
        warmed = 0
        
        for rule in self._preload_rules:
            try:
                if rule["condition"](context):
                    items = rule["loader"]()
                    warmed += self.cache.warmup(items)
            except Exception:
                continue
        
        return warmed
    
    def save_patterns(self):
        patterns_file = self.storage_root / "access_patterns.json"
        with open(patterns_file, "w", encoding="utf-8") as f:
            json.dump(self._access_patterns, f)
    
    def load_patterns(self):
        patterns_file = self.storage_root / "access_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    self._access_patterns = json.load(f)
            except Exception:
                pass
