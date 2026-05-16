from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from agent_framework.core.base_llm import BaseLLM, Message, UsageInfo
from agent_framework.core.base_tool import ToolResult
from agent_framework.core.base_memory import BaseMemory


class AgentEvent(BaseModel):
    type: str = Field(..., description="Event type: think, act, observe, final")
    content: str = Field(..., description="Event content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    answer: str = Field(default="", description="Final answer")
    trajectory: List[Dict[str, Any]] = Field(default_factory=list, description="Execution trajectory")
    usage: UsageInfo = Field(default_factory=UsageInfo)
    stopped_by_max_iterations: bool = Field(default=False)
    total_time_ms: float = Field(default=0.0)


class BaseAgent(ABC):
    def __init__(
        self,
        llm: BaseLLM,
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 10,
        name: str = "agent",
    ):
        self.llm = llm
        self.memory = memory
        self.max_iterations = max_iterations
        self.name = name

    @abstractmethod
    def perceive(self, task: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run(self, task: str) -> AgentResult:
        pass

    @abstractmethod
    async def run_stream(self, task: str) -> AsyncGenerator[AgentEvent, None]:
        pass
