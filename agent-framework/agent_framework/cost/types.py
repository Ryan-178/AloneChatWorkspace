"""
成本追踪类型定义 / Cost Tracking Type Definitions

定义成本相关的数据模型
Defines cost-related data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CostType(str, Enum):
    """
    成本类型 / Cost Type
    """
    INPUT = "input"
    OUTPUT = "output"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


class CostPeriod(str, Enum):
    """
    成本周期 / Cost Period
    """
    TURN = "turn"
    SESSION = "session"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class TokenUsage:
    """
    Token使用量 / Token Usage
    """
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """总Token数 / Total tokens"""
        return self.input_tokens + self.output_tokens

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率 / Cache hit rate"""
        total_read = self.cache_read_tokens + self.input_tokens
        if total_read == 0:
            return 0.0
        return self.cache_read_tokens / total_read

    def to_dict(self) -> Dict[str, int]:
        """转换为字典 / Convert to dictionary"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "total_tokens": self.total_tokens,
        }

    def add(self, other: "TokenUsage") -> "TokenUsage":
        """累加使用量 / Add usage"""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
        )


@dataclass
class CostRecord:
    """
    成本记录 / Cost Record
    """
    id: str
    session_id: str
    turn_id: Optional[str] = None
    model_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    usage: TokenUsage = field(default_factory=TokenUsage)
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_cost: float = 0.0
    total_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def cost_per_million(self) -> float:
        """每百万Token成本 / Cost per million tokens"""
        total = self.usage.total_tokens
        if total == 0:
            return 0.0
        return (self.total_cost / total) * 1_000_000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "model_id": self.model_id,
            "timestamp": self.timestamp.isoformat(),
            "usage": self.usage.to_dict(),
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "cache_cost": self.cache_cost,
            "total_cost": self.total_cost,
            "metadata": self.metadata,
        }


@dataclass
class SessionCost:
    """
    会话成本 / Session Cost
    """
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_usage: TokenUsage = field(default_factory=TokenUsage)
    total_cost: float = 0.0
    turn_count: int = 0
    model_costs: Dict[str, float] = field(default_factory=dict)
    records: List[CostRecord] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """持续时间（秒） / Duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def avg_cost_per_turn(self) -> float:
        """每轮平均成本 / Average cost per turn"""
        if self.turn_count == 0:
            return 0.0
        return self.total_cost / self.turn_count

    def add_record(self, record: CostRecord) -> None:
        """添加记录 / Add record"""
        self.records.append(record)
        self.total_usage = self.total_usage.add(record.usage)
        self.total_cost += record.total_cost
        if record.turn_id:
            self.turn_count += 1
        if record.model_id:
            if record.model_id not in self.model_costs:
                self.model_costs[record.model_id] = 0.0
            self.model_costs[record.model_id] += record.total_cost

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_usage": self.total_usage.to_dict(),
            "total_cost": self.total_cost,
            "turn_count": self.turn_count,
            "model_costs": self.model_costs,
            "duration_seconds": self.duration_seconds,
            "avg_cost_per_turn": self.avg_cost_per_turn,
        }


@dataclass
class DailyCost:
    """
    每日成本 / Daily Cost
    """
    date: str
    total_usage: TokenUsage = field(default_factory=TokenUsage)
    total_cost: float = 0.0
    session_count: int = 0
    model_costs: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "date": self.date,
            "total_usage": self.total_usage.to_dict(),
            "total_cost": self.total_cost,
            "session_count": self.session_count,
            "model_costs": self.model_costs,
        }


@dataclass
class CacheStats:
    """
    缓存统计 / Cache Statistics
    """
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved: int = 0
    cost_saved: float = 0.0

    @property
    def hit_rate(self) -> float:
        """命中率 / Hit rate"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """未命中率 / Miss rate"""
        return 1.0 - self.hit_rate

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "tokens_saved": self.tokens_saved,
            "cost_saved": self.cost_saved,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
        }


@dataclass
class CostAlert:
    """
    成本警告 / Cost Alert
    """
    alert_type: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def percentage(self) -> float:
        """达到阈值的百分比 / Percentage of threshold"""
        if self.threshold == 0:
            return 0.0
        return (self.current_value / self.threshold) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "alert_type": self.alert_type,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "percentage": self.percentage,
        }
