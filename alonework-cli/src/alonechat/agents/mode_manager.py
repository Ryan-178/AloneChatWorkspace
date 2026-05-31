"""
Agent Mode Manager - Agent模式管理器 - Agent Mode Manager
统一管理CODE模式和WORK模式的切换与路由
Unified management of CODE mode and WORK mode switching and routing
"""
import time
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from alonechat.core.types import AgentMode
from alonechat.core.base_agent import AgentResult, AgentEvent


class ExecutionMode(str, Enum):
    """
    执行模式枚举 - Execution Mode Enum
    定义用户可选择的两种主要模式
    Defines two main modes available to users
    """
    CODE = "code"
    WORK = "work"


class ModeSwitchEvent(BaseModel):
    """
    模式切换事件 - Mode Switch Event
    记录模式切换的详细信息
    Records detailed information about mode switching
    """
    from_mode: Optional[ExecutionMode] = Field(default=None, description="切换前模式 / Mode before switch")
    to_mode: ExecutionMode = Field(..., description="切换后模式 / Mode after switch")
    timestamp: float = Field(default_factory=time.time, description="切换时间戳 / Switch timestamp")
    reason: str = Field(default="", description="切换原因 / Switch reason")


@dataclass
class ModeConfig:
    """
    模式配置 - Mode Configuration
    配置各模式的参数和行为
    Configure parameters and behaviors for each mode
    """
    mode: ExecutionMode = ExecutionMode.WORK
    allow_mode_switch: bool = True
    auto_detect_mode: bool = False
    code_config: Dict[str, Any] = field(default_factory=lambda: {
        "use_codex_bridge": True,
        "enable_search_agent": True,
        "enable_plan_mode": True,
        "max_context_tokens": 128000,
    })
    work_config: Dict[str, Any] = field(default_factory=lambda: {
        "intent_clarification_enabled": True,
        "max_clarification_questions": 3,
    })


