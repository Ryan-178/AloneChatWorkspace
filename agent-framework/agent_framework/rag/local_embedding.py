"""
Local Embedding Provider - 本地向量生成器
支持 bge-large-zh, text2vec-large-chinese 等本地模型
无需API调用，完全本地运行，保护隐私
"""
import os
import hashlib
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import numpy as np


class LocalEmbeddingModel(Enum):
    BGE_LARGE_ZH = "bge-large-zh-v1.5"
    BGE_BASE_ZH = "bge-base-zh-v1.5"
    BGE_SMALL_ZH = "bge-small-zh-v1.5"
    TEXT2VEC_LARGE = "text2vec-large-chinese"
    TEXT2VEC_BASE = "text2vec-base-chinese"
    M3E_LARGE = "m3e-large"
    M3E_BASE = "m3e-base"


@dataclass
class LocalEmbeddingConfig:
    model: LocalEmbeddingModel = LocalEmbeddingModel.BGE_LARGE_ZH
    cache_dir: str = "./embedding_cache"
    cache_enabled: bool = True
    batch_size: int = 32
    max_seq_length: int = 512
    device: str = "cpu"
    normalize: bool = True


class LocalEmbeddingProvider:
    """
    本地Embedding提供者
    支持多种中文优化模型，完全本地运行
    
    Local Embedding Provider
    Supports multiple Chinese-optimized models, runs completely locally
    """
    
    MODEL_DIMENSIONS = {
        LocalEmbeddingModel.BGE_LARGE_ZH: 1024,
        LocalEmbeddingModel.BGE_BASE_ZH: 768,
        LocalEmbeddingModel.BGE_SMALL_ZH: 512,
        LocalEmbeddingModel.TEXT2VEC_LARGE: 1024,
        LocalEmbeddingModel.TEXT2VEC_BASE: 768,
        LocalEmbeddingModel.M3E_LARGE: 1024,
        LocalEmbeddingModel.M3E_BASE: 768,
    }
    
    def __init__(self, config: Optional[LocalEmbeddingConfig] = None):
        self.config = config or LocalEmbeddingConfig()
        self._model = None
        self._dimension = self.MODEL_DIMENSIONS.get(self.config.model, 768)
        self._cache: Dict[str, List[float]] = {}
        
        if self.config.cache_enabled:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
            self._load_cache()
    
    def _load_cache(self) -> None:
        cache_file = Path(self.config.cache_dir) / f"{self.config.model.value}_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
    
    def _save_cache(self) -> None:
        if not self.config.cache_enabled:
            return
        cache_file = Path(self.config.cache_dir) / f"{self.config.model.value}_cache.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False)
        except Exception:
            pass
    
    def _get_cache_key(self, text: str) -> str:
        return hashlib.sha256(f"{self.config.model.value}:{text}".encode()).hexdigest()
    
    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self._get_model_name()
            self._model = SentenceTransformer(
                model_name,
                device=self.config.device
            )
            return self._model
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for local embedding. "
                "Install with: pip install sentence-transformers"
            )
    
    def _get_model_name(self) -> str:
        model_mapping = {
            LocalEmbeddingModel.BGE_LARGE_ZH: "BAAI/bge-large-zh-v1.5",
            LocalEmbeddingModel.BGE_BASE_ZH: "BAAI/bge-base-zh-v1.5",
            LocalEmbeddingModel.BGE_SMALL_ZH: "BAAI/bge-small-zh-v1.5",
            LocalEmbeddingModel.TEXT2VEC_LARGE: "shibing624/text2vec-large-chinese",
            LocalEmbeddingModel.TEXT2VEC_BASE: "shibing624/text2vec-base-chinese",
            LocalEmbeddingModel.M3E_LARGE: "moka-ai/m3e-large",
            LocalEmbeddingModel.M3E_BASE: "moka-ai/m3e-base",
        }
        return model_mapping.get(self.config.model, "BAAI/bge-large-zh-v1.5")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成向量
        Batch generate embeddings
        """
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        if uncached_texts:
            model = self._load_model()
            
            for batch_start in range(0, len(uncached_texts), self.config.batch_size):
                batch = uncached_texts[batch_start:batch_start + self.config.batch_size]
                batch_indices = uncached_indices[batch_start:batch_start + self.config.batch_size]
                
                embeddings = model.encode(
                    batch,
                    max_seq_length=self.config.max_seq_length,
                    normalize_embeddings=self.config.normalize,
                    show_progress_bar=False,
                )
                
                for j, (idx, emb) in enumerate(zip(batch_indices, embeddings)):
                    emb_list = emb.tolist()
                    results[idx] = emb_list
                    
                    if self.config.cache_enabled:
                        cache_key = self._get_cache_key(uncached_texts[batch_start + j])
                        self._cache[cache_key] = emb_list
            
            if self.config.cache_enabled:
                self._save_cache()
        
        return results
    
    def embed_query(self, query: str) -> List[float]:
        return self.embed([query])[0]
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return self.embed(documents)
    
    def get_dimension(self) -> int:
        return self._dimension
    
    def similarity(self, emb1: List[float], emb2: List[float]) -> float:
        v1 = np.array(emb1)
        v2 = np.array(emb2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    
    def clear_cache(self) -> None:
        self._cache = {}
        if self.config.cache_enabled:
            cache_file = Path(self.config.cache_dir) / f"{self.config.model.value}_cache.json"
            if cache_file.exists():
                cache_file.unlink()


class HybridEmbeddingProvider:
    """
    混合Embedding提供者
    优先使用本地模型，可选降级到API
    
    Hybrid Embedding Provider
    Prioritizes local models, optional fallback to API
    """
    
    def __init__(
        self,
        local_config: Optional[LocalEmbeddingConfig] = None,
        api_model: str = "text-embedding-3-small",
        api_fallback: bool = True,
    ):
        self.local_provider = LocalEmbeddingProvider(local_config)
        self.api_model = api_model
        self.api_fallback = api_fallback
        self._api_client = None
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.local_provider.embed(texts)
        except Exception as e:
            if self.api_fallback:
                return self._embed_with_api(texts)
            raise e
    
    def _embed_with_api(self, texts: List[str]) -> List[List[float]]:
        if self._api_client is None:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set for API fallback")
            self._api_client = openai.OpenAI(api_key=api_key)
        
        embeddings = []
        for text in texts:
            response = self._api_client.embeddings.create(
                model=self.api_model,
                input=text,
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        return self.embed([query])[0]
    
    def get_dimension(self) -> int:
        return self.local_provider.get_dimension()
