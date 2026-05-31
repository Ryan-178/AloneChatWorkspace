from typing import Any, Dict, List, Optional

from alonechat.core.base_agent import BaseAgent, AgentResult
from alonechat.core.agent_bus import AgentBus, AgentMessage, MessageType


class MultiAgentTeam:
    def __init__(self, bus: Optional[AgentBus] = None):
        self.bus = bus or AgentBus()
        self.agents: Dict[str, BaseAgent] = {}
        self.roles: Dict[str, Dict[str, str]] = {}

    def add_agent(self, agent_id: str, agent: BaseAgent, role: str = "", backstory: str = "") -> None:
        self.agents[agent_id] = agent
        self.roles[agent_id] = {"role": role, "backstory": backstory}
        self.bus.register(agent_id, agent)
        if role or backstory:
            system_parts = []
            if role:
                system_parts.append(f"Your role: {role}")
            if backstory:
                system_parts.append(f"Your backstory: {backstory}")
            agent.system_prompt = "\n".join(system_parts) + "\n\n" + getattr(agent, "system_prompt", "")

    def remove_agent(self, agent_id: str) -> None:
        self.agents.pop(agent_id, None)
        self.roles.pop(agent_id, None)
        self.bus.unregister(agent_id)

    def send(self, from_agent: str, to_agent: str, content: str, msg_type: MessageType = MessageType.QUESTION) -> AgentMessage:
        return self.bus.send(from_agent, to_agent, content, msg_type)

    def broadcast(self, from_agent: str, content: str, msg_type: MessageType = MessageType.BROADCAST) -> List[AgentMessage]:
        return self.bus.broadcast(from_agent, content, msg_type)

    def sequential_discussion(self, task: str, agent_order: Optional[List[str]] = None) -> Dict[str, Any]:
        order = agent_order or list(self.agents.keys())
        if not order:
            return {"success": False, "error": "No agents in team"}

        current_input = task
        trajectory = []

        for agent_id in order:
            agent = self.agents.get(agent_id)
            if agent is None:
                continue
            result = agent.run(current_input)
            trajectory.append({
                "agent_id": agent_id,
                "role": self.roles.get(agent_id, {}).get("role", ""),
                "input": current_input,
                "output": result.answer,
                "usage": result.usage.model_dump() if result.usage else {},
            })
            current_input = result.answer

        return {
            "success": True,
            "final_output": current_input,
            "trajectory": trajectory,
        }

    def vote_aggregation(self, task: str, agents: Optional[List[str]] = None) -> Dict[str, Any]:
        agent_ids = agents or list(self.agents.keys())
        if not agent_ids:
            return {"success": False, "error": "No agents in team"}

        outputs = []
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if agent is None:
                continue
            result = agent.run(task)
            outputs.append({
                "agent_id": agent_id,
                "role": self.roles.get(agent_id, {}).get("role", ""),
                "output": result.answer,
                "usage": result.usage.model_dump() if result.usage else {},
            })

        return {
            "success": True,
            "outputs": outputs,
            "final_output": outputs[-1]["output"] if outputs else "",
        }
