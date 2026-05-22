"""
任务规划器

基于"为了行动而思考"理念的任务分解与规划：
- 将复杂任务分解为可执行的子任务
- 动态调整计划以响应环境反馈
- 支持多种分解策略
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import json

from ..agents.supervisor import Task, Subtask, TaskPriority, TaskStatus


class DecompositionStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    CONDITIONAL = "conditional"
    ADAPTIVE = "adaptive"


@dataclass
class PlanStep:
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    estimated_effort: float = 1.0
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())[:8]


@dataclass
class ExecutionPlan:
    id: str
    name: str
    description: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    strategy: DecompositionStrategy = DecompositionStrategy.SEQUENTIAL
    variables: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())[:12]
    
    def add_step(self, step: PlanStep) -> "ExecutionPlan":
        self.steps.append(step)
        return self
    
    def get_step(self, step_id: str) -> Optional[PlanStep]:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self, completed: set) -> List[PlanStep]:
        ready = []
        for step in self.steps:
            if step.id in completed:
                continue
            if all(dep in completed for dep in step.dependencies):
                ready.append(step)
        return sorted(ready, key=lambda s: -s.priority)
    
    def get_execution_order(self) -> List[List[PlanStep]]:
        completed = set()
        order = []
        
        while len(completed) < len(self.steps):
            ready = self.get_ready_steps(completed)
            if not ready:
                break
            order.append(ready)
            completed.update(s.id for s in ready)
        
        return order
    
    def validate(self) -> List[str]:
        errors = []
        step_ids = {s.id for s in self.steps}
        
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    errors.append(f"步骤 {step.id} 的依赖 {dep} 不存在")
        
        visited = set()
        path = set()
        
        def has_cycle(step_id: str) -> bool:
            if step_id in path:
                return True
            if step_id in visited:
                return False
            
            path.add(step_id)
            step = self.get_step(step_id)
            if step:
                for dep in step.dependencies:
                    if has_cycle(dep):
                        return True
            path.remove(step_id)
            visited.add(step_id)
            return False
        
        for step in self.steps:
            if has_cycle(step.id):
                errors.append(f"检测到循环依赖，涉及步骤 {step.id}")
                break
        
        return errors
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "dependencies": s.dependencies,
                    "assigned_agent": s.assigned_agent,
                    "estimated_effort": s.estimated_effort,
                    "priority": s.priority,
                    "metadata": s.metadata,
                }
                for s in self.steps
            ],
            "strategy": self.strategy.value,
            "variables": self.variables,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PlanResult:
    success: bool
    plan: Optional[ExecutionPlan] = None
    reasoning: str = ""
    alternatives: List[ExecutionPlan] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskPlanner:
    def __init__(
        self,
        model_client: Optional[Any] = None,
        max_depth: int = 5,
        max_steps: int = 20,
    ):
        self.model_client = model_client
        self.max_depth = max_depth
        self.max_steps = max_steps
        self._decomposers: Dict[DecompositionStrategy, callable] = {
            DecompositionStrategy.SEQUENTIAL: self._decompose_sequential,
            DecompositionStrategy.PARALLEL: self._decompose_parallel,
            DecompositionStrategy.HIERARCHICAL: self._decompose_hierarchical,
            DecompositionStrategy.CONDITIONAL: self._decompose_conditional,
            DecompositionStrategy.ADAPTIVE: self._decompose_adaptive,
        }
    
    def plan(
        self,
        task: Task,
        strategy: DecompositionStrategy = DecompositionStrategy.ADAPTIVE,
        context: Optional[Dict] = None,
    ) -> PlanResult:
        decomposer = self._decomposers.get(strategy)
        if not decomposer:
            return PlanResult(
                success=False,
                reasoning=f"未知的分解策略: {strategy}",
            )
        
        try:
            plan = decomposer(task, context or {})
            errors = plan.validate()
            
            if errors:
                return PlanResult(
                    success=False,
                    reasoning=f"计划验证失败: {errors}",
                )
            
            return PlanResult(
                success=True,
                plan=plan,
                reasoning=f"成功使用 {strategy.value} 策略分解任务",
                confidence=0.8,
            )
            
        except Exception as e:
            return PlanResult(
                success=False,
                reasoning=f"规划失败: {str(e)}",
            )
    
    def replan(
        self,
        original_plan: ExecutionPlan,
        feedback: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> PlanResult:
        failed_steps = feedback.get("failed_steps", [])
        new_info = feedback.get("new_info", {})
        
        new_steps = []
        for step in original_plan.steps:
            if step.id in failed_steps:
                new_step = PlanStep(
                    id=f"{step.id}_retry",
                    name=f"重试: {step.name}",
                    description=step.description,
                    dependencies=step.dependencies,
                    assigned_agent=step.assigned_agent,
                    estimated_effort=step.estimated_effort * 1.5,
                    priority=step.priority + 1,
                    metadata={**step.metadata, "retry": True},
                )
                new_steps.append(new_step)
            else:
                new_steps.append(step)
        
        if new_info.get("additional_steps"):
            for i, add_step in enumerate(new_info["additional_steps"]):
                new_steps.append(PlanStep(
                    id=f"additional_{i}",
                    name=add_step.get("name", f"额外步骤 {i}"),
                    description=add_step.get("description", ""),
                    dependencies=add_step.get("dependencies", []),
                    assigned_agent=add_step.get("agent"),
                    estimated_effort=add_step.get("effort", 1.0),
                ))
        
        new_plan = ExecutionPlan(
            id=f"{original_plan.id}_replan",
            name=f"重规划: {original_plan.name}",
            description=original_plan.description,
            steps=new_steps,
            strategy=original_plan.strategy,
            variables={**original_plan.variables, **new_info},
        )
        
        return PlanResult(
            success=True,
            plan=new_plan,
            reasoning="基于反馈重新规划",
            confidence=0.7,
        )
    
    def _decompose_sequential(
        self,
        task: Task,
        context: Dict,
    ) -> ExecutionPlan:
        steps = []
        
        analysis_step = PlanStep(
            id="analyze",
            name="分析任务",
            description=f"分析任务: {task.description}",
            assigned_agent="research_agent",
            estimated_effort=0.5,
            priority=10,
        )
        steps.append(analysis_step)
        
        plan_step = PlanStep(
            id="plan",
            name="制定计划",
            description="制定详细执行计划",
            dependencies=["analyze"],
            assigned_agent="supervisor",
            estimated_effort=0.5,
            priority=9,
        )
        steps.append(plan_step)
        
        execute_step = PlanStep(
            id="execute",
            name="执行任务",
            description="按计划执行",
            dependencies=["plan"],
            assigned_agent="code_agent",
            estimated_effort=task.metadata.get("complexity", 2.0),
            priority=8,
        )
        steps.append(execute_step)
        
        verify_step = PlanStep(
            id="verify",
            name="验证结果",
            description="验证执行结果",
            dependencies=["execute"],
            assigned_agent="test_agent",
            estimated_effort=0.5,
            priority=7,
        )
        steps.append(verify_step)
        
        return ExecutionPlan(
            name=f"顺序执行: {task.name}",
            description=task.description,
            steps=steps,
            strategy=DecompositionStrategy.SEQUENTIAL,
        )
    
    def _decompose_parallel(
        self,
        task: Task,
        context: Dict,
    ) -> ExecutionPlan:
        steps = []
        
        subtasks = task.metadata.get("subtasks", [])
        if not subtasks:
            subtasks = [
                {"name": f"子任务 {i}", "description": f"执行子任务 {i}"}
                for i in range(min(3, self.max_steps))
            ]
        
        for i, subtask in enumerate(subtasks[:self.max_steps]):
            steps.append(PlanStep(
                id=f"subtask_{i}",
                name=subtask.get("name", f"子任务 {i}"),
                description=subtask.get("description", ""),
                assigned_agent=subtask.get("agent", "code_agent"),
                estimated_effort=subtask.get("effort", 1.0),
                priority=subtask.get("priority", 5),
            ))
        
        merge_step = PlanStep(
            id="merge",
            name="合并结果",
            description="合并所有子任务结果",
            dependencies=[s.id for s in steps],
            assigned_agent="supervisor",
            estimated_effort=0.5,
            priority=10,
        )
        steps.append(merge_step)
        
        return ExecutionPlan(
            name=f"并行执行: {task.name}",
            description=task.description,
            steps=steps,
            strategy=DecompositionStrategy.PARALLEL,
        )
    
    def _decompose_hierarchical(
        self,
        task: Task,
        context: Dict,
    ) -> ExecutionPlan:
        steps = []
        depth = min(task.metadata.get("depth", 2), self.max_depth)
        
        def create_level(level: int, parent_deps: List[str]) -> List[str]:
            level_steps = []
            num_steps = min(2 ** level, self.max_steps - len(steps))
            
            for i in range(num_steps):
                step_id = f"level_{level}_task_{i}"
                steps.append(PlanStep(
                    id=step_id,
                    name=f"层级 {level} - 任务 {i}",
                    description=f"执行层级 {level} 的任务 {i}",
                    dependencies=parent_deps,
                    assigned_agent="code_agent",
                    estimated_effort=1.0 / (level + 1),
                    priority=10 - level,
                ))
                level_steps.append(step_id)
            
            return level_steps
        
        current_deps = []
        for level in range(depth):
            current_deps = create_level(level, current_deps)
        
        return ExecutionPlan(
            name=f"层次执行: {task.name}",
            description=task.description,
            steps=steps,
            strategy=DecompositionStrategy.HIERARCHICAL,
        )
    
    def _decompose_conditional(
        self,
        task: Task,
        context: Dict,
    ) -> ExecutionPlan:
        steps = []
        
        check_step = PlanStep(
            id="check_condition",
            name="检查条件",
            description="评估执行条件",
            assigned_agent="research_agent",
            estimated_effort=0.3,
            priority=10,
        )
        steps.append(check_step)
        
        conditions = task.metadata.get("conditions", ["default"])
        for i, cond in enumerate(conditions):
            steps.append(PlanStep(
                id=f"branch_{i}",
                name=f"分支: {cond}",
                description=f"条件 {cond} 的执行分支",
                dependencies=["check_condition"],
                assigned_agent="code_agent",
                estimated_effort=1.0,
                priority=8 - i,
                metadata={"condition": cond},
            ))
        
        steps.append(PlanStep(
            id="finalize",
            name="完成",
            description="完成条件执行",
            dependencies=[f"branch_{i}" for i in range(len(conditions))],
            assigned_agent="supervisor",
            estimated_effort=0.3,
            priority=7,
        ))
        
        return ExecutionPlan(
            name=f"条件执行: {task.name}",
            description=task.description,
            steps=steps,
            strategy=DecompositionStrategy.CONDITIONAL,
        )
    
    def _decompose_adaptive(
        self,
        task: Task,
        context: Dict,
    ) -> ExecutionPlan:
        complexity = task.metadata.get("complexity", 1.0)
        dependencies = task.metadata.get("dependencies", [])
        parallelism = task.metadata.get("parallelism", 0)
        
        if parallelism > 2 or len(dependencies) == 0:
            strategy = DecompositionStrategy.PARALLEL
        elif complexity > 3:
            strategy = DecompositionStrategy.HIERARCHICAL
        elif len(dependencies) > 0:
            strategy = DecompositionStrategy.SEQUENTIAL
        else:
            strategy = DecompositionStrategy.SEQUENTIAL
        
        base_plan = self._decomposers[strategy](task, context)
        base_plan.strategy = DecompositionStrategy.ADAPTIVE
        
        return base_plan
    
    def estimate_effort(self, plan: ExecutionPlan) -> float:
        total = 0.0
        completed = set()
        
        for level in plan.get_execution_order():
            level_effort = max(s.estimated_effort for s in level)
            total += level_effort
            completed.update(s.id for s in level)
        
        return total
    
    def get_critical_path(self, plan: ExecutionPlan) -> List[PlanStep]:
        if not plan.steps:
            return []
        
        earliest_finish = {}
        
        for level in plan.get_execution_order():
            for step in level:
                if not step.dependencies:
                    earliest_finish[step.id] = step.estimated_effort
                else:
                    max_dep_finish = max(
                        earliest_finish.get(dep, 0)
                        for dep in step.dependencies
                    )
                    earliest_finish[step.id] = (
                        max_dep_finish + step.estimated_effort
                    )
        
        if not earliest_finish:
            return []
        
        max_finish = max(earliest_finish.values())
        critical = []
        current_time = max_finish
        
        for step in reversed(plan.steps):
            if step.id not in earliest_finish:
                continue
            if abs(earliest_finish[step.id] - current_time) < 0.001:
                critical.insert(0, step)
                current_time -= step.estimated_effort
        
        return critical
