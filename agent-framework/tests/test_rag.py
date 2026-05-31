import pytest

from agent_framework.rag.loader import Document, load_document, load_txt, load_html
from agent_framework.rag.splitter import RecursiveCharacterTextSplitter
from agent_framework.rag.pipeline import RAGPipeline
from agent_framework.rag.embedding import EmbeddingProvider


class TestDocumentLoader:
    def test_txt_loader(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world", encoding="utf-8")
        doc = load_txt(str(p))
        assert doc.content == "hello world"
        assert doc.source == str(p)

    def test_html_loader(self, tmp_path):
        p = tmp_path / "test.html"
        p.write_text("<html><body>Hello</body></html>", encoding="utf-8")
        doc = load_html(str(p))
        assert "Hello" in doc.content

    def test_load_document_txt(self, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("content", encoding="utf-8")
        doc = load_document(str(p))
        assert doc.content == "content"

    def test_load_document_unknown(self, tmp_path):
        p = tmp_path / "data.xyz"
        p.write_text("fallback", encoding="utf-8")
        doc = load_document(str(p))
        assert doc.content == "fallback"

    def test_document_metadata(self):
        doc = Document(content="x", source="s", metadata={"k": "v"})
        assert doc.metadata == {"k": "v"}


class TestTextSplitter:
    def test_small_text(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_text("hello")
        assert chunks == ["hello"]

    def test_large_text(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)
        text = "a" * 50
        chunks = splitter.split_text(text)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 10 + 2

    def test_split_document(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)
        doc = Document(content="x" * 50, source="test")
        chunks = splitter.split_document(doc)
        assert len(chunks) > 1
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[0].metadata["total_chunks"] == len(chunks)

    def test_split_with_separators(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=5)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = splitter.split_text(text)
        assert len(chunks) >= 1

    def test_empty_text(self):
        splitter = RecursiveCharacterTextSplitter()
        chunks = splitter.split_text("")
        assert chunks == [""]


class TestEmbeddingProvider:
    def test_init(self):
        emb = EmbeddingProvider()
        assert emb.model == "text-embedding-ada-002"

    def test_embed_empty(self):
        emb = EmbeddingProvider()
        result = emb.embed([])
        assert result == []

    def test_embed_query_empty(self):
        emb = EmbeddingProvider(api_key="test-key")
        result = emb.embed_query("")
        assert result == []


class TestRAGPipeline:
    def test_ingest_text_mock(self, monkeypatch):
        pipeline = RAGPipeline(chunk_size=10, chunk_overlap=2)

        class FakeCollection:
            def __init__(self):
                self.added = []

            def add(self, ids, documents, metadatas, embeddings=None):
                self.added.append({"ids": ids, "docs": documents})

        class FakeClient:
            def get_or_create_collection(self, name):
                return FakeCollection()

        monkeypatch.setattr("chromadb.PersistentClient", lambda path: FakeClient())
        monkeypatch.setattr(
            pipeline.embedding, "embed", lambda texts: [[0.1] * 10 for _ in texts]
        )

        pipeline._client = FakeClient()
        pipeline._collection = FakeCollection()

        count = pipeline.ingest_text("a" * 100, source="inline")
        assert count > 0

    def test_retrieve_mock(self, monkeypatch):
        pipeline = RAGPipeline()

        class FakeCollection:
            def query(self, query_embeddings, n_results):
                return {
                    "ids": [["id1"]],
                    "documents": [["result"]],
                    "metadatas": [[{"source": "s"}]],
                    "distances": [[0.5]],
                }

        class FakeClient:
            def get_or_create_collection(self, name):
                return FakeCollection()

        monkeypatch.setattr("chromadb.PersistentClient", lambda path: FakeClient())
        monkeypatch.setattr(
            pipeline.embedding, "embed_query", lambda text: [0.1] * 10
        )

        pipeline._client = FakeClient()
        pipeline._collection = FakeCollection()
        pipeline._retriever = None

        results = pipeline.retrieve("query", k=1)
        assert len(results) == 1
        assert results[0]["content"] == "result"
        assert results[0]["source"] == "s"
        assert results[0]["score"] == 0.5
        assert results[0]["metadata"] == {"source": "s"}

    def test_ingest_empty_text(self, monkeypatch):
        pipeline = RAGPipeline()

        class FakeCollection:
            pass

        class FakeClient:
            def get_or_create_collection(self, name):
                return FakeCollection()

        monkeypatch.setattr("chromadb.PersistentClient", lambda path: FakeClient())
        monkeypatch.setattr(
            pipeline.embedding, "embed", lambda texts: [[0.1] * 10 for _ in texts]
        )
        pipeline._client = FakeClient()
        pipeline._collection = FakeCollection()

        count = pipeline.ingest_text("", source="empty")
        assert count == 0

    def test_pipeline_init(self):
        pipeline = RAGPipeline(
            chunk_size=500,
            chunk_overlap=50,
            embedding_model="text-embedding-3-small",
        )
        assert pipeline.chunk_size == 500
        assert pipeline.chunk_overlap == 50
        assert pipeline.embedding.model == "text-embedding-3-small"
