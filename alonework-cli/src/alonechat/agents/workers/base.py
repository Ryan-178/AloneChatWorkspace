"""
基礎工作Agent模块 / Base Worker Agent Module

定义所有工作Agent的基类
Defines base class for all worker agents
"""

from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime
from uuid import uuid4


class WorkerAgent(ABC):
    """
    基礎工作Agent / Base Worker Agent
    
    所有工作Agent的抽象基类
    Abstract base class for all worker agents
    
    不做训练，只记录交互数据
    No training, only records interaction data
    """
    
    def __init__(
        self,
        agent_id: str,
        environment: Any,
        model: Any = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化工作Agent / Initialize worker agent
        
        Args:
            agent_id: Agent标识 / Agent identifier
            environment: 环境实例 / Environment instance
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        self.id = agent_id
        self.environment = environment
        self.model = model
        self.config = config or {}
        
        self.status = "idle"
        self.current_task = None
        self.history: list[dict[str, Any]] = []
        self.tools: list[str] = self.config.get("tools", [])
    
    @abstractmethod
    async def execute(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行子任务 / Execute subtask
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            执行结果 / Execution result
        """
        pass
    
    def set_status(self, status: str) -> None:
        """
        设置状态 / Set status
        
        Args:
            status: 状态字符串 / Status string
        """
        self.status = status
    
    def add_history(
        self,
        action: str,
        result: dict[str, Any],
    ) -> None:
        """
        添加历史记录 / Add history record
        
        Args:
            action: 行动描述 / Action description
            result: 结果 / Result
        """
        self.history.append({
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        
        if len(self.history) > 100:
            self.history = self.history[-50:]
    
    def get_status(self) -> dict[str, Any]:
        """
        获取状态 / Get status
        
        Returns:
            状态字典 / Status dictionary
        """
        return {
            "id": self.id,
            "status": self.status,
            "current_task": self.current_task,
            "tools": self.tools,
            "history_count": len(self.history),
        }
    
    async def think(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        思考（调用模型）/ Think (call model)
        
        Args:
            prompt: 提示词 / Prompt
            context: 上下文 / Context
            
        Returns:
            思考结果 / Thinking result
        """
        if not self.model:
            return ""
        
        try:
            if hasattr(self.model, 'chat'):
                response = await self.model.chat(prompt)
                return response if isinstance(response, str) else str(response)
            return ""
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def act(
        self,
        action_type: str,
        params: dict[str, Any],
    ) -> tuple[bool, Any]:
        """
        执行行动 / Execute action
        
        Args:
            action_type: 行动类型 / Action type
            params: 行动参数 / Action parameters
            
        Returns:
            (成功, 结果) / (success, result)
        """
        from ...environment import Action, ActionType
        
        try:
            action_type_enum = ActionType(action_type)
        except ValueError:
            action_type_enum = ActionType.TOOL_CALL
        
        action = Action(
            type=action_type_enum,
            name=params.get("name", action_type),
            params=params,
        )
        
        observation, reward, done, info = await self.environment.step(
            self.id, action
        )
        
        success = info.get("result").success if info.get("result") else False
        result = info.get("result").output if info.get("result") else None
        
        return success, result
    
    def can_handle(self, task_type: str) -> bool:
        """
        检查是否能处理该类型任务 / Check if can handle task type
        
        Args:
            task_type: 任务类型 / Task type
            
        Returns:
            是否能处理 / Whether can handle
        """
        return True
