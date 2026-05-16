import pytest
from pydantic import ValidationError

from agent_framework.core.base_llm import Message, Chunk, LLMConfig, UsageInfo, BaseLLM
from agent_framework.core.base_tool import BaseTool, ToolDef, ToolResult
from agent_framework.core.base_memory import BaseMemory, MemoryEntry
from agent_framework.core.base_agent import BaseAgent, AgentResult, AgentEvent
from agent_framework.core.orchestrator import Orchestrator, WorkflowGraph, WorkflowNode
from agent_framework.core.agent_bus import AgentMessage, AgentBus, MessageType
from agent_framework.config import AgentConfig


class TestMessage:
    def test_message_creation(self):
        m = Message(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_message_with_tool_calls(self):
        m = Message(role="assistant", content="", tool_calls=[{"id": "1", "function": {"name": "calc", "arguments": "{}"}}])
        assert m.tool_calls is not None
        assert len(m.tool_calls) == 1

    def test_message_with_tool_call_id(self):
        m = Message(role="tool", content="result", tool_call_id="call_1")
        assert m.tool_call_id == "call_1"

    def test_chunk_creation(self):
        c = Chunk(content="hi", finish_reason="stop")
        assert c.content == "hi"
        assert c.finish_reason == "stop"

    def test_chunk_with_usage(self):
        c = Chunk(content="", usage={"prompt_tokens": 5, "completion_tokens": 3})
        assert c.usage["prompt_tokens"] == 5

    def test_llm_config_defaults(self):
        cfg = LLMConfig()
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096
        assert cfg.timeout == 60

    def test_llm_config_validation(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=3.0)

    def test_llm_config_max_tokens_validation(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_usage_info(self):
        u = UsageInfo(prompt_tokens=10, completion_tokens=5, estimated_cost=0.001)
        assert u.total_tokens == 15

    def test_usage_info_defaults(self):
        u = UsageInfo()
        assert u.prompt_tokens == 0
        assert u.completion_tokens == 0
        assert u.total_tokens == 0
        assert u.estimated_cost == 0.0


class TestBaseTool:
    def test_tool_def(self):
        class DummyTool(BaseTool):
            name = "dummy"
            description = "A dummy tool"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **kwargs):
                return "ok"

        t = DummyTool()
        d = t.get_definition()
        assert d.name == "dummy"
        assert isinstance(d, ToolDef)

    def test_tool_result_defaults(self):
        r = ToolResult()
        assert r.success is True
        assert r.data is None
        assert r.error is None
        assert r.execution_time_ms == 0.0

    def test_tool_result_failure(self):
        r = ToolResult(success=False, error="failed")
        assert r.success is False
        assert r.error == "failed"


class TestBaseMemory:
    def test_memory_entry(self):
        e = MemoryEntry(content="test", metadata={"k": "v"})
        assert e.content == "test"
        assert e.metadata == {"k": "v"}

    def test_memory_entry_defaults(self):
        e = MemoryEntry(content="x")
        assert e.metadata == {}
        assert e.id is None
        assert e.embedding is None
        assert e.score is None

    def test_memory_entry_with_embedding(self):
        e = MemoryEntry(content="test", embedding=[0.1, 0.2])
        assert e.embedding == [0.1, 0.2]


class TestBaseAgent:
    def test_agent_result(self):
        r = AgentResult(answer="yes", stopped_by_max_iterations=False)
        assert r.answer == "yes"
        assert not r.stopped_by_max_iterations

    def test_agent_result_defaults(self):
        r = AgentResult()
        assert r.answer == ""
        assert r.trajectory == []
        assert r.stopped_by_max_iterations is False
        assert r.total_time_ms == 0.0

    def test_agent_event(self):
        e = AgentEvent(type="think", content="planning")
        assert e.type == "think"
        assert e.content == "planning"

    def test_agent_event_metadata(self):
        e = AgentEvent(type="act", content="tool", metadata={"tool": "calc"})
        assert e.metadata == {"tool": "calc"}


class TestAgentBus:
    def test_send_and_receive(self):
        bus = AgentBus()
        bus.register("a", None)
        bus.register("b", None)
        msg = bus.send("a", "b", "hello")
        assert msg.from_agent == "a"
        assert msg.to_agent == "b"
        assert msg.content == "hello"
        assert msg.type == MessageType.QUESTION
        received = bus.receive("b")
        assert len(received) == 1

    def test_receive_limit(self):
        bus = AgentBus()
        bus.register("a", None)
        bus.register("b", None)
        for i in range(5):
            bus.send("a", "b", str(i))
        received = bus.receive("b", limit=2)
        assert len(received) == 2
        assert received[0].content == "3"
        assert received[1].content == "4"

    def test_broadcast(self):
        bus = AgentBus()
        bus.register("a", None)
        bus.register("b", None)
        bus.register("c", None)
        msgs = bus.broadcast("a", "alert")
        assert len(msgs) == 2

    def test_broadcast_excludes_sender(self):
        bus = AgentBus()
        bus.register("a", None)
        msgs = bus.broadcast("a", "alert")
        assert len(msgs) == 0

    def test_get_conversation(self):
        bus = AgentBus()
        bus.register("a", None)
        bus.register("b", None)
        bus.send("a", "b", "hello")
        bus.send("b", "a", "hi")
        bus.send("a", "b", "how are you")
        conv = bus.get_conversation("a", "b")
        assert len(conv) == 3

    def test_unregister(self):
        bus = AgentBus()
        bus.register("a", None)
        bus.unregister("a")
        msgs = bus.broadcast("a", "x")
        assert len(msgs) == 0

    def test_message_type_enum(self):
        assert MessageType.QUESTION.value == "question"
        assert MessageType.ANSWER.value == "answer"
        assert MessageType.RESULT.value == "result"
        assert MessageType.ERROR.value == "error"
        assert MessageType.BROADCAST.value == "broadcast"


class TestWorkflowGraph:
    def test_workflow_node(self):
        node = WorkflowNode(id="n1", dependencies=["n0"])
        assert node.id == "n1"
        assert node.dependencies == ["n0"]

    def test_workflow_graph(self):
        graph = WorkflowGraph(
            nodes=[WorkflowNode(id="n1")],
            edges=[("n0", "n1")],
        )
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1


class TestAgentConfig:
    def test_from_dict(self):
        cfg = AgentConfig.from_dict({"debug": True})
        assert cfg.debug is True

    def test_to_dict(self):
        cfg = AgentConfig()
        d = cfg.to_dict()
        assert "llm" in d
        assert "memory" in d
        assert "rag" in d
        assert "security" in d

    def test_llm_settings(self):
        cfg = AgentConfig()
        assert cfg.llm.provider == "openai"
        assert cfg.llm.model == "gpt-4o"

    def test_memory_settings(self):
        cfg = AgentConfig()
        assert cfg.memory.window_size == 10
        assert cfg.memory.vector_db_type == "chromadb"

    def test_rag_settings(self):
        cfg = AgentConfig()
        assert cfg.rag.chunk_size == 1000
        assert cfg.rag.chunk_overlap == 200

    def test_security_settings(self):
        cfg = AgentConfig()
        assert cfg.security.tool_timeout_seconds == 30
        assert cfg.security.rpm_limit == 60
