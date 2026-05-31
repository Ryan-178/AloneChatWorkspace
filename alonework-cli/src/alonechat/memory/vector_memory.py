import uuid
from typing import Any, Dict, List, Optional

from alonechat.core.base_memory import BaseMemory, MemoryEntry


class VectorMemory(BaseMemory):
    def __init__(
        self,
        collection_name: str = "agent_memory",
        embedding_model: str = "text-embedding-ada-002",
        persist_path: str = "./chroma_db",
        api_key: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.persist_path = persist_path
        self.api_key = api_key
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name
            )
        return self._client, self._collection

    def _get_embedding(self, text: str) -> List[float]:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            return []

    def add(self, entry: MemoryEntry) -> None:
        _, collection = self._get_client()
        entry_id = entry.id or str(uuid.uuid4())
        embedding = entry.embedding or self._get_embedding(entry.content)
        collection.add(
            ids=[entry_id],
            documents=[entry.content],
            metadatas=[entry.metadata],
            embeddings=[embedding] if embedding else None,
        )

    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        _, collection = self._get_client()
        embedding = self._get_embedding(text)
        if not embedding:
            return []
        results = collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )
        entries = []
        for i in range(len(results["ids"][0])):
            entries.append(
                MemoryEntry(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=results["distances"][0][i] if results["distances"] else None,
                )
            )
        return entries

    def clear(self) -> None:
        _, collection = self._get_client()
        collection.delete(where={})
