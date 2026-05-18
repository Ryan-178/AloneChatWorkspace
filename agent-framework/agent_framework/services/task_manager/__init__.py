"""
任务管理器 / Task Manager

增强的任务管理系统，支持依赖追踪 / Enhanced task management system with dependency tracking
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
import yaml
from pathlib import Path

from agent_framework.core.types import TaskStatus, TaskPriority


class DependencyType(Enum):
    """依赖类型 / Dependency type"""
    REQUIRES = "requires"
    BLOCKS = "blocks"
    TRIGGERS = "triggers"


@dataclass
class TaskDependency:
    """任务依赖 / Task dependency"""
    task_id: str
    dependency_type: DependencyType = DependencyType.REQUIRES
    condition: Optional[str] = None


@dataclass
class ManagedTask:
    """
    托管任务 / Managed Task
    
    具有依赖追踪能力的任务 / Task with dependency tracking capability
    """
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[TaskDependency] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def add_dependency(
        self,
        task_id: str,
        dependency_type: DependencyType = DependencyType.REQUIRES,
        condition: Optional[str] = None,
    ) -> None:
        """
        添加依赖 / Add dependency
        
        Args:
            task_id: 依赖任务ID / Dependency task ID
            dependency_type: 依赖类型 / Dependency type
            condition: 条件表达式 / Condition expression
        """
        dep = TaskDependency(
            task_id=task_id,
            dependency_type=dependency_type,
            condition=condition,
        )
        if dep not in self.dependencies:
            self.dependencies.append(dep)
    
    def remove_dependency(self, task_id: str) -> bool:
        """
        移除依赖 / Remove dependency
        
        Args:
            task_id: 依赖任务ID / Dependency task ID
            
        Returns:
            是否成功 / Whether successful
        """
        for i, dep in enumerate(self.dependencies):
            if dep.task_id == task_id:
                self.dependencies.pop(i)
                return True
        return False
    
    def get_dependency_ids(self) -> Set[str]:
        """
        获取所有依赖任务ID / Get all dependency task IDs
        
        Returns:
            依赖ID集合 / Set of dependency IDs
        """
        return {dep.task_id for dep in self.dependencies}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dict"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": [
                {
                    "task_id": dep.task_id,
                    "type": dep.dependency_type.value,
                    "condition": dep.condition,
                }
                for dep in self.dependencies
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "metadata": self.metadata,
            "tags": self.tags,
        }


class TaskDependencyGraph:
    """
    任务依赖图 / Task Dependency Graph
    
    管理任务之间的依赖关系 / Manages dependency relationships between tasks
    """
    
    def __init__(self):
        """初始化依赖图 / Initialize dependency graph"""
        self._tasks: Dict[str, ManagedTask] = {}
        self._adjacency: Dict[str, Set[str]] = {}
    
    def add_task(self, task: ManagedTask) -> None:
        """
        添加任务到图 / Add task to graph
        
        Args:
            task: 任务对象 / Task object
        """
        self._tasks[task.id] = task
        if task.id not in self._adjacency:
            self._adjacency[task.id] = set()
        
        for dep in task.dependencies:
            if dep.task_id not in self._adjacency:
                self._adjacency[dep.task_id] = set()
            self._adjacency[dep.task_id].add(task.id)
    
    def remove_task(self, task_id: str) -> bool:
        """
        从图中移除任务 / Remove task from graph
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            是否成功 / Whether successful
        """
        if task_id not in self._tasks:
            return False
        
        del self._tasks[task_id]
        
        for deps in self._adjacency.values():
            deps.discard(task_id)
        
        if task_id in self._adjacency:
            del self._adjacency[task_id]
        
        return True
    
    def get_dependencies(self, task_id: str) -> List[ManagedTask]:
        """
        获取任务的直接依赖 / Get direct dependencies of task
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            依赖任务列表 / List of dependency tasks
        """
        task = self._tasks.get(task_id)
        if not task:
            return []
        
        return [
            self._tasks[dep.task_id]
            for dep in task.dependencies
            if dep.task_id in self._tasks
        ]
    
    def get_dependents(self, task_id: str) -> List[ManagedTask]:
        """
        获取依赖此任务的任务 / Get tasks that depend on this task
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            依赖此任务的任务列表 / List of dependent tasks
        """
        dependent_ids = self._adjacency.get(task_id, set())
        return [
            self._tasks[tid]
            for tid in dependent_ids
            if tid in self._tasks
        ]
    
    def get_all_dependencies(self, task_id: str) -> Set[str]:
        """
        获取任务的所有依赖（递归） / Get all dependencies of task (recursive)
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            所有依赖ID集合 / Set of all dependency IDs
        """
        all_deps = set()
        to_visit = list(self.get_dependencies(task_id))
        
        while to_visit:
            dep = to_visit.pop()
            if dep.id not in all_deps:
                all_deps.add(dep.id)
                to_visit.extend(self.get_dependencies(dep.id))
        
        return all_deps
    
    def can_execute(self, task_id: str) -> bool:
        """
        检查任务是否可执行 / Check if task can execute
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            是否可执行 / Whether can execute
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        for dep in task.dependencies:
            dep_task = self._tasks.get(dep.task_id)
            if not dep_task:
                continue
            
            if dep.dependency_type == DependencyType.REQUIRES:
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
            
            elif dep.dependency_type == DependencyType.BLOCKS:
                if dep_task.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                    return False
        
        return True
    
    def detect_cycle(self) -> Optional[List[str]]:
        """
        检测循环依赖 / Detect circular dependency
        
        Returns:
            循环路径或 None / Cycle path or None
        """
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(task_id: str) -> Optional[List[str]]:
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)
            
            for dep_id in self._adjacency.get(task_id, set()):
                if dep_id not in visited:
                    result = dfs(dep_id)
                    if result:
                        return result
                elif dep_id in rec_stack:
                    cycle_start = path.index(dep_id)
                    return path[cycle_start:] + [dep_id]
            
            path.pop()
            rec_stack.remove(task_id)
            return None
        
        for task_id in self._tasks:
            if task_id not in visited:
                cycle = dfs(task_id)
                if cycle:
                    return cycle
        
        return None
    
    def topological_sort(self) -> List[str]:
        """
        拓扑排序 / Topological sort
        
        Returns:
            排序后的任务ID列表 / Sorted task ID list
        """
        in_degree = {tid: 0 for tid in self._tasks}
        
        for task_id, deps in self._adjacency.items():
            for dep_id in deps:
                if dep_id in in_degree:
                    in_degree[dep_id] += 1
        
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            task_id = queue.pop(0)
            result.append(task_id)
            
            for dep_id in self._adjacency.get(task_id, set()):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)
        
        return result


