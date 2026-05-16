"""
Compression Strategy
分层压缩策略 - 多种智能压缩策略
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass, field
from enum import Enum


class CompressionPriority(str, Enum):
    KEEP_ALL = "keep_all"
    KEEP_IMPORTANT = "keep_important"
    AGGRESSIVE = "aggressive"


@dataclass
class CompressionResult:
    original_messages: List[Dict[str, Any]]
    compressed_messages: List[Dict[str, Any]]
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_name: str
    messages_kept: int
    messages_compressed: int
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompressionStrategy(ABC):
    @abstractmethod
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        current_tokens: int,
        **kwargs
    ) -> CompressionResult:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class TailPreserveStrategy(CompressionStrategy):
    def __init__(self, preserve_last_n: int = 5):
        self.preserve_last_n = preserve_last_n
    
    @property
    def name(self) -> str:
        return "tail_preserve"
    
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        current_tokens: int,
        **kwargs
    ) -> CompressionResult:
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                strategy_name=self.name,
                messages_kept=len(messages),
                messages_compressed=0,
                summary="无需压缩"
            )
        
        preserved = messages[-self.preserve_last_n:] if messages else []
        early_messages = messages[:-self.preserve_last_n] if len(messages) > self.preserve_last_n else []
        
        summary_msg = {
            "role": "system",
            "content": f"[历史摘要] 已压缩 {len(early_messages)} 条早期消息"
        }
        
        compressed = [summary_msg] + preserved
        compressed_tokens = int(current_tokens * 0.3)
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed,
            original_tokens=current_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / current_tokens,
            strategy_name=self.name,
            messages_kept=len(preserved),
            messages_compressed=len(early_messages),
            summary=f"保留最后{self.preserve_last_n}条，压缩{len(early_messages)}条早期消息"
        )


class ImportanceBasedStrategy(CompressionStrategy):
    def __init__(
        self,
        importance_threshold: float = 0.5,
        preserve_system: bool = True
    ):
        self.importance_threshold = importance_threshold
        self.preserve_system = preserve_system
    
    @property
    def name(self) -> str:
        return "importance_based"
    
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        current_tokens: int,
        importance_scores: Optional[List[float]] = None,
        **kwargs
    ) -> CompressionResult:
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                strategy_name=self.name,
                messages_kept=len(messages),
                messages_compressed=0,
                summary="无需压缩"
            )
        
        if importance_scores is None:
            importance_scores = self._calculate_importance(messages)
        
        kept_messages = []
        compressed_messages = []
        
        for i, msg in enumerate(messages):
            score = importance_scores[i] if i < len(importance_scores) else 0.5
            is_system = msg.get("role") == "system"
            
            if score >= self.importance_threshold or (self.preserve_system and is_system):
                kept_messages.append(msg)
            else:
                compressed_messages.append(msg)
        
        if compressed_messages:
            summary_msg = {
                "role": "system",
                "content": f"[重要性压缩] 已压缩 {len(compressed_messages)} 条低重要性消息"
            }
            kept_messages.insert(0, summary_msg)
        
        compressed_tokens = int(current_tokens * len(kept_messages) / max(len(messages), 1))
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=kept_messages,
            original_tokens=current_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / current_tokens,
            strategy_name=self.name,
            messages_kept=len(kept_messages),
            messages_compressed=len(compressed_messages),
            summary=f"保留{len(kept_messages)}条重要消息，压缩{len(compressed_messages)}条低重要性消息",
            metadata={"importance_threshold": self.importance_threshold}
        )
    
    def _calculate_importance(self, messages: List[Dict[str, Any]]) -> List[float]:
        scores = []
        total = len(messages)
        
        for i, msg in enumerate(messages):
            score = 0.5
            content = msg.get("content", "")
            role = msg.get("role", "user")
            
            if role == "system":
                score += 0.4
            elif role == "assistant":
                score += 0.1
            
            recency = (i + 1) / total
            score += recency * 0.3
            
            if any(kw in content.lower() for kw in ["重要", "关键", "必须", "important", "critical"]):
                score += 0.2
            
            scores.append(min(1.0, score))
        
        return scores


class SemanticClusterStrategy(CompressionStrategy):
    def __init__(self, cluster_threshold: float = 0.7):
        self.cluster_threshold = cluster_threshold
    
    @property
    def name(self) -> str:
        return "semantic_cluster"
    
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        current_tokens: int,
        **kwargs
    ) -> CompressionResult:
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                strategy_name=self.name,
                messages_kept=len(messages),
                messages_compressed=0,
                summary="无需压缩"
            )
        
        clusters = self._cluster_messages(messages)
        
        compressed = []
        for cluster in clusters:
            if len(cluster) > 1:
                representative = cluster[-1]
                summary = {
                    "role": "system",
                    "content": f"[语义聚类] 代表 {len(cluster)} 条相似消息: {representative.get('content', '')[:50]}..."
                }
                compressed.append(summary)
            else:
                compressed.extend(cluster)
        
        compressed_tokens = int(current_tokens * len(compressed) / max(len(messages), 1))
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed,
            original_tokens=current_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / current_tokens,
            strategy_name=self.name,
            messages_kept=len(compressed),
            messages_compressed=len(messages) - len(compressed),
            summary=f"聚类压缩：{len(messages)}条 -> {len(compressed)}条"
        )
    
    def _cluster_messages(self, messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        clusters = []
        current_cluster = []
        
        for msg in messages:
            if not current_cluster:
                current_cluster = [msg]
            else:
                last_content = current_cluster[-1].get("content", "")
                curr_content = msg.get("content", "")
                
                similarity = self._simple_similarity(last_content, curr_content)
                
                if similarity >= self.cluster_threshold:
                    current_cluster.append(msg)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [msg]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


class HybridStrategy(CompressionStrategy):
    def __init__(
        self,
        preserve_last_n: int = 3,
        importance_threshold: float = 0.4,
        use_semantic: bool = True
    ):
        self.tail_strategy = TailPreserveStrategy(preserve_last_n)
        self.importance_strategy = ImportanceBasedStrategy(importance_threshold)
        self.semantic_strategy = SemanticClusterStrategy() if use_semantic else None
        self.use_semantic = use_semantic
    
    @property
    def name(self) -> str:
        return "hybrid"
    
    def compress(
        self,
        messages: List[Dict[str, Any]],
        target_tokens: int,
        current_tokens: int,
        **kwargs
    ) -> CompressionResult:
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                strategy_name=self.name,
                messages_kept=len(messages),
                messages_compressed=0,
                summary="无需压缩"
            )
        
        compression_ratio = target_tokens / current_tokens
        
        if compression_ratio > 0.7:
            result = self.tail_strategy.compress(messages, target_tokens, current_tokens)
        elif compression_ratio > 0.4:
            result = self.importance_strategy.compress(messages, target_tokens, current_tokens)
        else:
            if self.use_semantic and self.semantic_strategy:
                result = self.semantic_strategy.compress(messages, target_tokens, current_tokens)
            else:
                result = self.importance_strategy.compress(messages, target_tokens, current_tokens)
        
        result.strategy_name = self.name
        result.summary = f"[混合策略] {result.summary}"
        
        return result


class CompressionStrategyFactory:
    _strategies: Dict[str, type] = {
        "tail_preserve": TailPreserveStrategy,
        "importance_based": ImportanceBasedStrategy,
        "semantic_cluster": SemanticClusterStrategy,
        "hybrid": HybridStrategy,
    }
    
    @classmethod
    def create(cls, strategy_name: str, **kwargs) -> CompressionStrategy:
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return cls._strategies[strategy_name](**kwargs)
    
    @classmethod
    def register(cls, name: str, strategy_class: type):
        cls._strategies[name] = strategy_class
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())
