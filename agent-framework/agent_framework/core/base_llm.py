from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    role: str = Field(..., description="Message role: system, user, assistant, or tool")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Tool name for tool messages")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Tool calls from assistant")
    tool_call_id: Optional[str] = Field(default=None, description="Tool call ID for tool responses")


class Chunk(BaseModel):
    content: str = Field(default="", description="Chunk content")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason if this is the last chunk")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage info")


class LLMConfig(BaseModel):
    model: str = Field(default="gpt-4o", description="Model name")
    api_key: Optional[str] = Field(default=None, description="API key")
    api_base: Optional[str] = Field(default=None, description="API base URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    timeout: Optional[int] = Field(default=60, ge=1)
    extra_headers: Optional[Dict[str, str]] = Field(default=None)
    extra_body: Optional[Dict[str, Any]] = Field(default=None)


class UsageInfo(BaseModel):
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost: float = Field(default=0.0)

    def model_post_init(self, __context):
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class BaseLLM(ABC):
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._usage_history: List[UsageInfo] = []

    @abstractmethod
    def chat(self, messages: List[Message], config: Optional[LLMConfig] = None) -> Message:
        pass

    @abstractmethod
    async def chat_stream(
        self, messages: List[Message], config: Optional[LLMConfig] = None
    ) -> AsyncGenerator[Chunk, None]:
        pass

    def record_usage(self, usage: UsageInfo) -> None:
        self._usage_history.append(usage)

    def get_total_usage(self) -> UsageInfo:
        if not self._usage_history:
            return UsageInfo()
        return UsageInfo(
            prompt_tokens=sum(u.prompt_tokens for u in self._usage_history),
            completion_tokens=sum(u.completion_tokens for u in self._usage_history),
            total_tokens=sum(u.total_tokens for u in self._usage_history),
            estimated_cost=sum(u.estimated_cost for u in self._usage_history),
        )

    def clear_usage_history(self) -> None:
        self._usage_history.clear()