class TaskManager:
    """
    任务管理器 / Task Manager
    
    统一管理任务的生命周期和依赖关系 / Unified management of task lifecycle and dependencies
    """
    
    DEFAULT_STORAGE_FILE = Path.home() / ".alonechat" / "tasks.yaml"
    
    def __init__(self, storage_file: Optional[Path] = None):
        """
        初始化任务管理器 / Initialize task manager
        
        Args:
            storage_file: 存储文件路径 / Storage file path
        """
        self.storage_file = storage_file or self.DEFAULT_STORAGE_FILE
        self._graph = TaskDependencyGraph()
        self._callbacks: Dict[str, List[Callable]] = {}
        
        self._ensure_storage()
        self._load_tasks()
    
    def _ensure_storage(self) -> None:
        """确保存储文件存在 / Ensure storage file exists"""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            self._save_tasks()
    
    def _load_tasks(self) -> None:
        """从 YAML 加载任务 / Load tasks from YAML"""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                for task_data in data.get("tasks", []):
                    task = self._dict_to_task(task_data)
                    self._graph.add_task(task)
        except Exception:
            pass
    
    def _save_tasks(self) -> None:
        """保存任务到 YAML / Save tasks to YAML"""
        try:
            data = {
                "version": 1,
                "last_updated": datetime.utcnow().isoformat(),
                "tasks": [task.to_dict() for task in self._graph._tasks.values()],
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            pass
    
    def _dict_to_task(self, data: Dict[str, Any]) -> ManagedTask:
        """从字典创建任务 / Create task from dict"""
        task = ManagedTask(
            id=data.get("id", str(uuid4())[:8]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", 2)),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )
        
        for dep_data in data.get("dependencies", []):
            task.add_dependency(
                task_id=dep_data["task_id"],
                dependency_type=DependencyType(dep_data.get("type", "requires")),
                condition=dep_data.get("condition"),
            )
        
        return task
    
    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ManagedTask:
        """
        创建任务 / Create task
        
        Args:
            name: 任务名称 / Task name
            description: 任务描述 / Task description
            priority: 优先级 / Priority
            dependencies: 依赖任务ID列表 / Dependency task IDs
            tags: 标签 / Tags
            metadata: 元数据 / Metadata
            
        Returns:
            创建的任务 / Created task
        """
        task = ManagedTask(
            name=name,
            description=description,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        for dep_id in (dependencies or []):
            task.add_dependency(dep_id)
        
        self._graph.add_task(task)
        self._save_tasks()
        
        return task
    
    def get_task(self, task_id: str) -> Optional[ManagedTask]:
        """获取任务 / Get task"""
        return self._graph._tasks.get(task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        更新任务状态 / Update task status
        
        Args:
            task_id: 任务ID / Task ID
            status: 新状态 / New status
            result: 结果 / Result
            error: 错误 / Error
            
        Returns:
            是否成功 / Whether successful
        """
        task = self._graph._tasks.get(task_id)
        if not task:
            return False
        
        task.status = status
        
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.utcnow()
        elif status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            task.completed_at = datetime.utcnow()
        
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        
        self._save_tasks()
        self._notify_callbacks(task_id, status.value)
        
        return True
    
    def add_dependency(
        self,
        task_id: str,
        depends_on: str,
        dependency_type: DependencyType = DependencyType.REQUIRES,
    ) -> bool:
        """
        添加依赖关系 / Add dependency relationship
        
        Args:
            task_id: 任务ID / Task ID
            depends_on: 依赖的任务ID / Dependency task ID
            dependency_type: 依赖类型 / Dependency type
            
        Returns:
            是否成功 / Whether successful
        """
        task = self._graph._tasks.get(task_id)
        if not task:
            return False
        
        task.add_dependency(depends_on, dependency_type)
        self._graph._adjacency.setdefault(depends_on, set()).add(task_id)
        
        cycle = self._graph.detect_cycle()
        if cycle:
            task.remove_dependency(depends_on)
            return False
        
        self._save_tasks()
        return True
    
    def get_executable_tasks(self) -> List[ManagedTask]:
        """
        获取可执行的任务 / Get executable tasks
        
        Returns:
            可执行任务列表 / List of executable tasks
        """
        return [
            task
            for task in self._graph._tasks.values()
            if task.status == TaskStatus.PENDING and self._graph.can_execute(task.id)
        ]
    
    def get_execution_order(self) -> List[str]:
        """
        获取执行顺序 / Get execution order
        
        Returns:
            任务ID列表（按执行顺序）/ Task ID list in execution order
        """
        return self._graph.topological_sort()
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ManagedTask]:
        """
        列出任务 / List tasks
        
        Args:
            status: 过滤状态 / Filter status
            tags: 过滤标签 / Filter tags
            
        Returns:
            任务列表 / Task list
        """
        tasks = list(self._graph._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return sorted(tasks, key=lambda t: t.priority.value, reverse=True)
    
    def register_callback(
        self,
        event: str,
        callback: Callable[[ManagedTask], None],
    ) -> None:
        """
        注册回调 / Register callback
        
        Args:
            event: 事件名称 / Event name
            callback: 回调函数 / Callback function
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _notify_callbacks(self, task_id: str, event: str) -> None:
        """通知回调 / Notify callbacks"""
        task = self._graph._tasks.get(task_id)
        if not task:
            return
        
        for callback in self._callbacks.get(event, []):
            try:
                callback(task)
            except Exception:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息 / Get statistics"""
        tasks = list(self._graph._tasks.values())
        return {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED]),
        }


task_manager = TaskManager()
