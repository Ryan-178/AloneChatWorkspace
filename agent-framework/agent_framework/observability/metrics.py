"""
指标收集模块 - Metrics Collection
支持计数器、直方图、仪表盘等指标类型
"""
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """指标值"""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """直方图桶"""
    upper_bound: float
    count: int = 0


@dataclass
class Metric:
    """指标"""
    name: str
    type: MetricType
    description: str = ""
    values: List[MetricValue] = field(default_factory=list)
    buckets: Optional[List[HistogramBucket]] = None
    _sum: float = 0.0
    _count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __post_init__(self):
        if self.type == MetricType.HISTOGRAM and not self.buckets:
            # 默认桶
            self.buckets = [
                HistogramBucket(upper_bound=0.005),
                HistogramBucket(upper_bound=0.01),
                HistogramBucket(upper_bound=0.025),
                HistogramBucket(upper_bound=0.05),
                HistogramBucket(upper_bound=0.1),
                HistogramBucket(upper_bound=0.25),
                HistogramBucket(upper_bound=0.5),
                HistogramBucket(upper_bound=1.0),
                HistogramBucket(upper_bound=2.5),
                HistogramBucket(upper_bound=5.0),
                HistogramBucket(upper_bound=10.0),
            ]


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        self._started_at = time.time()
    
    def create_counter(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """创建计数器"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Metric(
                    name=name,
                    type=MetricType.COUNTER,
                    description=description
                )
            return self._metrics[name]
    
    def create_gauge(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """创建仪表盘"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Metric(
                    name=name,
                    type=MetricType.GAUGE,
                    description=description
                )
            return self._metrics[name]
    
    def create_histogram(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """创建直方图"""
        with self._lock:
            if name not in self._metrics:
                metric = Metric(
                    name=name,
                    type=MetricType.HISTOGRAM,
                    description=description
                )
                if buckets:
                    metric.buckets = [HistogramBucket(upper_bound=b) for b in sorted(buckets)]
                self._metrics[name] = metric
            return self._metrics[name]
    
    def create_timer(
        self,
        name: str,
        description: str = "",
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """创建计时器（基于直方图）"""
        return self.create_histogram(name, description, labels=labels)
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """增加计数器"""
        metric = self.create_counter(name, labels=labels)
        with metric._lock:
            metric._count += int(value)
            metric.values.append(MetricValue(
                value=metric._count,
                labels=labels or {}
            ))
    
    def decrement(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """减少计数器"""
        self.increment(name, -value, labels)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """设置仪表盘值"""
        metric = self.create_gauge(name, labels=labels)
        with metric._lock:
            metric.values.append(MetricValue(
                value=value,
                labels=labels or {}
            ))
    
    def observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """记录观察值（用于直方图）"""
        metric = self.create_histogram(name, labels=labels)
        with metric._lock:
            metric._sum += value
            metric._count += 1
            metric.values.append(MetricValue(
                value=value,
                labels=labels or {}
            ))
            
            # 更新桶
            if metric.buckets:
                for bucket in metric.buckets:
                    if value <= bucket.upper_bound:
                        bucket.count += 1
    
    def time(self, name: str, labels: Optional[Dict[str, str]] = None):
        """计时器上下文管理器"""
        class TimerContext:
            def __init__(self, collector: MetricsCollector, metric_name: str, metric_labels: Optional[Dict[str, str]]):
                self.collector = collector
                self.metric_name = metric_name
                self.metric_labels = metric_labels
                self.start_time: Optional[float] = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time:
                    duration = time.time() - self.start_time
                    self.collector.observe(self.metric_name, duration, self.metric_labels)
                return False
        
        return TimerContext(self, name, labels)
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """获取所有指标"""
        return dict(self._metrics)
    
    def export(self) -> Dict[str, Any]:
        """导出指标数据"""
        export_data = {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self._started_at,
            "metrics": {}
        }
        
        for name, metric in self._metrics.items():
            metric_data = {
                "type": metric.type,
                "description": metric.description,
                "count": metric._count
            }
            
            if metric.type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                metric_data["sum"] = metric._sum
                if metric._count > 0:
                    metric_data["avg"] = metric._sum / metric._count
                if metric.buckets:
                    metric_data["buckets"] = [
                        {"upper_bound": b.upper_bound, "count": b.count}
                        for b in metric.buckets
                    ]
            
            # 最新值
            if metric.values:
                metric_data["last_value"] = metric.values[-1].value
                metric_data["last_timestamp"] = metric.values[-1].timestamp
            
            export_data["metrics"][name] = metric_data
        
        return export_data
    
    def reset(self, name: Optional[str] = None):
        """重置指标"""
        with self._lock:
            if name:
                if name in self._metrics:
                    metric = self._metrics[name]
                    with metric._lock:
                        metric.values.clear()
                        metric._sum = 0.0
                        metric._count = 0
                        if metric.buckets:
                            for bucket in metric.buckets:
                                bucket.count = 0
            else:
                for metric in self._metrics.values():
                    with metric._lock:
                        metric.values.clear()
                        metric._sum = 0.0
                        metric._count = 0
                        if metric.buckets:
                            for bucket in metric.buckets:
                                bucket.count = 0


# 全局指标收集器实例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
