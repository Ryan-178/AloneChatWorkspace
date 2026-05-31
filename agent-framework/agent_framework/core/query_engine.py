"""
查询引擎 / Query Engine

参考 claude-code-claude 的 query 模式
Reference: claude-code-claude's query pattern

实现流式查询循环和工具执行
Implements streaming query loop and tool execution
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from enum import Enum

from .tool import Tool, ToolResult, ToolUseContext, Tools

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """
    消息角色 / Message Role
    
    对话中的消息角色
    Message role in conversation
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """
    消息 / Message
    
    对话中的单条消息
    Single message in conversation
    """
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamEvent:
    """
    流事件 / Stream Event
    
    查询过程中的流事件
    Stream event during query
    """
    type: str  # 'assistant', 'tool_use', 'tool_result', 'error', 'system', 'progress'
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryParams:
    """
    查询参数 / Query Parameters
    
    执行查询所需的参数
    Parameters needed to execute a query
    """
    messages: List[Message]
    system_prompt: str = ""
    tools: Tools = field(default_factory=list)
    model: Optional[str] = None
    max_turns: Optional[int] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = True


@dataclass
class QueryResult:
    """
    查询结果 / Query Result
    
    查询执行完成后的结果
    Result after query execution completes
    """
    messages: List[Message]
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None


class ModelClient(ABC):
    """
    模型客户端基类 / Model Client Base Class
    
    定义与 LLM 交互的接口
    Defines interface for LLM interaction
    """
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> Message:
        """
        同步聊天 / Synchronous chat
        
        Args:
            messages: 消息列表 / Message list
            model: 模型名称 / Model name
            
        Returns:
            助手消息 / Assistant message
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式聊天 / Streaming chat
        
        Args:
            messages: 消息列表 / Message list
            model: 模型名称 / Model name
            
        Yields:
            流事件 / Stream events
        """
        pass


class ToolExecutor(ABC):
    """
    工具执行器基类 / Tool Executor Base Class
    
    定义工具执行的接口
    Defines interface for tool execution
    """
    
    @abstractmethod
    async def execute(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: ToolUseContext,
        tools: Tools
    ) -> ToolResult:
        """
        执行工具 / Execute tool
        
        Args:
            tool_name: 工具名称 / Tool name
            tool_input: 工具输入 / Tool input
            context: 使用上下文 / Use context
            tools: 可用工具列表 / Available tools
            
        Returns:
            工具结果 / Tool result
        """
        pass


