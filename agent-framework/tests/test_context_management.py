"""
上下文管理模块单元测试
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from agent_framework.deepseek_optimization.context import (
    TokenEstimator,
    TokenBudget,
    EstimationMode,
    MegaContextManager,
    SessionManager,
    ContextSnapshot,
    CompressionStrategyFactory,
    TailPreserveStrategy,
    ImportanceBasedStrategy,
    HybridStrategy,
    SemanticRetriever,
    SearchQuery,
    SearchMode,
    ContextCache,
    ContextMonitor,
    HealthStatus,
)


class TestTokenEstimator:
    def test_estimate_text_fast_mode(self):
        estimator = TokenEstimator(mode=EstimationMode.FAST)
        result = estimator.estimate("Hello, world!")
        
        assert result.token_count > 0
        assert result.char_count == 13
        assert result.estimation_mode == EstimationMode.FAST
    
    def test_estimate_empty_text(self):
        estimator = TokenEstimator()
        result = estimator.estimate("")
        
        assert result.token_count == 0
        assert result.char_count == 0
    
    def test_estimate_message(self):
        estimator = TokenEstimator()
        message = {"role": "user", "content": "Hello, how are you?"}
        result = estimator.estimate(message)
        
        assert result.token_count > 0
        assert result.content_type == "message"
    
    def test_estimate_messages(self):
        estimator = TokenEstimator()
        messages = [
            {"role": "system", "content": "You are an assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = estimator.estimate(messages)
        
        assert result.token_count > 0
        assert result.content_type == "messages"
    
    def test_estimate_chinese_text(self):
        estimator = TokenEstimator(mode=EstimationMode.FAST)
        result = estimator.estimate("你好，世界！这是一段中文文本。")
        
        assert result.token_count > 0
        assert "chinese_chars" in result.breakdown
    
    def test_estimate_code(self):
        estimator = TokenEstimator(mode=EstimationMode.FAST)
        code = """
