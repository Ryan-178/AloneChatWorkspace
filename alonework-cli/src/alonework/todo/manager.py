"""
待办事项管理器 / Todo Manager

管理待办事项的创建、更新、删除和查询 / Manages todo item creation, update, deletion and query
数据持久化到 YAML 文件 / Data persisted to YAML file
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from alonework.todo.item import TodoItem, TodoStatus, TodoPriority


@dataclass
class TodoStats:
    """待办统计 / Todo statistics"""
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0
    overdue: int = 0


class TodoManager:
    """
    待办事项管理器 / Todo Manager
    
    管理所有待办事项 / Manages all todo items
    """
    
    DEFAULT_STORAGE_FILE = Path.home() / ".alonework" / "todos.yaml"
    
    def __init__(self, storage_file: Optional[Path] = None):
        """
        初始化待办管理器 / Initialize todo manager
        
        Args:
            storage_file: 存储文件路径 / Storage file path
        """
        self.storage_file = storage_file or self.DEFAULT_STORAGE_FILE
        self._todos: Dict[str, TodoItem] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        
        self._ensure_storage()
        self._load_todos()
    
    def _ensure_storage(self) -> None:
        """确保存储文件存在 / Ensure storage file exists"""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            self._save_todos()
    
    def _load_todos(self) -> None:
        """从 YAML 加载待办 / Load todos from YAML"""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                for todo_data in data.get("todos", []):
                    todo = TodoItem.from_dict(todo_data)
                    self._todos[todo.id] = todo
        except Exception:
            pass
    
    def _save_todos(self) -> None:
        """保存待办到 YAML / Save todos to YAML"""
        try:
            data = {
                "version": 1,
                "last_updated": datetime.utcnow().isoformat(),
                "todos": [todo.to_dict() for todo in self._todos.values()],
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            pass
    
    def create(
        self,
        content: str,
        priority: TodoPriority = TodoPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        due_date: Optional[datetime] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TodoItem:
        """
        创建待办事项 / Create todo item
        
        Args:
            content: 内容 / Content
            priority: 优先级 / Priority
            tags: 标签 / Tags
            due_date: 截止日期 / Due date
            parent_id: 父任务ID / Parent task ID
            metadata: 元数据 / Metadata
            
        Returns:
            创建的待办 / Created todo
        """
        todo = TodoItem(
            content=content,
            priority=priority,
            tags=tags or [],
            due_date=due_date,
            parent_id=parent_id,
            metadata=metadata or {},
        )
        
        self._todos[todo.id] = todo
        
        if parent_id and parent_id in self._todos:
            self._todos[parent_id].add_subtask(todo.id)
        
        self._save_todos()
        self._notify_callbacks("created", todo)
        
        return todo
    
    def get(self, todo_id: str) -> Optional[TodoItem]:
        """
        获取待办 / Get todo
        
        Args:
            todo_id: 待办ID / Todo ID
            
        Returns:
            待办或 None / Todo or None
        """
        return self._todos.get(todo_id)
    
    def update(
        self,
        todo_id: str,
        content: Optional[str] = None,
        priority: Optional[TodoPriority] = None,
        status: Optional[TodoStatus] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[datetime] = None,
    ) -> Optional[TodoItem]:
        """
        更新待办 / Update todo
        
        Args:
            todo_id: 待办ID / Todo ID
            content: 内容 / Content
            priority: 优先级 / Priority
            status: 状态 / Status
            tags: 标签 / Tags
            due_date: 截止日期 / Due date
            
        Returns:
            更新后的待办或 None / Updated todo or None
        """
        todo = self._todos.get(todo_id)
        if not todo:
            return None
        
        if content is not None:
            todo.update_content(content)
        if priority is not None:
            todo.set_priority(priority)
        if status is not None:
            if status == TodoStatus.IN_PROGRESS:
                todo.mark_in_progress()
            elif status == TodoStatus.COMPLETED:
                todo.mark_completed()
            elif status == TodoStatus.CANCELLED:
                todo.mark_cancelled()
            else:
                todo.status = status
                todo.updated_at = datetime.utcnow()
        if tags is not None:
            todo.tags = tags
            todo.updated_at = datetime.utcnow()
        if due_date is not None:
            todo.set_due_date(due_date)
        
        self._save_todos()
        self._notify_callbacks("updated", todo)
        
        return todo
    
    def delete(self, todo_id: str) -> bool:
        """
        删除待办 / Delete todo
        
        Args:
            todo_id: 待办ID / Todo ID
            
        Returns:
            是否成功 / Whether successful
        """
        todo = self._todos.get(todo_id)
        if not todo:
            return False
        
        if todo.parent_id and todo.parent_id in self._todos:
            self._todos[todo.parent_id].remove_subtask(todo_id)
        
        for subtask_id in todo.subtask_ids:
            if subtask_id in self._todos:
                self._todos[subtask_id].parent_id = None
        
        del self._todos[todo_id]
        self._save_todos()
        self._notify_callbacks("deleted", todo)
        
        return True
    
    def mark_in_progress(self, todo_id: str) -> bool:
        """
        标记为进行中 / Mark as in progress
        
        Args:
            todo_id: 待办ID / Todo ID
            
        Returns:
            是否成功 / Whether successful
        """
        todo = self._todos.get(todo_id)
        if not todo:
            return False
        
        todo.mark_in_progress()
        self._save_todos()
        self._notify_callbacks("status_changed", todo)
        
        return True
    
    def mark_completed(self, todo_id: str) -> bool:
        """
        标记为已完成 / Mark as completed
        
        Args:
            todo_id: 待办ID / Todo ID
            
        Returns:
            是否成功 / Whether successful
        """
        todo = self._todos.get(todo_id)
        if not todo:
            return False
        
        todo.mark_completed()
        self._save_todos()
        self._notify_callbacks("status_changed", todo)
        
        return True
    
    def mark_cancelled(self, todo_id: str) -> bool:
        """
        标记为已取消 / Mark as cancelled
        
        Args:
            todo_id: 待办ID / Todo ID
            
        Returns:
            是否成功 / Whether successful
        """
        todo = self._todos.get(todo_id)
        if not todo:
            return False
        
        todo.mark_cancelled()
        self._save_todos()
        self._notify_callbacks("status_changed", todo)
        
        return True
    
    def list_all(
        self,
        status: Optional[TodoStatus] = None,
        priority: Optional[TodoPriority] = None,
        tags: Optional[List[str]] = None,
        include_completed: bool = True,
    ) -> List[TodoItem]:
        """
        列出待办 / List todos
        
        Args:
            status: 过滤状态 / Filter status
            priority: 过滤优先级 / Filter priority
            tags: 过滤标签 / Filter tags
            include_completed: 是否包含已完成 / Include completed
            
        Returns:
            待办列表 / Todo list
        """
        todos = list(self._todos.values())
        
        if status:
            todos = [t for t in todos if t.status == status]
        
        if priority:
            todos = [t for t in todos if t.priority == priority]
        
        if tags:
            todos = [t for t in todos if any(tag in t.tags for tag in tags)]
        
        if not include_completed:
            todos = [t for t in todos if not t.is_finished]
        
        return sorted(todos, key=lambda t: (-t.priority.value, t.created_at))
    
    def get_pending(self) -> List[TodoItem]:
        """获取待处理待办 / Get pending todos"""
        return self.list_all(status=TodoStatus.PENDING)
    
    def get_in_progress(self) -> List[TodoItem]:
        """获取进行中待办 / Get in-progress todos"""
        return self.list_all(status=TodoStatus.IN_PROGRESS)
    
    def get_overdue(self) -> List[TodoItem]:
        """获取过期待办 / Get overdue todos"""
        return [t for t in self._todos.values() if t.is_overdue]
    
    def get_stats(self) -> TodoStats:
        """
        获取统计信息 / Get statistics
        
        Returns:
            统计信息 / Statistics
        """
        todos = list(self._todos.values())
        return TodoStats(
            total=len(todos),
            pending=len([t for t in todos if t.status == TodoStatus.PENDING]),
            in_progress=len([t for t in todos if t.status == TodoStatus.IN_PROGRESS]),
            completed=len([t for t in todos if t.status == TodoStatus.COMPLETED]),
            cancelled=len([t for t in todos if t.status == TodoStatus.CANCELLED]),
            overdue=len([t for t in todos if t.is_overdue]),
        )
    
    def search(self, query: str) -> List[TodoItem]:
        """
        搜索待办 / Search todos
        
        Args:
            query: 搜索查询 / Search query
            
        Returns:
            匹配的待办列表 / Matching todo list
        """
        query_lower = query.lower()
        return [
            t for t in self._todos.values()
            if query_lower in t.content.lower()
            or any(query_lower in tag.lower() for tag in t.tags)
        ]
    
    def clear_completed(self) -> int:
        """
        清除已完成的待办 / Clear completed todos
        
        Returns:
            清除数量 / Cleared count
        """
        completed_ids = [
            tid for tid, todo in self._todos.items()
            if todo.status == TodoStatus.COMPLETED
        ]
        
        for tid in completed_ids:
            del self._todos[tid]
        
        self._save_todos()
        
        return len(completed_ids)
    
    def register_callback(
        self,
        event: str,
        callback: Callable[[TodoItem], None],
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
    
    def _notify_callbacks(self, event: str, todo: TodoItem) -> None:
        """通知回调 / Notify callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(todo)
            except Exception:
                pass


todo_manager = TodoManager()
