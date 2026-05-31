"""
配置管理模块 - Configuration Management
支持多环境配置、配置热加载、配置验证
"""
import os
import json
import yaml
import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from threading import Lock
from watchfiles import awatch


class LLMSettings(BaseModel):
    """LLM配置"""
    provider: str = Field(default="openai", description="LLM提供商")
    model: str = Field(default="gpt-4o", description="模型名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    api_base: Optional[str] = Field(default=None, description="API基础URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, description="最大token数")
    timeout: float = Field(default=30.0, description="请求超时秒数")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟秒数")


class MemorySettings(BaseModel):
    """内存配置"""
    window_size: int = Field(default=10, description="对话窗口大小")
    vector_db_type: str = Field(default="chromadb", description="向量数据库类型")
    vector_db_path: str = Field(default="./data/chroma", description="向量数据库路径")
    embedding_model: str = Field(default="text-embedding-ada-002", description="嵌入模型")
    enable_persistence: bool = Field(default=True, description="是否启用持久化")


class GatewaySettings(BaseModel):
    """网关配置"""
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8787, ge=1, le=65535, description="监听端口")
    session_timeout: int = Field(default=3600, description="会话超时秒数")
    max_sessions: int = Field(default=1000, description="最大会话数")
    enable_cors: bool = Field(default=True, description="是否启用CORS")
    cors_origins: List[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
        description="CORS源"
    )
    enable_health_check: bool = Field(default=True, description="是否启用健康检查")
    health_check_path: str = Field(default="/health", description="健康检查路径")


class LoggingSettings(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="colored", description="日志格式: colored, json")
    file_path: Optional[str] = Field(default=None, description="日志文件路径")
    max_file_size: int = Field(default=10485760, description="最大文件大小(字节)")
    backup_count: int = Field(default=5, description="备份文件数")


class MetricsSettings(BaseModel):
    """指标配置"""
    enabled: bool = Field(default=True, description="是否启用指标收集")
    export_interval: int = Field(default=60, description="导出间隔秒数")
    export_path: Optional[str] = Field(default=None, description="导出文件路径")
    enable_prometheus: bool = Field(default=False, description="是否启用Prometheus导出")
    prometheus_port: int = Field(default=9090, description="Prometheus端口")


class TracingSettings(BaseModel):
    """追踪配置"""
    enabled: bool = Field(default=True, description="是否启用追踪")
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="采样率")
    export_path: Optional[str] = Field(default=None, description="导出文件路径")
    enable_zipkin: bool = Field(default=False, description="是否启用Zipkin导出")
    zipkin_endpoint: Optional[str] = Field(default=None, description="Zipkin端点")


