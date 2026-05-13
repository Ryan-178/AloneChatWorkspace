"""
DAG工作流编排 - DAG Workflow Orchestration
支持有向无环图工作流
"""
import time
import asyncio
import networkx as nx
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from agent_framework.core.base_agent import BaseAgent, AgentResult
from agent_framework.core.orchestrator import Orchestrator, WorkflowGraph, WorkflowNode


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowEdge:
    """工作流边 - 定义依赖关系"""
    from_node: str
    to_node: str
    condition: Optional[str] = None  # 条件表达式，可选


@dataclass
class NodeExecutionResult:
    node_id: str
    node_name: str
    status: NodeStatus
    input: Any = None
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DAGWorkflowResult:
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    results: List[NodeExecutionResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    failed_nodes: List[str] = field(default_factory=list)
    skipped_nodes: List[str] = field(default_factory=list)


class DAGOrchestrator(Orchestrator):
    """DAG编排器 - 执行有向无环图工作流"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_tasks: Dict[str, Callable] = {}
        self.timeout: Optional[float] = None
    
    def add_node(self, node_id: str, task: Callable, name: Optional[str] = None):
        """添加节点"""
        self.graph.add_node(node_id, name=name or node_id)
        self.node_tasks[node_id] = task
        return self
    
    def add_edge(self, from_node: str, to_node: str, condition: Optional[str] = None):
        """添加边（依赖关系）"""
        self.graph.add_edge(from_node, to_node, condition=condition)
        return self
    
    def set_timeout(self, seconds: float):
        """设置超时时间"""
        self.timeout = seconds
        return self
    
    def validate(self) -> bool:
        """验证DAG的有效性（无环）"""
        try:
            nx.find_cycle(self.graph, orientation='original')
            return False
        except nx.NetworkXNoCycle:
            return True
    
    def get_ready_nodes(self, completed: Set[str], failed: Set[str], skipped: Set[str]) -> List[str]:
        """获取可以执行的就绪节点"""
        ready = []
        for node in self.graph.nodes:
            if node in completed or node in failed or node in skipped:
                continue
            
            predecessors = set(self.graph.predecessors(node))
            if not predecessors:
                ready.append(node)
                continue
            
            # 检查所有前置依赖是否已完成
            completed_preds = predecessors & completed
            if completed_preds == predecessors:
                ready.append(node)
            elif (predecessors & (failed | skipped)):
                skipped.add(node)
        
        return ready
    
    async def execute_node_async(
        self,
        node_id: str,
        outputs: Dict[str, Any],
        results: List[NodeExecutionResult]
    ) -> NodeExecutionResult:
        """异步执行单个节点"""
        node_name = self.graph.nodes[node_id].get('name', node_id)
        task = self.node_tasks[node_id]
        
        # 收集依赖节点的输出作为输入
        dependencies = list(self.graph.predecessors(node_id))
        input_data = {}
        for dep in dependencies:
            input_data[dep] = outputs.get(dep)
        
        result = NodeExecutionResult(
            node_id=node_id,
            node_name=node_name,
            status=NodeStatus.PENDING,
            input=input_data,
            dependencies=dependencies
        )
        
        start_time = time.time()
        result.status = NodeStatus.RUNNING
        
        try:
            if asyncio.iscoroutinefunction(task):
                if self.timeout:
                    output = await asyncio.wait_for(
                        task(input_data),
                        timeout=self.timeout
                    )
                else:
                    output = await task(input_data)
            else:
                loop = asyncio.get_event_loop()
                if self.timeout:
                    output = await asyncio.wait_for(
                        loop.run_in_executor(None, task, input_data),
                        timeout=self.timeout
                    )
                else:
                    output = await loop.run_in_executor(None, task, input_data)
            
            result.output = output
            result.status = NodeStatus.SUCCESS
            outputs[node_id] = output
            
        except Exception as e:
            result.error = str(e)
            result.status = NodeStatus.FAILED
            
        finally:
            result.end_time = time.time()
            result.duration_ms = (result.end_time - start_time) * 1000
            result.start_time = start_time
            results.append(result)
        
        return result
    
    async def run_workflow_async(self) -> DAGWorkflowResult:
        """异步运行DAG工作流"""
        overall_start = time.time()
        
        if not self.validate():
            return DAGWorkflowResult(
                success=False,
                failed_nodes=[],
                total_duration_ms=0.0
            )
        
        outputs: Dict[str, Any] = {}
        results: List[NodeExecutionResult] = []
        completed: Set[str] = set()
        failed: Set[str] = set()
        skipped: Set[str] = set()
        
        all_nodes = set(self.graph.nodes)
        
        while (completed | failed | skipped) != all_nodes:
            ready_nodes = self.get_ready_nodes(completed, failed, skipped)
            
            if not ready_nodes:
                # 没有就绪节点且还有未完成节点，说明有未解决的依赖
                remaining = all_nodes - (completed | failed | skipped)
                skipped.update(remaining)
                break
            
            # 并行执行所有就绪节点
            coroutines = [
                self.execute_node_async(node_id, outputs, results)
                for node_id in ready_nodes
            ]
            
            node_results = await asyncio.gather(*coroutines)
            
            for r in node_results:
                if r.status == NodeStatus.SUCCESS:
                    completed.add(r.node_id)
                elif r.status == NodeStatus.FAILED:
                    failed.add(r.node_id)
        
        total_duration = (time.time() - overall_start) * 1000
        
        return DAGWorkflowResult(
            success=len(failed) == 0,
            outputs=outputs,
            results=results,
            total_duration_ms=total_duration,
            failed_nodes=list(failed),
            skipped_nodes=list(skipped)
        )
    
    def run_workflow(self) -> DAGWorkflowResult:
        """同步运行DAG工作流"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.run_workflow_async())
    
    def run(self, agent: BaseAgent, task: str) -> AgentResult:
        """运行单个Agent（兼容接口）"""
        return agent.run(task)
    
    def run_multi(self, agents: List[BaseAgent], task: str) -> List[AgentResult]:
        """运行多个Agent（兼容接口，这里简单并行）"""
        # 简单地并行运行所有Agent
        from .parallel import ParallelOrchestrator
        parallel_orch = ParallelOrchestrator()
        for agent in agents:
            parallel_orch.add_agent(agent)
        return parallel_orch.run_multi(agents, task)
    
    def run_workflow_from_graph(self, graph: WorkflowGraph, initial_input: Any) -> Dict[str, Any]:
        """从WorkflowGraph运行工作流"""
        # 构建DAG
        for node in graph.nodes:
            if node.agent:
                if isinstance(node.agent, BaseAgent):
                    self.add_node(
                        node.id,
                        lambda x, a=node.agent: a.run(x),
                        name=f"Agent: {node.id}"
                    )
                elif callable(node.agent):
                    self.add_node(
                        node.id,
                        node.agent,
                        name=f"Task: {node.id}"
                    )
        
        for edge in graph.edges:
            self.add_edge(edge[0], edge[1])
        
        result = self.run_workflow()
        
        return {
            "success": result.success,
            "outputs": result.outputs,
            "failed_nodes": result.failed_nodes,
            "skipped_nodes": result.skipped_nodes,
            "results": [
                {
                    "node_id": r.node_id,
                    "node_name": r.node_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms
                }
                for r in result.results
            ],
            "total_duration_ms": result.total_duration_ms
        }
