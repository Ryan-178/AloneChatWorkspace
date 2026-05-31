"""
双模式管理器 - Dual Mode Manager

管理 MTC (More Than Coding) 和 CODE 两种 Agent 模式的切换和协同。
Manages switching and collaboration between MTC and CODE Agent modes.

MTC 模式: 面向非开发用户，使用 DeepSeek，支持文档/数据/调研任务
CODE 模式: 面向开发者，集成 OpenAI Codex CLI，支持代码生成/调试/重构
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

from alonechat.core.types import AgentMode


class ModeSwitchReason(str, Enum):
    USER_REQUEST = "user_request"
    TASK_REQUIREMENT = "task_requirement"
    AUTO_DETECTED = "auto_detected"
    ERROR_FALLBACK = "error_fallback"


@dataclass
class ModeSessionState:
    mode: AgentMode = AgentMode.MTC
    switch_count: int = 0
    last_switch_time: float = 0.0
    last_switch_reason: ModeSwitchReason = ModeSwitchReason.USER_REQUEST
    context: Dict[str, Any] = field(default_factory=dict)
    task_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ModeConfig:
    name: str
    mode: AgentMode
    llm_provider: str = ""
    model: str = ""
    system_prompt: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    use_codex_bridge: bool = False
    codex_config: Optional[Any] = None
    max_iterations: int = 10
    extra: Dict[str, Any] = field(default_factory=dict)


class DualModeManager:
    """双模式管理器：MTC + CODE"""

    _instance: Optional["DualModeManager"] = None

    def __init__(self):
        self._sessions: Dict[str, ModeSessionState] = {}
        self._mode_configs: Dict[AgentMode, ModeConfig] = {}
        self._agents: Dict[str, Any] = {}
        self._on_switch_callbacks: List[Callable] = []
        self._init_default_configs()

    @classmethod
    def get_instance(cls) -> "DualModeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _init_default_configs(self) -> None:
        self._mode_configs[AgentMode.MTC] = ModeConfig(
            name="MTC",
            mode=AgentMode.MTC,
            llm_provider="deepseek",
            model="deepseek-chat",
            allowed_tools=[
                "document_generate",
                "data_analysis",
                "web_research",
                "file_read",
                "file_write",
                "file_search",
                "ppt_generate",
                "report_generate",
            ],
            use_codex_bridge=False,
        )
        self._mode_configs[AgentMode.CODE] = ModeConfig(
            name="CODE",
            mode=AgentMode.CODE,
            llm_provider="codex",
            model="default",
            allowed_tools=[
                "shell",
                "file_read",
                "file_write",
                "file_edit",
                "file_delete",
                "git",
                "search",
                "code_generate",
                "code_debug",
                "code_refactor",
                "test",
            ],
            use_codex_bridge=True,
        )

    def configure_mode(self, mode: AgentMode, config: ModeConfig) -> None:
        self._mode_configs[mode] = config

    def get_mode_config(self, mode: AgentMode) -> Optional[ModeConfig]:
        return self._mode_configs.get(mode)

    def get_session_state(self, session_id: str) -> ModeSessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ModeSessionState()
        return self._sessions[session_id]

    def get_current_mode(self, session_id: str) -> AgentMode:
        return self.get_session_state(session_id).mode

    async def switch_mode(
        self,
        session_id: str,
        target_mode: AgentMode,
        reason: ModeSwitchReason = ModeSwitchReason.USER_REQUEST,
        preserve_context: bool = True,
    ) -> bool:
        state = self.get_session_state(session_id)
        if state.mode == target_mode:
            return True
        old_mode = state.mode
        if preserve_context:
            state.context["previous_mode"] = old_mode.value
            state.context["previous_mode_config"] = self._mode_configs.get(old_mode)
        state.mode = target_mode
        state.switch_count += 1
        state.last_switch_time = time.time()
        state.last_switch_reason = reason
        state.task_history.append({
            "action": "mode_switch",
            "from": old_mode.value,
            "to": target_mode.value,
            "reason": reason.value,
            "timestamp": time.time(),
        })
        if session_id in self._agents:
            self._agents.pop(session_id, None)
        for callback in self._on_switch_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_mode, target_mode, session_id)
                else:
                    callback(old_mode, target_mode, session_id)
            except Exception:
                pass
        return True

    def on_mode_switch(self, callback: Callable) -> None:
        self._on_switch_callbacks.append(callback)

    def get_agent(self, session_id: str, llm=None, **kwargs) -> Any:
        state = self.get_session_state(session_id)
        if session_id in self._agents:
            return self._agents[session_id]
        config = self._mode_configs.get(state.mode)
        if config is None:
            raise ValueError(f"No config for mode {state.mode}")
        if state.mode == AgentMode.MTC:
            agent = self._create_mtc_agent(config, llm, **kwargs)
        elif state.mode == AgentMode.CODE:
            agent = self._create_code_agent(config, llm, **kwargs)
        else:
            raise ValueError(f"Unknown mode: {state.mode}")
        self._agents[session_id] = agent
        return agent

    def _create_mtc_agent(self, config: ModeConfig, llm=None, **kwargs) -> Any:
        from alonechat.agent.mtc_agent import MTCAgent
        from alonechat.tools.registry import ToolRegistry
        tool_registry = kwargs.get("tool_registry") or ToolRegistry()
        return MTCAgent(
            llm=llm,
            tool_registry=tool_registry,
            memory=kwargs.get("memory"),
            max_iterations=config.max_iterations,
            name=f"mtc_agent_{config.model}",
            config=kwargs.get("agent_config"),
        )

    def _create_code_agent(self, config: ModeConfig, llm=None, **kwargs) -> Any:
        from alonechat.agent.code_agent import CodeAgent
        from alonechat.tools.registry import ToolRegistry
        tool_registry = kwargs.get("tool_registry") or ToolRegistry()
        agent = CodeAgent(
            llm=llm,
            tool_registry=tool_registry,
            memory=kwargs.get("memory"),
            max_iterations=config.max_iterations,
            name=f"code_agent_{config.model}",
            config=kwargs.get("agent_config"),
            project_path=kwargs.get("project_path"),
        )
        if config.use_codex_bridge:
            try:
                from alonechat.code.codex_bridge import CodexBridge, CodexBridgeConfig
                codex_config = config.codex_config or CodexBridgeConfig()
                agent._codex_bridge = CodexBridge(codex_config)
            except ImportError:
                agent._codex_bridge = None
        return agent

    def detect_mode_from_task(self, task: str) -> AgentMode:
        code_keywords = [
            "代码", "编程", "函数", "类", "接口", "bug", "调试", "重构",
            "编译", "测试", "git", "commit", "push", "merge", "deploy",
            "code", "function", "class", "debug", "refactor", "implement",
            "npm", "pip", "cargo", "docker", "api", "sdk", "sql",
        ]
        task_lower = task.lower()
        code_score = sum(1 for kw in code_keywords if kw in task_lower)
        if code_score >= 2:
            return AgentMode.CODE
        return AgentMode.MTC

    async def auto_switch(
        self,
        session_id: str,
        task: str,
    ) -> bool:
        detected_mode = self.detect_mode_from_task(task)
        current_mode = self.get_current_mode(session_id)
        if detected_mode != current_mode:
            return await self.switch_mode(
                session_id,
                detected_mode,
                reason=ModeSwitchReason.AUTO_DETECTED,
            )
        return False

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        state = self.get_session_state(session_id)
        return {
            "session_id": session_id,
            "current_mode": state.mode.value,
            "switch_count": state.switch_count,
            "last_switch_time": state.last_switch_time,
            "last_switch_reason": state.last_switch_reason.value,
            "task_count": len(state.task_history),
            "mode_config": {
                "name": self._mode_configs[state.mode].name,
                "model": self._mode_configs[state.mode].model,
                "use_codex_bridge": self._mode_configs[state.mode].use_codex_bridge,
            },
        }

    def cleanup_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        agent = self._agents.pop(session_id, None)
        if agent and hasattr(agent, "_codex_bridge"):
            bridge = agent._codex_bridge
            if bridge and hasattr(bridge, "cleanup"):
                bridge.cleanup()
