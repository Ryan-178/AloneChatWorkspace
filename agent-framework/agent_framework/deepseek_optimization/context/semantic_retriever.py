"""
Semantic Retriever
语义检索器 - 基于向量嵌入的语义检索
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SearchMode(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class SearchResult:
    message: Dict[str, Any]
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    query: str
    mode: SearchMode = SearchMode.HYBRID
    limit: int = 10
    min_score: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)


class SemanticRetriever:
    """
    语义检索器
    支持关键词搜索、语义搜索和混合搜索
    """
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-ada-002",
        embedding_api_key: Optional[str] = None,
        cache_embeddings: bool = True,
    ):
        self.embedding_model = embedding_model
        self.embedding_api_key = embedding_api_key
        self.cache_embeddings = cache_embeddings
        
        self._embedding_cache: Dict[str, List[float]] = {}
        self._embedding_client = None
    
    def _get_embedding_client(self):
        if self._embedding_client is None:
            try:
                import openai
                self._embedding_client = openai.OpenAI(api_key=self.embedding_api_key)
            except ImportError:
                pass
        return self._embedding_client
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        if self.cache_embeddings and text in self._embedding_cache:
            return self._embedding_cache[text]
        
        client = self._get_embedding_client()
        if client is None:
            return None
        
        try:
            response = client.embeddings.create(
                model=self.embedding_model,
                input=text[:8192]
            )
            embedding = response.data[0].embedding
            
            if self.cache_embeddings:
                self._embedding_cache[text] = embedding
            
            return embedding
        except Exception:
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search(
        self,
        query: SearchQuery,
        messages: List[Dict[str, Any]],
        embeddings: Optional[Dict[int, List[float]]] = None,
    ) -> List[SearchResult]:
        if not messages:
            return []
        
        if query.mode == SearchMode.KEYWORD:
            return self._keyword_search(query, messages)
        elif query.mode == SearchMode.SEMANTIC:
            return self._semantic_search(query, messages, embeddings)
        else:
            return self._hybrid_search(query, messages, embeddings)
    
    def _keyword_search(
        self,
        query: SearchQuery,
        messages: List[Dict[str, Any]],
    ) -> List[SearchResult]:
        results = []
        query_lower = query.query.lower()
        query_words = set(query_lower.split())
        
        for i, msg in enumerate(messages):
            content = msg.get("content", "").lower()
            
            if query_lower in content:
                score = 1.0
            else:
                content_words = set(content.split())
                overlap = len(query_words & content_words)
                score = overlap / max(len(query_words), 1)
            
            if score >= query.min_score:
                results.append(SearchResult(
                    message=msg,
                    score=score,
                    source="keyword",
                    metadata={"index": i}
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.limit]
    
    def _semantic_search(
        self,
        query: SearchQuery,
        messages: List[Dict[str, Any]],
        embeddings: Optional[Dict[int, List[float]]] = None,
    ) -> List[SearchResult]:
        query_embedding = self.get_embedding(query.query)
        if query_embedding is None:
            return self._keyword_search(query, messages)
        
        results = []
        
        for i, msg in enumerate(messages):
            if embeddings and i in embeddings:
                msg_embedding = embeddings[i]
            else:
                content = msg.get("content", "")
                msg_embedding = self.get_embedding(content)
            
            if msg_embedding is None:
                continue
            
            score = self.cosine_similarity(query_embedding, msg_embedding)
            
            if score >= query.min_score:
                results.append(SearchResult(
                    message=msg,
                    score=score,
                    source="semantic",
                    metadata={"index": i}
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.limit]
    
    def _hybrid_search(
        self,
        query: SearchQuery,
        messages: List[Dict[str, Any]],
        embeddings: Optional[Dict[int, List[float]]] = None,
    ) -> List[SearchResult]:
        keyword_results = self._keyword_search(query, messages)
        semantic_results = self._semantic_search(query, messages, embeddings)
        
        combined: Dict[int, SearchResult] = {}
        
        for result in keyword_results:
            idx = result.metadata.get("index")
            if idx is not None:
                combined[idx] = result
        
        for result in semantic_results:
            idx = result.metadata.get("index")
            if idx is not None:
                if idx in combined:
                    existing = combined[idx]
                    combined[idx] = SearchResult(
                        message=result.message,
                        score=max(existing.score, result.score) * 1.2,
                        source="hybrid",
                        metadata=result.metadata
                    )
                else:
                    combined[idx] = result
        
        results = list(combined.values())
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results[:query.limit]
    
    def search_by_time(
        self,
        messages: List[Dict[str, Any]],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[SearchResult]:
        results = []
        
        for i, msg in enumerate(messages):
            msg_time = msg.get("timestamp")
            if msg_time is None:
                continue
            
            if isinstance(msg_time, str):
                msg_time = datetime.fromisoformat(msg_time)
            
            if start_time and msg_time < start_time:
                continue
            if end_time and msg_time > end_time:
                continue
            
            results.append(SearchResult(
                message=msg,
                score=1.0,
                source="time_filter",
                metadata={"index": i, "timestamp": msg_time}
            ))
        
        return results[:limit]
    
    def search_by_role(
        self,
        messages: List[Dict[str, Any]],
        roles: List[str],
        limit: int = 50,
    ) -> List[SearchResult]:
        results = []
        
        for i, msg in enumerate(messages):
            if msg.get("role") in roles:
                results.append(SearchResult(
                    message=msg,
                    score=1.0,
                    source="role_filter",
                    metadata={"index": i}
                ))
        
        return results[:limit]
    
    def multi_condition_search(
        self,
        query: SearchQuery,
        messages: List[Dict[str, Any]],
        embeddings: Optional[Dict[int, List[float]]] = None,
    ) -> List[SearchResult]:
        results = self.search(query, messages, embeddings)
        
        filters = query.filters
        
        if "roles" in filters:
            allowed_roles = filters["roles"]
            results = [r for r in results if r.message.get("role") in allowed_roles]
        
        if "min_length" in filters:
            min_len = filters["min_length"]
            results = [r for r in results if len(r.message.get("content", "")) >= min_len]
        
        if "max_length" in filters:
            max_len = filters["max_length"]
            results = [r for r in results if len(r.message.get("content", "")) <= max_len]
        
        if "contains" in filters:
            required = filters["contains"]
            if isinstance(required, str):
                required = [required]
            results = [
                r for r in results
                if any(kw in r.message.get("content", "") for kw in required)
            ]
        
        return results[:query.limit]
    
    def clear_cache(self):
        self._embedding_cache.clear()
