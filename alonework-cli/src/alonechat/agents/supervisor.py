"""
主管Agent模块 / Supervisor Agent Module

负责任务分解、分配、协调和监督
Responsible for task decomposition, assignment, coordination and supervision

不做训练，只记录交互数据
No training, only records interaction data
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from uuid import uuid4
import json


@dataclass
class Task:
    """
    任务定义 / Task Definition
    
    定义一个待执行的任务
    Defines a task to be executed
    """
    id: str
    description: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    timeout: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "params": self.params,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }


@dataclass
class Subtask(Task):
    """
    子任务 / Subtask
    
    从主任务分解出的子任务
    Subtask decomposed from main task
    """
    parent_id: str = ""
    assigned_agent: str = ""
    status: str = "pending"
    result: Any = None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        data = super().to_dict()
        data.update({
            "parent_id": self.parent_id,
            "assigned_agent": self.assigned_agent,
            "status": self.status,
        })
        return data


@dataclass
class Plan:
    """
    执行计划 / Execution Plan
    
    包含任务分解后的完整执行计划
    Contains complete execution plan after task decomposition
    """
    plan_id: str
    task: Task
    subtasks: list[Subtask]
    dependencies: dict[str, list[str]]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def execution_order(self) -> list[Subtask]:
        """
        返回拓扑排序后的执行顺序
        Returns execution order after topological sort
        """
        return self._topological_sort()
    
    def _topological_sort(self) -> list[Subtask]:
        """
        拓扑排序 / Topological sort
        
        Returns:
            排序后的子任务列表 / Sorted list of subtasks
        """
        subtask_map = {s.id: s for s in self.subtasks}
        in_degree = {s.id: 0 for s in self.subtasks}
        
        for subtask_id, deps in self.dependencies.items():
            for dep_id in deps:
                if dep_id in in_degree:
                    in_degree[subtask_id] = in_degree.get(subtask_id, 0) + 1
        
        queue = [s for s in self.subtasks if in_degree[s.id] == 0]
        result = []
        
        while queue:
            queue.sort(key=lambda x: x.priority, reverse=True)
            current = queue.pop(0)
            result.append(current)
            
            for subtask_id, deps in self.dependencies.items():
                if current.id in deps:
                    in_degree[subtask_id] -= 1
                    if in_degree[subtask_id] == 0 and subtask_id in subtask_map:
                        if subtask_map[subtask_id] not in result and subtask_map[subtask_id] not in queue:
                            queue.append(subtask_map[subtask_id])
        
        for subtask in self.subtasks:
            if subtask not in result:
                result.append(subtask)
        
        return result
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "plan_id": self.plan_id,
            "task": self.task.to_dict(),
            "subtasks": [s.to_dict() for s in self.subtasks],
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "status": self.status,
            "metadata": self.metadata,
        }


class SupervisorAgent:
    """
    主管Agent / Supervisor Agent
    
    负责任务分解、分配、协调和监督
    Responsible for task decomposition, assignment, coordination and supervision
    
    不做训练，只记录交互数据
    No training, only records interaction data
    """
    
    def __init__(
        self,
        model: Any,
        environment: Any,
        trajectory_recorder: Any = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化主管Agent / Initialize supervisor agent
        
        Args:
            model: 模型实例（DeepSeek V4 Flash）/ Model instance
            environment: 环境实例 / Environment instance
            trajectory_recorder: 轨迹记录器 / Trajectory recorder
            config: 配置字典 / Configuration dictionary
        """
        self.model = model
        self.environment = environment
        self.trajectory_recorder = trajectory_recorder
        self.config = config or {}
        
        self.workers: dict[str, "WorkerAgent"] = {}
        self.current_plan: Plan | None = None
        self.execution_results: dict[str, Any] = {}
        
        self.max_workers = self.config.get("max_workers", 4)
        self.planning_depth = self.config.get("planning_depth", 3)
        self.reflection_enabled = self.config.get("reflection_enabled", True)
        self.timeout = self.config.get("timeout", 600)
    
    def register_worker(self, worker: "WorkerAgent") -> None:
        """
        注册工作Agent / Register worker agent
        
        Args:
            worker: 工作Agent实例 / Worker agent instance
        """
        self.workers[worker.id] = worker
    
    def unregister_worker(self, worker_id: str) -> None:
        """
        注销工作Agent / Unregister worker agent
        
        Args:
            worker_id: 工作Agent标识 / Worker agent identifier
        """
        if worker_id in self.workers:
            del self.workers[worker_id]
    
    async def plan(self, task: Task) -> Plan:
        """
        任务规划 / Task planning
        
        Args:
            task: 任务对象 / Task object
            
        Returns:
            执行计划 / Execution plan
        """
        analysis = await self._analyze(task)
        
        subtasks = await self._decompose(task, analysis)
        
        assignments = await self._assign(subtasks)
        
        dependencies = self._build_dependencies(subtasks)
        
        plan = Plan(
            plan_id=str(uuid4()),
            task=task,
            subtasks=subtasks,
            dependencies=dependencies,
        )
        
        self.current_plan = plan
        
        return plan
    
    async def _analyze(self, task: Task) -> dict[str, Any]:
        """
        分析任务 / Analyze task
        
        Args:
            task: 任务对象 / Task object
            
        Returns:
            分析结果 / Analysis result
        """
        prompt = f"""分析以下任务，识别其类型、复杂度和关键要素：

任务描述: {task.description}
任务类型: {task.type}
任务参数: {json.dumps(task.params, ensure_ascii=False)}

请输出JSON格式的分析结果，包含：
- complexity: 复杂度评估 (simple/medium/complex)
- key_elements: 关键要素列表
- suggested_approach: 建议的处理方法
- potential_challenges: 潜在挑战
"""
        
        try:
            if hasattr(self.model, 'chat'):
                response = await self.model.chat(prompt)
            else:
                response = {"complexity": "medium", "key_elements": [], "suggested_approach": "decompose"}
            
            if isinstance(response, str):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {"complexity": "medium", "raw": response}
            return response
        except Exception as e:
            return {"complexity": "medium", "error": str(e)}
    
    async def _decompose(
        self,
        task: Task,
        analysis: dict[str, Any],
    ) -> list[Subtask]:
        """
        分解任务 / Decompose task
        
        Args:
            task: 任务对象 / Task object
            analysis: 分析结果 / Analysis result
            
        Returns:
            子任务列表 / List of subtasks
        """
        complexity = analysis.get("complexity", "medium")
        
        if complexity == "simple":
            return [Subtask(
                id=f"{task.id}_0",
                description=task.description,
                type=task.type,
                params=task.params,
                parent_id=task.id,
            )]
        
        prompt = f"""将以下任务分解为可并行执行的子任务：

任务描述: {task.description}
任务类型: {task.type}
任务参数: {json.dumps(task.params, ensure_ascii=False)}
分析结果: {json.dumps(analysis, ensure_ascii=False)}

请输出JSON格式的子任务列表，每个子任务包含：
- id: 子任务ID (格式: {task.id}_0, {task.id}_1, ...)
- description: 子任务描述
- type: 子任务类型 (code/data/research/test)
- params: 子任务参数
- dependencies: 依赖的其他子任务ID列表
- priority: 优先级 (0-10, 数字越大优先级越高)
"""
        
        try:
            if hasattr(self.model, 'chat'):
                response = await self.model.chat(prompt)
            else:
                response = []
            
            if isinstance(response, str):
                try:
                    subtasks_data = json.loads(response)
                except json.JSONDecodeError:
                    subtasks_data = []
            else:
                subtasks_data = response if isinstance(response, list) else []
            
            subtasks = []
            for i, st_data in enumerate(subtasks_data):
                subtask = Subtask(
                    id=st_data.get("id", f"{task.id}_{i}"),
                    description=st_data.get("description", ""),
                    type=st_data.get("type", "code"),
                    params=st_data.get("params", {}),
                    dependencies=st_data.get("dependencies", []),
                    priority=st_data.get("priority", 0),
                    parent_id=task.id,
                )
                subtasks.append(subtask)
            
            if not subtasks:
                subtasks = [Subtask(
                    id=f"{task.id}_0",
                    description=task.description,
                    type=task.type,
                    params=task.params,
                    parent_id=task.id,
                )]
            
            return subtasks
        except Exception as e:
            return [Subtask(
                id=f"{task.id}_0",
                description=task.description,
                type=task.type,
                params=task.params,
                parent_id=task.id,
                metadata={"error": str(e)},
            )]
    
    async def _assign(self, subtasks: list[Subtask]) -> dict[str, str]:
        """
        分配子任务给Worker / Assign subtasks to workers
        
        Args:
            subtasks: 子任务列表 / List of subtasks
            
        Returns:
            分配结果 / Assignment result
        """
        assignments = {}
        
        type_to_worker = {
            "code": "code_agent",
            "data": "data_agent",
            "research": "research_agent",
            "test": "test_agent",
        }
        
        for subtask in subtasks:
            worker_type = type_to_worker.get(subtask.type, "code_agent")
            
            if worker_type in self.workers:
                subtask.assigned_agent = worker_type
                assignments[subtask.id] = worker_type
            else:
                for worker_id in self.workers:
                    subtask.assigned_agent = worker_id
                    assignments[subtask.id] = worker_id
                    break
        
        return assignments
    
    def _build_dependencies(
        self,
        subtasks: list[Subtask],
    ) -> dict[str, list[str]]:
        """
        构建依赖关系 / Build dependencies
        
        Args:
            subtasks: 子任务列表 / List of subtasks
            
        Returns:
            依赖关系字典 / Dependencies dictionary
        """
        dependencies = {}
        for subtask in subtasks:
            dependencies[subtask.id] = subtask.dependencies
        return dependencies
    
    async def coordinate(self, plan: Plan) -> dict[str, Any]:
        """
        协调执行 / Coordinate execution
        
        Args:
            plan: 执行计划 / Execution plan
            
        Returns:
            执行结果 / Execution results
        """
        results = {}
        
        for subtask in plan.execution_order:
            if not self._check_dependencies(subtask, results):
                await self._handle_dependency_failure(subtask, results)
                continue
            
            worker = self._select_worker(subtask)
            if not worker:
                results[subtask.id] = {
                    "success": False,
                    "error": f"No worker available for subtask {subtask.id}",
                }
                continue
            
            try:
                result = await worker.execute(subtask, context=results)
                results[subtask.id] = result
                subtask.status = "completed" if result.get("success", False) else "failed"
                
                if not result.get("success", False):
                    plan = await self._replan(plan, subtask, result)
                    
            except Exception as e:
                results[subtask.id] = {
                    "success": False,
                    "error": str(e),
                }
                subtask.status = "failed"
        
        return results
    
    def _check_dependencies(
        self,
        subtask: Subtask,
        results: dict[str, Any],
    ) -> bool:
        """
        检查依赖是否满足 / Check if dependencies are satisfied
        
        Args:
            subtask: 子任务对象 / Subtask object
            results: 已完成的结果 / Completed results
            
        Returns:
            是否满足 / Whether satisfied
        """
        for dep_id in subtask.dependencies:
            if dep_id not in results:
                return False
            if not results[dep_id].get("success", False):
                return False
        return True
    
    async def _handle_dependency_failure(
        self,
        subtask: Subtask,
        results: dict[str, Any],
    ) -> None:
        """
        处理依赖失败 / Handle dependency failure
        
        Args:
            subtask: 子任务对象 / Subtask object
            results: 结果字典 / Results dictionary
        """
        results[subtask.id] = {
            "success": False,
            "error": f"Dependency not satisfied for subtask {subtask.id}",
            "dependencies": subtask.dependencies,
        }
        subtask.status = "skipped"
    
    def _select_worker(self, subtask: Subtask) -> "WorkerAgent | None":
        """
        选择Worker / Select worker
        
        Args:
            subtask: 子任务对象 / Subtask object
            
        Returns:
            Worker实例 / Worker instance
        """
        worker_id = subtask.assigned_agent
        return self.workers.get(worker_id)
    
    async def _replan(
        self,
        plan: Plan,
        failed_subtask: Subtask,
        result: dict[str, Any],
    ) -> Plan:
        """
        动态重规划 / Dynamic replanning
        
        Args:
            plan: 当前计划 / Current plan
            failed_subtask: 失败的子任务 / Failed subtask
            result: 失败结果 / Failure result
            
        Returns:
            新计划 / New plan
        """
        if not self.reflection_enabled:
            return plan
        
        failure_analysis = await self._analyze_failure(failed_subtask, result)
        
        decision = await self._decide_recovery(failure_analysis)
        
        if decision == "retry":
            failed_subtask.status = "pending"
            return plan
        elif decision == "skip":
            failed_subtask.status = "skipped"
            return plan
        elif decision == "alternative":
            alternative = await self._generate_alternative(failed_subtask)
            if alternative:
                plan.subtasks.append(alternative)
                plan.dependencies[alternative.id] = []
        
        return plan
    
    async def _analyze_failure(
        self,
        subtask: Subtask,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        分析失败原因 / Analyze failure
        
        Args:
            subtask: 子任务对象 / Subtask object
            result: 失败结果 / Failure result
            
        Returns:
            分析结果 / Analysis result
        """
        return {
            "subtask_id": subtask.id,
            "error": result.get("error", "Unknown error"),
            "type": subtask.type,
            "suggestion": "Consider retrying with different parameters",
        }
    
    async def _decide_recovery(
        self,
        failure_analysis: dict[str, Any],
    ) -> str:
        """
        决定恢复策略 / Decide recovery strategy
        
        Args:
            failure_analysis: 失败分析 / Failure analysis
            
        Returns:
            恢复策略 / Recovery strategy
        """
        return "retry"
    
    async def _generate_alternative(
        self,
        subtask: Subtask,
    ) -> Subtask | None:
        """
        生成替代方案 / Generate alternative
        
        Args:
            subtask: 子任务对象 / Subtask object
            
        Returns:
            替代子任务 / Alternative subtask
        """
        return None
    
    def get_status(self) -> dict[str, Any]:
        """
        获取状态 / Get status
        
        Returns:
            状态字典 / Status dictionary
        """
        return {
            "workers": list(self.workers.keys()),
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "execution_results": self.execution_results,
        }
