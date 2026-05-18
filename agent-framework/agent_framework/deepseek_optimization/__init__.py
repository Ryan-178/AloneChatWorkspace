"""
DeepSeek V4 Optimization System
面向D端和B端的重量级商业化闭源系统
核心理念：All in DeepSeek V4，通过软件优化弥补硬件差距，超越Claude Mythos
"""
from .llm import (
    DeepSeekProvider,
    DeepSeekConfig,
    DeepSeekModel,
    DeepSeekUsage
)
from .cache import (
    CacheEngine,
    SemanticCache,
    VectorCache,
    CacheStats,
    DeepSeekCacheManager
)
from .context import (
    WindowManager,
    ContextCompressor,
    MessageRanker,
    ImportanceCategory,
    MessageImportance,
    StructuredStorageEngine,
    StoredMessage,
    StorageStats,
    MegaContextManager,
    ContextDecision,
    ManagedMessage,
    ContextStats,
    ContextFeedbackGenerator,
    ContextFeedback
)
from .swe import SWEEngine
from .security import (
    LicenseManager,
    AuditLogger,
    EncryptionManager,
    DataProtectionManager
)
from .optimizer import (
    DeepSeekOptimizer,
    RequestQueue,
    CostController,
    BatchProcessor,
    RetryPolicy,
    DegradationStrategy,
    Priority,
    CostBudget,
    OptimizerStats,
)

__version__ = "2.0.0"
__author__ = "DeepSeek Optimization Team"

__all__ = [
    # LLM 专用
    "DeepSeekProvider",
    "DeepSeekConfig",
    "DeepSeekModel",
    "DeepSeekUsage",
    # 缓存引擎
    "CacheEngine",
    "SemanticCache",
    "VectorCache",
    "CacheStats",
    "DeepSeekCacheManager",
    # 上下文管理
    "WindowManager",
    "ContextCompressor",
    "MessageRanker",
    "ImportanceCategory",
    "MessageImportance",
    "StructuredStorageEngine",
    "StoredMessage",
    "StorageStats",
    "MegaContextManager",
    "ContextDecision",
    "ManagedMessage",
    "ContextStats",
    "ContextFeedbackGenerator",
    "ContextFeedback",
    # SWE 引擎
    "SWEEngine",
    # 安全体系
    "LicenseManager",
    "AuditLogger",
    "EncryptionManager",
    "DataProtectionManager",
    # 深度优化器
    "DeepSeekOptimizer",
    "RequestQueue",
    "CostController",
    "BatchProcessor",
    "RetryPolicy",
    "DegradationStrategy",
    "Priority",
    "CostBudget",
    "OptimizerStats",
]
