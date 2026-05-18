"""
ä»»å¡è§åæ¨¡å

è´è´£ï¼?- éæ±è§£æ?- ä»»å¡è¯å«
- ä¾èµåæ
- ä»»å¡æè§£
- æ§è¡è§å
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import re

from alonework.models import ModelRouter


class TaskType(Enum):
    """ä»»å¡ç±»å"""
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
    """ä»»å¡ä¼åçº?""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """ä»»å¡ç¶æ?""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """ä»»å¡å®ä¹"""
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
        """æ£æ¥ä»»å¡æ¯å¦å¯ä»¥æ§è¡?""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def to_dict(self) -> dict[str, Any]:
        """è½¬æ¢ä¸ºå­å?""
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
    """ä»»å¡åæå?""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
    
    def analyze(self, requirement: str) -> dict[str, Any]:
        """
        åæéæ±?        
        Args:
            requirement: ç¨æ·éæ±æè¿?            
        Returns:
            åæç»æ
        """
        prompt = f"""
è¯·åæä»¥ä¸éæ±ï¼è¯å«ä»»å¡ç±»ååå³é®ä¿¡æ¯ï¼

éæ±ï¼{requirement}

è¯·ä»¥JSONæ ¼å¼è¿åï¼?{{
    "task_type": "ä»»å¡ç±»åï¼code_generation/code_understanding/code_refactoring/file_processing/testing/documentation/git_operation/analysis/design_to_codeï¼?,
    "keywords": ["å³é®è¯åè¡?],
    "entities": {{
        "files": ["æ¶åçæä»?],
        "functions": ["æ¶åçå½æ?],
        "classes": ["æ¶åçç±»"],
        "languages": ["ç¼ç¨è¯­è¨"]
    }},
    "complexity": "å¤æåº¦ï¼simple/medium/complexï¼?,
    "estimated_steps": é¢ä¼°æ­¥éª¤æ?
    "requires_context": æ¯å¦éè¦ä¸ä¸æä»£ç ,
    "description": "ä»»å¡æè¿°"
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
        è¯å«ä»»å¡ä¾èµå³ç³»
        
        Args:
            tasks: ä»»å¡åè¡¨
            
        Returns:
            ä¾èµå³ç³»æ å°
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
    """ä»»å¡è§åå?""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.analyzer = TaskAnalyzer(model_router)
    
    def decompose(self, requirement: str) -> Task:
        """
        åè§£ä»»å¡
        
        Args:
            requirement: ç¨æ·éæ±?            
        Returns:
            ä»»å¡æ ?        """
        analysis = self.analyzer.analyze(requirement)
        
        prompt = f"""
è¯·å°ä»¥ä¸éæ±åè§£ä¸ºå·ä½çå­ä»»å¡ï¼?
éæ±ï¼{requirement}
åæç»æï¼{analysis}

è¯·ä»¥JSONæ ¼å¼è¿åä»»å¡åè¡¨ï¼?{{
    "main_task": {{
        "name": "ä¸»ä»»å¡åç§?,
        "description": "ä¸»ä»»å¡æè¿?
    }},
    "subtasks": [
        {{
            "id": "task_1",
            "name": "å­ä»»å¡åç§?,
            "description": "å­ä»»å¡æè¿?,
            "task_type": "ä»»å¡ç±»å",
            "priority": "ä¼åçº§ï¼high/medium/lowï¼?,
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
                name="æ§è¡ä»»å¡",
                description=requirement,
                task_type=analysis["task_type"],
                priority=TaskPriority.MEDIUM,
            )
    
    def optimize_execution_order(self, tasks: list[Task]) -> list[list[Task]]:
        """
        ä¼åæ§è¡é¡ºåºï¼è¯å«å¯å¹¶è¡æ§è¡çä»»å?        
        Args:
            tasks: ä»»å¡åè¡¨
            
        Returns:
            åå±çä»»å¡åè¡¨ï¼æ¯å±å¯å¹¶è¡æ§è¡?        """
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
