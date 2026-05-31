"""
DeepSeek V4 Optimizer - 深度优化器
API调用优化、成本控制、请求队列管理
"""
import asyncio
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import httpx

from agent_framework.core.base_llm import Message
from agent_framework.deepseek_optimization.llm.model_config import (
    DeepSeekConfig,
    DeepSeekModel,
    DEEPSEEK_PRICING,
)
from agent_framework.deepseek_optimization.cache.cache_engine import CacheEngine


class Priority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class QueuedRequest:
    id: str
    messages: List[Message]
    config: DeepSeekConfig
    priority: Priority
    created_at: float = field(default_factory=time.time)
    callback: Optional[Callable] = None
    retries: int = 0
    max_retries: int = 3


@dataclass
class CostBudget:
    daily_limit: float = 10.0
    monthly_limit: float = 100.0
    current_daily: float = 0.0
    current_monthly: float = 0.0
    last_reset_day: float = field(default_factory=time.time)
    last_reset_month: float = field(default_factory=time.time)


@dataclass
class OptimizerStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    queue_size: int = 0


class RequestQueue:
    """
    请求队列 - 支持优先级和并发控制
    Request Queue - Supports priority and concurrency control
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        max_queue_size: int = 1000,
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        
        self._queues: Dict[Priority, deque] = {
            Priority.HIGH: deque(),
            Priority.NORMAL: deque(),
            Priority.LOW: deque(),
        }
        
        self._current_concurrent = 0
        self._lock = asyncio.Lock()
    
    async def enqueue(self, request: QueuedRequest) -> bool:
        async with self._lock:
            total_size = sum(len(q) for q in self._queues.values())
            if total_size >= self.max_queue_size:
                return False
            
            self._queues[request.priority].append(request)
            return True
    
    async def dequeue(self) -> Optional[QueuedRequest]:
        async with self._lock:
            if self._current_concurrent >= self.max_concurrent:
                return None
            
            for priority in [Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                if self._queues[priority]:
                    self._current_concurrent += 1
                    return self._queues[priority].popleft()
            
            return None
    
    async def complete(self):
        async with self._lock:
            self._current_concurrent = max(0, self._current_concurrent - 1)
    
    def size(self) -> int:
        return sum(len(q) for q in self._queues.values())
    
    def is_empty(self) -> bool:
        return self.size() == 0


class CostController:
    """
    成本控制器 - 预算管理和成本追踪
    Cost Controller - Budget management and cost tracking
    """
    
    def __init__(self, budget: Optional[CostBudget] = None):
        self.budget = budget or CostBudget()
        self._cost_history: List[Dict[str, Any]] = []
    
    def check_budget(self, estimated_cost: float) -> bool:
        self._reset_if_needed()
        
        if self.budget.current_daily + estimated_cost > self.budget.daily_limit:
            return False
        
        if self.budget.current_monthly + estimated_cost > self.budget.monthly_limit:
            return False
        
        return True
    
    def record_cost(
        self,
        cost: float,
        tokens: int,
        model: str,
        request_id: str,
    ) -> None:
        self._reset_if_needed()
        
        self.budget.current_daily += cost
        self.budget.current_monthly += cost
        
        self._cost_history.append({
            "cost": cost,
            "tokens": tokens,
            "model": model,
            "request_id": request_id,
            "timestamp": time.time(),
        })
    
    def _reset_if_needed(self) -> None:
        now = time.time()
        
        day_seconds = 24 * 60 * 60
        if now - self.budget.last_reset_day > day_seconds:
            self.budget.current_daily = 0.0
            self.budget.last_reset_day = now
        
        month_seconds = 30 * day_seconds
        if now - self.budget.last_reset_month > month_seconds:
            self.budget.current_monthly = 0.0
            self.budget.last_reset_month = now
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: DeepSeekModel,
    ) -> float:
        pricing = DEEPSEEK_PRICING.get(model, DEEPSEEK_PRICING[DeepSeekModel.V4_FLASH])
        return (
            prompt_tokens * pricing["prompt"] +
            completion_tokens * pricing["completion"]
        ) / 1000.0
    
    def get_usage_report(self) -> Dict[str, Any]:
        return {
            "daily_used": self.budget.current_daily,
            "daily_limit": self.budget.daily_limit,
            "daily_remaining": self.budget.daily_limit - self.budget.current_daily,
            "monthly_used": self.budget.current_monthly,
            "monthly_limit": self.budget.monthly_limit,
            "monthly_remaining": self.budget.monthly_limit - self.budget.current_monthly,
            "total_requests": len(self._cost_history),
        }


class BatchProcessor:
    """
    批处理器 - 合并请求提高效率
    Batch Processor - Merge requests for efficiency
    """
    
    def __init__(
        self,
        batch_size: int = 5,
        batch_timeout: float = 0.1,
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending: List[QueuedRequest] = []
        self._lock = asyncio.Lock()
    
    async def add(self, request: QueuedRequest) -> Optional[List[QueuedRequest]]:
        async with self._lock:
            self._pending.append(request)
            
            if len(self._pending) >= self.batch_size:
                batch = self._pending[:self.batch_size]
                self._pending = self._pending[self.batch_size:]
                return batch
        
        return None
    
    async def flush(self) -> List[QueuedRequest]:
        async with self._lock:
            batch = self._pending
            self._pending = []
            return batch


class RetryPolicy:
    """
    重试策略 - 智能重试和退避
    Retry Policy - Smart retry and backoff
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, retry_count: int) -> float:
        delay = self.base_delay * (self.exponential_base ** retry_count)
        return min(delay, self.max_delay)
    
    def should_retry(
        self,
        retry_count: int,
        error: Optional[Exception] = None,
    ) -> bool:
        if retry_count >= self.max_retries:
            return False
        
        if error:
            if isinstance(error, httpx.HTTPStatusError):
                if error.response.status_code == 401:
                    return False
                if error.response.status_code == 400:
                    return False
        
        return True


