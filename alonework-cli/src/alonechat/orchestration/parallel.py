"""
并行编排 - Parallel Orchestration
支持多Agent并行执行
"""
import time
import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from alonechat.core.base_agent import BaseAgent, AgentResult
from alonechat.core.orchestrator import Orchestrator, WorkflowGraph, WorkflowNode


class ParallelTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ParallelTaskResult:
    task_id: str
    task_name: str
    status: ParallelTaskStatus
    input: Any = None
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: float = 0.0


@dataclass
class ParallelFlowResult:
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    results: List[ParallelTaskResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    failed_tasks: List[str] = field(default_factory=list)
    all_succeeded: bool = True


class ParallelFlow:
    """并行执行流"""
    
    def __init__(self, tasks: Optional[List[Dict]] = None):
        self.tasks: List[Dict] = tasks or []
        self.timeout: Optional[float] = None
    
    def add_task(self, task_id: str, task_name: str, task: Callable[[Any], Any], input_data: Any = None):
        """添加并行任务"""
        self.tasks.append({
            "id": task_id,
            "name": task_name,
            "task": task,
            "input": input_data
        })
        return self
    
    def set_timeout(self, seconds: float):
        """设置超时时间"""
        self.timeout = seconds
        return self
    
    async def run_async(self, shared_input: Optional[Any] = None) -> ParallelFlowResult:
        """异步执行并行流"""
        overall_start = time.time()
        
        async def execute_task(task_def: Dict) -> ParallelTaskResult:
            task_id = task_def["id"]
            task_name = task_def["name"]
            task = task_def["task"]
            task_input = task_def.get("input", shared_input)
            
            result = ParallelTaskResult(
                task_id=task_id,
                task_name=task_name,
                status=ParallelTaskStatus.PENDING,
                input=task_input
            )
            
            start_time = time.time()
            result.status = ParallelTaskStatus.RUNNING
            
            try:
                if asyncio.iscoroutinefunction(task):
                    if self.timeout:
                        output = await asyncio.wait_for(
                            task(task_input),
                            timeout=self.timeout
                        )
                    else:
                        output = await task(task_input)
                else:
                    loop = asyncio.get_event_loop()
                    if self.timeout:
                        output = await asyncio.wait_for(
                            loop.run_in_executor(None, task, task_input),
                            timeout=self.timeout
                        )
                    else:
                        output = await loop.run_in_executor(None, task, task_input)
                
                result.output = output
                result.status = ParallelTaskStatus.SUCCESS
                
            except asyncio.TimeoutError:
                result.error = "Task timed out"
                result.status = ParallelTaskStatus.TIMEOUT
                
            except Exception as e:
                result.error = str(e)
                result.status = ParallelTaskStatus.FAILED
                
            finally:
                result.end_time = time.time()
                result.duration_ms = (result.end_time - start_time) * 1000
                result.start_time = start_time
            
            return result
        
        coroutines = [execute_task(task) for task in self.tasks]
        results = await asyncio.gather(*coroutines)
        
        outputs: Dict[str, Any] = {}
        failed_tasks: List[str] = []
        all_succeeded = True
        
        for r in results:
            if r.status == ParallelTaskStatus.SUCCESS:
                outputs[r.task_id] = r.output
            else:
                failed_tasks.append(r.task_id)
                all_succeeded = False
        
        total_duration = (time.time() - overall_start) * 1000
        
        return ParallelFlowResult(
            success=all_succeeded,
            outputs=outputs,
            results=results,
            total_duration_ms=total_duration,
            failed_tasks=failed_tasks,
            all_succeeded=all_succeeded
        )
    
    def run(self, shared_input: Optional[Any] = None) -> ParallelFlowResult:
        """同步执行并行流"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.run_async(shared_input))


class ParallelOrchestrator(Orchestrator):
    """并行编排器 - 同时执行多个Agent"""
    
    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.agent_names: List[str] = []
        self.timeout: Optional[float] = None
    
    def add_agent(self, agent: BaseAgent, name: Optional[str] = None):
        """添加Agent到并行执行池"""
        self.agents.append(agent)
        self.agent_names.append(name or f"agent_{len(self.agents)}")
        return self
    
    def set_timeout(self, seconds: float):
        """设置超时时长"""
        self.timeout = seconds
        return self
    
    def run(self, agent: BaseAgent, task: str) -> AgentResult:
        """运行单个Agent"""
        return agent.run(task)
    
    async def run_async(self, agent: BaseAgent, task: str) -> AgentResult:
        """异步运行单个Agent"""
        if hasattr(agent, 'run_async'):
            return await agent.run_async(task)
        return agent.run(task)
    
    def run_multi(self, agents: List[BaseAgent], task: str) -> List[AgentResult]:
        """并行运行多个Agent，接收相同输入"""
        flow = ParallelFlow()
        
        for i, agent in enumerate(agents):
            flow.add_task(
                task_id=str(i),
                task_name=f"Agent_{i}",
                task=lambda x, a=agent: a.run(x),
                input_data=task
            )
        
        if self.timeout:
            flow.set_timeout(self.timeout)
        
        result = flow.run()
        
        agent_results: List[AgentResult] = []
        for task_result in result.results:
            if task_result.status == ParallelTaskStatus.SUCCESS:
                agent_results.append(task_result.output)
        
        return agent_results
    
    async def run_multi_async(self, agents: List[BaseAgent], task: str) -> List[AgentResult]:
        """异步并行运行多个Agent"""
        flow = ParallelFlow()
        
        for i, agent in enumerate(agents):
            flow.add_task(
                task_id=str(i),
                task_name=f"Agent_{i}",
                task=lambda x, a=agent: (
                    a.run_async(x) if hasattr(a, 'run_async') else a.run(x)
                ),
                input_data=task
            )
        
        if self.timeout:
            flow.set_timeout(self.timeout)
        
        result = await flow.run_async()
        
        agent_results: List[AgentResult] = []
        for task_result in result.results:
            if task_result.status == ParallelTaskStatus.SUCCESS:
                agent_results.append(task_result.output)
        
        return agent_results
    
    def run_workflow(self, graph: WorkflowGraph, initial_input: Any) -> Dict[str, Any]:
        """运行工作流图（并行模式）"""
        flow = ParallelFlow()
        
        for node in graph.nodes:
            if node.agent:
                if isinstance(node.agent, BaseAgent):
                    flow.add_task(
                        task_id=node.id,
                        task_name=f"Agent: {node.id}",
                        task=lambda x, a=node.agent: a.run(x),
                        input_data=initial_input
                    )
                elif callable(node.agent):
                    flow.add_task(
                        task_id=node.id,
                        task_name=f"Task: {node.id}",
                        task=node.agent,
                        input_data=initial_input
                    )
        
        result = flow.run()
        
        return {
            "success": result.success,
            "outputs": result.outputs,
            "all_succeeded": result.all_succeeded,
            "failed_tasks": result.failed_tasks,
            "results": [
                {
                    "task_id": r.task_id,
                    "task_name": r.task_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms
                }
                for r in result.results
            ],
            "total_duration_ms": result.total_duration_ms
        }
