"""
行动节点

执行具体行动的节点，与Agent层集成
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import asyncio

from .base import BaseNode, NodeContext, NodeResult, NodeState


@dataclass
class ActionConfig:
    action_type: str = "generic"
    agent_name: Optional[str] = None
    timeout: float = 300.0
    retries: int = 3
    retry_delay: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)


class ActionNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        action_config: Optional[ActionConfig] = None,
        action_handler: Optional[Callable] = None,
    ):
        super().__init__(node_id, name, description)
        self.action_config = action_config or ActionConfig()
        self.action_handler = action_handler
        self.config = {
            "action_type": self.action_config.action_type,
            "agent_name": self.action_config.agent_name,
            "timeout": self.action_config.timeout,
            "retries": self.action_config.retries,
            "params": self.action_config.params,
        }
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        retries = 0
        last_error = None
        
        params = {**self.action_config.params}
        for key, value in context.inputs.items():
            if key in params:
                params[key] = value
        
        while retries <= self.action_config.retries:
            try:
                output = await self._execute_action(params, context)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return NodeResult(
                    node_id=self.id,
                    success=True,
                    state=NodeState.COMPLETED,
                    output=output,
                    execution_time=execution_time,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    metadata={"retries": retries},
                )
                
            except asyncio.TimeoutError:
                last_error = "执行超时"
                retries += 1
            except Exception as e:
                last_error = str(e)
                retries += 1
            
            if retries <= self.action_config.retries:
                await asyncio.sleep(
                    self.action_config.retry_delay * retries
                )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return NodeResult(
            node_id=self.id,
            success=False,
            state=NodeState.FAILED,
            error=last_error,
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={"retries": retries - 1},
        )
    
    async def _execute_action(
        self,
        params: Dict[str, Any],
        context: NodeContext,
    ) -> Any:
        if self.action_handler:
            if asyncio.iscoroutinefunction(self.action_handler):
                return await self.action_handler(params, context)
            else:
                return self.action_handler(params, context)
        
        return {
            "action_type": self.action_config.action_type,
            "agent": self.action_config.agent_name,
            "params": params,
            "status": "simulated",
        }
    
    def set_handler(self, handler: Callable) -> None:
        self.action_handler = handler
    
    @classmethod
    def create_code_action(
        cls,
        node_id: str = "",
        name: str = "",
        params: Optional[Dict] = None,
    ) -> "ActionNode":
        config = ActionConfig(
            action_type="code",
            agent_name="code_agent",
            params=params or {},
        )
        return cls(node_id, name, "代码执行行动", config)
    
    @classmethod
    def create_data_action(
        cls,
        node_id: str = "",
        name: str = "",
        params: Optional[Dict] = None,
    ) -> "ActionNode":
        config = ActionConfig(
            action_type="data",
            agent_name="data_agent",
            params=params or {},
        )
        return cls(node_id, name, "数据处理行动", config)
    
    @classmethod
    def create_research_action(
        cls,
        node_id: str = "",
        name: str = "",
        params: Optional[Dict] = None,
    ) -> "ActionNode":
        config = ActionConfig(
            action_type="research",
            agent_name="research_agent",
            params=params or {},
        )
        return cls(node_id, name, "研究分析行动", config)
    
    @classmethod
    def create_test_action(
        cls,
        node_id: str = "",
        name: str = "",
        params: Optional[Dict] = None,
    ) -> "ActionNode":
        config = ActionConfig(
            action_type="test",
            agent_name="test_agent",
            params=params or {},
        )
        return cls(node_id, name, "测试验证行动", config)
