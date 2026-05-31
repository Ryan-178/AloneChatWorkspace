"""
模型注册表 / Model Registry

管理可用模型和模型能力查询
Manages available models and model capability queries
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """
    模型提供商 / Model Provider
    """
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelCapability(str, Enum):
    """
    模型能力 / Model Capability
    """
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    SYSTEM_PROMPT = "system_prompt"


@dataclass
class ModelInfo:
    """
    模型信息 / Model Information
    """
    id: str
    name: str
    provider: ModelProvider
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_window: int = 4096
    max_output_tokens: int = 2048
    input_price: float = 0.0
    output_price: float = 0.0
    cache_price: Optional[float] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    available: bool = True
    deprecated: bool = False

    def has_capability(self, capability: ModelCapability) -> bool:
        """检查是否具有指定能力 / Check if has specified capability"""
        return capability in self.capabilities

    def get_price_per_million(self, input_tokens: int, output_tokens: int) -> float:
        """计算每百万token的价格 / Calculate price per million tokens"""
        input_cost = (input_tokens / 1_000_000) * self.input_price
        output_cost = (output_tokens / 1_000_000) * self.output_price
        return input_cost + output_cost

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "capabilities": [c.value for c in self.capabilities],
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "input_price": self.input_price,
            "output_price": self.output_price,
            "cache_price": self.cache_price,
            "description": self.description,
            "tags": self.tags,
            "available": self.available,
            "deprecated": self.deprecated,
        }


class ModelRegistry:
    """
    模型注册表 / Model Registry

    管理所有可用模型
    Manages all available models
    """

    def __init__(self, config_path: Optional[str] = None):
        self._models: Dict[str, ModelInfo] = {}
        self._default_model: Optional[str] = None
        self._config_path = config_path

        if config_path:
            self._load_config(config_path)
        else:
            self._load_default_models()

    def _load_default_models(self) -> None:
        """
        加载默认模型配置 / Load default model configuration
        """
        default_models = [
            ModelInfo(
                id="deepseek-chat",
                name="DeepSeek Chat",
                provider=ModelProvider.DEEPSEEK,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=64000,
                max_output_tokens=8000,
                input_price=0.14,
                output_price=0.28,
                cache_price=0.014,
                description="DeepSeek通用对话模型",
                tags=["chat", "general"],
            ),
            ModelInfo(
                id="deepseek-reasoner",
                name="DeepSeek Reasoner",
                provider=ModelProvider.DEEPSEEK,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.STREAMING,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=64000,
                max_output_tokens=8000,
                input_price=0.55,
                output_price=2.19,
                description="DeepSeek推理增强模型",
                tags=["chat", "reasoning"],
            ),
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider=ModelProvider.OPENAI,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=128000,
                max_output_tokens=4096,
                input_price=5.0,
                output_price=15.0,
                description="OpenAI GPT-4o多模态模型",
                tags=["chat", "vision", "multimodal"],
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider=ModelProvider.OPENAI,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.JSON_MODE,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=128000,
                max_output_tokens=4096,
                input_price=0.15,
                output_price=0.6,
                description="OpenAI GPT-4o Mini轻量模型",
                tags=["chat", "fast"],
            ),
            ModelInfo(
                id="claude-3-5-sonnet",
                name="Claude 3.5 Sonnet",
                provider=ModelProvider.ANTHROPIC,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=200000,
                max_output_tokens=8192,
                input_price=3.0,
                output_price=15.0,
                cache_price=0.3,
                description="Anthropic Claude 3.5 Sonnet",
                tags=["chat", "vision", "reasoning"],
            ),
            ModelInfo(
                id="claude-3-haiku",
                name="Claude 3 Haiku",
                provider=ModelProvider.ANTHROPIC,
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.SYSTEM_PROMPT,
                ],
                context_window=200000,
                max_output_tokens=4096,
                input_price=0.25,
                output_price=1.25,
                cache_price=0.025,
                description="Anthropic Claude 3 Haiku快速模型",
                tags=["chat", "fast"],
            ),
        ]

        for model in default_models:
            self._models[model.id] = model

        self._default_model = "deepseek-chat"

    def _load_config(self, config_path: str) -> None:
        """
        从配置文件加载模型 / Load models from config file
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    models_config = config.get("models", {})
                    for model_id, model_data in models_config.items():
                        provider_str = model_data.get("provider", "custom")
                        try:
                            provider = ModelProvider(provider_str)
                        except ValueError:
                            provider = ModelProvider.CUSTOM

                        capabilities = []
                        for cap_str in model_data.get("capabilities", []):
                            try:
                                capabilities.append(ModelCapability(cap_str))
                            except ValueError:
                                pass

                        model = ModelInfo(
                            id=model_id,
                            name=model_data.get("name", model_id),
                            provider=provider,
                            capabilities=capabilities,
                            context_window=model_data.get("context_window", 4096),
                            max_output_tokens=model_data.get("max_output_tokens", 2048),
                            input_price=model_data.get("input_price", 0.0),
                            output_price=model_data.get("output_price", 0.0),
                            cache_price=model_data.get("cache_price"),
                            description=model_data.get("description", ""),
                            tags=model_data.get("tags", []),
                            available=model_data.get("available", True),
                            deprecated=model_data.get("deprecated", False),
                        )
                        self._models[model_id] = model

                    self._default_model = config.get("default_model", "deepseek-chat")
        except Exception as e:
            logger.warning(f"Failed to load model config: {e}")
            self._load_default_models()

    def register(self, model: ModelInfo) -> None:
        """
        注册模型 / Register model
        """
        self._models[model.id] = model

    def unregister(self, model_id: str) -> bool:
        """
        注销模型 / Unregister model
        """
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """
        获取模型信息 / Get model information
        """
        return self._models.get(model_id)

    def get_default(self) -> Optional[ModelInfo]:
        """
        获取默认模型 / Get default model
        """
        if self._default_model:
            return self._models.get(self._default_model)
        return None

    def set_default(self, model_id: str) -> bool:
        """
        设置默认模型 / Set default model
        """
        if model_id in self._models:
            self._default_model = model_id
            return True
        return False

    def list_all(self) -> List[ModelInfo]:
        """
        列出所有模型 / List all models
        """
        return list(self._models.values())

    def list_available(self) -> List[ModelInfo]:
        """
        列出可用模型 / List available models
        """
        return [m for m in self._models.values() if m.available and not m.deprecated]

    def list_by_provider(self, provider: ModelProvider) -> List[ModelInfo]:
        """
        按提供商列出模型 / List models by provider
        """
        return [m for m in self._models.values() if m.provider == provider]

    def list_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """
        按能力列出模型 / List models by capability
        """
        return [m for m in self._models.values() if m.has_capability(capability)]

    def search(self, query: str) -> List[ModelInfo]:
        """
        搜索模型 / Search models
        """
        query_lower = query.lower()
        results = []
        for model in self._models.values():
            if (
                query_lower in model.id.lower()
                or query_lower in model.name.lower()
                or query_lower in model.description.lower()
                or any(query_lower in tag.lower() for tag in model.tags)
            ):
                results.append(model)
        return results


_model_registry: Optional[ModelRegistry] = None


def get_model_registry(config_path: Optional[str] = None) -> ModelRegistry:
    """
    获取全局模型注册表 / Get global model registry
    """
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry(config_path)
    return _model_registry
