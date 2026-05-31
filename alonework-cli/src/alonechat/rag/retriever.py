from typing import Any, Dict, List, Optional

from alonechat.rag.loader import Document


class Retriever:
    def __init__(self, collection, embedding_provider):
        self.collection = collection
        self.embedding_provider = embedding_provider

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        embedding = self.embedding_provider.embed_query(query)
        if not embedding:
            return []
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
        )
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "content": results["documents"][0][i],
                "score": results["distances"][0][i] if results["distances"] else None,
                "source": (results["metadatas"][0][i] if results["metadatas"] else {}).get("source", ""),
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output
