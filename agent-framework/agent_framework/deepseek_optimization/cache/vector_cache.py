"""
Vector Cache
向量缓存层（可选FAISS）
"""
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class VectorItem:
    """向量条目"""
    key: str
    value: Any
    embedding: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    access_count: int = 0


class VectorCache:
    """
    向量缓存层
    用于更高级的语义相似度匹配
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, VectorItem] = {}
        self._embedding_model = None

    def _init_embeddings(self):
        """延迟初始化嵌入模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    "all-MiniLM-L6-v2",
                    device="cpu"
                )
            except Exception:
                pass

    def get_embedding(self, text: str) -> Any:
        """获取嵌入向量（可选）"""
        try:
            self._init_embeddings()
            if self._embedding_model:
                return self._embedding_model.encode(text)
        except Exception:
            pass
        return None

    def put(self, key: str, value: Any, text: str = "") -> bool:
        """添加缓存"""
        item = VectorItem(
            key=key,
            value=value,
            metadata={"text": text},
        )
        self._cache[key] = item
        if len(self._cache) > self.max_size:
            self._evict()
        return True

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            item = self._cache[key]
            item.access_count += 1
            return item.value
        return None

    def find_similar(self, text: str) -> Tuple[Optional[Any], float]:
        """查找相似项"""
        if not self._cache:
            return None, 0.0
        return None, 0.0

    def _evict(self):
        """淘汰策略"""
        if self._cache:
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].access_count
            )
            if sorted_keys:
                del self._cache[sorted_keys[0]]

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)
