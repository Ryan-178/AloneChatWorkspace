"""
工作流定义与引擎

核心概念：
- Workflow: 工作流定义，包含节点和边
- WorkflowEngine: 工作流引擎，负责执行工作流
- WorkflowContext: 执行上下文，维护状态和数据
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar
from uuid import uuid4
import asyncio
import json

T = TypeVar("T")


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeType(Enum):
    START = "start"
    END = "end"
    ACTION = "action"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    SUBWORKFLOW = "subworkflow"
    HUMAN = "human"


@dataclass
class Node:
    id: str
    name: str
    node_type: NodeType
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())[:8]


@dataclass
class Edge:
    source: str
    target: str
    condition: Optional[Callable[[Dict], bool]] = None
    label: str = ""
    
    def evaluate(self, context: Dict) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str = ""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())[:12]
    
    def add_node(self, node: Node) -> "WorkflowDefinition":
        self.nodes[node.id] = node
        return self
    
    def add_edge(
        self,
        source: str,
        target: str,
        condition: Optional[Callable] = None,
        label: str = ""
    ) -> "WorkflowDefinition":
        self.edges.append(Edge(source, target, condition, label))
        return self
    
    def get_start_node(self) -> Optional[Node]:
        for node in self.nodes.values():
            if node.node_type == NodeType.START:
                return node
        return None
    
    def get_next_nodes(self, node_id: str, context: Dict) -> List[Node]:
        next_nodes = []
        for edge in self.edges:
            if edge.source == node_id and edge.evaluate(context):
                if edge.target in self.nodes:
                    next_nodes.append(self.nodes[edge.target])
        return next_nodes
    
    def get_predecessors(self, node_id: str) -> List[Node]:
        predecessors = []
        for edge in self.edges:
            if edge.target == node_id:
                if edge.source in self.nodes:
                    predecessors.append(self.nodes[edge.source])
        return predecessors
    
    def validate(self) -> List[str]:
        errors = []
        
        start_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.START]
        if len(start_nodes) == 0:
            errors.append("工作流必须有一个开始节点")
        elif len(start_nodes) > 1:
            errors.append("工作流只能有一个开始节点")
        
        end_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.END]
        if len(end_nodes) == 0:
            errors.append("工作流必须有一个结束节点")
        
        for edge in self.edges:
            if edge.source not in self.nodes:
                errors.append(f"边的源节点 {edge.source} 不存在")
            if edge.target not in self.nodes:
                errors.append(f"边的目标节点 {edge.target} 不存在")
        
        return errors
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": {
                nid: {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "config": n.config,
                    "metadata": n.metadata,
                }
                for nid, n in self.nodes.items()
            },
            "edges": [
                {"source": e.source, "target": e.target, "label": e.label}
                for e in self.edges
            ],
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowDefinition":
        nodes = {}
        for nid, ndata in data.get("nodes", {}).items():
            nodes[nid] = Node(
                id=ndata["id"],
                name=ndata["name"],
                node_type=NodeType(ndata["type"]),
                config=ndata.get("config", {}),
                metadata=ndata.get("metadata", {}),
            )
        
        edges = []
        for edata in data.get("edges", []):
            edges.append(Edge(
                source=edata["source"],
                target=edata["target"],
                label=edata.get("label", ""),
            ))
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=nodes,
            edges=edges,
            variables=data.get("variables", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(),
        )


Workflow = WorkflowDefinition


@dataclass
class WorkflowContext:
    workflow_id: str
    execution_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    current_node: Optional[str] = None
    visited_nodes: Set[str] = field(default_factory=set)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.execution_id:
            self.execution_id = str(uuid4())[:12]
    
    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
    
    def set_node_output(self, node_id: str, output: Any) -> None:
        self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str) -> Any:
        return self.node_outputs.get(node_id)
    
    def mark_visited(self, node_id: str) -> None:
        self.visited_nodes.add(node_id)
    
    def is_visited(self, node_id: str) -> bool:
        return node_id in self.visited_nodes
    
    def add_error(self, node_id: str, error: str, details: Any = None) -> None:
        self.errors.append({
            "node_id": node_id,
            "error": error,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "variables": self.variables,
            "node_outputs": self.node_outputs,
            "current_node": self.current_node,
            "visited_nodes": list(self.visited_nodes),
            "errors": self.errors,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat(),
        }


@dataclass
class WorkflowResult:
    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    output: Any = None
    context: Optional[WorkflowContext] = None
    execution_time: float = 0.0
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "output": self.output,
            "context": self.context.to_dict() if self.context else None,
            "execution_time": self.execution_time,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at else None,
        }


class WorkflowEngine:
    def __init__(
        self,
        node_executor: Optional[Callable] = None,
        max_parallel: int = 10,
        timeout: float = 3600.0,
    ):
        self.node_executor = node_executor
        self.max_parallel = max_parallel
        self.timeout = timeout
        self._workflows: Dict[str, Workflow] = {}
        self._contexts: Dict[str, WorkflowContext] = {}
        self._running: Dict[str, asyncio.Task] = {}
    
    def register_workflow(self, workflow: Workflow) -> None:
        errors = workflow.validate()
        if errors:
            raise ValueError(f"工作流验证失败: {errors}")
        self._workflows[workflow.id] = workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)
    
    def create_context(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict] = None,
    ) -> WorkflowContext:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            execution_id="",
            variables={**workflow.variables, **(initial_variables or {})},
        )
        self._contexts[context.execution_id] = context
        return context
    
    async def execute(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict] = None,
        context: Optional[WorkflowContext] = None,
    ) -> WorkflowResult:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        if context is None:
            context = self.create_context(workflow_id, initial_variables)
        
        start_time = datetime.now()
        status = WorkflowStatus.RUNNING
        output = None
        
        try:
            start_node = workflow.get_start_node()
            if not start_node:
                raise ValueError("工作流没有开始节点")
            
            output = await self._execute_from_node(
                workflow, start_node.id, context
            )
            status = WorkflowStatus.COMPLETED
            
        except asyncio.CancelledError:
            status = WorkflowStatus.CANCELLED
        except Exception as e:
            status = WorkflowStatus.FAILED
            context.add_error("workflow", str(e))
        finally:
            execution_time = (datetime.now() - start_time).total_seconds()
        
        return WorkflowResult(
            workflow_id=workflow_id,
            execution_id=context.execution_id,
            status=status,
            output=output,
            context=context,
            execution_time=execution_time,
            completed_at=datetime.now(),
        )
    
    async def _execute_from_node(
        self,
        workflow: Workflow,
        node_id: str,
        context: WorkflowContext,
    ) -> Any:
        if node_id in context.visited_nodes:
            return context.get_node_output(node_id)
        
        node = workflow.nodes.get(node_id)
        if not node:
            raise ValueError(f"节点 {node_id} 不存在")
        
        context.current_node = node_id
        context.mark_visited(node_id)
        
        if node.node_type == NodeType.END:
            return context.get_node_output(
                workflow.get_predecessors(node_id)[0].id
            ) if workflow.get_predecessors(node_id) else None
        
        node_output = await self._execute_node(node, context)
        context.set_node_output(node_id, node_output)
        
        next_nodes = workflow.get_next_nodes(
            node_id, {"output": node_output, **context.variables}
        )
        
        if not next_nodes:
            return node_output
        
        if len(next_nodes) == 1:
            return await self._execute_from_node(
                workflow, next_nodes[0].id, context
            )
        
        tasks = [
            self._execute_from_node(workflow, n.id, context)
            for n in next_nodes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results[-1] if results else node_output
    
    async def _execute_node(
        self,
        node: Node,
        context: WorkflowContext,
    ) -> Any:
        if self.node_executor:
            return await self.node_executor(node, context)
        
        return {
            "node_id": node.id,
            "node_name": node.name,
            "type": node.node_type.value,
            "config": node.config,
        }
    
    def cancel(self, execution_id: str) -> bool:
        if execution_id in self._running:
            self._running[execution_id].cancel()
            return True
        return False
    
    def get_context(self, execution_id: str) -> Optional[WorkflowContext]:
        return self._contexts.get(execution_id)
    
    def list_workflows(self) -> List[Dict]:
        return [
            {"id": w.id, "name": w.name, "description": w.description}
            for w in self._workflows.values()
        ]
