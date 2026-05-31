import pytest
from unittest.mock import MagicMock

from agent_framework.agent.react_agent import ReActAgent, AgentCallback
from agent_framework.core.base_agent import AgentEvent
from agent_framework.core.base_llm import Message, LLMConfig, UsageInfo
from agent_framework.tools.registry import ToolRegistry
from agent_framework.tools.builtin.calculator import CalculatorTool


class MockLLM:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.index = 0
        self._usage = UsageInfo()

    def chat(self, messages, config=None):
        resp = self.responses[self.index % len(self.responses)]
        self.index += 1
        return Message(role="assistant", content=resp)

    def get_total_usage(self):
        return self._usage

    def record_usage(self, usage):
        pass


class TestReActAgent:
    def test_run_final_answer(self):
        llm = MockLLM(["Thought: I know the answer\nFinal Answer: 42"])
        agent = ReActAgent(llm=llm)
        result = agent.run("What is the answer?")
        assert result.answer == "42"
        assert not result.stopped_by_max_iterations
        assert result.total_time_ms >= 0

    def test_run_with_tool(self):
        llm = MockLLM([
            "Thought: Need to calculate\nAction: calculator({\"expression\": \"1+1\"})",
            "Thought: Got result\nFinal Answer: 2",
        ])
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        agent = ReActAgent(llm=llm, tool_registry=registry)
        result = agent.run("Calculate 1+1")
        assert result.answer == "2"
        assert len(result.trajectory) == 2

    def test_max_iterations_stop(self):
        llm = MockLLM(["Thought: Need to calculate\nAction: calculator({\"expression\": \"1+1\"})"] * 15)
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        agent = ReActAgent(llm=llm, tool_registry=registry, max_iterations=3)
        result = agent.run("Calculate")
        assert result.stopped_by_max_iterations is True
        assert len(result.trajectory) == 3

    def test_callback(self):
        class TestCallback(AgentCallback):
            def __init__(self):
                self.events = []

            def on_think(self, content):
                self.events.append(("think", content))

            def on_act(self, content):
                self.events.append(("act", content))

            def on_observe(self, content):
                self.events.append(("observe", content))

            def on_final(self, content):
                self.events.append(("final", content))

        llm = MockLLM(["Thought: I know\nFinal Answer: yes"])
        agent = ReActAgent(llm=llm)
        cb = TestCallback()
        agent.add_callback(cb)
        agent.run("Test")
        assert any(e[0] == "final" for e in cb.events)

    def test_parse_response_final(self):
        agent = ReActAgent(llm=MockLLM())
        parsed = agent._parse_response("Thought: Done\nFinal Answer: 99")
        assert parsed["type"] == "final"
        assert parsed["answer"] == "99"
        assert parsed["thought"] == "Done"

    def test_parse_response_action(self):
        agent = ReActAgent(llm=MockLLM())
        parsed = agent._parse_response('Thought: Need tool\nAction: calculator({"expression": "2+2"})')
        assert parsed["type"] == "action"
        assert parsed["tool"] == "calculator"
        assert parsed["params"]["expression"] == "2+2"
        assert parsed["thought"] == "Need tool"

    def test_parse_response_no_structure(self):
        agent = ReActAgent(llm=MockLLM())
        parsed = agent._parse_response("Just some text")
        assert parsed["type"] == "final"
        assert parsed["answer"] == "Just some text"

    def test_parse_response_action_invalid_json(self):
        agent = ReActAgent(llm=MockLLM())
        parsed = agent._parse_response("Thought: Do it\nAction: tool(some plain text)")
        assert parsed["type"] == "action"
        assert parsed["tool"] == "tool"
        assert "query" in parsed["params"]

    def test_system_prompt_generation(self):
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        agent = ReActAgent(llm=MockLLM(), tool_registry=registry)
        prompt = agent.system_prompt
        assert "calculator" in prompt
        assert "Available tools" in prompt

    def test_custom_system_prompt(self):
        agent = ReActAgent(llm=MockLLM(), system_prompt="Custom prompt")
        assert agent.system_prompt == "Custom prompt"

    def test_perceive_plan_act_reflect(self):
        agent = ReActAgent(llm=MockLLM())
        assert agent.perceive("task") == {"task": "task"}
        assert agent.plan({"x": 1}) == {"x": 1}
        assert agent.act({"x": 1}) == {"x": 1}
        assert agent.reflect({"x": 1}) == {"x": 1}

    def test_tool_execution_failure(self):
        llm = MockLLM([
            "Thought: Need to calculate\nAction: calculator({\"expression\": \"bad\"})",
            "Thought: Got error\nFinal Answer: error occurred",
        ])
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        agent = ReActAgent(llm=llm, tool_registry=registry)
        result = agent.run("Calculate bad")
        assert result.answer == "error occurred"
        assert any(not step.get("success", True) for step in result.trajectory)


class TestAgentResult:
    def test_fields(self):
        from agent_framework.core.base_agent import AgentResult
        r = AgentResult(answer="ok", stopped_by_max_iterations=False, total_time_ms=100.0)
        assert r.total_time_ms == 100.0

    def test_usage_field(self):
        from agent_framework.core.base_agent import AgentResult
        u = UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        r = AgentResult(answer="ok", usage=u)
        assert r.usage.total_tokens == 15


class TestAgentEvent:
    def test_event_types(self):
        e1 = AgentEvent(type="think", content="reasoning")
        assert e1.type == "think"
        e2 = AgentEvent(type="act", content="action")
        assert e2.type == "act"
        e3 = AgentEvent(type="observe", content="obs")
        assert e3.type == "observe"
        e4 = AgentEvent(type="final", content="answer")
        assert e4.type == "final"

    def test_timestamp(self):
        import datetime
        e = AgentEvent(type="think", content="x")
        assert isinstance(e.timestamp, datetime.datetime)
