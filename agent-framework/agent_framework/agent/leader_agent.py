"""
Leader Agent基类 / Leader Agent Base Class

负责统筹、规划、调度、聚合
Responsible for orchestration, planning, dispatching, aggregation
"""

import asyncio
import logging
import uuid
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.base_agent import BaseAgent
from ..core.types import (
    AgentRole,
    RoleConfig,
    SubTask,
    TeamState,
    TeamPhase,
    WorkerState,
    TaskPriority,
    Message,
)

logger = logging.getLogger(__name__)


class LeaderAgent(BaseAgent):
    """
    Leader Agent基类 / Leader Agent Base Class

    职责：
    - 任务理解和规划
    - 子任务拆分
    - Worker调度和监控
    - 结果聚合和最终交付

    Responsibilities:
    - Task understanding and planning
    - Subtask decomposition
    - Worker scheduling and monitoring
    - Result aggregation and final delivery
    """

    role = AgentRole.LEADER

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[RoleConfig] = None,
        **kwargs,
    ):
        super().__init__(agent_id=agent_id or str(uuid.uuid4()), **kwargs)
        self.config = config or RoleConfig(role=AgentRole.LEADER)
        self._team_state: Optional[TeamState] = None
        self._workers: Dict[str, Any] = {}
        self._verifiers: Dict[str, Any] = {}
        self._subtasks: Dict[str, SubTask] = {}
        self._results: Dict[str, Any] = {}

    @property
    def team_state(self) -> Optional[TeamState]:
        """获取Team状态 / Get Team state"""
        return self._team_state

    def register_worker(self, worker: Any, capabilities: Optional[List[str]] = None) -> str:
        """
        注册Worker / Register Worker

        Args:
            worker: Worker Agent实例
            capabilities: Worker的能力列表

        Returns:
            Worker ID
        """
        worker_id = getattr(worker, "agent_id", str(uuid.uuid4()))
        self._workers[worker_id] = {
            "agent": worker,
            "capabilities": capabilities or [],
            "status": WorkerState.PENDING,
        }
        logger.info(f"Registered worker: {worker_id} with capabilities: {capabilities}")
        return worker_id

    def register_verifier(self, verifier: Any) -> str:
        """
        注册Verifier / Register Verifier

        Args:
            verifier: Verifier Agent实例

        Returns:
            Verifier ID
        """
        verifier_id = getattr(verifier, "agent_id", str(uuid.uuid4()))
        self._verifiers[verifier_id] = {
            "agent": verifier,
            "status": WorkerState.PENDING,
        }
        logger.info(f"Registered verifier: {verifier_id}")
        return verifier_id

    async def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> List[SubTask]:
        """
        规划任务，拆分为子任务 / Plan task, decompose into subtasks

        Args:
            task: 主任务描述
            context: 上下文信息

        Returns:
            子任务列表
        """
        logger.info(f"Leader planning task: {task[:100]}...")

        subtasks = await self._decompose_task(task, context or {})

        for subtask in subtasks:
            self._subtasks[subtask.id] = subtask

        self._update_team_phase(TeamPhase.PLANNING)

        logger.info(f"Created {len(subtasks)} subtasks")
        return subtasks

    @abstractmethod
    async def _decompose_task(self, task: str, context: Dict[str, Any]) -> List[SubTask]:
        """
        分解任务为子任务 / Decompose task into subtasks

        子类需要实现此方法
        Subclasses must implement this method
        """
        pass

    async def dispatch(self, subtasks: Optional[List[SubTask]] = None) -> Dict[str, str]:
        """
        调度子任务到Worker / Dispatch subtasks to Workers

        Args:
            subtasks: 要调度的子任务列表，如果为None则调度所有待处理的子任务

        Returns:
            子任务ID到Worker ID的映射
        """
        tasks_to_dispatch = subtasks or list(self._subtasks.values())
        tasks_to_dispatch = [t for t in tasks_to_dispatch if t.status == WorkerState.PENDING]

        assignments = {}
        self._update_team_phase(TeamPhase.DISPATCHING)

        for subtask in tasks_to_dispatch:
            worker_id = await self._select_worker(subtask)
            if worker_id:
                subtask.assigned_to = worker_id
                subtask.status = WorkerState.PRODUCING
                assignments[subtask.id] = worker_id
                logger.info(f"Assigned subtask {subtask.id} to worker {worker_id}")
            else:
                logger.warning(f"No available worker for subtask {subtask.id}")

        return assignments

    async def _select_worker(self, subtask: SubTask) -> Optional[str]:
        """
        选择合适的Worker执行子任务 / Select appropriate Worker for subtask

        Args:
            subtask: 子任务

        Returns:
            选中的Worker ID，如果没有可用Worker则返回None
        """
        available_workers = []
        for worker_id, worker_info in self._workers.items():
            if worker_info["status"] in [WorkerState.PENDING, WorkerState.DONE]:
                available_workers.append((worker_id, worker_info))

        if not available_workers:
            return None

        return available_workers[0][0]

    async def monitor(self) -> TeamState:
        """
        监控执行进度 / Monitor execution progress

        Returns:
            当前Team状态
        """
        if not self._team_state:
            self._team_state = self._create_team_state()

        worker_states = {}
        for worker_id, worker_info in self._workers.items():
            worker_states[worker_id] = worker_info["status"]

        verifier_states = {}
        for verifier_id, verifier_info in self._verifiers.items():
            verifier_states[verifier_id] = verifier_info["status"]

        self._team_state.workers = worker_states
        self._team_state.verifiers = verifier_states
        self._team_state.subtasks = self._subtasks

        return self._team_state

    async def aggregate(self) -> Dict[str, Any]:
        """
        聚合所有子任务结果 / Aggregate all subtask results

        Returns:
            聚合后的结果
        """
        self._update_team_phase(TeamPhase.AGGREGATING)

        completed_results = {}
        for subtask_id, subtask in self._subtasks.items():
            if subtask.status == WorkerState.DONE and subtask.result is not None:
                completed_results[subtask_id] = subtask.result

        aggregated = await self._aggregate_results(completed_results)

        self._update_team_phase(TeamPhase.DONE)
        self._team_state.end_time = datetime.utcnow()

        logger.info(f"Aggregated {len(completed_results)} results")
        return aggregated

    @abstractmethod
    async def _aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        聚合结果的具体实现 / Specific implementation of result aggregation

        子类需要实现此方法
        Subclasses must implement this method
        """
        pass

    async def handle_verification_result(self, result: Any) -> bool:
        """
        处理验证结果 / Handle verification result

        Args:
            result: VerificationResult实例

        Returns:
            是否需要重试
        """
        from ..core.types import VerificationResult

        if not isinstance(result, VerificationResult):
            return False

        subtask = self._subtasks.get(result.subtask_id)
        if not subtask:
            return False

        if result.passed:
            subtask.status = WorkerState.DONE
            logger.info(f"Subtask {result.subtask_id} passed verification")
            return False
        else:
            if subtask.retry_count < self.config.max_retries:
                subtask.status = WorkerState.RETRY
                subtask.retry_count += 1
                logger.warning(
                    f"Subtask {result.subtask_id} failed verification, "
                    f"retry {subtask.retry_count}/{self.config.max_retries}"
                )
                return True
            else:
                subtask.status = WorkerState.FAILED
                subtask.error = result.feedback
                logger.error(f"Subtask {result.subtask_id} failed after max retries")
                return False

    def _create_team_state(self) -> TeamState:
        """创建Team状态 / Create Team state"""
        return TeamState(
            team_id=str(uuid.uuid4()),
            phase=TeamPhase.PLANNING,
            leader_state=WorkerState.PENDING,
        )

    def _update_team_phase(self, phase: TeamPhase) -> None:
        """更新Team阶段 / Update Team phase"""
        if self._team_state:
            self._team_state.phase = phase
            logger.debug(f"Team phase updated to: {phase.value}")

    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        """获取子任务 / Get subtask"""
        return self._subtasks.get(subtask_id)

    def get_all_subtasks(self) -> List[SubTask]:
        """获取所有子任务 / Get all subtasks"""
        return list(self._subtasks.values())

    def get_pending_subtasks(self) -> List[SubTask]:
        """获取待处理的子任务 / Get pending subtasks"""
        return [s for s in self._subtasks.values() if s.status == WorkerState.PENDING]

    def get_failed_subtasks(self) -> List[SubTask]:
        """获取失败的子任务 / Get failed subtasks"""
        return [s for s in self._subtasks.values() if s.status == WorkerState.FAILED]
