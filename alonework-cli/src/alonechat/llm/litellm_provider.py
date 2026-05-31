import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from alonechat.core.base_llm import BaseLLM, Message, Chunk, LLMConfig, UsageInfo


MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
    "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
    "gemini/gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
    "gemini/gemini-1.5-flash": {"prompt": 0.00035, "completion": 0.00105},
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("gpt-4o", {"prompt": 0.005, "completion": 0.015}))
    return (prompt_tokens * pricing["prompt"] + completion_tokens * pricing["completion"]) / 1000.0


def _messages_to_litellm(messages: List[Message]) -> List[Dict[str, Any]]:
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


class LiteLLMProvider(BaseLLM):
    def __init__(self, config: Optional[LLMConfig] = None):
        super().__init__(config)
        try:
            import litellm
            litellm.drop_params = True
        except ImportError:
            raise ImportError("litellm is required. Install with: pip install litellm")

    def chat(self, messages: List[Message], config: Optional[LLMConfig] = None) -> Message:
        import litellm

        cfg = config or self.config
        start = time.time()

        response = litellm.completion(
            model=cfg.model,
            messages=_messages_to_litellm(messages),
            api_key=cfg.api_key,
            api_base=cfg.api_base,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            top_p=cfg.top_p,
            timeout=cfg.timeout,
            extra_headers=cfg.extra_headers,
            extra_body=cfg.extra_body,
        )

        choice = response.choices[0]
        message = choice.message
        usage = response.usage

        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", 0) or 0
        cost = _estimate_cost(cfg.model, prompt_tokens, completion_tokens)

        usage_info = UsageInfo(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
        )
        self.record_usage(usage_info)

        return Message(
            role=getattr(message, "role", "assistant"),
            content=getattr(message, "content", "") or "",
            tool_calls=getattr(message, "tool_calls", None),
        )

    async def chat_stream(
        self, messages: List[Message], config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[Chunk, None]:
        import litellm

        cfg = config or self.config
        response = await litellm.acompletion(
            model=cfg.model,
            messages=_messages_to_litellm(messages),
            api_key=cfg.api_key,
            api_base=cfg.api_base,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            top_p=cfg.top_p,
            timeout=cfg.timeout,
            extra_headers=cfg.extra_headers,
            extra_body=cfg.extra_body,
            stream=True,
        )

        total_prompt_tokens = 0
        total_completion_tokens = 0
        finish_reason = None

        async for part in response:
            delta = part.choices[0].delta
            finish_reason = part.choices[0].finish_reason

            content = getattr(delta, "content", "") or ""
            usage = getattr(part, "usage", None)
            if usage:
                total_prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                total_completion_tokens = getattr(usage, "completion_tokens", 0) or 0

            yield Chunk(
                content=content,
                finish_reason=finish_reason,
                usage={
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                } if usage else None,
            )

        cost = _estimate_cost(cfg.model, total_prompt_tokens, total_completion_tokens)
        self.record_usage(
            UsageInfo(
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=total_prompt_tokens + total_completion_tokens,
                estimated_cost=cost,
            )
        )
