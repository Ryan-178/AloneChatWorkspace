import asyncio
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import AgentSession, User
from agent_framework.llm.litellm_provider import LiteLLMProvider
from agent_framework.agent.react_agent import ReActAgent
from agent_framework.agent.multi_agent import MultiAgentTeam, AgentConfig
from agent_framework.core.agent_bus import AgentBus
from agent_framework.tools.registry import ToolRegistry
from agent_framework.tools.builtin.web_search import WebSearchTool
from agent_framework.tools.builtin.calculator import CalculatorTool
from agent_framework.tools.builtin.current_time import CurrentTimeTool
from agent_framework.core.base_llm import LLMConfig
from config import get_settings

settings = get_settings()


def get_llm_config(model: Optional[str] = None) -> LLMConfig:
    return LLMConfig(
        model=model or getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
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


async def run_multi_agent_team(
    user_id: str,
    session_id: str,
    user_message: str,
    manager: "ConnectionManager",
    agent_ids: Optional[List[str]] = None,
):
    from database import AsyncSessionLocal
    from agent_service import get_session_messages, save_agent_message

    async with AsyncSessionLocal() as db:
        session_result = await db.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            await manager.send_personal_message({
                "type": "agent_response",
                "payload": {
                    "sender_id": "__agent__",
                    "content": f"Session {session_id} not found",
                    "session_id": session_id,
                }
            }, user_id)
            return

        await save_agent_message(db, session_id, "user", user_message)

        history = await get_session_messages(db, session_id, limit=20)

        llm = LiteLLMProvider(get_llm_config())
        registry = create_tool_registry()

        agent_configs = [
            AgentConfig(
                name="researcher",
                system_prompt="You are a research specialist. Your job is to gather information and provide detailed findings.",
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                tools=["web_search", "current_time"],
            ),
            AgentConfig(
                name="analyst",
                system_prompt="You are an analytical specialist. Your job is to analyze data, perform calculations, and draw conclusions.",
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                tools=["calculator", "current_time"],
            ),
            AgentConfig(
                name="coordinator",
                system_prompt="You are a coordinator. Your job is to synthesize information from other agents and provide a final, coherent response.",
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                tools=["current_time"],
            ),
        ]

        if agent_ids:
            agent_configs = [c for c in agent_configs if c.name in agent_ids]

        team = MultiAgentTeam(
            agents=agent_configs,
            llm=llm,
            tool_registry=registry,
        )

        await manager.send_personal_message({
            "type": "agent_stream",
            "payload": {
                "event": "thinking",
                "content": "Multi-agent team is collaborating...",
                "session_id": session_id,
            }
        }, user_id)

        try:
            result = team.run(user_message)

            for step in result.trajectory:
                if step.get("type") == "agent_think":
                    await manager.send_personal_message({
                        "type": "agent_stream",
                        "payload": {
                            "event": "thinking",
                            "content": f"[{step.get('agent')}] {step.get('content', '')}",
                            "session_id": session_id,
                        }
                    }, user_id)
                elif step.get("type") == "agent_act":
                    await manager.send_personal_message({
                        "type": "agent_stream",
                        "payload": {
                            "event": "tool_call",
                            "content": f"[{step.get('agent')}] {step.get('content', '')}",
                            "session_id": session_id,
                        }
                    }, user_id)

            final_answer = result.answer

            await manager.send_personal_message({
                "type": "agent_stream",
                "payload": {
                    "event": "final",
                    "content": final_answer,
                    "session_id": session_id,
                }
            }, user_id)

            await save_agent_message(
                db,
                session_id,
                "agent",
                final_answer,
                metadata={
                    "multi_agent": True,
                    "agents": [c.name for c in agent_configs],
                },
            )

        except Exception as e:
            await manager.send_personal_message({
                "type": "agent_stream",
                "payload": {
                    "event": "error",
                    "content": str(e),
                    "session_id": session_id,
                }
            }, user_id)
