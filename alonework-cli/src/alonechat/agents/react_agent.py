import time
import json
import re
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from alonechat.core.base_agent import BaseAgent, AgentResult, AgentEvent
from alonechat.core.base_llm import Message, UsageInfo
from alonechat.core.base_tool import ToolResult
from alonechat.tools.registry import ToolRegistry


class AgentCallback:
    def on_think(self, content: str) -> None:
        pass

    def on_act(self, content: str) -> None:
        pass

    def on_observe(self, content: str) -> None:
        pass

    def on_final(self, content: str) -> None:
        pass


class ReActAgent(BaseAgent):
    def __init__(
        self,
        llm,
        tool_registry: Optional[ToolRegistry] = None,
        memory=None,
        max_iterations: int = 10,
        name: str = "react_agent",
        system_prompt: Optional[str] = None,
    ):
        super().__init__(llm, memory, max_iterations, name)
        self.tool_registry = tool_registry or ToolRegistry()
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.callbacks: List[AgentCallback] = []

    def _default_system_prompt(self) -> str:
        tools = self.tool_registry.list_tools()
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in tools
        )
        return (
            "You are a helpful assistant that can use tools to solve problems.\n"
            "Available tools:\n" + tool_descriptions + "\n\n"
            "When you need to use a tool, respond with:\n"
            "Thought: <your reasoning>\n"
            "Action: <tool_name>(<json_params>)\n\n"
            "When you have the final answer, respond with:\n"
            "Thought: <your reasoning>\n"
            "Final Answer: <your answer>\n\n"
            "Always include 'Thought:' before every step."
        )

    def add_callback(self, callback: AgentCallback) -> None:
        self.callbacks.append(callback)

    def _emit(self, event_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        for cb in self.callbacks:
            if event_type == "think":
                cb.on_think(content)
            elif event_type == "act":
                cb.on_act(content)
            elif event_type == "observe":
                cb.on_observe(content)
            elif event_type == "final":
                cb.on_final(content)

    def perceive(self, task: str) -> Dict[str, Any]:
        return {"task": task}

    def plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return context

    def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return plan

    def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def _parse_response(self, text: str) -> Dict[str, Any]:
        thought_match = re.search(r"Thought:\s*(.*?)(?=\n(?:Action|Final Answer):|$)", text, re.DOTALL | re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""

        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        final_match = re.search(r"Final Answer:\s*(.+?)(?:\n|$)", text, re.DOTALL | re.IGNORECASE)

        if final_match:
            return {"type": "final", "thought": thought, "answer": final_match.group(1).strip()}

        if action_match:
            action_str = action_match.group(1).strip()
            tool_match = re.match(r"(\w+)\s*\((.*)\)", action_str, re.DOTALL)
            if tool_match:
                tool_name = tool_match.group(1)
                params_str = tool_match.group(2).strip()
                try:
                    params = json.loads(params_str) if params_str else {}
                except json.JSONDecodeError:
                    params = {"query": params_str}
                return {"type": "action", "thought": thought, "tool": tool_name, "params": params}

        return {"type": "final", "thought": thought, "answer": text.strip()}

    def run(self, task: str) -> AgentResult:
        start_time = time.time()
        trajectory: List[Dict[str, Any]] = []
        messages: List[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=task),
        ]

        for iteration in range(self.max_iterations):
            response = self.llm.chat(messages)
            parsed = self._parse_response(response.content)

            step = {
                "iteration": iteration + 1,
                "type": parsed["type"],
                "thought": parsed.get("thought", ""),
            }

            if parsed["type"] == "final":
                step["answer"] = parsed["answer"]
                trajectory.append(step)
                self._emit("final", parsed["answer"])
                total_time_ms = (time.time() - start_time) * 1000
                return AgentResult(
                    answer=parsed["answer"],
                    trajectory=trajectory,
                    usage=self.llm.get_total_usage(),
                    stopped_by_max_iterations=False,
                    total_time_ms=total_time_ms,
                )

            if parsed["type"] == "action":
                tool_name = parsed["tool"]
                params = parsed["params"]
                step["tool"] = tool_name
                step["params"] = params
                self._emit("think", parsed.get("thought", ""))
                self._emit("act", f"{tool_name}({params})")

                result = self.tool_registry.execute_tool(tool_name, params)
                observation = result.data if result.success else f"Error: {result.error}"
                step["observation"] = observation
                step["success"] = result.success
                trajectory.append(step)
                self._emit("observe", str(observation))

                messages.append(Message(role="assistant", content=response.content))
                messages.append(
                    Message(
                        role="user",
                        content=f"Observation: {observation}",
                    )
                )

        total_time_ms = (time.time() - start_time) * 1000
        last_thought = trajectory[-1]["thought"] if trajectory else ""
        return AgentResult(
            answer=last_thought,
            trajectory=trajectory,
            usage=self.llm.get_total_usage(),
            stopped_by_max_iterations=True,
            total_time_ms=total_time_ms,
        )

    async def run_stream(self, task: str) -> AsyncGenerator[AgentEvent, None]:
        start_time = time.time()
        trajectory: List[Dict[str, Any]] = []
        messages: List[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=task),
        ]

        for iteration in range(self.max_iterations):
            response = self.llm.chat(messages)
            parsed = self._parse_response(response.content)

            step = {
                "iteration": iteration + 1,
                "type": parsed["type"],
                "thought": parsed.get("thought", ""),
            }

            if parsed["type"] == "final":
                step["answer"] = parsed["answer"]
                trajectory.append(step)
                yield AgentEvent(type="think", content=parsed.get("thought", ""))
                yield AgentEvent(type="final", content=parsed["answer"])
                return

            if parsed["type"] == "action":
                tool_name = parsed["tool"]
                params = parsed["params"]
                step["tool"] = tool_name
                step["params"] = params
                yield AgentEvent(type="think", content=parsed.get("thought", ""))
                yield AgentEvent(type="act", content=f"{tool_name}({params})")

                result = self.tool_registry.execute_tool(tool_name, params)
                observation = result.data if result.success else f"Error: {result.error}"
                step["observation"] = observation
                step["success"] = result.success
                trajectory.append(step)
                yield AgentEvent(type="observe", content=str(observation))

                messages.append(Message(role="assistant", content=response.content))
                messages.append(
                    Message(
                        role="user",
                        content=f"Observation: {observation}",
                    )
                )

        last_thought = trajectory[-1]["thought"] if trajectory else ""
        yield AgentEvent(type="final", content=last_thought)
