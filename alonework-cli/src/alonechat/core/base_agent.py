"""
Agent 基类模块 - Base Agent Module
定义Agent的核心抽象基类和基础数据结构
Defines the core abstract base class and basic data structures for Agents
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from alonechat.core.base_llm import BaseLLM, Message, UsageInfo
from alonechat.core.base_tool import ToolResult
from alonechat.core.base_memory import BaseMemory


class AgentEvent(BaseModel):
    """
    Agent事件 - Agent Event
    表示Agent执行过程中的一个事件
    Represents an event during agent execution
    """
    type: str = Field(..., description="事件类型: think, act, observe, final / Event type: think, act, observe, final")
    content: str = Field(..., description="事件内容 / Event content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """
    Agent执行结果 - Agent Execution Result
    包含最终答案和执行轨迹
    Contains the final answer and execution trajectory
    """
    answer: str = Field(default="", description="最终答案 / Final answer")
    trajectory: List[Dict[str, Any]] = Field(default_factory=list, description="执行轨迹 / Execution trajectory")
    usage: UsageInfo = Field(default_factory=UsageInfo)
    stopped_by_max_iterations: bool = Field(default=False)
    total_time_ms: float = Field(default=0.0)


class BaseAgent(ABC):
    """
    Agent抽象基类 - Abstract Base Agent Class
    定义Agent的核心接口：感知、规划、行动、反思
    Defines the core interface for agents: perceive, plan, act, reflect
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 10,
        name: str = "agent",
    ):
        """
        初始化Agent - Initialize Agent
        
        Args:
            llm: 语言模型实例 / Language model instance
            memory: 记忆模块 / Memory module
            max_iterations: 最大迭代次数 / Maximum iteration count
            name: Agent名称 / Agent name
        """
        self.llm = llm
        self.memory = memory
        self.max_iterations = max_iterations
        self.name = name

    @abstractmethod
    def perceive(self, task: str) -> Dict[str, Any]:
        """
        感知阶段 - Perceive Phase
        理解任务并收集相关信息
        Understand the task and gather relevant information
        """
        pass

    @abstractmethod
    def plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划阶段 - Plan Phase
        制定执行计划
        Create an execution plan
        """
        pass

    @abstractmethod
    def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        行动阶段 - Act Phase
        执行计划中的动作
        Execute actions from the plan
        """
        pass

    @abstractmethod
    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        反思阶段 - Reflect Phase
        评估结果并决定下一步
        Evaluate results and decide next steps
        """
        pass

    @abstractmethod
    def run(self, task: str) -> AgentResult:
        """
        同步执行任务 - Run Task Synchronously
        完整执行一个任务并返回结果
        Execute a task completely and return the result
        """
        pass

    @abstractmethod
    async def run_stream(self, task: str) -> AsyncGenerator[AgentEvent, None]:
        """
        流式执行任务 - Run Task with Streaming
        逐步产生执行事件
        Yield execution events step by step
        """
        pass
