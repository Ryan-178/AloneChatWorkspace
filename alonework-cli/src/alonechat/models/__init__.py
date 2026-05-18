"""
模型路由模块 / Model Router Module

负责 / Responsible for:
- DeepSeek V4 Flash API调用 / DeepSeek V4 Flash API calls
- 思考模式支持 / Thinking mode support
- 多轮对话 / Multi-turn conversation
- 上下文缓存 / Context caching
"""

import httpx
import os
from typing import Any, Generator
from pathlib import Path
from dataclasses import dataclass

from alonechat.config import ConfigManager


DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"
REASONING_EFFORT = "high"


@dataclass
class UsageInfo:
    """使用量信息 / Usage Info"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率 / Cache hit rate"""
        if self.prompt_tokens == 0:
            return 0.0
        return self.prompt_cache_hit_tokens / self.prompt_tokens


@dataclass
class ChatResponse:
    """聊天响应 / Chat Response"""
    content: str
    reasoning_content: str = ""
    usage: UsageInfo | None = None
    
    def __str__(self) -> str:
        return self.content
    
    def to_message(self) -> dict[str, str]:
        """转换为消息格式 / Convert to message format"""
        return {"role": "assistant", "content": self.content}


class DeepSeekProvider:
    """
    DeepSeek V4 Flash 提供商 / DeepSeek V4 Flash Provider
    
    固定使用 DeepSeek V4 Flash 模型，启用思考模式 / Fixed to use DeepSeek V4 Flash model with thinking mode
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = DEEPSEEK_API_BASE
        self.model = DEEPSEEK_MODEL
        self.reasoning_effort = REASONING_EFFORT
    
    def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> str | Generator[str, None, None] | ChatResponse:
        """聊天接口 / Chat interface"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "reasoning_effort": self.reasoning_effort,
        }
        
        timeout = httpx.Timeout(120.0, connect=30.0)
        
        with httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout) as client:
            if stream:
                return self._stream_chat(client, data)
            else:
                response = client.post("/chat/completions", json=data)
                response.raise_for_status()
                result = response.json()
                
                message = result["choices"][0]["message"]
                content = message.get("content", "")
                reasoning_content = message.get("reasoning_content", "")
                
                usage_data = result.get("usage", {})
                usage = UsageInfo(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                    prompt_cache_hit_tokens=usage_data.get("prompt_cache_hit_tokens", 0),
                    prompt_cache_miss_tokens=usage_data.get("prompt_cache_miss_tokens", 0),
                )
                
                return ChatResponse(
                    content=content,
                    reasoning_content=reasoning_content,
                    usage=usage,
                )
    
    def _stream_chat(
        self,
        client: httpx.Client,
        data: dict[str, Any]
    ) -> Generator[str, None, None]:
        """流式聊天 / Stream chat"""
        import json
        
        with client.stream("POST", "/chat/completions", json=data) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    if line == "data: [DONE]":
                        break
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk["choices"][0]["delta"]
                        
                        if reasoning := delta.get("reasoning_content"):
                            yield f"[思考] {reasoning}"
                        
                        if content := delta.get("content"):
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class ModelRouter:
    """
    模型路由器 / Model Router
    
    固定使用 DeepSeek V4 Flash，启用思考模式 / Fixed to use DeepSeek V4 Flash with thinking mode
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._provider: DeepSeekProvider | None = None
    
    def _get_api_key(self) -> str:
        """获取API密钥 / Get API key"""
        env_key = os.getenv("DEEPSEEK_API_KEY")
        if env_key:
            return env_key
        
        config_path = Path.home() / ".alonechat" / ".alonechat_key"
        if config_path.exists():
            config_manager = ConfigManager()
            encrypted_key = config_path.read_text(encoding="utf-8")
            return config_manager.decrypt_api_key(encrypted_key)
        
        raise ValueError("API密钥未配置 / API key not configured. Please run: alonechat init")
    
    def _get_provider(self) -> DeepSeekProvider:
        """获取提供商 / Get provider"""
        if self._provider is None:
            api_key = self._get_api_key()
            self._provider = DeepSeekProvider(api_key)
        return self._provider
    
    def chat(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        stream: bool = False,
        **kwargs
    ) -> str | Generator[str, None, None] | ChatResponse:
        """聊天接口 / Chat interface"""
        if messages is None:
            messages = []
        
        provider = self._get_provider()
        return provider.chat(messages, stream, **kwargs)
    
    def stream_chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """流式聊天 / Stream chat"""
        result = self.chat(messages=messages, stream=True, **kwargs)
        if isinstance(result, Generator):
            yield from result
    
    def chat_with_reasoning(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> ChatResponse:
        """带思考的聊天 / Chat with reasoning"""
        result = self.chat(messages=messages, stream=False, **kwargs)
        if isinstance(result, ChatResponse):
            return result
        return ChatResponse(content=str(result))