class AgentModeManager:
    """
    Agent模式管理器 - Agent Mode Manager
    统一管理CODE模式和WORK模式的创建、切换和执行
    Unified management of CODE mode and WORK mode creation, switching and execution
    
    模式说明 / Mode Description:
    - CODE模式: 面向开发者，使用Codex CLI进行编程任务
      CODE mode: For developers, uses Codex CLI for programming tasks
    - WORK模式: 面向非开发者，使用自研MTCAgent处理办公任务
      WORK mode: For non-developers, uses self-developed MTCAgent for office tasks
    """
    
    def __init__(
        self,
        llm: Any = None,
        config: Optional[ModeConfig] = None,
        tool_registry: Any = None,
        memory: Any = None,
    ):
        """
        初始化模式管理器 - Initialize mode manager
        
        Args:
            llm: 语言模型实例 / Language model instance
            config: 模式配置 / Mode configuration
            tool_registry: 工具注册表 / Tool registry
            memory: 记忆模块 / Memory module
        """
        self.llm = llm
        self.config = config or ModeConfig()
        self.tool_registry = tool_registry
        self.memory = memory
        
        self._current_mode: ExecutionMode = self.config.mode
        self._code_agent: Optional[Any] = None
        self._work_agent: Optional[Any] = None
        self._mode_history: List[ModeSwitchEvent] = []
        self._initialized: bool = False
    
    @property
    def current_mode(self) -> ExecutionMode:
        """获取当前模式 - Get current mode"""
        return self._current_mode
    
    @property
    def is_code_mode(self) -> bool:
        """是否为CODE模式 - Whether in CODE mode"""
        return self._current_mode == ExecutionMode.CODE
    
    @property
    def is_work_mode(self) -> bool:
        """是否为WORK模式 - Whether in WORK mode"""
        return self._current_mode == ExecutionMode.WORK
    
    def initialize(self) -> None:
        """
        初始化当前模式的Agent - Initialize agent for current mode
        延迟初始化，只在需要时创建Agent实例
        Lazy initialization, creates Agent instance only when needed
        """
        if self._initialized:
            return
        
        self._ensure_agent(self._current_mode)
        self._initialized = True
    
    def _ensure_agent(self, mode: ExecutionMode) -> None:
        """
        确保指定模式的Agent已创建 - Ensure agent for specified mode is created
        
        Args:
            mode: 目标模式 / Target mode
        """
        if mode == ExecutionMode.CODE:
            if self._code_agent is None:
                self._code_agent = self._create_code_agent()
        else:
            if self._work_agent is None:
                self._work_agent = self._create_work_agent()
    
    def _create_code_agent(self) -> Any:
        """
        创建CODE模式Agent - Create CODE mode agent
        使用CodexBridge连接Codex CLI进行编程任务
        Uses CodexBridge to connect Codex CLI for programming tasks
        
        Returns:
            CodeAgent实例 / CodeAgent instance
        """
        from alonechat.agents.code_agent import CodeAgent
        from alonechat.code.codex_bridge import CodexBridge, CodexBridgeConfig
        
        code_config = self.config.code_config
        use_codex_bridge = code_config.get("use_codex_bridge", True)
        
        codex_config = None
        if use_codex_bridge:
            codex_config = CodexBridgeConfig(
                llm=self.llm,
                working_directory=".",
            )
        
        agent = CodeAgent(
            llm=self.llm,
            tool_registry=self.tool_registry,
            memory=self.memory,
            name="code_agent",
            use_codex_bridge=use_codex_bridge,
            codex_config=codex_config,
        )
        
        return agent
    
    def _create_work_agent(self) -> Any:
        """
        创建WORK模式Agent - Create WORK mode agent
        使用自研MTCAgent处理非开发者的办公任务
        Uses self-developed MTCAgent for non-developer office tasks
        
        Returns:
            MTCAgent实例 / MTCAgent instance
        """
        from alonechat.agents.mtc_agent import MTCAgent
        
        work_config = self.config.work_config
        
        agent = MTCAgent(
            llm=self.llm,
            tool_registry=self.tool_registry,
            memory=self.memory,
            name="work_agent",
        )
        
        return agent
    
    def switch_mode(
        self,
        target_mode: ExecutionMode,
        reason: str = ""
    ) -> ModeSwitchEvent:
        """
        切换执行模式 - Switch execution mode
        
        Args:
            target_mode: 目标模式 / Target mode
            reason: 切换原因 / Switch reason
            
        Returns:
            模式切换事件 / Mode switch event
            
        Raises:
            RuntimeError: 如果不允许模式切换 / If mode switching is not allowed
        """
        if not self.config.allow_mode_switch:
            raise RuntimeError("模式切换已被禁用 / Mode switching is disabled")
        
        if target_mode == self._current_mode:
            return ModeSwitchEvent(
                from_mode=self._current_mode,
                to_mode=target_mode,
                reason="模式未改变 / Mode unchanged"
            )
        
        event = ModeSwitchEvent(
            from_mode=self._current_mode,
            to_mode=target_mode,
            reason=reason
        )
        
        self._current_mode = target_mode
        self._mode_history.append(event)
        
        self._ensure_agent(target_mode)
        
        return event
    
    def get_agent(self) -> Any:
        """
        获取当前模式的Agent实例 - Get agent instance for current mode
        
        Returns:
            当前模式的Agent / Agent for current mode
        """
        self.initialize()
        
        if self.is_code_mode:
            return self._code_agent
        else:
            return self._work_agent
    
    def run(self, task: str, mode: Optional[ExecutionMode] = None) -> AgentResult:
        """
        执行任务 - Execute task
        使用当前模式或指定模式的Agent执行任务
        Uses current mode or specified mode's agent to execute task
        
        Args:
            task: 任务描述 / Task description
            mode: 可选的执行模式 / Optional execution mode
            
        Returns:
            执行结果 / Execution result
        """
        if mode is not None and mode != self._current_mode:
            self.switch_mode(mode, reason="任务指定模式 / Task specified mode")
        
        agent = self.get_agent()
        return agent.run(task)
    
    async def run_stream(
        self,
        task: str,
        mode: Optional[ExecutionMode] = None
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        流式执行任务 - Execute task with streaming
        
        Args:
            task: 任务描述 / Task description
            mode: 可选的执行模式 / Optional execution mode
            
        Yields:
            执行事件流 / Execution event stream
        """
        if mode is not None and mode != self._current_mode:
            self.switch_mode(mode, reason="任务指定模式 / Task specified mode")
        
        agent = self.get_agent()
        async for event in agent.run_stream(task):
            yield event
    
    def detect_mode(self, task: str) -> ExecutionMode:
        """
        自动检测任务适合的模式 - Auto-detect suitable mode for task
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            检测到的模式 / Detected mode
        """
        if not self.config.auto_detect_mode:
            return self._current_mode
        
        code_keywords = [
            "代码", "编程", "debug", "修复bug", "重构", "写函数",
            "实现", "开发", "code", "function", "class",
            "git", "commit", "测试", "test", "lint"
        ]
        
        work_keywords = [
            "文档", "报告", "分析", "整理", "总结", "写文章",
            "PPT", "Excel", "表格", "演示", "调研", "翻译"
        ]
        
        task_lower = task.lower()
        
        code_score = sum(1 for kw in code_keywords if kw in task_lower)
        work_score = sum(1 for kw in work_keywords if kw in task_lower)
        
        if code_score > work_score:
            return ExecutionMode.CODE
        elif work_score > code_score:
            return ExecutionMode.WORK
        else:
            return self._current_mode
    
    def run_auto(self, task: str) -> AgentResult:
        """
        自动检测模式并执行任务 - Auto-detect mode and execute task
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            执行结果 / Execution result
        """
        detected_mode = self.detect_mode(task)
        return self.run(task, mode=detected_mode)
    
    def get_mode_info(self) -> Dict[str, Any]:
        """
        获取模式信息 - Get mode information
        
        Returns:
            模式详细信息 / Detailed mode information
        """
        return {
            "current_mode": self._current_mode.value,
            "is_code_mode": self.is_code_mode,
            "is_work_mode": self.is_work_mode,
            "allow_mode_switch": self.config.allow_mode_switch,
            "auto_detect_mode": self.config.auto_detect_mode,
            "switch_history": [
                {
                    "from": e.from_mode.value if e.from_mode else None,
                    "to": e.to_mode.value,
                    "timestamp": e.timestamp,
                    "reason": e.reason,
                }
                for e in self._mode_history
            ],
            "agents": {
                "code_agent": self._code_agent is not None,
                "work_agent": self._work_agent is not None,
            }
        }
    
    def reset(self) -> None:
        """
        重置模式管理器状态 - Reset mode manager state
        """
        if self._code_agent:
            self._code_agent.reset()
        if self._work_agent:
            self._work_agent.reset()
        
        self._mode_history.clear()
        self._current_mode = self.config.mode
    
    def cleanup(self) -> None:
        """
        清理资源 - Cleanup resources
        """
        if self._code_agent:
            if hasattr(self._code_agent, 'cleanup'):
                self._code_agent.cleanup()
        if self._work_agent:
            if hasattr(self._work_agent, 'reset'):
                self._work_agent.reset()
        
        self._code_agent = None
        self._work_agent = None
        self._initialized = False


def create_mode_manager(
    llm: Any = None,
    mode: str = "work",
    allow_mode_switch: bool = True,
    auto_detect_mode: bool = False,
    **kwargs
) -> AgentModeManager:
    """
    创建模式管理器的便捷函数 - Convenience function to create mode manager
    
    Args:
        llm: 语言模型实例 / Language model instance
        mode: 初始模式 ("code" 或 "work") / Initial mode
        allow_mode_switch: 是否允许模式切换 / Whether to allow mode switching
        auto_detect_mode: 是否自动检测模式 / Whether to auto-detect mode
        **kwargs: 其他参数 / Other arguments
        
    Returns:
        AgentModeManager实例 / AgentModeManager instance
    """
    execution_mode = ExecutionMode.CODE if mode.lower() == "code" else ExecutionMode.WORK
    
    config = ModeConfig(
        mode=execution_mode,
        allow_mode_switch=allow_mode_switch,
        auto_detect_mode=auto_detect_mode,
    )
    
    return AgentModeManager(
        llm=llm,
        config=config,
        **kwargs
    )
