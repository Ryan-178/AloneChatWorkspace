import uuid
from typing import Any, Dict, List, Optional

from alonechat.rag.loader import Document, load_document
from alonechat.rag.splitter import RecursiveCharacterTextSplitter
from alonechat.rag.embedding import EmbeddingProvider
from alonechat.rag.retriever import Retriever


class RAGPipeline:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "text-embedding-ada-002",
        embedding_api_key: Optional[str] = None,
        collection_name: str = "rag_docs",
        persist_path: str = "./chroma_db",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding = EmbeddingProvider(model=embedding_model, api_key=embedding_api_key)
        self.collection_name = collection_name
        self.persist_path = persist_path
        self._client = None
        self._collection = None
        self._retriever = None

    def _get_collection(self):
        if self._collection is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
            self._retriever = Retriever(self._collection, self.embedding)
        return self._collection

    def ingest(self, path: str) -> int:
        document = load_document(path)
        chunks = self.splitter.split_document(document)
        if not chunks:
            return 0

        collection = self._get_collection()
        texts = [c.content for c in chunks]
        embeddings = self.embedding.embed(texts)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {**c.metadata, "source": c.source, "chunk_index": c.metadata.get("chunk_index", i)}
            for i, c in enumerate(chunks)
        ]

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def ingest_text(self, text: str, source: str = "inline") -> int:
        doc = Document(content=text, source=source)
        chunks = self.splitter.split_document(doc)
        if not chunks:
            return 0

        collection = self._get_collection()
        texts = [c.content for c in chunks]
        embeddings = self.embedding.embed(texts)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {**c.metadata, "source": c.source, "chunk_index": c.metadata.get("chunk_index", i)}
            for i, c in enumerate(chunks)
        ]

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        collection = self._get_collection()
        if self._retriever is None:
            self._retriever = Retriever(collection, self.embedding)
        return self._retriever.retrieve(query, k)