class MTCSettings(BaseModel):
    """MTC模式配置 - More Than Coding模式，面向非开发用户"""
    sandbox_root: str = Field(default="./workspace/mtc", description="MTC模式沙箱根目录")
    allowed_file_extensions: List[str] = Field(
        default_factory=lambda: [".txt", ".md", ".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".json", ".html"],
        description="允许处理的文件扩展名"
    )
    max_file_size: int = Field(default=10485760, description="最大文件大小(字节)，默认10MB")
    intent_clarification_enabled: bool = Field(default=True, description="是否启用意图澄清")
    max_clarification_questions: int = Field(default=3, ge=1, le=5, description="最大追问问题数")
    allowed_commands: List[str] = Field(default_factory=list, description="允许执行的命令白名单")
    output_formats: List[str] = Field(
        default_factory=lambda: ["markdown", "pdf", "pptx", "xlsx", "docx"],
        description="支持的输出格式"
    )


class CODESettings(BaseModel):
    """CODE模式配置 - 面向开发者用户"""
    sandbox_root: str = Field(default="./workspace/code", description="CODE模式沙箱根目录")
    allowed_commands: List[str] = Field(
        default_factory=lambda: ["git", "npm", "yarn", "pip", "pip3", "node", "npx", "python", "python3", "make", "docker"],
        description="允许执行的命令白名单"
    )
    enable_linting: bool = Field(default=True, description="是否启用代码检查")
    enable_testing: bool = Field(default=True, description="是否启用测试生成")
    enable_browser_automation: bool = Field(default=False, description="是否启用浏览器自动化")
    max_file_size: int = Field(default=52428800, description="最大文件大小(字节)，默认50MB")
    enable_search_agent: bool = Field(default=True, description="是否启用Search子Agent")
    enable_plan_mode: bool = Field(default=True, description="是否启用Plan Mode")
    max_context_tokens: int = Field(default=128000, description="最大上下文token数")


class ModeSettings(BaseModel):
    """模式管理配置"""
    default_mode: str = Field(default="MTC", description="默认模式")
    allow_mode_switch: bool = Field(default=True, description="是否允许模式切换")
    mtc_config: MTCSettings = Field(default_factory=MTCSettings, description="MTC模式配置")
    code_config: CODESettings = Field(default_factory=CODESettings, description="CODE模式配置")


class AgentConfig(BaseSettings):
    """主配置类"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow"
    )
    
    # 各子配置
    llm: LLMSettings = Field(default_factory=LLMSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    tracing: TracingSettings = Field(default_factory=TracingSettings)
    mode: ModeSettings = Field(default_factory=ModeSettings, description="模式管理配置")
    
    # 全局配置
    debug: bool = Field(default=False, description="调试模式")
    data_dir: str = Field(default="./data", description="数据目录")
    
    @field_validator('data_dir')
    @classmethod
    def ensure_data_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def from_yaml(cls, path: str) -> "AgentConfig":
        """从YAML文件加载配置"""
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
    
    @classmethod
    def from_json(cls, path: str) -> "AgentConfig":
        """从JSON文件加载配置"""
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """从字典加载配置"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_yaml(self, path: str):
        """保存为YAML文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
    
    def to_json(self, path: str):
        """保存为JSON文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class ConfigManager:
    """配置管理器，支持热加载"""
    
    def __init__(self, config_path: Optional[str] = None):
        self._lock = Lock()
        self._config: Optional[AgentConfig] = None
        self._config_path: Optional[str] = config_path
        self._watch_task: Optional[asyncio.Task] = None
        self._change_callbacks: List[Callable[[AgentConfig], None]] = []
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        with self._lock:
            if self._config_path:
                path = Path(self._config_path)
                if path.exists():
                    if path.suffix in ['.yaml', '.yml']:
                        self._config = AgentConfig.from_yaml(str(path))
                    elif path.suffix == '.json':
                        self._config = AgentConfig.from_json(str(path))
                    else:
                        self._config = AgentConfig()
                else:
                    self._config = AgentConfig()
            else:
                self._config = AgentConfig()
    
    @property
    def config(self) -> AgentConfig:
        """获取当前配置"""
        with self._lock:
            return self._config
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
        self._notify_callbacks()
    
    def update(self, updates: Dict[str, Any]):
        """更新配置"""
        with self._lock:
            current_dict = self._config.to_dict()
            # 深度更新
            self._deep_update(current_dict, updates)
            self._config = AgentConfig.from_dict(current_dict)
        self._notify_callbacks()
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """深度更新字典"""
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._deep_update(target[k], v)
            else:
                target[k] = v
    
    def add_change_callback(self, callback: Callable[[AgentConfig], None]):
        """添加配置变化回调"""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[AgentConfig], None]):
        """移除配置变化回调"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """通知所有回调"""
        config = self.config
        for callback in self._change_callbacks:
            try:
                callback(config)
            except Exception:
                pass
    
    async def watch_changes(self):
        """监视配置文件变化"""
        if not self._config_path:
            return
        
        path = Path(self._config_path)
        if not path.exists():
            return
        
        try:
            async for changes in awatch(path):
                self.reload()
        except asyncio.CancelledError:
            pass
    
    async def start_watching(self):
        """开始监视配置文件"""
        if self._config_path and not self._watch_task:
            self._watch_task = asyncio.create_task(self.watch_changes())
    
    async def stop_watching(self):
        """停止监视配置文件"""
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_path)
    return _global_config_manager


def get_config() -> AgentConfig:
    """获取当前配置"""
    return get_config_manager().config
