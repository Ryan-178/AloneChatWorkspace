from typing import List, Optional


class EmbeddingProvider:
    def __init__(self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
            response = client.embeddings.create(model=self.model, input=texts)
            return [d.embedding for d in response.data]
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return []
        results = self.embed([text])
        return results[0] if results else []