class DeepSeekOptimizer:
    """
    DeepSeek V4 深度优化器
    API调用优化、成本控制、请求队列管理
    
    DeepSeek V4 Deep Optimizer
    API call optimization, cost control, request queue management
    """
    
    def __init__(
        self,
        config: Optional[DeepSeekConfig] = None,
        cache: Optional[CacheEngine] = None,
        budget: Optional[CostBudget] = None,
        max_concurrent: int = 10,
    ):
        self.config = config or DeepSeekConfig()
        self.cache = cache or CacheEngine()
        self.cost_controller = CostController(budget)
        self.queue = RequestQueue(max_concurrent=max_concurrent)
        self.batch_processor = BatchProcessor()
        self.retry_policy = RetryPolicy()
        self.stats = OptimizerStats()
        
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
    
    def _init_client(self) -> None:
        if self._client is not None:
            return
        
        api_key = self.config.api_key
        if not api_key:
            raise ValueError("DeepSeek API key not configured")
        
        timeout = httpx.Timeout(self.config.timeout, connect=10.0)
        self._client = httpx.AsyncClient(
            base_url=self.config.api_base,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    
    async def chat(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None,
        priority: Priority = Priority.NORMAL,
    ) -> Message:
        """
        优化的聊天调用
        Optimized chat call
        """
        self._init_client()
        cfg = config or self.config
        
        cached = await self.cache.get(messages, cfg.model.value)
        if cached:
            self.stats.cache_hits += 1
            return cached
        
        estimated_cost = self.cost_controller.estimate_cost(
            sum(len(m.content or "") // 4 for m in messages),
            cfg.max_tokens or 1000,
            cfg.model,
        )
        
        if not self.cost_controller.check_budget(estimated_cost):
            raise RuntimeError("Cost budget exceeded")
        
        request_id = hashlib.sha256(
            f"{time.time()}:{id(messages)}".encode()
        ).hexdigest()[:16]
        
        request = QueuedRequest(
            id=request_id,
            messages=messages,
            config=cfg,
            priority=priority,
        )
        
        return await self._execute_with_retry(request)
    
    async def _execute_with_retry(self, request: QueuedRequest) -> Message:
        """
        带重试的执行
        Execute with retry
        """
        last_error: Optional[Exception] = None
        
        for retry in range(self.retry_policy.max_retries + 1):
            try:
                result = await self._execute_request(request)
                
                self.stats.successful_requests += 1
                return result
            
            except Exception as e:
                last_error = e
                request.retries = retry
                
                if not self.retry_policy.should_retry(retry, e):
                    break
                
                delay = self.retry_policy.get_delay(retry)
                await asyncio.sleep(delay)
        
        self.stats.failed_requests += 1
        raise last_error or RuntimeError("Request failed")
    
    async def _execute_request(self, request: QueuedRequest) -> Message:
        """
        执行单个请求
        Execute single request
        """
        start_time = time.time()
        
        payload = {
            "model": request.config.model.value,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "temperature": request.config.temperature,
            "max_tokens": request.config.max_tokens,
            "top_p": request.config.top_p,
        }
        
        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        
        choice = data["choices"][0]
        message = Message(
            role=choice["message"]["role"],
            content=choice["message"]["content"],
        )
        
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        cost = self.cost_controller.estimate_cost(
            prompt_tokens,
            completion_tokens,
            request.config.model,
        )
        
        self.cost_controller.record_cost(
            cost,
            total_tokens,
            request.config.model.value,
            request.id,
        )
        
        self.cache.put(
            request.messages,
            message,
            total_tokens,
            request.config.model.value,
        )
        
        latency = (time.time() - start_time) * 1000
        self._update_stats(latency, total_tokens, cost)
        
        return message
    
    def _update_stats(
        self,
        latency_ms: float,
        tokens: int,
        cost: float,
    ) -> None:
        self.stats.total_requests += 1
        self.stats.total_tokens += tokens
        self.stats.total_cost += cost
        
        total = self.stats.total_requests
        self.stats.avg_latency_ms = (
            self.stats.avg_latency_ms * (total - 1) + latency_ms
        ) / total
    
    async def batch_chat(
        self,
        requests: List[Tuple[List[Message], Optional[DeepSeekConfig]]],
    ) -> List[Message]:
        """
        批量聊天调用
        Batch chat calls
        """
        results = []
        
        tasks = [
            self.chat(messages, config)
            for messages, config in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if isinstance(r, Message) else Message(role="assistant", content=str(r))
            for r in results
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        Get statistics
        """
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "cache_hits": self.stats.cache_hits,
            "cache_hit_rate": (
                self.stats.cache_hits / max(self.stats.total_requests, 1)
            ),
            "total_tokens": self.stats.total_tokens,
            "total_cost": self.stats.total_cost,
            "avg_latency_ms": self.stats.avg_latency_ms,
            "queue_size": self.queue.size(),
            "budget": self.cost_controller.get_usage_report(),
        }
    
    async def close(self) -> None:
        """
        关闭客户端
        Close client
        """
        if self._client:
            await self._client.aclose()
            self._client = None


class DegradationStrategy:
    """
    降级策略 - 当主服务不可用时的备选方案
    Degradation Strategy - Fallback when main service unavailable
    """
    
    def __init__(
        self,
        primary: DeepSeekOptimizer,
        fallback_model: str = "gpt-3.5-turbo",
        enable_fallback: bool = True,
    ):
        self.primary = primary
        self.fallback_model = fallback_model
        self.enable_fallback = enable_fallback
        self._failure_count = 0
        self._threshold = 5
        self._using_fallback = False
    
    async def chat(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None,
    ) -> Message:
        if self._using_fallback and self.enable_fallback:
            try:
                return await self._fallback_chat(messages, config)
            except Exception:
                pass
        
        try:
            result = await self.primary.chat(messages, config)
            self._failure_count = 0
            return result
        except Exception as e:
            self._failure_count += 1
            
            if self._failure_count >= self._threshold:
                self._using_fallback = True
            
            if self.enable_fallback:
                return await self._fallback_chat(messages, config)
            
            raise e
    
    async def _fallback_chat(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None,
    ) -> Message:
        import openai
        
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.fallback_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        
        return Message(
            role="assistant",
            content=response.choices[0].message.content,
        )
    
    def reset(self) -> None:
        self._failure_count = 0
        self._using_fallback = False
