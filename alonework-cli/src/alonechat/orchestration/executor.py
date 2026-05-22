"""
工作流执行器

负责执行工作流并与Agent层集成：
- 管理执行生命周期
- 处理节点执行
- 收集执行轨迹
- 支持暂停/恢复/取消
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4
import asyncio
import time

from .workflow import (
    Workflow,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    Node,
    NodeType,
)
from .planner import ExecutionPlan, PlanStep


class ExecutionState(Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionConfig:
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 3600.0
    parallel_limit: int = 10
    checkpoint_interval: float = 60.0
    enable_trajectory: bool = True
    enable_reflection: bool = True
    stop_on_error: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    execution_id: str
    workflow_id: str
    status: ExecutionState
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    final_output: Any = None
    total_time: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    trajectory: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "step_results": {
                sid: {
                    "step_id": sr.step_id,
                    "success": sr.success,
                    "output": sr.output,
                    "error": sr.error,
                    "execution_time": sr.execution_time,
                    "retries": sr.retries,
                }
                for sid, sr in self.step_results.items()
            },
            "final_output": self.final_output,
            "total_time": self.total_time,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at else None,
            "errors": self.errors,
        }


@dataclass
class Checkpoint:
    execution_id: str
    step_id: str
    context_snapshot: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "step_id": self.step_id,
            "context_snapshot": self.context_snapshot,
            "timestamp": self.timestamp.isoformat(),
        }


class WorkflowExecutor:
    def __init__(
        self,
        config: Optional[ExecutionConfig] = None,
        agent_factory: Optional[Callable] = None,
        trajectory_collector: Optional[Any] = None,
    ):
        self.config = config or ExecutionConfig()
        self.agent_factory = agent_factory
        self.trajectory_collector = trajectory_collector
        self._executions: Dict[str, ExecutionResult] = {}
        self._contexts: Dict[str, WorkflowContext] = {}
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._state: ExecutionState = ExecutionState.IDLE
        self._current_execution: Optional[str] = None
        self._pause_event: Optional[asyncio.Event] = None
        self._cancel_flag: bool = False
    
    @property
    def state(self) -> ExecutionState:
        return self._state
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_context: Optional[Dict] = None,
    ) -> ExecutionResult:
        execution_id = str(uuid4())[:12]
        self._current_execution = execution_id
        self._state = ExecutionState.PREPARING
        self._cancel_flag = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        
        context = WorkflowContext(
            workflow_id=workflow.id,
            execution_id=execution_id,
            variables=initial_context or {},
        )
        self._contexts[execution_id] = context
        
        result = ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow.id,
            status=ExecutionState.RUNNING,
        )
        self._executions[execution_id] = result
        
        start_time = time.time()
        self._state = ExecutionState.RUNNING
        
        try:
            start_node = workflow.get_start_node()
            if not start_node:
                raise ValueError("工作流没有开始节点")
            
            output = await self._execute_from_node(
                workflow, start_node.id, context, result
            )
            
            result.final_output = output
            result.status = ExecutionState.COMPLETED
            self._state = ExecutionState.COMPLETED
            
        except asyncio.CancelledError:
            result.status = ExecutionState.CANCELLED
            self._state = ExecutionState.CANCELLED
            result.errors.append({
                "type": "cancelled",
                "message": "执行被取消",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            result.status = ExecutionState.FAILED
            self._state = ExecutionState.FAILED
            result.errors.append({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            })
        finally:
            result.total_time = time.time() - start_time
            result.completed_at = datetime.now()
        
        return result
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        step_executor: Optional[Callable] = None,
    ) -> ExecutionResult:
        execution_id = str(uuid4())[:12]
        self._current_execution = execution_id
        self._cancel_flag = False
        
        result = ExecutionResult(
            execution_id=execution_id,
            workflow_id=plan.id,
            status=ExecutionState.RUNNING,
        )
        self._executions[execution_id] = result
        
        start_time = time.time()
        completed_steps: set = set()
        
        try:
            while len(completed_steps) < len(plan.steps):
                if self._cancel_flag:
                    raise asyncio.CancelledError()
                
                await self._wait_if_paused()
                
                ready_steps = plan.get_ready_steps(completed_steps)
                if not ready_steps:
                    break
                
                for step in ready_steps:
                    step_result = await self._execute_plan_step(
                        step, step_executor, result
                    )
                    result.step_results[step.id] = step_result
                    
                    if step_result.success:
                        completed_steps.add(step.id)
                    elif self.config.stop_on_error:
                        raise RuntimeError(
                            f"步骤 {step.id} 失败: {step_result.error}"
                        )
                
                if self.config.enable_trajectory:
                    self._record_trajectory(result, completed_steps)
            
            result.status = ExecutionState.COMPLETED
            result.final_output = self._get_final_output(result, plan)
            
        except asyncio.CancelledError:
            result.status = ExecutionState.CANCELLED
        except Exception as e:
            result.status = ExecutionState.FAILED
            result.errors.append({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            })
        finally:
            result.total_time = time.time() - start_time
            result.completed_at = datetime.now()
        
        return result
    
    async def _execute_from_node(
        self,
        workflow: Workflow,
        node_id: str,
        context: WorkflowContext,
        result: ExecutionResult,
    ) -> Any:
        if self._cancel_flag:
            raise asyncio.CancelledError()
        
        await self._wait_if_paused()
        
        if node_id in context.visited_nodes:
            return context.get_node_output(node_id)
        
        node = workflow.nodes.get(node_id)
        if not node:
            raise ValueError(f"节点 {node_id} 不存在")
        
        context.current_node = node_id
        context.mark_visited(node_id)
        
        if node.node_type == NodeType.END:
            predecessors = workflow.get_predecessors(node_id)
            if predecessors:
                return context.get_node_output(predecessors[0].id)
            return None
        
        node_output = await self._execute_node(node, context)
        context.set_node_output(node_id, node_output)
        
        step_result = StepResult(
            step_id=node_id,
            success=True,
            output=node_output,
        )
        result.step_results[node_id] = step_result
        
        if self.config.enable_trajectory:
            result.trajectory.append({
                "node_id": node_id,
                "node_type": node.node_type.value,
                "output": node_output,
                "timestamp": datetime.now().isoformat(),
            })
        
        next_nodes = workflow.get_next_nodes(
            node_id, {"output": node_output, **context.variables}
        )
        
        if not next_nodes:
            return node_output
        
        if len(next_nodes) == 1:
            return await self._execute_from_node(
                workflow, next_nodes[0].id, context, result
            )
        
        tasks = [
            self._execute_from_node(workflow, n.id, context, result)
            for n in next_nodes[:self.config.parallel_limit]
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results[-1] if results else node_output
    
    async def _execute_node(
        self,
        node: Node,
        context: WorkflowContext,
    ) -> Any:
        start_time = time.time()
        retries = 0
        last_error = None
        
        while retries <= self.config.max_retries:
            try:
                if self.agent_factory:
                    agent = self.agent_factory(node.assigned_agent)
                    if agent:
                        return await agent.execute(
                            node.config,
                            context.variables,
                        )
                
                return await self._default_node_executor(node, context)
                
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * retries)
        
        raise RuntimeError(f"节点执行失败: {last_error}")
    
    async def _default_node_executor(
        self,
        node: Node,
        context: WorkflowContext,
    ) -> Any:
        return {
            "node_id": node.id,
            "node_name": node.name,
            "node_type": node.node_type.value,
            "config": node.config,
            "context_vars": context.variables,
        }
    
    async def _execute_plan_step(
        self,
        step: PlanStep,
        executor: Optional[Callable],
        result: ExecutionResult,
    ) -> StepResult:
        start_time = time.time()
        retries = 0
        last_error = None
        
        while retries <= self.config.max_retries:
            try:
                if executor:
                    output = await executor(step, result.step_results)
                else:
                    output = await self._default_step_executor(step, result)
                
                return StepResult(
                    step_id=step.id,
                    success=True,
                    output=output,
                    execution_time=time.time() - start_time,
                    retries=retries,
                )
                
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * retries)
        
        return StepResult(
            step_id=step.id,
            success=False,
            error=str(last_error),
            execution_time=time.time() - start_time,
            retries=retries,
        )
    
    async def _default_step_executor(
        self,
        step: PlanStep,
        result: ExecutionResult,
    ) -> Any:
        return {
            "step_id": step.id,
            "step_name": step.name,
            "description": step.description,
        }
    
    async def _wait_if_paused(self) -> None:
        if self._pause_event:
            await self._pause_event.wait()
    
    def _record_trajectory(
        self,
        result: ExecutionResult,
        completed_steps: set,
    ) -> None:
        result.trajectory.append({
            "completed_steps": list(completed_steps),
            "timestamp": datetime.now().isoformat(),
        })
    
    def _get_final_output(
        self,
        result: ExecutionResult,
        plan: ExecutionPlan,
    ) -> Any:
        if not plan.steps:
            return None
        
        last_step = plan.steps[-1]
        if last_step.id in result.step_results:
            return result.step_results[last_step.id].output
        return None
    
    def pause(self) -> bool:
        if self._state == ExecutionState.RUNNING:
            self._state = ExecutionState.PAUSED
            if self._pause_event:
                self._pause_event.clear()
            return True
        return False
    
    def resume(self) -> bool:
        if self._state == ExecutionState.PAUSED:
            self._state = ExecutionState.RUNNING
            if self._pause_event:
                self._pause_event.set()
            return True
        return False
    
    def cancel(self) -> bool:
        if self._state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            self._cancel_flag = True
            if self._pause_event:
                self._pause_event.set()
            return True
        return False
    
    def create_checkpoint(
        self,
        execution_id: str,
        step_id: str,
    ) -> Optional[Checkpoint]:
        context = self._contexts.get(execution_id)
        if not context:
            return None
        
        checkpoint = Checkpoint(
            execution_id=execution_id,
            step_id=step_id,
            context_snapshot=context.to_dict(),
        )
        self._checkpoints[f"{execution_id}_{step_id}"] = checkpoint
        return checkpoint
    
    def restore_checkpoint(
        self,
        execution_id: str,
        step_id: str,
    ) -> Optional[WorkflowContext]:
        checkpoint = self._checkpoints.get(f"{execution_id}_{step_id}")
        if not checkpoint:
            return None
        
        context = WorkflowContext(
            workflow_id=checkpoint.context_snapshot["workflow_id"],
            execution_id=checkpoint.context_snapshot["execution_id"],
            variables=checkpoint.context_snapshot["variables"],
            node_outputs=checkpoint.context_snapshot["node_outputs"],
            current_node=checkpoint.context_snapshot["current_node"],
            visited_nodes=set(checkpoint.context_snapshot["visited_nodes"]),
        )
        return context
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        return self._executions.get(execution_id)
    
    def get_context(self, execution_id: str) -> Optional[WorkflowContext]:
        return self._contexts.get(execution_id)
    
    def list_executions(self) -> List[Dict]:
        return [
            {
                "execution_id": r.execution_id,
                "workflow_id": r.workflow_id,
                "status": r.status.value,
                "total_time": r.total_time,
                "started_at": r.started_at.isoformat(),
            }
            for r in self._executions.values()
        ]
