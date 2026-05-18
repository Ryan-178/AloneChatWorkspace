"""
任务规划模块

负责：
- 需求解析
- 任务识别
- 依赖分析
- 任务拆解
- 执行规划
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import re

from alonechat.models import ModelRouter


class TaskType(Enum):
    """任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_UNDERSTANDING = "code_understanding"
    CODE_REFACTORING = "code_refactoring"
    FILE_PROCESSING = "file_processing"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GIT_OPERATION = "git_operation"
    ANALYSIS = "analysis"
    DESIGN_TO_CODE = "design_to_code"
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    description: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    subtasks: list["Task"] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str | None = None
    
    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否可以执行"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "subtasks": [t.to_dict() for t in self.subtasks],
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
        }


class TaskAnalyzer:
    """任务分析器"""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
    
    def analyze(self, requirement: str) -> dict[str, Any]:
        """
        分析需求
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            分析结果
        """
        prompt = f"""
请分析以下需求，识别任务类型和关键信息：

需求：{requirement}

请以JSON格式返回：
{{
    "task_type": "任务类型（code_generation/code_understanding/code_refactoring/file_processing/testing/documentation/git_operation/analysis/design_to_code）",
    "keywords": ["关键词列表"],
    "entities": {{
        "files": ["涉及的文件"],
        "functions": ["涉及的函数"],
        "classes": ["涉及的类"],
        "languages": ["编程语言"]
    }},
    "complexity": "复杂度（simple/medium/complex）",
    "estimated_steps": 预估步骤数,
    "requires_context": 是否需要上下文代码,
    "description": "任务描述"
}}
"""
        
        response = self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        
        import json
        try:
            result = json.loads(response)
            result["task_type"] = TaskType(result.get("task_type", "unknown"))
            return result
        except (json.JSONDecodeError, ValueError):
            return {
                "task_type": TaskType.UNKNOWN,
                "keywords": [],
                "entities": {},
                "complexity": "medium",
                "estimated_steps": 1,
                "requires_context": False,
                "description": requirement,
            }
    
    def identify_dependencies(self, tasks: list[Task]) -> dict[str, list[str]]:
        """
        识别任务依赖关系
        
        Args:
            tasks: 任务列表
            
        Returns:
            依赖关系映射
        """
        dependencies = {}
        
        for i, task in enumerate(tasks):
            deps = []
            
            if task.task_type == TaskType.TESTING:
                for j, prev_task in enumerate(tasks[:i]):
                    if prev_task.task_type in [TaskType.CODE_GENERATION, TaskType.CODE_REFACTORING]:
                        deps.append(prev_task.id)
            
            elif task.task_type == TaskType.DOCUMENTATION:
                for j, prev_task in enumerate(tasks[:i]):
                    if prev_task.task_type in [TaskType.CODE_GENERATION, TaskType.CODE_REFACTORING]:
                        deps.append(prev_task.id)
            
            elif task.task_type == TaskType.GIT_OPERATION:
                for j, prev_task in enumerate(tasks[:i]):
                    if prev_task.task_type in [TaskType.CODE_GENERATION, TaskType.CODE_REFACTORING, TaskType.TESTING]:
                        deps.append(prev_task.id)
            
            dependencies[task.id] = deps
        
        return dependencies


class TaskPlanner:
    """任务规划器"""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.analyzer = TaskAnalyzer(model_router)
    
    def decompose(self, requirement: str) -> Task:
        """
        分解任务
        
        Args:
            requirement: 用户需求
            
        Returns:
            任务树
        """
        analysis = self.analyzer.analyze(requirement)
        
        prompt = f"""
请将以下需求分解为具体的子任务：

需求：{requirement}
分析结果：{analysis}

请以JSON格式返回任务列表：
{{
    "main_task": {{
        "name": "主任务名称",
        "description": "主任务描述"
    }},
    "subtasks": [
        {{
            "id": "task_1",
            "name": "子任务名称",
            "description": "子任务描述",
            "task_type": "任务类型",
            "priority": "优先级（high/medium/low）",
            "parameters": {{}}
        }}
    ],
    "execution_order": ["task_1", "task_2", ...],
    "parallel_groups": [["task_1", "task_2"], ["task_3"]]
}}
"""
        
        response = self.model_router.chat(
            model="deepseek",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        
        import json
        try:
            plan = json.loads(response)
            
            main_task = Task(
                id="main",
                name=plan["main_task"]["name"],
                description=plan["main_task"]["description"],
                task_type=analysis["task_type"],
                priority=TaskPriority.HIGH,
            )
            
            subtask_map = {}
            for subtask_data in plan.get("subtasks", []):
                subtask = Task(
                    id=subtask_data["id"],
                    name=subtask_data["name"],
                    description=subtask_data["description"],
                    task_type=TaskType(subtask_data.get("task_type", "unknown")),
                    priority=TaskPriority(subtask_data.get("priority", "medium")),
                    parameters=subtask_data.get("parameters", {}),
                )
                subtask_map[subtask.id] = subtask
                main_task.subtasks.append(subtask)
            
            execution_order = plan.get("execution_order", [])
            for i, task_id in enumerate(execution_order):
                if task_id in subtask_map:
                    for prev_id in execution_order[:i]:
                        if prev_id in subtask_map:
                            subtask_map[task_id].dependencies.append(prev_id)
            
            return main_task
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            return Task(
                id="main",
                name="执行任务",
                description=requirement,
                task_type=analysis["task_type"],
                priority=TaskPriority.MEDIUM,
            )
    
    def optimize_execution_order(self, tasks: list[Task]) -> list[list[Task]]:
        """
        优化执行顺序，识别可并行执行的任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            分层的任务列表，每层可并行执行
        """
        layers = []
        remaining = set(t.id for t in tasks)
        completed = set()
        task_map = {t.id: t for t in tasks}
        
        while remaining:
            ready_tasks = []
            
            for task_id in remaining:
                task = task_map[task_id]
                if task.is_ready(completed):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                break
            
            layers.append(ready_tasks)
            
            for task in ready_tasks:
                remaining.remove(task.id)
                completed.add(task.id)
        
        return layers
