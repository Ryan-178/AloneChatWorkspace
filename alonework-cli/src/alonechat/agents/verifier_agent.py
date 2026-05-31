"""
Verifier Agent基类 / Verifier Agent Base Class

负责验收和质量门禁
Responsible for validation and quality gate
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
    WorkerState,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class VerifierAgent(BaseAgent):
    """
    Verifier Agent基类 / Verifier Agent Base Class

    职责：
    - 独立审查Worker输出
    - 质量评分和门禁
    - 打回策略
    - 最大对抗轮数控制

    关键：与Worker形成目标函数相反的对抗关系

    Responsibilities:
    - Independently review Worker output
    - Quality scoring and gate
    - Rejection strategy
    - Maximum adversarial rounds control

    Key: Forms adversarial relationship with Worker (opposite objective function)
    """

    role = AgentRole.VERIFIER

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[RoleConfig] = None,
        quality_threshold: float = 0.8,
        **kwargs,
    ):
        super().__init__(agent_id=agent_id or str(uuid.uuid4()), **kwargs)
        self.config = config or RoleConfig(role=AgentRole.VERIFIER)
        self._quality_threshold = quality_threshold
        self._status = WorkerState.PENDING
        self._verification_history: List[VerificationResult] = []

    @property
    def status(self) -> WorkerState:
        """获取当前状态 / Get current status"""
        return self._status

    @property
    def quality_threshold(self) -> float:
        """获取质量阈值 / Get quality threshold"""
        return self._quality_threshold

    def set_status(self, status: WorkerState) -> None:
        """设置状态 / Set status"""
        self._status = status
        logger.debug(f"Verifier {self.agent_id} status changed to: {status.value}")

    async def verify(self, subtask: SubTask, result: Any) -> VerificationResult:
        """
        验证Worker输出 / Verify Worker output

        Args:
            subtask: 子任务
            result: Worker的输出结果

        Returns:
            验证结果
        """
        self._status = WorkerState.VERIFYING
        logger.info(f"Verifier {self.agent_id} verifying subtask: {subtask.id}")

        try:
            verification = await self._perform_verification(subtask, result)

            verification.verifier_id = self.agent_id
            verification.subtask_id = subtask.id
            verification.timestamp = datetime.utcnow()

            self._verification_history.append(verification)

            if verification.passed:
                self._status = WorkerState.DONE
                logger.info(
                    f"Verifier {self.agent_id} passed subtask {subtask.id} "
                    f"(score: {verification.score:.2f})"
                )
            else:
                self._status = WorkerState.RETRY
                logger.warning(
                    f"Verifier {self.agent_id} rejected subtask {subtask.id} "
                    f"(score: {verification.score:.2f}, threshold: {self._quality_threshold})"
                )

            return verification

        except Exception as e:
            self._status = WorkerState.FAILED
            logger.error(f"Verifier {self.agent_id} failed on subtask {subtask.id}: {e}")
            return VerificationResult(
                subtask_id=subtask.id,
                passed=False,
                score=0.0,
                feedback=f"Verification failed: {str(e)}",
                verifier_id=self.agent_id,
            )

    @abstractmethod
    async def _perform_verification(self, subtask: SubTask, result: Any) -> VerificationResult:
        """
        执行验证的具体实现 / Specific implementation of verification

        子类需要实现此方法
        Subclasses must implement this method
        """
        pass

    def get_feedback(self, verification: VerificationResult) -> str:
        """
        生成反馈信息 / Generate feedback

        Args:
            verification: 验证结果

        Returns:
            反馈信息
        """
        if verification.passed:
            return f"验证通过，质量分数: {verification.score:.2f}"

        feedback_parts = [f"验证未通过，质量分数: {verification.score:.2f} (阈值: {self._quality_threshold})"]

        if verification.issues:
            feedback_parts.append("\n问题列表:")
            for issue in verification.issues:
                feedback_parts.append(f"  - {issue}")

        if verification.suggestions:
            feedback_parts.append("\n改进建议:")
            for suggestion in verification.suggestions:
                feedback_parts.append(f"  - {suggestion}")

        return "\n".join(feedback_parts)

    def get_verification_history(self, subtask_id: Optional[str] = None) -> List[VerificationResult]:
        """
        获取验证历史 / Get verification history

        Args:
            subtask_id: 可选的子任务ID筛选

        Returns:
            验证结果列表
        """
        if subtask_id:
            return [v for v in self._verification_history if v.subtask_id == subtask_id]
        return self._verification_history.copy()

    def should_retry(self, subtask: SubTask, verification: VerificationResult) -> bool:
        """
        判断是否应该重试 / Determine if should retry

        Args:
            subtask: 子任务
            verification: 验证结果

        Returns:
            是否应该重试
        """
        if verification.passed:
            return False

        max_retries = self.config.max_retries
        return subtask.retry_count < max_retries

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self._status.value,
            "quality_threshold": self._quality_threshold,
            "verification_count": len(self._verification_history),
        }


class CodeVerifierAgent(VerifierAgent):
    """
    代码Verifier Agent / Code Verifier Agent

    专门验证代码质量
    Specialized for code quality verification
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("quality_threshold", 0.75)
        super().__init__(**kwargs)
        self.config.capabilities = ["code_review", "syntax_check", "test_validation"]

    async def _perform_verification(self, subtask: SubTask, result: Any) -> VerificationResult:
        """执行代码验证 / Perform code verification"""
        issues = []
        suggestions = []
        score = 1.0

        if isinstance(result, dict):
            code = result.get("code", "")
            if code:
                if len(code) < 10:
                    issues.append("代码太短，可能不完整")
                    score -= 0.3

                if "TODO" in code or "FIXME" in code:
                    issues.append("代码包含TODO/FIXME标记")
                    score -= 0.1

                if not any(kw in code for kw in ["def ", "class ", "function ", "const ", "let "]):
                    issues.append("未检测到有效的代码结构")
                    score -= 0.2

        score = max(0.0, min(1.0, score))
        passed = score >= self._quality_threshold

        if not passed:
            suggestions.append("请完善代码实现")
            suggestions.append("确保代码结构完整")

        return VerificationResult(
            subtask_id=subtask.id,
            passed=passed,
            score=score,
            feedback=self._generate_code_feedback(issues, suggestions),
            issues=issues,
            suggestions=suggestions,
            verifier_id=self.agent_id,
        )

    def _generate_code_feedback(self, issues: List[str], suggestions: List[str]) -> str:
        """生成代码反馈 / Generate code feedback"""
        parts = []
        if issues:
            parts.append("发现问题:")
            parts.extend(f"  - {i}" for i in issues)
        if suggestions:
            parts.append("建议:")
            parts.extend(f"  - {s}" for s in suggestions)
        return "\n".join(parts) if parts else "代码质量良好"


