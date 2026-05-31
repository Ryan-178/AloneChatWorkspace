"""
角色间通信路由 / Role Communication Router

管理Leader/Worker/Verifier之间的消息传递
Manages message passing between Leader/Worker/Verifier
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.types import (
    AgentRole,
    SubTask,
    VerificationResult,
    WorkerState,
    Message,
)

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """
    消息类型枚举 / Message Type Enum
    """
    TASK_DISPATCH = "task_dispatch"
    TASK_RESULT = "task_result"
    VERIFICATION_REQUEST = "verification_request"
    VERIFICATION_RESULT = "verification_result"
    REJECT_NOTIFICATION = "reject_notification"
    APPROVE_NOTIFICATION = "approve_notification"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class RoleMessage:
    """
    角色间消息 / Inter-role message
    """

    def __init__(
        self,
        msg_type: MessageType,
        sender_role: AgentRole,
        sender_id: str,
        receiver_role: AgentRole,
        receiver_id: Optional[str],
        payload: Any,
        correlation_id: Optional[str] = None,
    ):
        self.msg_type = msg_type
        self.sender_role = sender_role
        self.sender_id = sender_id
        self.receiver_role = receiver_role
        self.receiver_id = receiver_id
        self.payload = payload
        self.correlation_id = correlation_id or f"{sender_id}-{datetime.utcnow().timestamp()}"
        self.timestamp = datetime.utcnow()
        self.retries = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "msg_type": self.msg_type.value,
            "sender_role": self.sender_role.value,
            "sender_id": self.sender_id,
            "receiver_role": self.receiver_role.value,
            "receiver_id": self.receiver_id,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "retries": self.retries,
        }


class RoleRouter:
    """
    角色间通信路由器 / Role Communication Router

    路由规则：
    - Leader → Worker: 任务分发 (TASK_DISPATCH)
    - Worker → Verifier: 成果提交 (VERIFICATION_REQUEST)
    - Verifier → Leader: 验收结果 (VERIFICATION_RESULT)
    - Verifier → Worker: 打回修正 (REJECT_NOTIFICATION)
    - 所有角色: 状态更新 (STATUS_UPDATE)

    Routing rules:
    - Leader → Worker: Task dispatch (TASK_DISPATCH)
    - Worker → Verifier: Result submission (VERIFICATION_REQUEST)
    - Verifier → Leader: Validation result (VERIFICATION_RESULT)
    - Verifier → Worker: Rejection for correction (REJECT_NOTIFICATION)
    - All roles: Status update (STATUS_UPDATE)
    """

    def __init__(self):
        self._handlers: Dict[Tuple[AgentRole, AgentRole, MessageType], List[Callable]] = {}
        self._message_queue: asyncio.Queue = None
        self._message_history: List[RoleMessage] = []
        self._max_history = 1000

    async def initialize(self) -> None:
        """初始化路由器 / Initialize router"""
        self._message_queue = asyncio.Queue()

    async def send(
        self,
        msg_type: MessageType,
        sender_role: AgentRole,
        sender_id: str,
        receiver_role: AgentRole,
        receiver_id: Optional[str],
        payload: Any,
    ) -> bool:
        """
        发送消息 / Send message

        Args:
            msg_type: 消息类型
            sender_role: 发送者角色
            sender_id: 发送者ID
            receiver_role: 接收者角色
            receiver_id: 接收者ID（None表示广播）
            payload: 消息载荷

        Returns:
            是否发送成功
        """
        message = RoleMessage(
            msg_type=msg_type,
            sender_role=sender_role,
            sender_id=sender_id,
            receiver_role=receiver_role,
            receiver_id=receiver_id,
            payload=payload,
        )

        if not self._validate_route(message):
            logger.warning(f"Invalid route: {sender_role.value} -> {receiver_role.value} ({msg_type.value})")
            return False

        if self._message_queue:
            await self._message_queue.put(message)

        self._record_message(message)
        await self._dispatch_to_handlers(message)

        return True

    def _validate_route(self, message: RoleMessage) -> bool:
        """验证路由是否有效 / Validate route is valid"""
        valid_routes = {
            (AgentRole.LEADER, AgentRole.WORKER, MessageType.TASK_DISPATCH),
            (AgentRole.WORKER, AgentRole.VERIFIER, MessageType.VERIFICATION_REQUEST),
            (AgentRole.VERIFIER, AgentRole.LEADER, MessageType.VERIFICATION_RESULT),
            (AgentRole.VERIFIER, AgentRole.WORKER, MessageType.REJECT_NOTIFICATION),
            (AgentRole.WORKER, AgentRole.LEADER, MessageType.TASK_RESULT),
        }

        key = (message.sender_role, message.receiver_role, message.msg_type)
        return key in valid_routes

    def register_handler(
        self,
        from_role: AgentRole,
        to_role: AgentRole,
        msg_type: MessageType,
        handler: Callable[[RoleMessage], Any],
    ) -> None:
        """
        注册消息处理器 / Register message handler

        Args:
            from_role: 发送者角色
            to_role: 接收者角色
            msg_type: 消息类型
            handler: 处理函数
        """
        key = (from_role, to_role, msg_type)
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    async def _dispatch_to_handlers(self, message: RoleMessage) -> None:
        """分发消息到处理器 / Dispatch message to handlers"""
        key = (message.sender_role, message.receiver_role, message.msg_type)
        handlers = self._handlers.get(key, [])

        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in handler for {key}: {e}")

    def _record_message(self, message: RoleMessage) -> None:
        """记录消息到历史 / Record message to history"""
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]

    async def dispatch_task(
        self,
        leader_id: str,
        worker_id: str,
        subtask: SubTask,
    ) -> bool:
        """
        分发任务给Worker / Dispatch task to Worker

        Args:
            leader_id: Leader ID
            worker_id: Worker ID
            subtask: 子任务

        Returns:
            是否分发成功
        """
        return await self.send(
            msg_type=MessageType.TASK_DISPATCH,
            sender_role=AgentRole.LEADER,
            sender_id=leader_id,
            receiver_role=AgentRole.WORKER,
            receiver_id=worker_id,
            payload=subtask.to_dict(),
        )

    async def submit_for_verification(
        self,
        worker_id: str,
        verifier_id: str,
        subtask_id: str,
        result: Any,
    ) -> bool:
        """
        提交结果给Verifier验证 / Submit result to Verifier

        Args:
            worker_id: Worker ID
            verifier_id: Verifier ID
            subtask_id: 子任务ID
            result: 执行结果

        Returns:
            是否提交成功
        """
        return await self.send(
            msg_type=MessageType.VERIFICATION_REQUEST,
            sender_role=AgentRole.WORKER,
            sender_id=worker_id,
            receiver_role=AgentRole.VERIFIER,
            receiver_id=verifier_id,
            payload={
                "subtask_id": subtask_id,
                "result": result,
            },
        )

    async def report_verification_result(
        self,
        verifier_id: str,
        leader_id: str,
        verification_result: VerificationResult,
    ) -> bool:
        """
        报告验证结果给Leader / Report verification result to Leader

        Args:
            verifier_id: Verifier ID
            leader_id: Leader ID
            verification_result: 验证结果

        Returns:
            是否报告成功
        """
        return await self.send(
            msg_type=MessageType.VERIFICATION_RESULT,
            sender_role=AgentRole.VERIFIER,
            sender_id=verifier_id,
            receiver_role=AgentRole.LEADER,
            receiver_id=leader_id,
            payload=verification_result.to_dict(),
        )

    async def reject_worker_output(
        self,
        verifier_id: str,
        worker_id: str,
        subtask_id: str,
        feedback: str,
    ) -> bool:
        """
        通知Worker打回修正 / Notify Worker of rejection

        Args:
            verifier_id: Verifier ID
            worker_id: Worker ID
            subtask_id: 子任务ID
            feedback: 反馈信息

        Returns:
            是否通知成功
        """
        return await self.send(
            msg_type=MessageType.REJECT_NOTIFICATION,
            sender_role=AgentRole.VERIFIER,
            sender_id=verifier_id,
            receiver_role=AgentRole.WORKER,
            receiver_id=worker_id,
            payload={
                "subtask_id": subtask_id,
                "feedback": feedback,
            },
        )

    async def report_task_result(
        self,
        worker_id: str,
        leader_id: str,
        subtask_id: str,
        result: Any,
    ) -> bool:
        """
        报告任务完成给Leader / Report task completion to Leader

        Args:
            worker_id: Worker ID
            leader_id: Leader ID
            subtask_id: 子任务ID
            result: 执行结果

        Returns:
            是否报告成功
        """
        return await self.send(
            msg_type=MessageType.TASK_RESULT,
            sender_role=AgentRole.WORKER,
            sender_id=worker_id,
            receiver_role=AgentRole.LEADER,
            receiver_id=leader_id,
            payload={
                "subtask_id": subtask_id,
                "result": result,
            },
        )

    def get_message_history(
        self,
        limit: int = 100,
        filter_by_type: Optional[MessageType] = None,
        filter_by_sender: Optional[AgentRole] = None,
    ) -> List[RoleMessage]:
        """
        获取消息历史 / Get message history

        Args:
            limit: 最大数量
            filter_by_type: 按类型筛选
            filter_by_sender: 按发送者角色筛选

        Returns:
            消息列表
        """
        history = self._message_history.copy()

        if filter_by_type:
            history = [m for m in history if m.msg_type == filter_by_type]

        if filter_by_sender:
            history = [m for m in history if m.sender_role == filter_by_sender]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取路由统计 / Get routing statistics

        Returns:
            统计信息字典
        """
        type_counts = {}
        role_counts = {}

        for message in self._message_history:
            type_key = message.msg_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1

            route_key = f"{message.sender_role.value}->{message.receiver_role.value}"
            role_counts[route_key] = role_counts.get(route_key, 0) + 1

        return {
            "total_messages": len(self._message_history),
            "by_type": type_counts,
            "by_route": role_counts,
        }