```python
def hello():
    print("Hello, world!")
```
"""
        result = estimator.estimate(code)
        
        assert result.token_count > 0
        assert result.content_type == "code"
    
    def test_get_model_limit(self):
        estimator = TokenEstimator()
        
        assert estimator.get_model_limit("gpt-4") == 8192
        assert estimator.get_model_limit("deepseek-v4") == 1000000
        assert estimator.get_model_limit("unknown-model") == 8192
    
    def test_create_budget(self):
        estimator = TokenEstimator()
        budget = estimator.create_budget("deepseek-v4", reserve_ratio=0.1)
        
        assert budget.total_budget == 1000000
        assert budget.reserved == 100000
    
    def test_check_budget(self):
        estimator = TokenEstimator()
        budget = TokenBudget(total_budget=100, reserved=10)
        messages = [{"role": "user", "content": "Hello"}]
        
        result = estimator.check_budget(messages, budget)
        
        assert "token_count" in result
        assert "would_exceed" in result
        assert "remaining" in result
    
    def test_select_messages_for_budget(self):
        estimator = TokenEstimator()
        budget = TokenBudget(total_budget=100, reserved=10)
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
        ]
        
        selected = estimator.select_messages_for_budget(messages, budget, preserve_last=1)
        
        assert len(selected) >= 1


class TestTokenBudget:
    def test_available(self):
        budget = TokenBudget(total_budget=100, used=30, reserved=10)
        
        assert budget.available == 60
    
    def test_usage_ratio(self):
        budget = TokenBudget(total_budget=100, used=30, reserved=10)
        
        assert budget.usage_ratio == 0.4
    
    def test_zero_total_budget(self):
        budget = TokenBudget(total_budget=0)
        
        assert budget.available == 0
        assert budget.usage_ratio == 0.0


class TestMegaContextManager:
    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_init(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        
        assert manager.max_context_tokens == 1000000
        assert manager.target_active_tokens == 800000
    
    def test_add_message(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        message = {"role": "user", "content": "Hello"}
        
        managed = manager.add_message(message)
        
        assert managed.message == message
        assert managed.token_count > 0
        assert manager.get_message_count() == 1
    
    def test_add_messages(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        
        results = manager.add_messages(messages)
        
        assert len(results) == 2
        assert manager.get_message_count() == 2
    
    def test_get_active_context(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        messages = [
            {"role": "system", "content": "You are an assistant"},
            {"role": "user", "content": "Hello"},
        ]
        manager.add_messages(messages)
        
        active, managed = manager.get_active_context()
        
        assert len(active) > 0
    
    def test_get_token_usage(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        manager.add_message({"role": "user", "content": "Hello"})
        
        usage = manager.get_token_usage()
        
        assert "active_tokens" in usage
        assert "total_tokens" in usage
        assert "usage_ratio" in usage
    
    def test_check_token_budget(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        manager.add_message({"role": "user", "content": "Hello"})
        
        result = manager.check_token_budget()
        
        assert "current_usage" in result
        assert "remaining" in result
    
    def test_clear(self, temp_storage):
        manager = MegaContextManager(storage_root=temp_storage)
        manager.add_message({"role": "user", "content": "Hello"})
        
        manager.clear()
        
        assert manager.get_message_count() == 0


class TestSessionManager:
    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_session(self, temp_storage):
        manager = SessionManager(storage_root=temp_storage)
        
        session = manager.create_session(title="Test Session")
        
        assert session.session_id
        assert session.title == "Test Session"
    
    def test_load_session(self, temp_storage):
        manager = SessionManager(storage_root=temp_storage)
        created = manager.create_session(title="Test")
        
        loaded = manager.load_session(created.session_id)
        
        assert loaded is not None
        assert loaded.session_id == created.session_id
    
    def test_update_session(self, temp_storage):
        manager = SessionManager(storage_root=temp_storage)
        session = manager.create_session(title="Test")
        
        updated = manager.update_session(
            session.session_id,
            message_count=10,
            title="Updated"
        )
        
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.message_count == 10
    
    def test_list_sessions(self, temp_storage):
        manager = SessionManager(storage_root=temp_storage)
        manager.create_session(title="Session 1")
        manager.create_session(title="Session 2")
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 2
    
    def test_delete_session(self, temp_storage):
        manager = SessionManager(storage_root=temp_storage)
        session = manager.create_session(title="Test")
        
        deleted = manager.delete_session(session.session_id)
        
        assert deleted is True
        assert manager.load_session(session.session_id) is None


class TestContextSnapshot:
    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_snapshot(self, temp_storage):
        snapshot_manager = ContextSnapshot(storage_root=temp_storage)
        messages = [{"role": "user", "content": "Hello"}]
        
        snapshot = snapshot_manager.create_snapshot(
            session_id="test-session",
            messages=messages,
            token_count=10,
        )
        
        assert snapshot.snapshot_id
        assert snapshot.message_count == 1
    
    def test_load_snapshot(self, temp_storage):
        snapshot_manager = ContextSnapshot(storage_root=temp_storage)
        messages = [{"role": "user", "content": "Hello"}]
        
        created = snapshot_manager.create_snapshot(
            session_id="test-session",
            messages=messages,
            token_count=10,
        )
        
        loaded = snapshot_manager.load_snapshot(created.snapshot_id)
        
        assert loaded is not None
        assert len(loaded.messages) == 1
    
    def test_list_snapshots(self, temp_storage):
        snapshot_manager = ContextSnapshot(storage_root=temp_storage)
        
        snapshot_manager.create_snapshot(
            session_id="session-1",
            messages=[{"role": "user", "content": "Hello"}],
        )
        snapshot_manager.create_snapshot(
            session_id="session-1",
            messages=[{"role": "user", "content": "World"}],
        )
        
        snapshots = snapshot_manager.list_snapshots(session_id="session-1")
        
        assert len(snapshots) == 2


class TestCompressionStrategies:
    def test_tail_preserve_strategy(self):
        strategy = TailPreserveStrategy(preserve_last_n=2)
        messages = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Message 2"},
            {"role": "user", "content": "Message 3"},
            {"role": "assistant", "content": "Message 4"},
        ]
        
        result = strategy.compress(messages, target_tokens=50, current_tokens=200)
        
        assert result.strategy_name == "tail_preserve"
        assert len(result.compressed_messages) == 3
    
    def test_importance_based_strategy(self):
        strategy = ImportanceBasedStrategy(importance_threshold=0.5)
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        
        result = strategy.compress(messages, target_tokens=50, current_tokens=200)
        
        assert result.strategy_name == "importance_based"
    
    def test_hybrid_strategy(self):
        strategy = HybridStrategy()
        messages = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Message 2"},
        ]
        
        result = strategy.compress(messages, target_tokens=50, current_tokens=200)
        
        assert result.strategy_name == "hybrid"
    
    def test_compression_strategy_factory(self):
        strategy = CompressionStrategyFactory.create("tail_preserve", preserve_last_n=3)
        
        assert strategy.name == "tail_preserve"
        
        strategies = CompressionStrategyFactory.list_strategies()
        assert "tail_preserve" in strategies
        assert "importance_based" in strategies
        assert "hybrid" in strategies


class TestSemanticRetriever:
    def test_keyword_search(self):
        retriever = SemanticRetriever()
        messages = [
            {"role": "user", "content": "Hello world"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        
        query = SearchQuery(query="hello", mode=SearchMode.KEYWORD, limit=5)
        results = retriever.search(query, messages)
        
        assert len(results) >= 1
        assert results[0].source == "keyword"
    
    def test_search_by_role(self):
        retriever = SemanticRetriever()
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        
        results = retriever.search_by_role(messages, ["user"])
        
        assert len(results) == 1


class TestContextCache:
    def test_set_and_get(self):
        cache = ContextCache(max_size=10)
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_cache_miss(self):
        cache = ContextCache()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_eviction(self):
        cache = ContextCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
    
    def test_cache_stats(self):
        cache = ContextCache()
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 1
    
    def test_cache_clear(self):
        cache = ContextCache()
        cache.set("key1", "value1")
        
        cache.clear()
        
        assert cache.get("key1") is None


class TestContextMonitor:
    def test_record_message_processed(self):
        monitor = ContextMonitor()
        
        monitor.record_message_processed(token_count=100, processing_time_ms=50)
        
        metrics = monitor.get_metrics()
        assert metrics.total_messages_processed == 1
        assert metrics.total_tokens_processed == 100
    
    def test_record_compression(self):
        monitor = ContextMonitor()
        
        monitor.record_compression(original_tokens=100, compressed_tokens=40, time_ms=30)
        
        metrics = monitor.get_metrics()
        assert metrics.total_compressions == 1
    
    def test_health_check_memory(self):
        monitor = ContextMonitor()
        monitor.update_memory_usage(100.0)
        
        result = monitor.run_health_check("memory")
        
        assert result.status == HealthStatus.HEALTHY
    
    def test_health_check_cache(self):
        monitor = ContextMonitor()
        monitor.record_cache_hit()
        monitor.record_cache_hit()
        monitor.record_cache_miss()
        
        result = monitor.run_health_check("cache")
        
        assert result.status == HealthStatus.HEALTHY
    
    def test_get_summary(self):
        monitor = ContextMonitor()
        monitor.record_message_processed(token_count=100, processing_time_ms=50)
        
        summary = monitor.get_summary()
        
        assert summary["messages_processed"] == 1
        assert summary["tokens_processed"] == 100
