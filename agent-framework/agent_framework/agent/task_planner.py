"""
任务规划器 - Task Planner
将复杂任务分解为子任务并管理依赖关系
"""
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from agent_framework.core.task import Task, TaskDependency
from agent_framework.core.types import TaskStatus, TaskPriority


class TaskPlanner:
    """任务规划器"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def decompose(self, task: str) -> List[Task]:
        """将复杂任务分解为子任务列表"""
        task_lower = task.lower()
        
        if "文档" in task or "报告" in task or "写" in task:
            return self._decompose_document_task(task)
        elif "数据" in task or "分析" in task:
            return self._decompose_data_task(task)
        elif "调研" in task or "搜索" in task:
            return self._decompose_research_task(task)
        elif "代码" in task or "开发" in task or "实现" in task:
            return self._decompose_code_task(task)
        else:
            return self._decompose_general_task(task)
    
    def _decompose_document_task(self, task: str) -> List[Task]:
        """分解文档任务"""
        tasks = [
            Task(
                description="分析文档需求和目标",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "analysis"},
            ),
            Task(
                description="收集相关信息和数据",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "collection"},
            ),
            Task(
                description="生成文档大纲",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "planning"},
            ),
            Task(
                description="填充文档内容",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "writing"},
            ),
            Task(
                description="格式化和优化输出",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                metadata={"type": "formatting"},
            ),
        ]
        return self._add_dependencies(tasks)
    
    def _decompose_data_task(self, task: str) -> List[Task]:
        """分解数据分析任务"""
        tasks = [
            Task(
                description="加载数据源",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "loading"},
            ),
            Task(
                description="数据清洗和预处理",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "preprocessing"},
            ),
            Task(
                description="统计分析和计算",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "analysis"},
            ),
            Task(
                description="生成可视化图表",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "visualization"},
            ),
            Task(
                description="输出分析报告",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                metadata={"type": "reporting"},
            ),
        ]
        return self._add_dependencies(tasks)
    
    def _decompose_research_task(self, task: str) -> List[Task]:
        """分解调研任务"""
        tasks = [
            Task(
                description="提取关键词和搜索策略",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "planning"},
            ),
            Task(
                description="执行信息搜索",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "searching"},
            ),
            Task(
                description="筛选和整理信息",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "filtering"},
            ),
            Task(
                description="生成调研报告",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                metadata={"type": "reporting"},
            ),
        ]
        return self._add_dependencies(tasks)
    
    def _decompose_code_task(self, task: str) -> List[Task]:
        """分解代码任务"""
        tasks = [
            Task(
                description="理解需求和设计",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "planning"},
            ),
            Task(
                description="实现核心功能",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                metadata={"type": "implementation"},
            ),
            Task(
                description="编写测试用例",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                metadata={"type": "testing"},
            ),
            Task(
                description="代码审查和优化",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                metadata={"type": "review"},
            ),
        ]
        return self._add_dependencies(tasks)
    
    def _decompose_general_task(self, task: str) -> List[Task]:
        """分解通用任务"""
        return [
            Task(
                description=f"执行任务：{task}",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
            ),
        ]
    
    def _add_dependencies(self, tasks: List[Task]) -> List[Task]:
        """添加任务依赖关系"""
        for i in range(1, len(tasks)):
            tasks[i].dependencies.append(
                TaskDependency(task_id=tasks[i-1].id, type="requires")
            )
        return tasks
    
    def identify_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """识别任务间依赖关系"""
        dependencies = {}
        for task in tasks:
            dep_ids = [dep.task_id for dep in task.dependencies]
            if dep_ids:
                dependencies[task.id] = dep_ids
        return dependencies
    
    def build_dag(self, tasks: List[Task]) -> Dict[str, Any]:
        """构建任务DAG图"""
        nodes = {task.id: task.model_dump() for task in tasks}
        edges = []
        
        for task in tasks:
            for dep in task.dependencies:
                edges.append({
                    "from": dep.task_id,
                    "to": task.id,
                    "type": dep.type,
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "task_count": len(tasks),
            "edge_count": len(edges),
        }
    
    def get_execution_order(self, tasks: List[Task]) -> List[List[Task]]:
        """获取执行顺序（拓扑排序，返回分层结果）"""
        if not tasks:
            return []
        
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: 0 for task in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in in_degree:
                    in_degree[task.id] += 1
        
        layers = []
        remaining = set(task.id for task in tasks)
        
        while remaining:
            ready = [tid for tid in remaining if in_degree[tid] == 0]
            
            if not ready:
                ready = [list(remaining)[0]]
            
            layer = [task_map[tid] for tid in ready]
            layers.append(layer)
            
            for tid in ready:
                remaining.remove(tid)
                for task in tasks:
                    if any(dep.task_id == tid for dep in task.dependencies):
                        in_degree[task.id] -= 1
        
        return layers
    
    def estimate_complexity(self, task: str) -> str:
        """估算任务复杂度"""
        complexity_indicators = {
            "high": ["完整", "详细", "全面", "多个", "复杂", "系统", "全部"],
            "medium": ["分析", "报告", "整理", "优化", "实现", "开发"],
            "low": ["简单", "快速", "简要", "概述", "查看", "检查"],
        }
        
        task_lower = task.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                return level
        
        word_count = len(task.split())
        if word_count > 20:
            return "high"
        elif word_count > 10:
            return "medium"
        else:
            return "low"
    
    def estimate_time(self, tasks: List[Task]) -> Dict[str, Any]:
        """估算执行时间"""
        complexity_weights = {
            TaskPriority.CRITICAL: 5,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1,
        }
        
        total_weight = sum(complexity_weights.get(t.priority, 2) for t in tasks)
        
        base_time_minutes = 2
        estimated_minutes = total_weight * base_time_minutes
        
        return {
            "estimated_minutes": estimated_minutes,
            "task_count": len(tasks),
            "parallel_layers": len(self.get_execution_order(tasks)),
        }
    
    def validate_dag(self, tasks: List[Task]) -> Dict[str, Any]:
        """验证DAG有效性（无环）"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        task_map = {task.id: task for task in tasks}
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = task_map.get(task_id)
            if task:
                for dep in task.dependencies:
                    if dep.task_id not in visited:
                        if has_cycle(dep.task_id):
                            return True
                    elif dep.task_id in rec_stack:
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    return {
                        "valid": False,
                        "error": "检测到循环依赖",
                    }
        
        return {
            "valid": True,
            "error": None,
        }
    
    def get_task_status_summary(self, tasks: List[Task]) -> Dict[str, int]:
        """获取任务状态统计"""
        summary = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            summary[task.status.value] += 1
        return summary
