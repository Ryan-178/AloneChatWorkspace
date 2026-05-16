"""
Context Monitor
上下文监控 - 性能指标收集和健康检查
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    total_messages_processed: int = 0
    total_tokens_processed: int = 0
    total_compressions: int = 0
    total_archives: int = 0
    total_cache_hits: int = 0
    total_cache_misses: int = 0
    
    avg_message_processing_time_ms: float = 0.0
    avg_compression_time_ms: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    
    peak_memory_usage_mb: float = 0.0
    current_memory_usage_mb: float = 0.0
    
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class ContextMonitor:
    """
    上下文监控器
    收集性能指标，执行健康检查
    """
    
    def __init__(
        self,
        enable_metrics: bool = True,
        metrics_retention_hours: int = 24,
        alert_thresholds: Optional[Dict[str, float]] = None,
    ):
        self.enable_metrics = enable_metrics
        self.metrics_retention = timedelta(hours=metrics_retention_hours)
        
        self.alert_thresholds = alert_thresholds or {
            "memory_usage_mb": 500.0,
            "token_usage_ratio": 0.9,
            "cache_hit_ratio": 0.5,
            "message_processing_time_ms": 100.0,
        }
        
        self._metrics = PerformanceMetrics()
        self._metric_history: Dict[str, List[MetricPoint]] = {}
        self._health_checks: Dict[str, Callable] = {}
        self._alerts: List[Dict[str, Any]] = []
        
        self._register_default_health_checks()
    
    def _register_default_health_checks(self):
        self.register_health_check("memory", self._check_memory)
        self.register_health_check("token_budget", self._check_token_budget)
        self.register_health_check("cache", self._check_cache)
        self.register_health_check("storage", self._check_storage)
    
    def register_health_check(self, name: str, check_func: Callable):
        self._health_checks[name] = check_func
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        if not self.enable_metrics:
            return
        
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {},
        )
        
        if name not in self._metric_history:
            self._metric_history[name] = []
        
        self._metric_history[name].append(point)
        
        self._cleanup_old_metrics(name)
    
    def _cleanup_old_metrics(self, name: str):
        cutoff = datetime.now() - self.metrics_retention
        self._metric_history[name] = [
            p for p in self._metric_history[name]
            if p.timestamp > cutoff
        ]
    
    def record_message_processed(self, token_count: int, processing_time_ms: float):
        self._metrics.total_messages_processed += 1
        self._metrics.total_tokens_processed += token_count
        
        total = self._metrics.total_messages_processed
        old_avg = self._metrics.avg_message_processing_time_ms
        self._metrics.avg_message_processing_time_ms = (
            old_avg * (total - 1) + processing_time_ms
        ) / total
        
        self._metrics.last_update = datetime.now()
        
        self.record_metric("message_processing_time", processing_time_ms)
        self.record_metric("tokens_per_message", token_count)
    
    def record_compression(self, original_tokens: int, compressed_tokens: int, time_ms: float):
        self._metrics.total_compressions += 1
        
        total = self._metrics.total_compressions
        old_avg = self._metrics.avg_compression_time_ms
        self._metrics.avg_compression_time_ms = (
            old_avg * (total - 1) + time_ms
        ) / total
        
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0
        self.record_metric("compression_ratio", ratio)
        self.record_metric("compression_time", time_ms)
    
    def record_archive(self):
        self._metrics.total_archives += 1
        self.record_metric("archive_count", self._metrics.total_archives)
    
    def record_cache_hit(self):
        self._metrics.total_cache_hits += 1
    
    def record_cache_miss(self):
        self._metrics.total_cache_misses += 1
    
    def update_memory_usage(self, current_mb: float):
        self._metrics.current_memory_usage_mb = current_mb
        self._metrics.peak_memory_usage_mb = max(
            self._metrics.peak_memory_usage_mb,
            current_mb
        )
        self.record_metric("memory_usage", current_mb)
    
    def run_health_check(self, name: str, **kwargs) -> HealthCheckResult:
        if name not in self._health_checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.WARNING,
                message=f"Unknown health check: {name}",
            )
        
        try:
            return self._health_checks[name](**kwargs)
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
            )
    
    def run_all_health_checks(self, **kwargs) -> Dict[str, HealthCheckResult]:
        results = {}
        for name in self._health_checks:
            results[name] = self.run_health_check(name, **kwargs)
        return results
    
    def _check_memory(self, **kwargs) -> HealthCheckResult:
        current = self._metrics.current_memory_usage_mb
        threshold = self.alert_thresholds.get("memory_usage_mb", 500.0)
        
        if current < threshold * 0.7:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {current:.1f}MB"
        elif current < threshold:
            status = HealthStatus.WARNING
            message = f"Memory usage elevated: {current:.1f}MB"
        else:
            status = HealthStatus.CRITICAL
            message = f"Memory usage critical: {current:.1f}MB"
        
        return HealthCheckResult(
            name="memory",
            status=status,
            message=message,
            details={"current_mb": current, "threshold_mb": threshold},
        )
    
    def _check_token_budget(self, **kwargs) -> HealthCheckResult:
        usage_ratio = kwargs.get("token_usage_ratio", 0.0)
        threshold = self.alert_thresholds.get("token_usage_ratio", 0.9)
        
        if usage_ratio < threshold * 0.7:
            status = HealthStatus.HEALTHY
            message = f"Token usage normal: {usage_ratio:.1%}"
        elif usage_ratio < threshold:
            status = HealthStatus.WARNING
            message = f"Token usage elevated: {usage_ratio:.1%}"
        else:
            status = HealthStatus.CRITICAL
            message = f"Token usage critical: {usage_ratio:.1%}"
        
        return HealthCheckResult(
            name="token_budget",
            status=status,
            message=message,
            details={"usage_ratio": usage_ratio, "threshold": threshold},
        )
    
    def _check_cache(self, **kwargs) -> HealthCheckResult:
        hits = self._metrics.total_cache_hits
        misses = self._metrics.total_cache_misses
        total = hits + misses
        
        if total == 0:
            ratio = 1.0
        else:
            ratio = hits / total
        
        threshold = self.alert_thresholds.get("cache_hit_ratio", 0.5)
        
        if ratio >= threshold:
            status = HealthStatus.HEALTHY
            message = f"Cache hit ratio good: {ratio:.1%}"
        else:
            status = HealthStatus.WARNING
            message = f"Cache hit ratio low: {ratio:.1%}"
        
        return HealthCheckResult(
            name="cache",
            status=status,
            message=message,
            details={"hit_ratio": ratio, "hits": hits, "misses": misses},
        )
    
    def _check_storage(self, **kwargs) -> HealthCheckResult:
        archived = self._metrics.total_archives
        storage_available = kwargs.get("storage_available", True)
        
        if storage_available:
            status = HealthStatus.HEALTHY
            message = f"Storage healthy, {archived} items archived"
        else:
            status = HealthStatus.CRITICAL
            message = "Storage unavailable"
        
        return HealthCheckResult(
            name="storage",
            status=status,
            message=message,
            details={"archived_count": archived, "available": storage_available},
        )
    
    def check_alerts(self, **kwargs) -> List[Dict[str, Any]]:
        alerts = []
        
        health_results = self.run_all_health_checks(**kwargs)
        
        for name, result in health_results.items():
            if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                alerts.append({
                    "name": name,
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat(),
                    "details": result.details,
                })
        
        self._alerts = alerts
        return alerts
    
    def get_metrics(self) -> PerformanceMetrics:
        return self._metrics
    
    def get_metric_history(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> List[MetricPoint]:
        history = self._metric_history.get(name, [])
        
        if since:
            history = [p for p in history if p.timestamp >= since]
        
        return history
    
    def get_summary(self) -> Dict[str, Any]:
        runtime = datetime.now() - self._metrics.start_time
        
        cache_total = self._metrics.total_cache_hits + self._metrics.total_cache_misses
        cache_ratio = (
            self._metrics.total_cache_hits / cache_total
            if cache_total > 0 else 0
        )
        
        return {
            "runtime_seconds": runtime.total_seconds(),
            "messages_processed": self._metrics.total_messages_processed,
            "tokens_processed": self._metrics.total_tokens_processed,
            "compressions": self._metrics.total_compressions,
            "archives": self._metrics.total_archives,
            "cache_hit_ratio": cache_ratio,
            "avg_processing_time_ms": self._metrics.avg_message_processing_time_ms,
            "avg_compression_time_ms": self._metrics.avg_compression_time_ms,
            "current_memory_mb": self._metrics.current_memory_usage_mb,
            "peak_memory_mb": self._metrics.peak_memory_usage_mb,
            "active_alerts": len(self._alerts),
        }
