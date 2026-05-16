"""
DeepSeek V4 Model Configuration
DeepSeek V4专属模型配置，支持Flash和Pro型号
从配置文件加载，替代硬编码
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from agent_framework.configs import get_models_config


class DeepSeekModel(str, Enum):
    """DeepSeek V4模型枚举"""
    V4_FLASH = "deepseek-chat"
    V4_PRO = "deepseek-pro"
    V4_REASONER = "deepseek-reasoner"


class DeepSeekConfig(BaseModel):
    """DeepSeek V4配置"""
    model: DeepSeekModel = Field(
        default=DeepSeekModel.V4_FLASH,
        description="DeepSeek V4模型型号"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="DeepSeek API密钥"
    )
    api_base: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API基础URL"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="温度参数"
    )
    max_tokens: Optional[int] = Field(
        default=8192,
        ge=1,
        description="最大输出token数"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p采样"
    )
    timeout: int = Field(
        default=120,
        ge=1,
        description="请求超时时间(秒)"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="最大重试次数"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="重试延迟(秒)"
    )
    streaming: bool = Field(
        default=True,
        description="是否启用流式输出"
    )


def _load_pricing_from_config() -> Dict[DeepSeekModel, Dict[str, float]]:
    """从配置文件加载定价信息"""
    config = get_models_config()
    pricing = {}
    
    for model_key in ["v4_flash", "v4_pro", "v4_reasoner"]:
        model_config = config.get_deepseek_model(model_key)
        if model_config:
            model_pricing = model_config.get("pricing", {})
            model_id = model_config.get("model_id", "")
            if model_id == "deepseek-chat":
                pricing[DeepSeekModel.V4_FLASH] = model_pricing
            elif model_id == "deepseek-pro":
                pricing[DeepSeekModel.V4_PRO] = model_pricing
            elif model_id == "deepseek-reasoner":
                pricing[DeepSeekModel.V4_REASONER] = model_pricing
    
    if not pricing:
        pricing = {
            DeepSeekModel.V4_FLASH: {"prompt": 0.0002, "completion": 0.0008},
            DeepSeekModel.V4_PRO: {"prompt": 0.001, "completion": 0.004},
            DeepSeekModel.V4_REASONER: {"prompt": 0.002, "completion": 0.008},
        }
    
    return pricing


def _load_context_windows_from_config() -> Dict[DeepSeekModel, int]:
    """从配置文件加载上下文窗口大小"""
    config = get_models_config()
    context_windows = {}
    
    for model_key in ["v4_flash", "v4_pro", "v4_reasoner"]:
        model_config = config.get_deepseek_model(model_key)
        if model_config:
            ctx_window = model_config.get("context_window", 1000000)
            model_id = model_config.get("model_id", "")
            if model_id == "deepseek-chat":
                context_windows[DeepSeekModel.V4_FLASH] = ctx_window
            elif model_id == "deepseek-pro":
                context_windows[DeepSeekModel.V4_PRO] = ctx_window
            elif model_id == "deepseek-reasoner":
                context_windows[DeepSeekModel.V4_REASONER] = ctx_window
    
    if not context_windows:
        context_windows = {
            DeepSeekModel.V4_FLASH: 1000000,
            DeepSeekModel.V4_PRO: 1000000,
            DeepSeekModel.V4_REASONER: 1000000,
        }
    
    return context_windows


DEEPSEEK_PRICING: Dict[DeepSeekModel, Dict[str, float]] = _load_pricing_from_config()

DEEPSEEK_CONTEXT_WINDOWS: Dict[DeepSeekModel, int] = _load_context_windows_from_config()


def reload_model_config():
    """重新加载模型配置"""
    global DEEPSEEK_PRICING, DEEPSEEK_CONTEXT_WINDOWS
    
    get_models_config().reload()
    DEEPSEEK_PRICING = _load_pricing_from_config()
    DEEPSEEK_CONTEXT_WINDOWS = _load_context_windows_from_config()
