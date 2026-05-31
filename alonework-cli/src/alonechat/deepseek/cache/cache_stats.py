"""
Cache Statistics
缓存统计分析系统
"""
import time
from typing import Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class CacheStats:
    """
    缓存统计器
    用于跟踪缓存命中、命中、成本节约等关键指标
    """

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # 各层级的命中
    l1_hits: int = 0  # 内存缓存
    l2_hits: int = 0  # 向量缓存
    l3_hits: int = 0  # 持久化缓存

    # 成本节约
    total_tokens_saved: int = 0
    estimated_cost_saved: float = 0.0

    # 响应时间
    total_response_time: float = 0.0
    cache_hit_time: float = 0.0
    cache_miss_time: float = 0.0

    # 缓存大小
    cache_size: int = 0

    # 时间窗口统计
    start_time: float = field(default_factory=time.time)

    # 细粒度记录
    _request_times: list = field(default_factory=list, repr=False)
    _hit_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int), repr=False)

    def record_request(self, is_hit: bool, hit_type: str = "l1", response_time: float = 0.0):
        """记录请求"""
        self.total_requests += 1

        if is_hit:
            self.cache_hits += 1
            self.cache_hit_time += response_time
            self._hit_types[hit_type] += 1

            if hit_type == "l1":
                self.l1_hits += 1
            elif hit_type == "l2":
                self.l2_hits += 1
            elif hit_type == "l3":
                self.l3_hits += 1
        else:
            self.cache_misses += 1
            self.cache_miss_time += response_time

        self.total_response_time += response_time
        self._request_times.append(
            {"time": time.time(), "hit": is_hit, "duration": response_time}
        )

    def record_savings(self, tokens_saved: int, cost_saved: float):
        """记录节约的成本"""
        self.total_tokens_saved += tokens_saved
        self.estimated_cost_saved += cost_saved

    def update_size(self, size: int):
        """更新缓存大小"""
        self.cache_size = size

    @property
    def hit_rate(self) -> float:
        """获取命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """获取未命中率"""
        return 1.0 - self.hit_rate

    @property
    def avg_response_time(self) -> float:
        """获取平均响应时间"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    @property
    def avg_hit_time(self) -> float:
        """获取平均缓存命中时间"""
        if self.cache_hits == 0:
            return 0.0
        return self.cache_hit_time / self.cache_hits

    @property
    def avg_miss_time(self) -> float:
        """获取平均未命中时间"""
        if self.cache_misses == 0:
            return 0.0
        return self.cache_miss_time / self.cache_misses

    def get_summary(self) -> Dict[str, Any]:
        """获取完整统计摘要"""
        uptime = time.time() - self.start_time
        requests_per_second = self.total_requests / max(uptime, 1)

        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "hit_types": dict(self._hit_types),
            "total_tokens_saved": self.total_tokens_saved,
            "estimated_cost_saved": self.estimated_cost_saved,
            "avg_response_time_ms": self.avg_response_time * 1000,
            "avg_hit_time_ms": self.avg_hit_time * 1000,
            "avg_miss_time_ms": self.avg_miss_time * 1000,
            "cache_size": self.cache_size,
            "uptime_seconds": uptime,
            "requests_per_second": requests_per_second,
            "cost_savings_rate": self.estimated_cost_saved / max(self.total_requests * 0.01, 1),
        }

    def reset(self):
        """重置统计"""
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.total_tokens_saved = 0
        self.estimated_cost_saved = 0.0
        self.total_response_time = 0.0
        self.cache_hit_time = 0.0
        self.cache_miss_time = 0.0
        self.cache_size = 0
        self.start_time = time.time()
        self._request_times = []
        self._hit_types.clear()
