"""
Team Engine状态机Runtime / Team Engine State Machine Runtime

管理多Agent协作的状态转换、对抗验证循环、局部重试
Manages multi-agent collaboration state transitions, adversarial verification loop, local retry
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

from ..core.types import (
    AgentRole,
    SubTask,
    TeamState,
    TeamPhase,
    WorkerState,
    TaskPriority,
    VerificationResult,
    RoleConfig,
)
from ..core.role_router import RoleRouter, RoleMessage, MessageType

logger = logging.getLogger(__name__)


@dataclass
class TeamEngineConfig:
    """
    Team Engine配置 / Team Engine Configuration
    """
    max_retries: int = 3
    verification_threshold: float = 0.8
    worker_timeout: int = 300
    verifier_timeout: int = 60
    parallel_workers: int = 4
    max_adversarial_rounds: int = 5
    """
    Team Engine配置 / Team Engine Configuration
    """
    max_retries: int = 3
    verification_threshold: float = 0.8
    worker_timeout: int = 300
    verifier_timeout: int = 60
    parallel_workers: int = 4
    max_adversarial_rounds: int = 5


class TeamEngine:
    """
    Team Engine状态机Runtime / Team Engine State Machine Runtime

    功能：
    - 状态机核心：管理Agent生命周期状态转换
    - 对抗验证循环：Worker交付 → Verifier审查 → 通过/打回 → 重试/继续
    - 局部重试：只重试失败的Worker，不影响已成功的Worker
    - 失败恢复机制
    - 超时控制
    - 确定性调度

    Features:
    - State machine core: Manages Agent lifecycle state transitions
    - Adversarial verification loop: Worker delivery → Verifier review → Pass/Reject → Retry/Continue
    - Local retry: Only retry failed Workers, doesn't affect successful ones
    - Failure recovery mechanism
    - Timeout control
    - Deterministic scheduling
    """

    def __init__(self, config: Optional[TeamEngineConfig] = None):
        self.config = config or TeamEngineConfig()
        self._state: Optional[TeamState] = None
        self._router = RoleRouter()
        self._leader: Optional[Any] = None
        self._workers: Dict[str, Any] = {}
        self._verifiers: Dict[str, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._cancel_event: Optional[asyncio.Event] = None

    @property
    def state(self) -> Optional[TeamState]:
        """获取当前状态 / Get current state"""
        return self._state

    @property
    def is_running(self) -> bool:
        """检查是否运行中 / Check if running"""
        return self._running

    async def initialize(self, team_id: Optional[str] = None) -> None:
        """
        初始化Team Engine / Initialize Team Engine
        """
        self._state = TeamState(
            team_id=team_id or str(uuid.uuid4()),
            phase=TeamPhase.PLANNING,
        )
        await self._router.initialize()
        self._cancel_event = asyncio.Event()
        logger.info(f"Team Engine initialized with team ID: {self._state.team_id}")

    async def shutdown(self) -> None:
        """
        关闭Team Engine / Shutdown Team Engine
        """
        self._running = False
        if self._cancel_event:
            self._cancel_event.set()

        if self._state:
            self._state.phase = TeamPhase.DONE
            self._state.end_time = datetime.utcnow()

        logger.info("Team Engine shut down")

    def register_leader(self, leader: Any) -> None:
        """
        注册Leader / Register Leader
        """
        self._leader = leader
        self._state.leader_state = WorkerState.PENDING
        logger.info(f"Registered leader: {leader.agent_id}")

    def register_worker(self, worker: Any, capabilities: Optional[List[str]] = None) -> str:
        """
        注册Worker / Register Worker
        """
        worker_id = worker.agent_id
        self._workers[worker_id] = {
            "agent": worker,
            "capabilities": capabilities or [],
            "status": WorkerState.PENDING,
        }
        self._state.workers[worker_id] = WorkerState.PENDING
        logger.info(f"Registered worker: {worker_id}")
        return worker_id

    def register_verifier(self, verifier: Any) -> str:
        """
        注册Verifier / Register Verifier
        """
        verifier_id = verifier.agent_id
        self._verifiers[verifier_id] = {
            "agent": verifier,
            "status": WorkerState.PENDING,
        }
        self._state.verifiers[verifier_id] = WorkerState.PENDING
        logger.info(f"Registered verifier: {verifier_id}")
        return verifier_id

    def on_event(self, event_name: str, handler: Callable) -> None:
        """
        注册事件处理器 / Register event handler
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)

    async def _emit_event(self, event_name: str, data: Any = None) -> None:
        """
        触发事件 / Emit event
        """
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")

    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行Team执行流程 / Run Team execution flow

        Args:
            task: 主任务描述
            context: 执行上下文

        Returns:
            最终聚合结果
        """
        self._running = True
        context = context or {}

        try:
            await self._transition(TeamPhase.PLANNING)

            subtasks = await self._leader.plan(task, context)
            self._state.subtasks = {st.id: st for st in subtasks}

            await self._emit_event("planning_completed", {"subtasks": subtasks})

            await self._transition(TeamPhase.DISPATCHING)

            assignments = await self._dispatch_subtasks(subtasks)
            await self._emit_event("dispatching_completed", {"assignments": assignments})

            await self._transition(TeamPhase.EXECUTING)

            results = await self._execute_with_verification(subtasks)
            self._state.results = results

            await self._transition(TeamPhase.AGGREGATING)

            final_result = await self._leader.aggregate()
            self._state.results["final"] = final_result

            await self._transition(TeamPhase.DONE)

            await self._emit_event("completed", {"result": final_result})

            return final_result

        except Exception as e:
            self._state.phase = TeamPhase.FAILED
            self._state.errors.append(str(e))
            self._state.end_time = datetime.utcnow()
            await self._emit_event("failed", {"error": str(e)})
            raise

    async def _dispatch_subtasks(self, subtasks: List[SubTask]) -> Dict[str, str]:
        """
        分发子任务 / Dispatch subtasks
        """
        assignments = {}

        for subtask in subtasks:
            if self._cancel_event.is_set():
                break

            available_workers = [
                wid for wid, winfo in self._workers.items()
                if winfo["status"] in [WorkerState.PENDING, WorkerState.DONE]
            ]

            if not available_workers:
                logger.warning(f"No available workers for subtask {subtask.id}")
                continue

            worker_id = available_workers[0]
            worker_info = self._workers[worker_id]

            await self._router.dispatch_task(
                leader_id=self._leader.agent_id,
                worker_id=worker_id,
                subtask=subtask,
            )

            subtask.assigned_to = worker_id
            subtask.status = WorkerState.PRODUCING
            worker_info["status"] = WorkerState.PRODUCING
            self._state.workers[worker_id] = WorkerState.PRODUCING

            assignments[subtask.id] = worker_id
            logger.info(f"Dispatched subtask {subtask.id} to worker {worker_id}")

        return assignments

    async def _execute_with_verification(self, subtasks: List[SubTask]) -> Dict[str, Any]:
        """
        带验证的执行 / Execute with verification
        """
        results = {}
        pending_tasks = list(subtasks)

        while pending_tasks and not self._cancel_event.is_set():
            completed_tasks = []
            failed_tasks = []

            execution_coroutines = []
            for subtask in pending_tasks:
                if subtask.status in [WorkerState.PENDING, WorkerState.PRODUCING, WorkerState.RETRY]:
                    worker_id = subtask.assigned_to
                    if worker_id and worker_id in self._workers:
                        worker_info = self._workers[worker_id]
                        worker_agent = worker_info["agent"]
                        execution_coroutines.append(
                            self._execute_worker_task(worker_agent, subtask)
                        )

            if execution_coroutines:
                executed_results = await asyncio.gather(*execution_coroutines, return_exceptions=True)

                for i, result in enumerate(executed_results):
                    subtask = pending_tasks[i]
                    if isinstance(result, Exception):
                        subtask.status = WorkerState.FAILED
                        subtask.error = str(result)
                        failed_tasks.append(subtask)
                    else:
                        completed_tasks.append(subtask)
                        results[subtask.id] = result

            await self._transition(TeamPhase.VERIFYING)

            verification_results = await self._verify_results(completed_tasks)

            for subtask, verification in zip(completed_tasks, verification_results):
                if verification.passed:
                    subtask.status = WorkerState.DONE
                    results[subtask.id] = subtask.result
                elif subtask.retry_count < self.config.max_retries:
                    subtask.status = WorkerState.RETRY
                    subtask.retry_count += 1

                    worker_id = subtask.assigned_to
                    if worker_id and worker_id in self._workers:
                        worker_agent = self._workers[worker_id]["agent"]
                        feedback = verification.feedback
                        await worker_agent.retry(subtask, feedback)
                else:
                    subtask.status = WorkerState.FAILED
                    failed_tasks.append(subtask)

            pending_tasks = [t for t in pending_tasks if t.status == WorkerState.RETRY]

            if failed_tasks:
                self._state.errors.extend([f"Subtask {t.id}: {t.error}" for t in failed_tasks])

        return results

    async def _execute_worker_task(self, worker: Any, subtask: SubTask) -> Any:
        """
        执行Worker任务 / Execute Worker task
        """
        try:
            return await asyncio.wait_for(
                worker.execute(subtask),
                timeout=self.config.worker_timeout,
            )
        except asyncio.TimeoutError:
            subtask.status = WorkerState.FAILED
            subtask.error = f"Execution timeout after {self.config.worker_timeout}s"
            raise TimeoutError(subtask.error)

    async def _verify_results(self, subtasks: List[SubTask]) -> List[VerificationResult]:
        """
        验证结果 / Verify results
        """
        verifications = []
        verifier_ids = list(self._verifiers.keys())

        for i, subtask in enumerate(subtasks):
            if not verifier_ids:
                verifications.append(VerificationResult(
                    subtask_id=subtask.id,
                    passed=True,
                    score=1.0,
                    feedback="No verifier available, auto-pass",
                    verifier_id="system",
                ))
                continue

            verifier_id = verifier_ids[i % len(verifier_ids)]
            verifier_info = self._verifiers[verifier_id]
            verifier_agent = verifier_info["agent"]

            try:
                verification = await asyncio.wait_for(
                    verifier_agent.verify(subtask, subtask.result),
                    timeout=self.config.verifier_timeout,
                )
                verifications.append(verification)
            except asyncio.TimeoutError:
                verifications.append(VerificationResult(
                    subtask_id=subtask.id,
                    passed=False,
                    score=0.0,
                    feedback=f"Verification timeout after {self.config.verifier_timeout}s",
                    verifier_id=verifier_id,
                ))

        return verifications

    async def _transition(self, phase: TeamPhase) -> None:
        """
        状态转换 / State transition
        """
        old_phase = self._state.phase
        self._state.phase = phase
        logger.debug(f"State transition: {old_phase.value} -> {phase.value}")
        await self._emit_event("phase_transition", {"from": old_phase.value, "to": phase.value})

    def get_status(self) -> Dict[str, Any]:
        """
        获取详细状态 / Get detailed status
        """
        if not self._state:
            return {"status": "not_initialized"}

        summary = {
            "team_id": self._state.team_id,
            "phase": self._state.phase.value,
            "is_running": self._running,
            "leader_state": self._state.leader_state.value,
            "worker_count": len(self._workers),
            "verifier_count": len(self._verifiers),
            "subtask_count": len(self._state.subtasks),
            "completed_subtasks": sum(
                1 for s in self._state.subtasks.values()
                if s.status == WorkerState.DONE
            ),
            "failed_subtasks": sum(
                1 for s in self._state.subtasks.values()
                if s.status == WorkerState.FAILED
            ),
            "pending_subtasks": sum(
                1 for s in self._state.subtasks.values()
                if s.status in [WorkerState.PENDING, WorkerState.PRODUCING, WorkerState.RETRY]
            ),
            "errors": self._state.errors,
        }

        if self._state.start_time:
            elapsed = (datetime.utcnow() - self._state.start_time).total_seconds()
            summary["elapsed_seconds"] = elapsed

        return summary

    async def abort(self) -> None:
        """
        中止执行 / Abort execution
        """
        if self._cancel_event:
            self._cancel_event.set()
        self._running = False
        self._state.phase = TeamPhase.FAILED
        self._state.errors.append("Execution aborted by user")
        await self._emit_event("aborted", {})
        logger.info("Team execution aborted")
