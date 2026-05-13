from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"
    RESULT = "result"
    ERROR = "error"
    BROADCAST = "broadcast"


class AgentMessage(BaseModel):
    id: str = Field(..., description="Message ID")
    from_agent: str = Field(..., alias="from", description="Sender agent ID")
    to_agent: str = Field(..., alias="to", description="Recipient agent ID")
    content: str = Field(..., description="Message content")
    type: MessageType = Field(default=MessageType.QUESTION)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class AgentBus:
    def __init__(self):
        self._messages: List[AgentMessage] = []
        self._agents: Dict[str, Any] = {}

    def register(self, agent_id: str, agent: Any) -> None:
        self._agents[agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def send(self, from_agent: str, to_agent: str, content: str, msg_type: MessageType = MessageType.QUESTION, metadata: Optional[Dict[str, Any]] = None) -> AgentMessage:
        import uuid
        msg = AgentMessage(
            id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            type=msg_type,
            metadata=metadata or {},
        )
        self._messages.append(msg)
        return msg

    def broadcast(self, from_agent: str, content: str, msg_type: MessageType = MessageType.BROADCAST, metadata: Optional[Dict[str, Any]] = None) -> List[AgentMessage]:
        import uuid
        messages = []
        for agent_id in self._agents:
            if agent_id != from_agent:
                msg = AgentMessage(
                    id=str(uuid.uuid4()),
                    from_agent=from_agent,
                    to_agent=agent_id,
                    content=content,
                    type=msg_type,
                    metadata=metadata or {},
                )
                self._messages.append(msg)
                messages.append(msg)
        return messages

    def receive(self, agent_id: str, limit: int = 100) -> List[AgentMessage]:
        msgs = [m for m in self._messages if m.to_agent == agent_id]
        return msgs[-limit:]

    def get_conversation(self, agent_a: str, agent_b: str, limit: int = 100) -> List[AgentMessage]:
        msgs = [
            m for m in self._messages
            if (m.from_agent == agent_a and m.to_agent == agent_b)
            or (m.from_agent == agent_b and m.to_agent == agent_a)
        ]
        return msgs[-limit:]
