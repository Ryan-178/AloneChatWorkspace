"""
Context Config
上下文配置 - 集中管理所有配置项
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml


@dataclass
class TokenEstimationConfig:
    mode: str = "auto"
    encoding: str = "cl100k_base"
    fallback_ratio: float = 0.25


@dataclass
class CompressionConfig:
    strategy: str = "hybrid"
    preserve_last_n: int = 5
    importance_threshold: float = 0.4
    min_compression_ratio: float = 0.5


@dataclass
class StorageConfig:
    root_path: str = "./data/context_archive"
    max_file_size_mb: float = 10.0
    auto_cleanup_days: int = 30


@dataclass
class CacheConfig:
    max_size: int = 1000
    max_memory_mb: float = 100.0
    default_ttl_seconds: int = 3600
    enable_preload: bool = True


@dataclass
class SessionConfig:
    auto_save: bool = True
    max_sessions: int = 1000
    snapshot_interval: int = 10


@dataclass
class ContextManagementConfig:
    max_context_tokens: int = 1000000
    target_active_tokens: int = 800000
    reserve_ratio: float = 0.1
    
    token_estimation: TokenEstimationConfig = field(default_factory=TokenEstimationConfig)
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextManagementConfig":
        token_est = TokenEstimationConfig(**data.get("token_estimation", {}))
        compression = CompressionConfig(**data.get("compression", {}))
        storage = StorageConfig(**data.get("storage", {}))
        cache = CacheConfig(**data.get("cache", {}))
        session = SessionConfig(**data.get("session", {}))
        
        return cls(
            max_context_tokens=data.get("max_context_tokens", 1000000),
            target_active_tokens=data.get("target_active_tokens", 800000),
            reserve_ratio=data.get("reserve_ratio", 0.1),
            token_estimation=token_est,
            compression=compression,
            storage=storage,
            cache=cache,
            session=session,
        )
    
    @classmethod
    def from_yaml(cls, path: Path) -> "ContextManagementConfig":
        if not path.exists():
            return cls()
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_context_tokens": self.max_context_tokens,
            "target_active_tokens": self.target_active_tokens,
            "reserve_ratio": self.reserve_ratio,
            "token_estimation": {
                "mode": self.token_estimation.mode,
                "encoding": self.token_estimation.encoding,
                "fallback_ratio": self.token_estimation.fallback_ratio,
            },
            "compression": {
                "strategy": self.compression.strategy,
                "preserve_last_n": self.compression.preserve_last_n,
                "importance_threshold": self.compression.importance_threshold,
                "min_compression_ratio": self.compression.min_compression_ratio,
            },
            "storage": {
                "root_path": self.storage.root_path,
                "max_file_size_mb": self.storage.max_file_size_mb,
                "auto_cleanup_days": self.storage.auto_cleanup_days,
            },
            "cache": {
                "max_size": self.cache.max_size,
                "max_memory_mb": self.cache.max_memory_mb,
                "default_ttl_seconds": self.cache.default_ttl_seconds,
                "enable_preload": self.cache.enable_preload,
            },
            "session": {
                "auto_save": self.session.auto_save,
                "max_sessions": self.session.max_sessions,
                "snapshot_interval": self.session.snapshot_interval,
            },
        }


class ContextConfig:
    """
    上下文配置管理器
    支持从文件、环境变量加载配置
    """
    
    _instance: Optional["ContextConfig"] = None
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config = ContextManagementConfig()
        self._load_config()
    
    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> "ContextConfig":
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance
    
    def _load_config(self):
        if self.config_path and self.config_path.exists():
            self._config = ContextManagementConfig.from_yaml(self.config_path)
        
        self._load_from_env()
    
    def _load_from_env(self):
        if "CONTEXT_MAX_TOKENS" in os.environ:
            self._config.max_context_tokens = int(os.environ["CONTEXT_MAX_TOKENS"])
        
        if "CONTEXT_TARGET_TOKENS" in os.environ:
            self._config.target_active_tokens = int(os.environ["CONTEXT_TARGET_TOKENS"])
        
        if "CONTEXT_STORAGE_PATH" in os.environ:
            self._config.storage.root_path = os.environ["CONTEXT_STORAGE_PATH"]
        
        if "CONTEXT_CACHE_SIZE" in os.environ:
            self._config.cache.max_size = int(os.environ["CONTEXT_CACHE_SIZE"])
        
        if "CONTEXT_COMPRESSION_STRATEGY" in os.environ:
            self._config.compression.strategy = os.environ["CONTEXT_COMPRESSION_STRATEGY"]
    
    @property
    def config(self) -> ContextManagementConfig:
        return self._config
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def save(self, path: Optional[Path] = None):
        save_path = path or self.config_path
        if save_path is None:
            return
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config.to_dict(), f, default_flow_style=False)
    
    def validate(self) -> List[str]:
        errors = []
        
        if self._config.max_context_tokens <= 0:
            errors.append("max_context_tokens must be positive")
        
        if self._config.target_active_tokens > self._config.max_context_tokens:
            errors.append("target_active_tokens cannot exceed max_context_tokens")
        
        if self._config.reserve_ratio < 0 or self._config.reserve_ratio >= 1:
            errors.append("reserve_ratio must be between 0 and 1")
        
        if self._config.compression.strategy not in ["tail_preserve", "importance_based", "semantic_cluster", "hybrid"]:
            errors.append(f"Unknown compression strategy: {self._config.compression.strategy}")
        
        return errors
