"""
Agent Framework Entry Point - Agent框架统一入口 - Agent Framework Entry Point
提供简洁的API供上层应用调用
Provides simple API for upper-layer applications to call

使用示例 / Usage Examples:

1. 基本使用 - Basic Usage:
   from agent_framework import Agent
   agent = Agent()
   result = agent.run("帮我写一个Python函数")

2. 指定模式 - Specify Mode:
   from agent_framework import Agent, ExecutionMode
   agent = Agent(mode="code")  # 或 mode="work"
   result = agent.run("实现一个排序算法")

3. 自动模式检测 - Auto Mode Detection:
   from agent_framework import Agent
   agent = Agent(auto_detect=True)
   result = agent.run("写一份项目报告")  # 自动路由到WORK模式
   result = agent.run("修复这个bug")      # 自动路由到CODE模式

4. 流式执行 - Streaming Execution:
   from agent_framework import Agent
   agent = Agent()
   async for event in agent.stream("分析这份数据"):
       print(event.content)
"""
from typing import Any, AsyncGenerator, Dict, Optional

from agent_framework.agent.mode_manager import (
    AgentModeManager,
    ExecutionMode,
    ModeConfig,
    create_mode_manager,
)
from agent_framework.agent.mode_router import (
    ModeRouter,
    RouterConfig,
    create_router,
)
from agent_framework.core.base_agent import AgentResult, AgentEvent
from agent_framework.config import get_config, AgentConfig


class Agent:
    """
    Agent统一入口 - Agent Unified Entry Point
    提供简洁的API，自动处理CODE/WORK模式切换
    Provides simple API, automatically handles CODE/WORK mode switching
    
    模式说明 / Mode Description:
    - CODE模式: 使用Codex CLI进行编程任务，适合开发者
      CODE mode: Uses Codex CLI for programming tasks, suitable for developers
    - WORK模式: 使用自研MTCAgent处理办公任务，适合非开发者
      WORK mode: Uses self-developed MTCAgent for office tasks, suitable for non-developers
    """
    
    def __init__(
        self,
        llm: Any = None,
        mode: str = "work",
        auto_detect: bool = True,
        config: Optional[AgentConfig] = None,
        **kwargs
    ):
        """
        初始化Agent - Initialize Agent
        
        Args:
            llm: 语言模型实例 / Language model instance
            mode: 初始模式 ("code" 或 "work") / Initial mode
            auto_detect: 是否自动检测模式 / Whether to auto-detect mode
            config: 配置对象 / Configuration object
            **kwargs: 其他参数 / Other arguments
        """
        self._config = config or get_config()
        
        self._mode_manager = create_mode_manager(
            llm=llm,
            mode=mode,
            auto_detect_mode=auto_detect,
            **kwargs
        )
        
        self._router = create_router(
            llm=llm,
            initial_mode=mode,
            enable_auto_routing=auto_detect,
        )
        self._router.mode_manager = self._mode_manager
    
    @property
    def mode(self) -> str:
        """获取当前模式 - Get current mode"""
        return self._mode_manager.current_mode.value
    
    @property
    def is_code_mode(self) -> bool:
        """是否为CODE模式 - Whether in CODE mode"""
        return self._mode_manager.is_code_mode
    
    @property
    def is_work_mode(self) -> bool:
        """是否为WORK模式 - Whether in WORK mode"""
        return self._mode_manager.is_work_mode
    
    def switch_mode(self, mode: str, reason: str = "") -> Dict[str, Any]:
        """
        切换模式 - Switch mode
        
        Args:
            mode: 目标模式 ("code" 或 "work") / Target mode
            reason: 切换原因 / Switch reason
            
        Returns:
            切换事件信息 / Switch event info
        """
        target_mode = ExecutionMode.CODE if mode.lower() == "code" else ExecutionMode.WORK
        event = self._mode_manager.switch_mode(target_mode, reason)
        return {
            "from_mode": event.from_mode.value if event.from_mode else None,
            "to_mode": event.to_mode.value,
            "reason": event.reason,
        }
    
    def run(
        self,
        task: str,
        mode: Optional[str] = None,
    ) -> AgentResult:
        """
        执行任务 - Execute task
        
        Args:
            task: 任务描述 / Task description
            mode: 可选的执行模式 / Optional execution mode
            
        Returns:
            执行结果 / Execution result
        """
        target_mode = None
        if mode is not None:
            target_mode = ExecutionMode.CODE if mode.lower() == "code" else ExecutionMode.WORK
        
        return self._mode_manager.run(task, mode=target_mode)
    
    async def stream(
        self,
        task: str,
        mode: Optional[str] = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        流式执行任务 - Execute task with streaming
        
        Args:
            task: 任务描述 / Task description
            mode: 可选的执行模式 / Optional execution mode
            
        Yields:
            执行事件流 / Execution event stream
        """
        target_mode = None
        if mode is not None:
            target_mode = ExecutionMode.CODE if mode.lower() == "code" else ExecutionMode.WORK
        
        async for event in self._mode_manager.run_stream(task, mode=target_mode):
            yield event
    
    def run_auto(self, task: str) -> AgentResult:
        """
        自动检测模式并执行 - Auto-detect mode and execute
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            执行结果 / Execution result
        """
        return self._mode_manager.run_auto(task)
    
    def route(self, task: str) -> Dict[str, Any]:
        """
        获取路由信息（不执行） - Get routing info (without execution)
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            路由信息 / Routing info
        """
        return self._router.get_routing_info(task)
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息 - Get agent info
        
        Returns:
            Agent详细信息 / Detailed agent info
        """
        return {
            "mode": self._mode_manager.get_mode_info(),
            "config": {
                "llm": str(self._config.llm.model) if self._config else None,
            }
        }
    
    def reset(self) -> None:
        """重置状态 - Reset state"""
        self._mode_manager.reset()
    
    def cleanup(self) -> None:
        """清理资源 - Cleanup resources"""
        self._mode_manager.cleanup()


def create_agent(
    llm: Any = None,
    mode: str = "work",
    auto_detect: bool = True,
    **kwargs
) -> Agent:
    """
    创建Agent的便捷函数 - Convenience function to create Agent
    
    Args:
        llm: 语言模型实例 / Language model instance
        mode: 初始模式 / Initial mode
        auto_detect: 是否自动检测模式 / Whether to auto-detect mode
        **kwargs: 其他参数 / Other arguments
        
    Returns:
        Agent实例 / Agent instance
    """
    return Agent(llm=llm, mode=mode, auto_detect=auto_detect, **kwargs)


__all__ = [
    "Agent",
    "ExecutionMode",
    "ModeConfig",
    "create_agent",
    "create_mode_manager",
    "create_router",
    "AgentModeManager",
    "ModeRouter",
]
