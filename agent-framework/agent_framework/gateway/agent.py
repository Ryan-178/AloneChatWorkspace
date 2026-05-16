"""
Agent 核心实现
ReAct 模式 Agent - 思考、行动、观察循环
"""
import json
import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field

from agent_framework.core.base_llm import BaseLLM, Message, Chunk, LLMConfig
from agent_framework.llm.litellm_provider import LiteLLMProvider
from agent_framework.core.base_tool import ToolResult
from .tools import ToolExecutor

ToolRegistry = ToolExecutor
get_tool_registry = lambda: ToolExecutor()


class AgentState(str, Enum):
    """Agent执行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"


class AgentStep(BaseModel):
    """Agent执行的一步"""
    step: int = Field(..., description="Step number")
    state: AgentState = Field(..., description="Current state")
    thought: Optional[str] = Field(default=None, description="Agent's thought")
    action: Optional[Dict[str, Any]] = Field(default=None, description="Action taken")
    observation: Optional[str] = Field(default=None, description="Observation result")


class AgentResult(BaseModel):
    """Agent执行结果"""
    success: bool = Field(default=True)
    final_answer: Optional[str] = Field(default=None)
    steps: List[AgentStep] = Field(default_factory=list)
    total_tokens: int = Field(default=0)
    execution_time_ms: float = Field(default=0.0)
    error: Optional[str] = Field(default=None)


DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant that can use tools to accomplish tasks.

You follow this process:
1. THOUGHT: First, think about what you need to do and decide if you need to use a tool
2. ACTION: If you need a tool, call it; otherwise, give your final answer
3. OBSERVATION: Observe the tool's output
4. Repeat until you can give a final answer

When you want to give a final answer, just respond with the answer naturally without using tools.

Always respond in the same language as the user's question."""


