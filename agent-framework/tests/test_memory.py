import pytest

from agent_framework.memory.conversation_memory import ConversationMemory
from agent_framework.memory.vector_memory import VectorMemory
from agent_framework.core.base_memory import MemoryEntry


class TestConversationMemory:
    def test_add_and_query(self):
        mem = ConversationMemory(window_size=3)
        mem.add_message("user", "hello")
        mem.add_message("assistant", "hi")
        results = mem.query("", k=2)
        assert len(results) == 2

    def test_window_truncation(self):
        mem = ConversationMemory(window_size=2)
        mem.add_message("user", "a")
        mem.add_message("user", "b")
        mem.add_message("user", "c")
        msgs = mem.get_messages()
        assert len(msgs) == 2
        assert msgs[0].content == "b"
        assert msgs[1].content == "c"

    def test_clear(self):
        mem = ConversationMemory()
        mem.add_message("user", "x")
        mem.clear()
        assert len(mem.get_messages()) == 0

    def test_summarize_without_llm(self):
        mem = ConversationMemory()
        mem.add_message("user", "hello")
        summary = mem.summarize()
        assert "user: hello" in summary

    def test_get_messages_limit(self):
        mem = ConversationMemory(window_size=5)
        for i in range(5):
            mem.add_message("user", str(i))
        msgs = mem.get_messages(limit=2)
        assert len(msgs) == 2
        assert msgs[-1].content == "4"

    def test_add_entry_directly(self):
        mem = ConversationMemory()
        mem.add(MemoryEntry(content="direct"))
        assert len(mem.get_messages()) == 1

    def test_query_returns_recent(self):
        mem = ConversationMemory(window_size=5)
        for i in range(5):
            mem.add_message("user", str(i))
        results = mem.query("anything", k=3)
        assert len(results) == 3
        assert results[0].content == "2"
        assert results[1].content == "3"
        assert results[2].content == "4"


class TestVectorMemory:
    def test_init(self):
        mem = VectorMemory(collection_name="test_collection")
        assert mem.collection_name == "test_collection"
        assert mem.embedding_model == "text-embedding-ada-002"

    def test_init_custom_params(self):
        mem = VectorMemory(
            collection_name="custom",
            embedding_model="text-embedding-3-small",
            persist_path="./custom_db",
        )
        assert mem.collection_name == "custom"
        assert mem.embedding_model == "text-embedding-3-small"
        assert mem.persist_path == "./custom_db"

    def test_add_and_query_mock(self, monkeypatch):
        mem = VectorMemory(collection_name="test_mem")

        class FakeCollection:
            def __init__(self):
                self.data = []

            def add(self, ids, documents, metadatas, embeddings=None):
                self.data.append({"ids": ids, "docs": documents, "metas": metadatas})

            def query(self, query_embeddings, n_results):
                return {
                    "ids": [["id1"]],
                    "documents": [["hello world"]],
                    "metadatas": [[{"source": "test"}]],
                    "distances": [[0.1]],
                }

        class FakeClient:
            def get_or_create_collection(self, name):
                return FakeCollection()

        monkeypatch.setattr("chromadb.PersistentClient", lambda path: FakeClient())
        monkeypatch.setattr(
            VectorMemory, "_get_embedding", lambda self, text: [0.1, 0.2, 0.3]
        )

        mem._client = FakeClient()
        mem._collection = FakeCollection()

        mem.add(MemoryEntry(content="hello world", metadata={"source": "test"}))
        results = mem.query("hello", k=1)
        assert len(results) == 1
        assert results[0].content == "hello world"
        assert results[0].metadata == {"source": "test"}
        assert results[0].score == 0.1

    def test_clear_mock(self, monkeypatch):
        mem = VectorMemory(collection_name="test_clear")

        class FakeCollection:
            def delete(self, where):
                self.deleted = True

        class FakeClient:
            def get_or_create_collection(self, name):
                return FakeCollection()

        monkeypatch.setattr("chromadb.PersistentClient", lambda path: FakeClient())
        mem._client = FakeClient()
        mem._collection = FakeCollection()
        mem.clear()
        assert mem._collection.deleted is True

    def test_query_empty_embedding(self, monkeypatch):
        mem = VectorMemory(collection_name="test_empty")
        monkeypatch.setattr(VectorMemory, "_get_embedding", lambda self, text: [])
        results = mem.query("test", k=5)
        assert results == []
