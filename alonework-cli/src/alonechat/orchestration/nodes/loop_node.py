"""
循环节点

支持循环迭代执行
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import asyncio

from .base import BaseNode, NodeContext, NodeResult, NodeState


class LoopType(Enum):
    FOR = "for"
    WHILE = "while"
    UNTIL = "until"


@dataclass
class LoopConfig:
    loop_type: LoopType = LoopType.FOR
    max_iterations: int = 1000
    collect_results: bool = True
    break_on_error: bool = False
    delay: float = 0.0


class LoopNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        body_node: Optional[BaseNode] = None,
        loop_config: Optional[LoopConfig] = None,
        condition: Optional[Callable[[NodeContext, int], bool]] = None,
    ):
        super().__init__(node_id, name, description)
        self.body_node = body_node
        self.loop_config = loop_config or LoopConfig()
        self.condition = condition
        self.config = {
            "loop_type": self.loop_config.loop_type.value,
            "max_iterations": self.loop_config.max_iterations,
            "break_on_error": self.loop_config.break_on_error,
        }
    
    def set_body(self, node: BaseNode) -> "LoopNode":
        self.body_node = node
        return self
    
    def set_condition(
        self,
        condition: Callable[[NodeContext, int], bool],
    ) -> "LoopNode":
        self.condition = condition
        return self
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        
        if not self.body_node:
            return NodeResult(
                node_id=self.id,
                success=True,
                state=NodeState.COMPLETED,
                output=[],
                execution_time=0.0,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        results: List[Any] = []
        iterations = 0
        should_continue = True
        last_error = None
        
        while should_continue and iterations < self.loop_config.max_iterations:
            if self.loop_config.delay > 0:
                await asyncio.sleep(self.loop_config.delay)
            
            should_continue = self._evaluate_condition(context, iterations)
            
            if not should_continue:
                break
            
            iter_context = NodeContext(
                variables=context.variables,
                inputs={
                    **context.inputs,
                    "iteration": iterations,
                    "results": results,
                },
                parent_output=results[-1] if results else None,
            )
            
            result = await self.body_node.run(iter_context)
            
            if self.loop_config.collect_results:
                results.append(result.output if result.success else None)
            
            iterations += 1
            
            if not result.success and self.loop_config.break_on_error:
                last_error = result.error
                break
            
            if self.loop_config.loop_type == LoopType.UNTIL:
                should_continue = not result.success
        
        success = last_error is None
        execution_time = (datetime.now() - start_time).total_seconds()
        
        output = results if self.loop_config.collect_results else results[-1] if results else None
        
        return NodeResult(
            node_id=self.id,
            success=success,
            state=NodeState.COMPLETED if success else NodeState.FAILED,
            output=output,
            error=last_error,
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={
                "iterations": iterations,
                "loop_type": self.loop_config.loop_type.value,
            },
        )
    
    def _evaluate_condition(
        self,
        context: NodeContext,
        iteration: int,
    ) -> bool:
        if self.condition:
            try:
                return self.condition(context, iteration)
            except Exception:
                return False
        
        return True
    
    @classmethod
    def create_for_loop(
        cls,
        node_id: str = "",
        name: str = "",
        body_node: Optional[BaseNode] = None,
        items_key: str = "items",
        max_iterations: int = 1000,
    ) -> "LoopNode":
        def condition(ctx: NodeContext, iteration: int) -> bool:
            items = ctx.get(items_key, [])
            return iteration < len(items)
        
        config = LoopConfig(
            loop_type=LoopType.FOR,
            max_iterations=max_iterations,
        )
        
        return cls(
            node_id,
            name,
            "For循环",
            body_node,
            config,
            condition,
        )
    
    @classmethod
    def create_while_loop(
        cls,
        node_id: str = "",
        name: str = "",
        body_node: Optional[BaseNode] = None,
        condition: Optional[Callable[[NodeContext, int], bool]] = None,
        max_iterations: int = 1000,
    ) -> "LoopNode":
        config = LoopConfig(
            loop_type=LoopType.WHILE,
            max_iterations=max_iterations,
        )
        
        return cls(
            node_id,
            name,
            "While循环",
            body_node,
            config,
            condition,
        )
    
    @classmethod
    def create_until_loop(
        cls,
        node_id: str = "",
        name: str = "",
        body_node: Optional[BaseNode] = None,
        max_iterations: int = 1000,
    ) -> "LoopNode":
        config = LoopConfig(
            loop_type=LoopType.UNTIL,
            max_iterations=max_iterations,
        )
        
        return cls(
            node_id,
            name,
            "Until循环",
            body_node,
            config,
        )


class RetryNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        target_node: Optional[BaseNode] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        retry_condition: Optional[Callable[[NodeResult], bool]] = None,
    ):
        super().__init__(node_id, name, description)
        self.target_node = target_node
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.retry_condition = retry_condition or (lambda r: not r.success)
    
    def set_target(self, node: BaseNode) -> "RetryNode":
        self.target_node = node
        return self
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        
        if not self.target_node:
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error="没有设置目标节点",
                execution_time=0.0,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        last_result = None
        current_delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            result = await self.target_node.run(context)
            last_result = result
            
            if not self.retry_condition(result):
                execution_time = (datetime.now() - start_time).total_seconds()
                return NodeResult(
                    node_id=self.id,
                    success=result.success,
                    state=result.state,
                    output=result.output,
                    execution_time=execution_time,
                    started_at=start_time,
                    completed_at=datetime.now(),
                    metadata={"attempts": attempt + 1},
                )
            
            if attempt < self.max_retries:
                await asyncio.sleep(current_delay)
                current_delay *= self.backoff_factor
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return NodeResult(
            node_id=self.id,
            success=False,
            state=NodeState.FAILED,
            output=last_result.output if last_result else None,
            error=f"重试 {self.max_retries} 次后仍然失败",
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={"attempts": self.max_retries + 1},
        )
