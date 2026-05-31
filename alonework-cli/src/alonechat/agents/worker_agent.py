"""
Worker Agent基类 / Worker Agent Base Class

负责执行具体任务
Responsible for executing specific tasks
"""

import asyncio
import logging
import uuid
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ..core.base_agent import BaseAgent
from ..core.types import (
    AgentRole,
    RoleConfig,
    SubTask,
    WorkerState,
    Message,
)

logger = logging.getLogger(__name__)


class WorkerAgent(BaseAgent):
    """
    Worker Agent基类 / Worker Agent Base Class

    职责：
    - 专注执行具体子任务
    - 配备独立工具集
    - 独立上下文容器
    - 标准化输出协议

    Responsibilities:
    - Focus on executing specific subtasks
    - Equipped with independent tool set
    - Independent context container
    - Standardized output protocol
    """

    role = AgentRole.WORKER

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[RoleConfig] = None,
        tools: Optional[List[str]] = None,
        **kwargs,
    ):
        super().__init__(agent_id=agent_id or str(uuid.uuid4()), **kwargs)
        self.config = config or RoleConfig(role=AgentRole.WORKER)
        self._tools = tools or self.config.tools
        self._status = WorkerState.PENDING
        self._current_task: Optional[SubTask] = None
        self._context: Dict[str, Any] = {}
        self._result: Optional[Any] = None

    @property
    def status(self) -> WorkerState:
        """获取当前状态 / Get current status"""
        return self._status

    @property
    def current_task(self) -> Optional[SubTask]:
        """获取当前任务 / Get current task"""
        return self._current_task

    @property
    def tools(self) -> List[str]:
        """获取可用工具列表 / Get available tools list"""
        return self._tools

    def set_status(self, status: WorkerState) -> None:
        """设置状态 / Set status"""
        self._status = status
        logger.debug(f"Worker {self.agent_id} status changed to: {status.value}")

    async def execute(self, subtask: SubTask, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        执行子任务 / Execute subtask

        Args:
            subtask: 要执行的子任务
            context: 执行上下文

        Returns:
            执行结果
        """
        self._current_task = subtask
        self._status = WorkerState.PRODUCING
        self._context = context or {}

        logger.info(f"Worker {self.agent_id} executing subtask: {subtask.id}")

        try:
            result = await self._execute_task(subtask)
            self._result = result
            self._status = WorkerState.VERIFYING
            subtask.result = result
            logger.info(f"Worker {self.agent_id} completed subtask: {subtask.id}")
            return result

        except Exception as e:
            self._status = WorkerState.FAILED
            subtask.status = WorkerState.FAILED
            subtask.error = str(e)
            logger.error(f"Worker {self.agent_id} failed on subtask {subtask.id}: {e}")
            raise

    @abstractmethod
    async def _execute_task(self, subtask: SubTask) -> Any:
        """
        执行任务的具体实现 / Specific implementation of task execution

        子类需要实现此方法
        Subclasses must implement this method
        """
        pass

    async def retry(self, subtask: SubTask, feedback: Optional[str] = None) -> Any:
        """
        重试任务 / Retry task

        Args:
            subtask: 要重试的子任务
            feedback: Verifier的反馈

        Returns:
            执行结果
        """
        logger.info(
            f"Worker {self.agent_id} retrying subtask: {subtask.id} "
            f"(attempt {subtask.retry_count + 1})"
        )

        if feedback:
            self._context["verification_feedback"] = feedback

        self._status = WorkerState.RETRY
        return await self.execute(subtask, self._context)

    def update_context(self, key: str, value: Any) -> None:
        """更新上下文 / Update context"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文值 / Get context value"""
        return self._context.get(key, default)

    def clear_context(self) -> None:
        """清空上下文 / Clear context"""
        self._context.clear()

    def can_handle(self, subtask: SubTask) -> bool:
        """
        检查是否能处理该子任务 / Check if can handle the subtask

        Args:
            subtask: 子任务

        Returns:
            是否能处理
        """
        required_tools = subtask.metadata.get("required_tools", [])
        return all(tool in self._tools for tool in required_tools)

    def get_capabilities(self) -> List[str]:
        """获取能力列表 / Get capabilities list"""
        return self.config.capabilities

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self._status.value,
            "tools": self._tools,
            "capabilities": self.config.capabilities,
            "current_task_id": self._current_task.id if self._current_task else None,
        }


class CodeWorkerAgent(WorkerAgent):
    """
    代码Worker Agent / Code Worker Agent

    专门处理代码相关任务
    Specialized for code-related tasks
    """

    def __init__(self, **kwargs):
        default_tools = [
            "file_read",
            "file_write",
            "file_edit",
            "file_search",
            "shell",
            "git_status",
            "git_diff",
        ]
        kwargs.setdefault("tools", default_tools)
        super().__init__(**kwargs)
        self.config.capabilities = ["code_generation", "code_editing", "debugging"]

    async def _execute_task(self, subtask: SubTask) -> Any:
        """执行代码任务 / Execute code task"""
        task_type = subtask.metadata.get("type", "general")

        if task_type == "generate":
            return await self._generate_code(subtask)
        elif task_type == "edit":
            return await self._edit_code(subtask)
        elif task_type == "debug":
            return await self._debug_code(subtask)
        else:
            return await self._general_code_task(subtask)

    async def _generate_code(self, subtask: SubTask) -> Dict[str, Any]:
        """生成代码 / Generate code"""
        return {
            "type": "code_generation",
            "description": subtask.description,
            "status": "completed",
        }

    async def _edit_code(self, subtask: SubTask) -> Dict[str, Any]:
        """编辑代码 / Edit code"""
        return {
            "type": "code_editing",
            "description": subtask.description,
            "status": "completed",
        }

    async def _debug_code(self, subtask: SubTask) -> Dict[str, Any]:
        """调试代码 / Debug code"""
        return {
            "type": "debugging",
            "description": subtask.description,
            "status": "completed",
        }

    async def _general_code_task(self, subtask: SubTask) -> Dict[str, Any]:
        """通用代码任务 / General code task"""
        return {
            "type": "general",
            "description": subtask.description,
            "status": "completed",
        }


class ResearchWorkerAgent(WorkerAgent):
    """
    研究Worker Agent / Research Worker Agent

    专门处理研究和分析任务
    Specialized for research and analysis tasks
    """

    def __init__(self, **kwargs):
        default_tools = [
            "web_search",
            "file_read",
            "file_search",
        ]
        kwargs.setdefault("tools", default_tools)
        super().__init__(**kwargs)
        self.config.capabilities = ["research", "analysis", "summarization"]

    async def _execute_task(self, subtask: SubTask) -> Any:
        """执行研究任务 / Execute research task"""
        return {
            "type": "research",
            "description": subtask.description,
            "findings": [],
            "status": "completed",
        }
