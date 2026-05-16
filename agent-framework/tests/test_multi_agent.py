import pytest
from unittest.mock import MagicMock

from agent_framework.agent.multi_agent import MultiAgentTeam
from agent_framework.agent.react_agent import ReActAgent
from agent_framework.core.agent_bus import MessageType


class MockLLM:
    def __init__(self, response="mock answer"):
        self.response = response

    def chat(self, messages, config=None):
        from agent_framework.core.base_llm import Message
        return Message(role="assistant", content=self.response)

    def get_total_usage(self):
        from agent_framework.core.base_llm import UsageInfo
        return UsageInfo()

    def record_usage(self, usage):
        pass


class TestMultiAgentTeam:
    def test_add_and_remove_agent(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("agent1", agent, role="planner", backstory="You plan things")
        assert "agent1" in team.agents
        assert team.roles["agent1"]["role"] == "planner"
        assert team.roles["agent1"]["backstory"] == "You plan things"
        team.remove_agent("agent1")
        assert "agent1" not in team.agents
        assert "agent1" not in team.roles

    def test_add_agent_injects_role(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("a", agent, role="coder", backstory="You code")
        assert "Your role: coder" in agent.system_prompt
        assert "Your backstory: You code" in agent.system_prompt

    def test_send_message(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("a", agent)
        team.add_agent("b", agent)
        msg = team.send("a", "b", "hello")
        assert msg.from_agent == "a"
        assert msg.to_agent == "b"
        assert msg.content == "hello"
        assert msg.type == MessageType.QUESTION
        received = team.bus.receive("b")
        assert len(received) == 1

    def test_send_with_type(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("a", agent)
        team.add_agent("b", agent)
        msg = team.send("a", "b", "result", msg_type=MessageType.RESULT)
        assert msg.type == MessageType.RESULT

    def test_broadcast(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("a", agent)
        team.add_agent("b", agent)
        team.add_agent("c", agent)
        msgs = team.broadcast("a", "alert")
        assert len(msgs) == 2

    def test_broadcast_with_type(self):
        team = MultiAgentTeam()
        agent = ReActAgent(llm=MockLLM())
        team.add_agent("a", agent)
        team.add_agent("b", agent)
        msgs = team.broadcast("a", "alert", msg_type=MessageType.ERROR)
        assert msgs[0].type == MessageType.ERROR

    def test_sequential_discussion(self):
        team = MultiAgentTeam()
        agent1 = ReActAgent(llm=MockLLM("answer1"))
        agent2 = ReActAgent(llm=MockLLM("answer2"))
        team.add_agent("a1", agent1)
        team.add_agent("a2", agent2)
        result = team.sequential_discussion("task")
        assert result["success"] is True
        assert result["final_output"] == "answer2"
        assert len(result["trajectory"]) == 2
        assert result["trajectory"][0]["agent_id"] == "a1"
        assert result["trajectory"][1]["agent_id"] == "a2"

    def test_sequential_discussion_empty(self):
        team = MultiAgentTeam()
        result = team.sequential_discussion("task")
        assert result["success"] is False
        assert "No agents" in result["error"]

    def test_vote_aggregation(self):
        team = MultiAgentTeam()
        agent1 = ReActAgent(llm=MockLLM("vote A"))
        agent2 = ReActAgent(llm=MockLLM("vote B"))
        team.add_agent("a1", agent1)
        team.add_agent("a2", agent2)
        result = team.vote_aggregation("task")
        assert result["success"] is True
        assert len(result["outputs"]) == 2
        outputs = [o["output"] for o in result["outputs"]]
        assert "vote A" in outputs
        assert "vote B" in outputs

    def test_vote_aggregation_empty(self):
        team = MultiAgentTeam()
        result = team.vote_aggregation("task")
        assert result["success"] is False
        assert "No agents" in result["error"]

    def test_vote_with_subset(self):
        team = MultiAgentTeam()
        agent1 = ReActAgent(llm=MockLLM("A"))
        agent2 = ReActAgent(llm=MockLLM("B"))
        agent3 = ReActAgent(llm=MockLLM("C"))
        team.add_agent("a1", agent1)
        team.add_agent("a2", agent2)
        team.add_agent("a3", agent3)
        result = team.vote_aggregation("task", agents=["a1", "a3"])
        assert result["success"] is True
        assert len(result["outputs"]) == 2
