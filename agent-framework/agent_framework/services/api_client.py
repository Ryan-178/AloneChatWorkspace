"""
API 客户端抽象 / API Client Abstraction

参考 claude-code-claude 的 API 客户端模式
Reference: claude-code-claude's API client pattern

提供统一的 LLM API 客户端接口
Provides unified LLM API client interface
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """
    API 提供商 / API Provider
    
    支持的 LLM API 提供商
    Supported LLM API providers
    """
    OPENAI = "openai"            # OpenAI API
    DEEPSEEK = "deepseek"        # DeepSeek API
    ANTHROPIC = "anthropic"      # Anthropic API
    LOCAL = "local"              # 本地模型 / Local model
    CUSTOM = "custom"            # 自定义 API / Custom API


@dataclass
class APIConfig:
    """
    API 配置 / API Configuration
    
    API 连接配置
    API connection configuration
    """
    provider: APIProvider = APIProvider.OPENAI
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "default"
    timeout: int = 60
    max_retries: int = 3
    extra_headers: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """
    聊天消息 / Chat Message
    
    API 交互中的消息
    Message in API interaction
    """
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatResponse:
    """
    聊天响应 / Chat Response
    
    API 返回的响应
    Response returned by API
    """
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """
    流式响应块 / Stream Response Chunk
    
    流式 API 返回的单个块
    Single chunk from streaming API
    """
    content: str = ""
    role: str = "assistant"
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    delta: bool = True


class APIClient(ABC):
    """
    API 客户端基类 / API Client Base Class
    
    所有 API 客户端必须继承此基类
    All API clients must inherit from this base class
    
    使用示例 / Usage Example:
        client = OpenAIClient(api_config)
        response = await client.chat([{"role": "user", "content": "Hello!"}])
        
        async for chunk in client.chat_stream([{"role": "user", "content": "Hello!"}]):
            print(chunk.content, end="")
    """
    
    def __init__(self, config: APIConfig):
        self._config = config
    
    @property
    def config(self) -> APIConfig:
        """获取配置 / Get config"""
        return self._config
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """
        同步聊天 / Synchronous chat
        
        Args:
            messages: 消息列表 / Message list
            model: 模型名称（覆盖默认）/ Model name (overrides default)
            
        Returns:
            聊天响应 / Chat response
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式聊天 / Streaming chat
        
        Args:
            messages: 消息列表 / Message list
            model: 模型名称（覆盖默认）/ Model name (overrides default)
            
        Yields:
            流式响应块 / Stream chunks
        """
        pass
    
    async def health_check(self) -> bool:
        """
        健康检查 / Health check
        
        检查 API 连接是否正常
        Check if API connection is healthy
        
        Returns:
            是否健康 / Whether healthy
        """
        try:
            response = await self.chat(
                [ChatMessage(role="user", content="ping")],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


class OpenAIClient(APIClient):
    """
    OpenAI 兼容客户端 / OpenAI Compatible Client
    
    支持 OpenAI 和兼容 API（如 DeepSeek）
    Supports OpenAI and compatible APIs (like DeepSeek)
    """
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """获取或创建客户端 / Get or create client"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self._config.api_key,
                    base_url=self._config.base_url,
                    timeout=self._config.timeout,
                    max_retries=self._config.max_retries,
                    default_headers=self._config.extra_headers
                )
            except ImportError:
                raise ImportError("openai package is required. Install with: pip install openai")
        return self._client
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        client = await self._get_client()
        
        # 转换消息格式 / Convert message format
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        # 合并参数 / Merge parameters
        params = {
            "model": model or self._config.model,
            "messages": api_messages,
            **self._config.extra_params,
            **kwargs
        }
        
        response = await client.chat.completions.create(**params)
        
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            role=choice.message.role,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        )
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        client = await self._get_client()
        
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        params = {
            "model": model or self._config.model,
            "messages": api_messages,
            "stream": True,
            **self._config.extra_params,
            **kwargs
        }
        
        async for chunk in await client.chat.completions.create(**params):
            if chunk.choices:
                choice = chunk.choices[0]
                yield StreamChunk(
                    content=choice.delta.content or "",
                    role=choice.delta.role or "assistant",
                    finish_reason=choice.finish_reason,
                    delta=True
                )


class LocalModelClient(APIClient):
    """
    本地模型客户端 / Local Model Client
    
    支持本地运行的模型（如 Ollama）
    Supports locally running models (like Ollama)
    """
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        self._session = None
    
    async def _get_session(self):
        """获取 HTTP 会话 / Get HTTP session"""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self._config.timeout)
                )
            except ImportError:
                raise ImportError("aiohttp package is required. Install with: pip install aiohttp")
        return self._session
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        session = await self._get_session()
        
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        payload = {
            "model": model or self._config.model,
            "messages": api_messages,
            "stream": False,
            **self._config.extra_params,
            **kwargs
        }
        
        base_url = self._config.base_url or "http://localhost:11434"
        
        async with session.post(f"{base_url}/v1/chat/completions", json=payload) as resp:
            data = await resp.json()
            
            choice = data["choices"][0]
            return ChatResponse(
                content=choice["message"]["content"],
                role=choice["message"]["role"],
                finish_reason=choice.get("finish_reason"),
                usage=data.get("usage")
            )
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        session = await self._get_session()
        
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        payload = {
            "model": model or self._config.model,
            "messages": api_messages,
            "stream": True,
            **self._config.extra_params,
            **kwargs
        }
        
        base_url = self._config.base_url or "http://localhost:11434"
        
        async with session.post(f"{base_url}/v1/chat/completions", json=payload) as resp:
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    
                    import json
                    chunk_data = json.loads(data)
                    if chunk_data.get('choices'):
                        choice = chunk_data['choices'][0]
                        yield StreamChunk(
                            content=choice.get('delta', {}).get('content', ''),
                            role="assistant",
                            finish_reason=choice.get('finish_reason'),
                            delta=True
                        )
    
    async def close(self):
        """关闭会话 / Close session"""
        if self._session:
            await self._session.close()
            self._session = None


def create_api_client(config: APIConfig) -> APIClient:
    """
    创建 API 客户端 / Create API client
    
    根据配置创建对应的 API 客户端
    Create appropriate API client based on config
    
    Args:
        config: API 配置 / API config
        
    Returns:
        API 客户端实例 / API client instance
    """
    if config.provider == APIProvider.LOCAL:
        return LocalModelClient(config)
    else:
        return OpenAIClient(config)
