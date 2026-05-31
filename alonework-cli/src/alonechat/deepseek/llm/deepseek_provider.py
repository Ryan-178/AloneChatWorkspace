"""
DeepSeek V4 Provider
专属Provider，直接调用DeepSeek API，无需LiteLLM
"""
import time
import asyncio
import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field

from alonechat.core.base_llm import BaseLLM, Message, Chunk
from .model_config import (
    DeepSeekConfig,
    DeepSeekModel,
    DEEPSEEK_PRICING,
    DEEPSEEK_CONTEXT_WINDOWS,
)
from .temperature_controller import (
    TemperatureController,
    TemperatureManager,
    TaskType,
    AdjustmentStrategy,
    FeedbackSignal,
)


@dataclass
class DeepSeekUsage:
    """DeepSeek使用统计 - 支持KV Cache"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    requests_count: int = 0
    
    # KV Cache 字段
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    total_cache_hits: int = 0
    
    start_time: float = field(default_factory=time.time)

    def add_usage(
        self, 
        prompt: int, 
        completion: int, 
        model: DeepSeekModel,
        cache_hit_tokens: int = 0,
        cache_miss_tokens: int = 0,
    ):
        """添加使用记录 - 包含KV Cache"""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        self.prompt_cache_hit_tokens += cache_hit_tokens
        self.prompt_cache_miss_tokens += cache_miss_tokens
        self.requests_count += 1
        
        if cache_hit_tokens > 0:
            self.total_cache_hits += 1
        
        # DeepSeek 定价：命中缓存 0.1元/百万tokens，未命中 1元/百万tokens
        pricing = DEEPSEEK_PRICING.get(model, DEEPSEEK_PRICING[DeepSeekModel.V4_FLASH])
        cost_hit = (cache_hit_tokens * 0.0000001)
        cost_miss = (cache_miss_tokens * 0.000001)
        cost_completion = (completion * pricing["completion"]) / 1000.0
        self.estimated_cost += cost_hit + cost_miss + cost_completion

    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        elapsed = time.time() - self.start_time
        total_prompt = max(self.prompt_cache_hit_tokens + self.prompt_cache_miss_tokens, self.prompt_tokens)
        cache_hit_rate = (self.prompt_cache_hit_tokens / max(total_prompt, 1)) if total_prompt > 0 else 0
        request_hit_rate = (self.total_cache_hits / max(self.requests_count, 1)) if self.requests_count > 0 else 0
        
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cache_hit_tokens": self.prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": self.prompt_cache_miss_tokens,
            "estimated_cost": self.estimated_cost,
            "requests_count": self.requests_count,
            "total_cache_hits": self.total_cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "request_hit_rate": request_hit_rate,
            "cost_saved": self._calculate_savings(),
            "avg_tokens_per_request": self.total_tokens / max(self.requests_count, 1),
            "duration_seconds": elapsed,
        }
    
    def _calculate_savings(self) -> float:
        """计算使用缓存节省的费用"""
        if self.prompt_cache_hit_tokens == 0:
            return 0.0
        # 节省的是原本要按 1元/百万tokens 计费的部分，现在只需要 0.1元/百万tokens
        saved_per_token = 0.000001 - 0.0000001
        return self.prompt_cache_hit_tokens * saved_per_token


class DeepSeekProvider(BaseLLM):
    """
    DeepSeek V4专属Provider
    All in DeepSeek V4，极致优化，直接API调用
    支持动态温度调整
    """

    def __init__(
        self, 
        config: Optional[DeepSeekConfig] = None,
        temperature_controller: Optional[TemperatureController] = None,
        enable_dynamic_temperature: bool = True,
    ):
        self.config = config or DeepSeekConfig()
        self.usage = DeepSeekUsage()
        self._client: Optional[httpx.AsyncClient] = None
        self._init_client()
        
        self.enable_dynamic_temperature = enable_dynamic_temperature
        if temperature_controller:
            self._temperature_controller = temperature_controller
        elif enable_dynamic_temperature:
            self._temperature_controller = TemperatureController()
        else:
            self._temperature_controller = None
        
        self._current_task_type: Optional[TaskType] = None

    def _init_client(self):
        """初始化HTTP客户端"""
        api_key = self.config.api_key
        if not api_key:
            raise ValueError(
                "DeepSeek API key is not configured. "
                "Please set the DEEPSEEK_API_KEY environment variable or provide it in the config."
            )

        timeout = httpx.Timeout(self.config.timeout, connect=10.0)
        self._client = httpx.AsyncClient(
            base_url=self.config.api_base,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "DeepSeek-Optimization/2.0.0",
            },
        )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """估算成本"""
        pricing = DEEPSEEK_PRICING.get(
            self.config.model,
            DEEPSEEK_PRICING[DeepSeekModel.V4_FLASH]
        )
        return (
            prompt_tokens * pricing["prompt"]
            + completion_tokens * pricing["completion"]
        ) / 1000.0

    def _messages_to_deepseek(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """转换消息格式"""
        result = []
        for m in messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.name:
                msg["name"] = m.name
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            result.append(msg)
        return result

    def chat(self, messages: List[Message], config: Optional[DeepSeekConfig] = None) -> Message:
        """
        同步聊天调用
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.chat_async(messages, config))

    async def chat_async(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None
    ) -> Message:
        """
        异步聊天调用 - 核心方法，支持KV Cache和动态温度调整
        """
        cfg = config or self.config
        
        effective_temperature = self._get_effective_temperature(messages, config)

        request_payload = {
            "model": cfg.model.value,
            "messages": self._messages_to_deepseek(messages),
            "temperature": effective_temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
        }

        start_time = time.time()
        response = await self._client.post(
            "/chat/completions",
            json=request_payload,
        )
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        message_data = choice["message"]
        usage = data.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # DeepSeek KV Cache 字段
        prompt_cache_hit_tokens = usage.get("prompt_cache_hit_tokens", 0)
        prompt_cache_miss_tokens = usage.get("prompt_cache_miss_tokens", 0)

        # 记录使用（包含KV Cache）
        self.usage.add_usage(
            prompt_tokens, 
            completion_tokens, 
            cfg.model,
            prompt_cache_hit_tokens,
            prompt_cache_miss_tokens,
        )

        return Message(
            role=message_data.get("role", "assistant"),
            content=message_data.get("content", "") or "",
            tool_calls=message_data.get("tool_calls"),
        )

    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None
    ) -> AsyncGenerator[Chunk, None]:
        """
        流式输出 - DeepSeek V4优化，支持KV Cache和动态温度调整
        """
        cfg = config or self.config
        
        effective_temperature = self._get_effective_temperature(messages, config)

        request_payload = {
            "model": cfg.model.value,
            "messages": self._messages_to_deepseek(messages),
            "temperature": effective_temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
            "stream": True,
        }

        total_prompt = 0
        total_completion = 0
        total_cache_hit = 0
        total_cache_miss = 0

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json=request_payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        import json
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            finish_reason = data["choices"][0].get("finish_reason")

                            content = delta.get("content", "") or ""

                            if "usage" in data:
                                u = data["usage"]
                                total_prompt = u.get("prompt_tokens", 0)
                                total_completion = u.get("completion_tokens", 0)
                                total_cache_hit = u.get("prompt_cache_hit_tokens", 0)
                                total_cache_miss = u.get("prompt_cache_miss_tokens", 0)

                            yield Chunk(
                                content=content,
                                finish_reason=finish_reason,
                                usage={
                                    "prompt_tokens": total_prompt,
                                    "completion_tokens": total_completion,
                                    "prompt_cache_hit_tokens": total_cache_hit,
                                    "prompt_cache_miss_tokens": total_cache_miss,
                                } if total_prompt else None,
                            )
                    except Exception:
                        continue

        # 记录使用（包含KV Cache）
        if total_prompt or total_completion:
            self.usage.add_usage(
                total_prompt, 
                total_completion, 
                cfg.model,
                total_cache_hit,
                total_cache_miss,
            )

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.usage.get_stats()

    def reset_usage(self):
        """重置使用统计"""
        self.usage = DeepSeekUsage()
    
    def set_task_type(self, task_type: TaskType) -> float:
        """
        设置当前任务类型，自动调整温度
        
        Args:
            task_type: 任务类型
            
        Returns:
            调整后的温度值
        """
        self._current_task_type = task_type
        if self._temperature_controller:
            return self._temperature_controller.set_task_type(task_type)
        return self.config.temperature
    
    def get_dynamic_temperature(
        self,
        context: Optional[str] = None,
        feedback: Optional[FeedbackSignal] = None,
    ) -> float:
        """
        获取动态调整后的温度
        
        Args:
            context: 上下文内容
            feedback: 反馈信号
            
        Returns:
            动态调整后的温度值
        """
        if not self._temperature_controller:
            return self.config.temperature
        
        return self._temperature_controller.get_temperature(
            task_type=self._current_task_type,
            context=context,
            feedback=feedback,
        )
    
    def update_feedback(self, feedback: FeedbackSignal) -> None:
        """
        更新反馈信号，用于自适应温度调整
        
        Args:
            feedback: 反馈信号
        """
        if self._temperature_controller:
            self._temperature_controller.update_feedback(feedback)
    
    def adjust_temperature_for_context(
        self,
        context: str,
        token_count: Optional[int] = None,
    ) -> float:
        """
        根据上下文复杂度调整温度
        
        Args:
            context: 上下文内容
            token_count: Token数量
            
        Returns:
            调整后的温度值
        """
        if self._temperature_controller:
            return self._temperature_controller.adjust_for_context_complexity(
                context, token_count
            )
        return self.config.temperature
    
    def get_temperature_stats(self) -> Dict[str, Any]:
        """
        获取温度控制器统计信息
        """
        if self._temperature_controller:
            return self._temperature_controller.get_statistics()
        return {"dynamic_temperature_enabled": False}
    
    def _get_effective_temperature(
        self,
        messages: List[Message],
        config: Optional[DeepSeekConfig] = None,
    ) -> float:
        """
        获取有效温度值
        
        如果启用了动态温度调整，会根据消息内容自动调整
        """
        if not self._temperature_controller:
            cfg = config or self.config
            return cfg.temperature
        
        context = "\n".join(m.content for m in messages if m.content)
        
        return self._temperature_controller.get_temperature(
            task_type=self._current_task_type,
            context=context,
        )
