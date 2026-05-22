"""
条件节点

基于条件判断选择执行路径
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio

from .base import BaseNode, NodeContext, NodeResult, NodeState


@dataclass
class Condition:
    name: str
    evaluator: Callable[[NodeContext], bool]
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Branch:
    condition_name: str
    node: BaseNode
    is_default: bool = False


class ConditionNode(BaseNode):
    def __init__(
        self,
        node_id: str = "",
        name: str = "",
        description: str = "",
        conditions: Optional[List[Condition]] = None,
        branches: Optional[List[Branch]] = None,
    ):
        super().__init__(node_id, name, description)
        self.conditions = conditions or []
        self.branches = branches or []
        self._condition_cache: Dict[str, bool] = {}
    
    def add_condition(
        self,
        name: str,
        evaluator: Callable[[NodeContext], bool],
        priority: int = 0,
    ) -> "ConditionNode":
        self.conditions.append(Condition(name, evaluator, priority))
        return self
    
    def add_branch(
        self,
        condition_name: str,
        node: BaseNode,
        is_default: bool = False,
    ) -> "ConditionNode":
        self.branches.append(Branch(condition_name, node, is_default))
        return self
    
    def set_default_branch(self, node: BaseNode) -> "ConditionNode":
        self.branches.append(Branch("default", node, is_default=True))
        return self
    
    async def execute(
        self,
        context: NodeContext,
    ) -> NodeResult:
        start_time = datetime.now()
        
        sorted_conditions = sorted(
            self.conditions,
            key=lambda c: -c.priority
        )
        
        matched_condition = None
        for condition in sorted_conditions:
            try:
                result = condition.evaluator(context)
                self._condition_cache[condition.name] = result
                if result:
                    matched_condition = condition.name
                    break
            except Exception as e:
                self._condition_cache[condition.name] = False
        
        selected_branch = None
        if matched_condition:
            for branch in self.branches:
                if branch.condition_name == matched_condition:
                    selected_branch = branch
                    break
        
        if not selected_branch:
            for branch in self.branches:
                if branch.is_default:
                    selected_branch = branch
                    break
        
        if not selected_branch:
            execution_time = (datetime.now() - start_time).total_seconds()
            return NodeResult(
                node_id=self.id,
                success=False,
                state=NodeState.FAILED,
                error="没有匹配的条件分支",
                execution_time=execution_time,
                started_at=start_time,
                completed_at=datetime.now(),
            )
        
        branch_result = await selected_branch.node.run(context)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return NodeResult(
            node_id=self.id,
            success=branch_result.success,
            state=branch_result.state,
            output={
                "matched_condition": matched_condition or "default",
                "branch_output": branch_result.output,
            },
            error=branch_result.error,
            execution_time=execution_time,
            started_at=start_time,
            completed_at=datetime.now(),
            metadata={
                "condition_evaluations": self._condition_cache,
                "selected_branch": selected_branch.condition_name,
            },
        )
    
    @classmethod
    def create_simple(
        cls,
        node_id: str = "",
        name: str = "",
        condition: Callable[[NodeContext], bool] = None,
        true_node: Optional[BaseNode] = None,
        false_node: Optional[BaseNode] = None,
    ) -> "ConditionNode":
        node = cls(node_id, name, "简单条件判断")
        
        if condition:
            node.add_condition("true", condition)
        
        if true_node:
            node.add_branch("true", true_node)
        
        if false_node:
            node.add_branch("default", false_node, is_default=True)
        
        return node
    
    @classmethod
    def create_switch(
        cls,
        node_id: str = "",
        name: str = "",
        cases: Optional[List[Tuple[str, Callable, BaseNode]]] = None,
        default_node: Optional[BaseNode] = None,
    ) -> "ConditionNode":
        node = cls(node_id, name, "多路分支")
        
        if cases:
            for i, (cond_name, evaluator, branch_node) in enumerate(cases):
                node.add_condition(cond_name, evaluator, priority=10 - i)
                node.add_branch(cond_name, branch_node)
        
        if default_node:
            node.set_default_branch(default_node)
        
        return node


def create_comparison_condition(
    key: str,
    operator: str,
    value: Any,
) -> Callable[[NodeContext], bool]:
    def evaluator(context: NodeContext) -> bool:
        actual = context.get(key)
        if actual is None:
            return False
        
        if operator == "==":
            return actual == value
        elif operator == "!=":
            return actual != value
        elif operator == ">":
            return actual > value
        elif operator == ">=":
            return actual >= value
        elif operator == "<":
            return actual < value
        elif operator == "<=":
            return actual <= value
        elif operator == "in":
            return actual in value
        elif operator == "not_in":
            return actual not in value
        else:
            return False
    
    return evaluator


def create_exists_condition(key: str) -> Callable[[NodeContext], bool]:
    def evaluator(context: NodeContext) -> bool:
        return context.get(key) is not None
    return evaluator


def create_type_condition(
    key: str,
    expected_type: type,
) -> Callable[[NodeContext], bool]:
    def evaluator(context: NodeContext) -> bool:
        value = context.get(key)
        return isinstance(value, expected_type)
    return evaluator
