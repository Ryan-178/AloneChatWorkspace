"""
顺序编排 - Sequential Orchestration
"""
import time
import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from alonechat.core.base_agent import BaseAgent, AgentResult
from alonechat.core.orchestrator import Orchestrator, WorkflowGraph, WorkflowNode


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    step_id: str
    step_name: str
    status: StepStatus
    input: Any = None
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: float = 0.0


@dataclass
class SequentialFlowResult:
    success: bool
    final_output: Any = None
    trajectory: List[StepResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    failed_step: Optional[str] = None


class SequentialFlow:
    """顺序执行流"""
    
    def __init__(self, steps: Optional[List[Dict]] = None):
        self.steps: List[Dict] = steps or []
    
    def add_step(self, step_id: str, step_name: str, task: Callable[[Any], Any]):
        """添加步骤"""
        self.steps.append({
            "id": step_id,
            "name": step_name,
            "task": task
        })
        return self
    
    async def run_async(self, initial_input: Any) -> SequentialFlowResult:
        """异步执行顺序流"""
        overall_start = time.time()
        trajectory: List[StepResult] = []
        result = initial_input
        
        for step in self.steps:
            step_result = StepResult(
                step_id=step["id"],
                step_name=step["name"],
                status=StepStatus.PENDING
            )
            step_start = time.time()
            step_result.status = StepStatus.RUNNING
            
            try:
                step_result.input = result
                task = step["task"]
                
                if asyncio.iscoroutinefunction(task):
                    output = await task(result)
                else:
                    output = task(result)
                
                step_result.output = output
                step_result.status = StepStatus.SUCCESS
                result = output
                
            except Exception as e:
                step_result.error = str(e)
                step_result.status = StepStatus.FAILED
                trajectory.append(step_result)
                
                total_duration = (time.time() - overall_start) * 1000
                return SequentialFlowResult(
                    success=False,
                    final_output=result,
                    trajectory=trajectory,
                    total_duration_ms=total_duration,
                    failed_step=step["id"]
                )
            finally:
                step_result.end_time = time.time()
                step_result.duration_ms = (step_result.end_time - step_start) * 1000
            
            trajectory.append(step_result)
        
        total_duration = (time.time() - overall_start) * 1000
        return SequentialFlowResult(
            success=True,
            final_output=result,
            trajectory=trajectory,
            total_duration_ms=total_duration
        )
    
    def run(self, initial_input: Any) -> SequentialFlowResult:
        """同步执行顺序流"""
        overall_start = time.time()
        trajectory: List[StepResult] = []
        result = initial_input
        
        for step in self.steps:
            step_result = StepResult(
                step_id=step["id"],
                step_name=step["name"],
                status=StepStatus.PENDING
            )
            step_start = time.time()
            step_result.status = StepStatus.RUNNING
            
            try:
                step_result.input = result
                task = step["task"]
                
                if asyncio.iscoroutinefunction(task):
                    loop = asyncio.get_event_loop()
                    output = loop.run_until_complete(task(result))
                else:
                    output = task(result)
                
                step_result.output = output
                step_result.status = StepStatus.SUCCESS
                result = output
                
            except Exception as e:
                step_result.error = str(e)
                step_result.status = StepStatus.FAILED
                trajectory.append(step_result)
                
                total_duration = (time.time() - overall_start) * 1000
                return SequentialFlowResult(
                    success=False,
                    final_output=result,
                    trajectory=trajectory,
                    total_duration_ms=total_duration,
                    failed_step=step["id"]
                )
            finally:
                step_result.end_time = time.time()
                step_result.duration_ms = (step_result.end_time - step_start) * 1000
            
            trajectory.append(step_result)
        
        total_duration = (time.time() - overall_start) * 1000
        return SequentialFlowResult(
            success=True,
            final_output=result,
            trajectory=trajectory,
            total_duration_ms=total_duration
        )


class SequentialOrchestrator(Orchestrator):
    """顺序编排器 - 执行多个Agent的顺序协作"""
    
    def __init__(self):
        self.agent_sequence: List[BaseAgent] = []
        self.agent_names: List[str] = []
    
    def add_agent(self, agent: BaseAgent, name: Optional[str] = None):
        """添加Agent到执行序列"""
        self.agent_sequence.append(agent)
        self.agent_names.append(name or f"agent_{len(self.agent_sequence)}")
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
        """顺序运行多个Agent，每个接收前一个的输出"""
        results = []
        current_input = task
        
        for i, agent in enumerate(agents):
            result = agent.run(current_input)
            results.append(result)
            current_input = result.answer
        
        return results
    
    async def run_multi_async(self, agents: List[BaseAgent], task: str) -> List[AgentResult]:
        """异步顺序运行多个Agent"""
        results = []
        current_input = task
        
        for agent in agents:
            if hasattr(agent, 'run_async'):
                result = await agent.run_async(current_input)
            else:
                result = agent.run(current_input)
            results.append(result)
            current_input = result.answer
        
        return results
    
    def run_workflow(self, graph: WorkflowGraph, initial_input: Any) -> Dict[str, Any]:
        """运行工作流图（顺序模式）"""
        flow = SequentialFlow()
        
        for node in graph.nodes:
            if node.agent:
                if isinstance(node.agent, BaseAgent):
                    flow.add_step(
                        step_id=node.id,
                        step_name=f"Agent: {node.id}",
                        task=lambda x, a=node.agent: a.run(x)
                    )
                elif callable(node.agent):
                    flow.add_step(
                        step_id=node.id,
                        step_name=f"Task: {node.id}",
                        task=node.agent
                    )
        
        result = flow.run(initial_input)
        
        return {
            "success": result.success,
            "final_output": result.final_output,
            "trajectory": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "status": s.status,
                    "duration_ms": s.duration_ms
                }
                for s in result.trajectory
            ],
            "total_duration_ms": result.total_duration_ms
        }
