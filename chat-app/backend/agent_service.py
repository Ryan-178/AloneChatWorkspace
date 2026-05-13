import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from models import AgentSession, AgentMessage
from agent_framework.llm.litellm_provider import LiteLLMProvider
from agent_framework.agent.react_agent import ReActAgent
from agent_framework.tools.registry import ToolRegistry
from agent_framework.tools.builtin.web_search import WebSearchTool
from agent_framework.tools.builtin.calculator import CalculatorTool
from agent_framework.tools.builtin.current_time import CurrentTimeTool
from agent_framework.core.base_llm import LLMConfig
from config import get_settings

settings = get_settings()


def get_llm_config() -> LLMConfig:
    return LLMConfig(
        model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
        api_key=getattr(settings, "LLM_API_KEY", None),
        api_base=getattr(settings, "LLM_API_BASE", None),
        temperature=0.7,
        max_tokens=4096,
    )


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(WebSearchTool())
    registry.register(CalculatorTool())
    registry.register(CurrentTimeTool())
    return registry


async def get_or_create_agent_session(
    db: AsyncSession,
    user_id: str,
    conversation_id: Optional[str] = None,
    title: Optional[str] = None,
) -> AgentSession:
    if conversation_id:
        result = await db.execute(
            select(AgentSession).where(
                and_(
                    AgentSession.user_id == user_id,
                    AgentSession.conversation_id == conversation_id,
                    AgentSession.status == "active",
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    session = AgentSession(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title or "New Agent Session",
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    limit: int = 20,
) -> List[AgentMessage]:
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.session_id == session_id)
        .order_by(desc(AgentMessage.created_at))
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))


async def save_agent_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentMessage:
    message = AgentMessage(
        session_id=session_id,
        role=role,
        content=content,
        tool_calls=json.dumps(tool_calls) if tool_calls else None,
        tool_results=json.dumps(tool_results) if tool_results else None,
        metadata=json.dumps(metadata) if metadata else None,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def run_agent_task(
    db: AsyncSession,
    session_id: str,
    user_message: str,
) -> str:
    from agent_framework.core.base_llm import Message

    session_result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise ValueError(f"Agent session {session_id} not found")

    await save_agent_message(db, session_id, "user", user_message)

    history = await get_session_messages(db, session_id, limit=20)

    llm = LiteLLMProvider(get_llm_config())
    registry = create_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=registry)

    messages: List[Message] = [Message(role="system", content=agent.system_prompt)]
    for msg in history:
        if msg.role == "user":
            messages.append(Message(role="user", content=msg.content))
        elif msg.role == "agent":
            messages.append(Message(role="assistant", content=msg.content))
    messages.append(Message(role="user", content=user_message))

    result = agent.run(user_message)

    tool_calls = None
    tool_results = None
    if result.trajectory:
        calls = []
        results = []
        for step in result.trajectory:
            if step.get("type") == "action":
                calls.append({
                    "tool": step.get("tool"),
                    "params": step.get("params"),
                })
                results.append({
                    "observation": step.get("observation"),
                    "success": step.get("success"),
                })
        if calls:
            tool_calls = calls
        if results:
            tool_results = results

    await save_agent_message(
        db,
        session_id,
        "agent",
        result.answer,
        tool_calls=tool_calls,
        tool_results=tool_results,
        metadata={
            "usage": result.usage.model_dump() if result.usage else {},
            "stopped_by_max_iterations": result.stopped_by_max_iterations,
            "total_time_ms": result.total_time_ms,
        },
    )

    session.updated_at = datetime.utcnow()
    await db.commit()

    return result.answer


async def run_agent_task_stream(
    db: AsyncSession,
    session_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    from agent_framework.core.base_llm import Message

    session_result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise ValueError(f"Agent session {session_id} not found")

    await save_agent_message(db, session_id, "user", user_message)

    history = await get_session_messages(db, session_id, limit=20)

    llm = LiteLLMProvider(get_llm_config())
    registry = create_tool_registry()
    agent = ReActAgent(llm=llm, tool_registry=registry)

    messages: List[Message] = [Message(role="system", content=agent.system_prompt)]
    for msg in history:
        if msg.role == "user":
            messages.append(Message(role="user", content=msg.content))
        elif msg.role == "agent":
            messages.append(Message(role="assistant", content=msg.content))
    messages.append(Message(role="user", content=user_message))

    yield {"event": "thinking", "content": "Agent is thinking..."}

    final_answer = ""
    tool_calls = []
    tool_results = []

    async for event in agent.run_stream(user_message):
        if event.type == "think":
            yield {"event": "thinking", "content": event.content}
        elif event.type == "act":
            yield {"event": "tool_call", "content": event.content}
            tool_calls.append({"action": event.content})
        elif event.type == "observe":
            yield {"event": "tool_result", "content": event.content}
            tool_results.append({"observation": event.content})
        elif event.type == "final":
            final_answer = event.content
            yield {"event": "final", "content": event.content}

    await save_agent_message(
        db,
        session_id,
        "agent",
        final_answer,
        tool_calls=tool_calls if tool_calls else None,
        tool_results=tool_results if tool_results else None,
        metadata={
            "streamed": True,
        },
    )

    session.updated_at = datetime.utcnow()
    await db.commit()