class ReActAgent:
    """ReAct模式 Agent - 思考、行动、观察循环"""
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
    ):
        self.llm = llm or LiteLLMProvider()
        self.tool_registry = tool_registry or get_tool_registry()
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_iterations = max_iterations
        self.messages: List[Message] = []
    
    def reset(self):
        """重置Agent状态"""
        self.messages = []
    
    async def run(self, user_input: str) -> AgentResult:
        """运行Agent，返回完整结果"""
        import time
        start_time = time.time()
        
        self.reset()
        steps: List[AgentStep] = []
        
        # 添加系统提示和用户输入
        self.messages.append(Message(role="system", content=self.system_prompt))
        self.messages.append(Message(role="user", content=user_input))
        
        try:
            for i in range(self.max_iterations):
                # Step 1: THINK - 让LLM思考
                steps.append(AgentStep(step=i+1, state=AgentState.THINKING))
                
                # 获取工具定义
                tools = self.tool_registry.get_all_openai_format()
                
                # 调用LLM
                response = self.llm.chat(
                    self.messages,
                    config=LLMConfig(temperature=0.7),
                )
                
                # 更新消息历史
                self.messages.append(response)
                
                # 检查是否有工具调用
                if response.tool_calls and len(response.tool_calls) > 0:
                    # 有工具调用 - 进入ACT阶段
                    steps[-1].thought = "I need to use a tool."
                    steps[-1].action = response.tool_calls[0]
                    steps[-1].state = AgentState.ACTING
                    
                    # 执行工具
                    tool_call = response.tool_calls[0]
                    function_name = tool_call.get("function", {}).get("name", "")
                    arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                    
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Step 2: ACT - 执行工具
                    tool_result = await self.tool_registry.execute_tool(function_name, **arguments)
                    
                    # Step 3: OBSERVE - 观察结果
                    steps.append(AgentStep(step=i+1, state=AgentState.OBSERVING))
                    
                    if tool_result.success:
                        observation = json.dumps(tool_result.data, ensure_ascii=False)
                    else:
                        observation = f"Error: {tool_result.error}"
                    
                    steps[-1].observation = observation
                    
                    # 添加工具响应到消息历史
                    self.messages.append(Message(
                        role="tool",
                        content=observation,
                        tool_call_id=tool_call.get("id", ""),
                        name=function_name,
                    ))
                    
                else:
                    # 没有工具调用 - 结束
                    final_answer = response.content or "I'm not sure how to help with that."
                    steps[-1].thought = "I can give a final answer."
                    steps[-1].state = AgentState.FINISHED
                    
                    total_time = (time.time() - start_time) * 1000
                    total_tokens = self.llm.get_total_usage().total_tokens
                    
                    return AgentResult(
                        success=True,
                        final_answer=final_answer,
                        steps=steps,
                        total_tokens=total_tokens,
                        execution_time_ms=total_time,
                    )
            
            # 超过最大迭代次数
            total_time = (time.time() - start_time) * 1000
            total_tokens = self.llm.get_total_usage().total_tokens
            
            return AgentResult(
                success=False,
                final_answer="I couldn't complete the task within the maximum number of iterations.",
                steps=steps,
                total_tokens=total_tokens,
                execution_time_ms=total_time,
                error="Max iterations reached.",
            )
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            total_tokens = self.llm.get_total_usage().total_tokens
            
            return AgentResult(
                success=False,
                final_answer=None,
                steps=steps,
                total_tokens=total_tokens,
                execution_time_ms=total_time,
                error=str(e),
            )
    
    async def run_stream(self, user_input: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式运行Agent，产生事件流"""
        import time
        start_time = time.time()
        
        self.reset()
        
        # 添加系统提示和用户输入
        self.messages.append(Message(role="system", content=self.system_prompt))
        self.messages.append(Message(role="user", content=user_input))
        
        try:
            for i in range(self.max_iterations):
                # 发出思考状态
                yield {
                    "type": "thinking",
                    "step": i+1,
                    "message": "Thinking...",
                }
                
                # 首先进行非流式调用以获取完整响应，包括可能的tool_calls
                response = self.llm.chat(self.messages)
                self.messages.append(response)
                
                if response.tool_calls and len(response.tool_calls) > 0:
                    # 有工具调用，先流式输出思考内容（如果有）
                    if response.content:
                        yield {
                            "type": "content",
                            "content": response.content,
                        }
                    
                    # 执行工具
                    yield {
                        "type": "acting",
                        "message": "Executing tool...",
                    }
                    
                    tool_call = response.tool_calls[0]
                    function_name = tool_call.get("function", {}).get("name", "")
                    arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                    
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    tool_result = await self.tool_registry.execute_tool(function_name, **arguments)
                    
                    if tool_result.success:
                        observation = json.dumps(tool_result.data, ensure_ascii=False)
                    else:
                        observation = f"Error: {tool_result.error}"
                    
                    yield {
                        "type": "observation",
                        "tool": function_name,
                        "result": observation,
                    }
                    
                    # 添加工具响应
                    self.messages.append(Message(
                        role="tool",
                        content=observation,
                        tool_call_id=tool_call.get("id", ""),
                        name=function_name,
                    ))
                    
                else:
                    # 没有工具调用，流式输出最终答案
                    # 为了提供用户体验，我们模拟流式输出
                    final_content = response.content or "I'm not sure how to help with that."
                    chunk_size = 3
                    for j in range(0, len(final_content), chunk_size):
                        chunk = final_content[j:j+chunk_size]
                        yield {
                            "type": "content",
                            "content": chunk,
                        }
                        await asyncio.sleep(0.01)  # 短暂延迟模拟真实流式
                    
                    # 完成
                    total_time = (time.time() - start_time) * 1000
                    total_tokens = self.llm.get_total_usage().total_tokens
                    
                    yield {
                        "type": "finished",
                        "final_answer": final_content,
                        "total_tokens": total_tokens,
                        "execution_time_ms": total_time,
                    }
                    return
            
            # 超过最大迭代
            total_time = (time.time() - start_time) * 1000
            yield {
                "type": "error",
                "message": "Max iterations reached.",
                "execution_time_ms": total_time,
            }
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            yield {
                "type": "error",
                "message": str(e),
                "execution_time_ms": total_time,
            }