class QueryEngine:
    """
    查询引擎 / Query Engine
    
    执行查询循环，处理工具调用
    Executes query loop, handles tool calls
    
    使用示例 / Usage Example:
        engine = QueryEngine(model_client, tool_executor)
        
        async for event in engine.query(params):
            if event.type == 'assistant':
                print(event.data)
            elif event.type == 'tool_result':
                print(f"Tool result: {event.data}")
    """
    
    def __init__(
        self,
        model_client: ModelClient,
        tool_executor: Optional[ToolExecutor] = None
    ):
        self._model_client = model_client
        self._tool_executor = tool_executor
    
    async def query(self, params: QueryParams) -> AsyncGenerator[StreamEvent, None]:
        """
        执行查询 / Execute query
        
        执行查询循环，处理模型响应和工具调用
        Execute query loop, handle model responses and tool calls
        
        Args:
            params: 查询参数 / Query parameters
            
        Yields:
            流事件 / Stream events
        """
        messages = params.messages.copy()
        turn_count = 0
        
        while True:
            turn_count += 1
            
            # 检查最大轮数 / Check max turns
            if params.max_turns and turn_count > params.max_turns:
                yield StreamEvent(
                    type='system',
                    data=f'Max turns ({params.max_turns}) reached'
                )
                break
            
            # 调用模型 / Call model
            yield StreamEvent(type='progress', data={'turn': turn_count, 'phase': 'model_call'})
            
            try:
                if params.stream:
                    # 流式调用 / Streaming call
                    assistant_message = None
                    async for event in self._model_client.chat_stream(
                        messages=messages,
                        model=params.model or 'default',
                        temperature=params.temperature,
                        max_tokens=params.max_tokens
                    ):
                        yield event
                        if event.type == 'assistant':
                            assistant_message = event.data
                else:
                    # 同步调用 / Synchronous call
                    assistant_message = await self._model_client.chat(
                        messages=messages,
                        model=params.model or 'default',
                        temperature=params.temperature,
                        max_tokens=params.max_tokens
                    )
                    yield StreamEvent(type='assistant', data=assistant_message)
                
                if assistant_message is None:
                    yield StreamEvent(type='error', data='No response from model')
                    break
                
                messages.append(assistant_message)
                
            except Exception as e:
                logger.error(f"Model call failed: {e}")
                yield StreamEvent(type='error', data=str(e))
                break
            
            # 检查是否有工具调用 / Check for tool calls
            tool_calls = self._extract_tool_calls(assistant_message)
            if not tool_calls:
                # 没有工具调用，查询完成 / No tool calls, query complete
                break
            
            # 执行工具调用 / Execute tool calls
            if self._tool_executor is None:
                yield StreamEvent(
                    type='error',
                    data='Tool calls requested but no tool executor configured'
                )
                break
            
            for tool_call in tool_calls:
                tool_name = tool_call.get('name', '')
                tool_input = tool_call.get('input', {})
                tool_id = tool_call.get('id', '')
                
                yield StreamEvent(
                    type='tool_use',
                    data={'id': tool_id, 'name': tool_name, 'input': tool_input}
                )
                
                try:
                    result = await self._tool_executor.execute(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        context=ToolUseContext(),
                        tools=params.tools
                    )
                    
                    yield StreamEvent(
                        type='tool_result',
                        data={'id': tool_id, 'result': result}
                    )
                    
                    # 添加工具结果到消息 / Add tool result to messages
                    messages.append(Message(
                        role=MessageRole.TOOL,
                        content=str(result.data),
                        tool_call_id=tool_id,
                        name=tool_name
                    ))
                    
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    yield StreamEvent(
                        type='tool_result',
                        data={'id': tool_id, 'error': str(e)}
                    )
                    
                    messages.append(Message(
                        role=MessageRole.TOOL,
                        content=f"Error: {e}",
                        tool_call_id=tool_id,
                        name=tool_name
                    ))
    
    def _extract_tool_calls(self, message: Message) -> List[Dict[str, Any]]:
        """
        提取工具调用 / Extract tool calls
        
        从助手消息中提取工具调用
        Extract tool calls from assistant message
        
        Args:
            message: 助手消息 / Assistant message
            
        Returns:
            工具调用列表 / Tool call list
        """
        if message.tool_calls:
            return message.tool_calls
        
        # 尝试从内容解析 / Try to parse from content
        # 这里可以根据不同的模型格式实现解析逻辑
        return []


class SimpleQueryEngine:
    """
    简单查询引擎 / Simple Query Engine
    
    简化版查询引擎，不包含工具调用
    Simplified query engine without tool calls
    
    使用示例 / Usage Example:
        engine = SimpleQueryEngine(model_client)
        response = await engine.query("Hello!")
    """
    
    def __init__(self, model_client: ModelClient):
        self._model_client = model_client
    
    async def query(
        self,
        user_input: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        history: Optional[List[Message]] = None
    ) -> str:
        """
        执行查询 / Execute query
        
        Args:
            user_input: 用户输入 / User input
            system_prompt: 系统提示 / System prompt
            model: 模型名称 / Model name
            history: 历史消息 / Message history
            
        Returns:
            助手回复 / Assistant response
        """
        messages = []
        
        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        
        if history:
            messages.extend(history)
        
        messages.append(Message(role=MessageRole.USER, content=user_input))
        
        response = await self._model_client.chat(
            messages=messages,
            model=model or 'default'
        )
        
        return response.content
    
    async def query_stream(
        self,
        user_input: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        history: Optional[List[Message]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式查询 / Streaming query
        
        Args:
            user_input: 用户输入 / User input
            system_prompt: 系统提示 / System prompt
            model: 模型名称 / Model name
            history: 历史消息 / Message history
            
        Yields:
            响应片段 / Response chunks
        """
        messages = []
        
        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        
        if history:
            messages.extend(history)
        
        messages.append(Message(role=MessageRole.USER, content=user_input))
        
        async for event in self._model_client.chat_stream(
            messages=messages,
            model=model or 'default'
        ):
            if event.type == 'assistant' and isinstance(event.data, Message):
                yield event.data.content
