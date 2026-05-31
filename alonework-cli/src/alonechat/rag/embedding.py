import os
from typing import List
import hashlib
import base64


class EmbeddingGenerator:
    """
    Embedding Generator - 向量生成器
    使用 OpenAI API 生成文本向量
    API Key 使用环境变量获取，不在内存中长期存储明文
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self._api_key: str = ""
        self._load_api_key()

    def _load_api_key(self) -> None:
        """从环境变量加载 API Key"""
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it before using the embedding generator."
            )

    def _get_api_key(self) -> str:
        """获取 API Key - 每次从环境变量重新读取"""
        # 优先从环境变量读取，避免内存中长期存储
        env_key = os.environ.get("OPENAI_API_KEY", "")
        if env_key:
            return env_key
        return self._api_key

    def _mask_key(self, key: str) -> str:
        """掩码显示 API Key"""
        if len(key) <= 8:
            return "***"
        return key[:4] + "..." + key[-4:]

    def generate(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        import openai

        api_key = self._get_api_key()
        client = openai.OpenAI(api_key=api_key)

        embeddings = []
        for text in texts:
            response = client.embeddings.create(
                model=self.model,
                input=text,
            )
            embeddings.append(response.data[0].embedding)

        return embeddings

    def generate_single(self, text: str) -> List[float]:
        """生成单个文本向量"""
        result = self.generate([text])
        return result[0]
