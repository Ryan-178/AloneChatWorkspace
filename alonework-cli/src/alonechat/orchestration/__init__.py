"""
工作流编排模块

实现基于"为了行动而思考"理念的工作流编排系统：
- 工作流定义与执行
- 任务规划与分解
- 多节点编排（顺序、并行、条件、循环）
- 与Agent层无缝集成
"""

from .workflow import (
    Workflow,
    WorkflowEngine,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
)
from .planner import (
    TaskPlanner,
    PlanResult,
    DecompositionStrategy,
)
from .executor import (
    WorkflowExecutor,
    ExecutionConfig,
    ExecutionResult,
)

__all__ = [
    "Workflow",
    "WorkflowEngine",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    "TaskPlanner",
    "PlanResult",
    "DecompositionStrategy",
    "WorkflowExecutor",
    "ExecutionConfig",
    "ExecutionResult",
]