class TestVerifierAgent(VerifierAgent):
    """
    测试Verifier Agent / Test Verifier Agent

    专门验证测试覆盖率
    Specialized for test coverage verification
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("quality_threshold", 0.7)
        super().__init__(**kwargs)
        self.config.capabilities = ["test_coverage", "test_execution", "assertion_check"]

    async def _perform_verification(self, subtask: SubTask, result: Any) -> VerificationResult:
        """执行测试验证 / Perform test verification"""
        issues = []
        suggestions = []
        score = 0.8

        if isinstance(result, dict):
            test_result = result.get("test_result", {})
            if test_result.get("passed", True):
                score = 1.0
            else:
                issues.append("测试未通过")
                score = 0.5
                suggestions.append("请修复失败的测试用例")

            coverage = test_result.get("coverage", 0)
            if coverage < 0.8:
                issues.append(f"测试覆盖率不足: {coverage * 100:.1f}%")
                score -= 0.1
                suggestions.append("请增加测试用例以提高覆盖率")

        score = max(0.0, min(1.0, score))
        passed = score >= self._quality_threshold

        return VerificationResult(
            subtask_id=subtask.id,
            passed=passed,
            score=score,
            feedback="测试验证完成",
            issues=issues,
            suggestions=suggestions,
            verifier_id=self.agent_id,
        )
