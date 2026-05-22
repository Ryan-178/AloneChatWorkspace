"""
并行节点

并行执行多个子节点
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from .base import BaseNode, NodeContext, NodeResult, NodeState


@dataclass
class ParallelConfig:
    max_concurrency: int = 10
    fail_fast: bool = False
    timeout: float = 300.0
    collect_results: bool = True


class ParallelNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        children: Optional[List[BaseNode]] = None,
        parallel_config: Optional[ParallelConfig] = None,
    ):
        super().__init__(node_id, name, description)
        self.children = children or []
        self.parallel_config = parallel_config or ParallelConfig()
        self.config = {
            "max_concurrency": self.parallel_config.max_concurrency,
            "fail_fast": self.parallel_config.fail_fast,
            "timeout": self.parallel_config.timeout,
        }
    
    def add_child(self, node: BaseNode) -> "ParallelNode":
        self.children.append(node)
        return self
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        
        if not self.children:
            return NodeResult(
                node_id=self.id,
                success=True,
                state=NodeState.COMPLETED,
                output=[],
                execution_time=0.0,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        semaphore = asyncio.Semaphore(self.parallel_config.max_concurrency)
        results: List[NodeResult] = []
        errors: List[str] = []
        
        async def run_with_semaphore(
            node: BaseNode,
            ctx: NodeContext,
        ) -> NodeResult:
            async with semaphore:
                return await node.run(ctx)
        
        tasks = [
            run_with_semaphore(child, context)
            for child in self.children
        ]
        
        try:
            if self.parallel_config.fail_fast:
                results = await asyncio.gather(
                    *tasks,
                    return_exceptions=False,
                )
            else:
                results = await asyncio.gather(
                    *tasks,
                    return_exceptions=True,
                )
                
                processed_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        errors.append(f"子节点 {i} 失败: {result}")
                        processed_results.append(NodeResult(
                            node_id=self.children[i].id,
                            success=False,
                            state=NodeState.FAILED,
                            error=str(result),
                        ))
                    else:
                        processed_results.append(result)
                results = processed_results
                
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error="并行执行超时",
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error=str(e),
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        success = all(r.success for r in results)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        output = None
        if self.parallel_config.collect_results:
            output = {
                "results": [r.output for r in results],
                "success_count": sum(1 for r in results if r.success),
                "failure_count": sum(1 for r in results if not r.success),
                "children": [
                    {
                        "node_id": r.node_id,
                        "success": r.success,
                        "execution_time": r.execution_time,
                    }
                    for r in results
                ],
            }
        
        return NodeResult(
            node_id=self.id,
            success=success,
            state=NodeState.COMPLETED if success else NodeState.FAILED,
            output=output,
            error="; ".join(errors) if errors else None,
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={
                "children_count": len(self.children),
                "max_concurrency": self.parallel_config.max_concurrency,
            },
        )
    
    def get_child(self, index: int) -> Optional[BaseNode]:
        if 0 <= index < len(self.children):
            return self.children[index]
        return None
    
    def remove_child(self, index: int) -> Optional[BaseNode]:
        if 0 <= index < len(self.children):
            return self.children.pop(index)
        return None
    
    @classmethod
    def create(
        cls,
        node_id: str = "",
        name: str = "",
        children: Optional[List[BaseNode]] = None,
        max_concurrency: int = 10,
        fail_fast: bool = False,
    ) -> "ParallelNode":
        config = ParallelConfig(
            max_concurrency=max_concurrency,
            fail_fast=fail_fast,
        )
        return cls(node_id, name, "并行执行", children, config)


class MapNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        template_node: Optional[BaseNode] = None,
        input_key: str = "items",
        output_key: str = "results",
        max_concurrency: int = 10,
    ):
        super().__init__(node_id, name, description)
        self.template_node = template_node
        self.input_key = input_key
        self.output_key = output_key
        self.max_concurrency = max_concurrency
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        
        items = context.get(self.input_key, [])
        if not items:
            return NodeResult(
                node_id=self.id,
                success=True,
                state=NodeState.COMPLETED,
                output={self.output_key: []},
                execution_time=0.0,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        if not self.template_node:
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error="没有设置模板节点",
                execution_time=0.0,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        semaphore = asyncio.Semaphore(self.max_concurrency)
        results = []
        
        async def process_item(item: Any, index: int) -> Any:
            async with semaphore:
                item_context = NodeContext(
                    variables=context.variables,
                    inputs={"item": item, "index": index},
                    parent_output=context.parent_output,
                )
                result = await self.template_node.run(item_context)
                return result.output if result.success else None
        
        tasks = [process_item(item, i) for i, item in enumerate(items)]
        results = await asyncio.gather(*tasks)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return NodeResult(
            node_id=self.id,
            success=True,
            state=NodeState.COMPLETED,
            output={self.output_key: list(results)},
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={"processed_count": len(items)},
        )
