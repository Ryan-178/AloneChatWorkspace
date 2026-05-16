"""
分布式追踪模块 - Distributed Tracing
支持追踪span、span嵌套、span导出等功能
"""
import time
import uuid
import threading
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextvars import ContextVar


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanEvent:
    """Span事件"""
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceSpan:
    """追踪Span"""
    span_id: str
    parent_span_id: Optional[str]
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def end(self, status: Optional[SpanStatus] = None):
        with self._lock:
            if self.end_time is None:
                self.end_time = time.time()
                if status:
                    self.status = status
    
    def add_attribute(self, key: str, value: Any):
        with self._lock:
            self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        with self._lock:
            self.events.append(SpanEvent(
                name=name,
                attributes=attributes or {}
            ))
    
    def record_exception(self, exception: Exception):
        with self._lock:
            self.status = SpanStatus.ERROR
            self.add_event("exception", {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception)
            })


_current_span: ContextVar[Optional[TraceSpan]] = ContextVar("current_span", default=None)


class Tracer:
    """追踪器"""
    
    def __init__(self, service_name: str = "agent-gateway"):
        self.service_name = service_name
        self._spans: Dict[str, TraceSpan] = {}
        self._lock = threading.Lock()
        self._export_callbacks: List[callable] = []
    
    def start_span(
        self,
        name: str,
        parent_span: Optional[TraceSpan] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """开始一个新的Span"""
        span_id = str(uuid.uuid4())
        
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None
        
        span = TraceSpan(
            span_id=span_id,
            parent_span_id=parent_span_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {}
        )
        
        with self._lock:
            self._spans[span_id] = span
        
        return span
    
    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """获取Span"""
        with self._lock:
            return self._spans.get(span_id)
    
    def end_span(self, span: TraceSpan, status: Optional[SpanStatus] = None):
        """结束Span"""
        span.end(status)
        
        # 调用导出回调
        for callback in self._export_callbacks:
            try:
                callback(span)
            except Exception:
                pass
    
    def add_export_callback(self, callback: callable):
        """添加导出回调"""
        self._export_callbacks.append(callback)
    
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Span装饰器/上下文管理器"""
        class SpanContext:
            def __init__(self, tracer: Tracer, span_name: str, span_attrs: Optional[Dict[str, Any]]):
                self.tracer = tracer
                self.span_name = span_name
                self.span_attrs = span_attrs
                self.span: Optional[TraceSpan] = None
                self._prev_span: Optional[TraceSpan] = None
            
            def __call__(self, func):
                def wrapper(*args, **kwargs):
                    with self:
                        return func(*args, **kwargs)
                return wrapper
            
            def __enter__(self):
                self._prev_span = _current_span.get()
                self.span = self.tracer.start_span(
                    self.span_name, self._prev_span, self.span_attrs)
                _current_span.set(self.span)
                return self.span
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_val:
                        self.span.record_exception(exc_val)
                        self.tracer.end_span(self.span, SpanStatus.ERROR)
                    else:
                        self.tracer.end_span(self.span, SpanStatus.OK)
                if self._prev_span:
                    _current_span.set(self._prev_span)
                return False
        
        return SpanContext(self, name, attributes)
    
    def get_current_span(self) -> Optional[TraceSpan]:
        """获取当前Span"""
        return _current_span.get()
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """获取整个追踪链"""
        with self._lock:
            return [
                span for span in self._spans.values() if span.trace_id == trace_id]
    
    def export_spans(self) -> List[Dict[str, Any]]:
        """导出所有Span"""
        with self._lock:
            return [self._span_to_dict(span) for span in self._spans.values()]
    
    def _span_to_dict(self, span: TraceSpan) -> Dict[str, Any]:
        """将Span转换为字典"""
        return {
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "trace_id": span.trace_id,
            "name": span.name,
            "service_name": self.service_name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "duration_ms": span.duration_ms,
            "status": span.status,
            "attributes": span.attributes,
            "events": [
                {
                    "name": e.name,
                    "timestamp": e.timestamp,
                    "attributes": e.attributes
                }
                for e in span.events
            ]
        }
    
    def clear(self):
        """清除所有Span"""
        with self._lock:
            self._spans.clear()


# 全局追踪器实例
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "agent-gateway") -> Tracer:
    """获取全局追踪器"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer
