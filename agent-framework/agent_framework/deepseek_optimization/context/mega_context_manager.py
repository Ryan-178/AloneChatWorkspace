"""
Mega Context Manager
100万上下文智能管理器 - 协调活跃窗口与本地存储
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .message_ranker import (
    MessageRanker, MessageImportance, ImportanceCategory
)
from .storage_engine import StructuredStorageEngine, StoredMessage
from .token_estimator import TokenEstimator, TokenBudget, EstimationMode


@dataclass
class ContextDecision:
    keep_in_context: bool
    reason: str
    suggested_action: str


@dataclass
class ManagedMessage:
    message: Dict[str, Any]
    importance: MessageImportance
    decision: ContextDecision
    stored: Optional[StoredMessage] = None
    token_count: int = 0


@dataclass
class ContextStats:
    total_messages: int = 0
    in_context_count: int = 0
    archived_count: int = 0
    estimated_tokens_used: int = 0
    estimated_tokens_saved: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None


class MegaContextManager:
    """
    100万上下文管理器
    智能协调活跃上下文窗口与本地存储
    支持精确Token估算和会话管理
    """
    
    def __init__(
        self,
        storage_root: Optional[Path] = None,
        max_context_tokens: int = 1000000,
        target_active_tokens: int = 800000,
        token_estimation_mode: EstimationMode = EstimationMode.AUTO,
        session_id: Optional[str] = None,
    ):
        if storage_root is None:
            storage_root = Path("./data/context_archive")
        
        self.max_context_tokens = max_context_tokens
        self.target_active_tokens = target_active_tokens
        self.session_id = session_id
        
        self.ranker = MessageRanker()
        self.storage = StructuredStorageEngine(storage_root)
        self.token_estimator = TokenEstimator(mode=token_estimation_mode)
        
        self._all_messages: List[ManagedMessage] = []
        self._stats = ContextStats(session_id=session_id)
        
        self._token_budget = TokenBudget(
            total_budget=max_context_tokens,
            reserved=int(max_context_tokens * 0.1)
        )
    
    def set_session_id(self, session_id: str):
        self.session_id = session_id
        self._stats.session_id = session_id
    
    def add_message(
        self,
        message: Dict[str, Any]
    ) -> ManagedMessage:
        message_index = len(self._all_messages)
        importance = self.ranker.rank_message(
            message,
            message_index,
            max(len(self._all_messages), 1)
        )
        
        token_estimate = self.token_estimator.estimate(message)
        token_count = token_estimate.token_count
        
        decision = self._make_decision(importance, message, token_count)
        
        managed = ManagedMessage(
            message=message,
            importance=importance,
            decision=decision,
            token_count=token_count
        )
        
        self._execute_decision(managed)
        
        self._all_messages.append(managed)
        
        self._update_stats()
        
        return managed
    
    def add_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[ManagedMessage]:
        results = []
        for message in messages:
            managed = self.add_message(message)
            results.append(managed)
        return results
    
    def _make_decision(
        self,
        importance: MessageImportance,
        message: Dict[str, Any],
        token_count: int
    ) -> ContextDecision:
        current_usage = sum(m.token_count for m in self._all_messages if m.keep_in_context)
        
        if current_usage + token_count > self._token_budget.available:
            if importance.category in [ImportanceCategory.CRITICAL, ImportanceCategory.IMPORTANT]:
                return ContextDecision(
                    keep_in_context=True,
                    reason=f"重要性高，强制保留 ({importance.score:.2f})",
                    suggested_action="keep"
                )
            else:
                return ContextDecision(
                    keep_in_context=False,
                    reason=f"超出预算，建议归档 (当前: {current_usage}, 新增: {token_count})",
                    suggested_action="archive"
                )
        
        if importance.category in [
            ImportanceCategory.CRITICAL,
            ImportanceCategory.IMPORTANT
        ]:
            return ContextDecision(
                keep_in_context=True,
                reason=f"重要性高 ({importance.score:.2f}): {importance.reasoning}",
                suggested_action="keep"
            )
        elif importance.category == ImportanceCategory.NORMAL:
            return ContextDecision(
                keep_in_context=True,
                reason=f"普通重要性 ({importance.score:.2f})",
                suggested_action="compress"
            )
        else:
            return ContextDecision(
                keep_in_context=False,
                reason=f"重要性较低 ({importance.score:.2f})，建议归档保存",
                suggested_action="archive"
            )
    
    def _execute_decision(self, managed: ManagedMessage):
        if managed.decision.suggested_action == "archive":
            stored = self.storage.archive_message(
                managed.message,
                managed.importance
            )
            managed.stored = stored
            managed.keep_in_context = False
        else:
            managed.keep_in_context = True
    
    def get_active_context(
        self,
        current_usage_tokens: int = 0
    ) -> Tuple[List[Dict[str, Any]], List[ManagedMessage]]:
        available = self.max_context_tokens - current_usage_tokens
        
        active_messages = []
        active_managed = []
        used_tokens = 0
        
        sorted_messages = sorted(
            self._all_messages,
            key=lambda m: m.importance.score,
            reverse=True
        )
        
        for managed in sorted_messages:
            token_count = managed.token_count or self._estimate_tokens(managed.message)
            
            if used_tokens + token_count <= available:
                active_messages.append(managed.message)
                active_managed.append(managed)
                used_tokens += token_count
            else:
                if not managed.stored and not managed.keep_in_context:
                    stored = self.storage.archive_message(
                        managed.message,
                        managed.importance
                    )
                    managed.stored = stored
        
        return active_messages, active_managed
    
    def _estimate_tokens(self, message: Dict[str, Any]) -> int:
        return self.token_estimator.estimate(message).token_count
    
    def get_token_usage(self) -> Dict[str, Any]:
        active_tokens = sum(
            m.token_count for m in self._all_messages 
            if getattr(m, "keep_in_context", True)
        )
        archived_tokens = sum(
            m.token_count for m in self._all_messages 
            if m.stored
        )
        
        return {
            "active_tokens": active_tokens,
            "archived_tokens": archived_tokens,
            "total_tokens": active_tokens + archived_tokens,
            "budget_total": self._token_budget.total_budget,
            "budget_available": self._token_budget.available,
            "usage_ratio": active_tokens / self._token_budget.total_budget if self._token_budget.total_budget > 0 else 0,
        }
    
    def check_token_budget(self, new_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        current_usage = sum(
            m.token_count for m in self._all_messages 
            if getattr(m, "keep_in_context", True)
        )
        
        result = {
            "current_usage": current_usage,
            "budget_available": self._token_budget.available,
            "remaining": self._token_budget.available - current_usage,
            "would_exceed": False,
        }
        
        if new_message:
            new_tokens = self._estimate_tokens(new_message)
            result["new_message_tokens"] = new_tokens
            result["would_exceed"] = current_usage + new_tokens > self._token_budget.available
            result["remaining_after"] = result["remaining"] - new_tokens
        
        return result
    
    def optimize_context(self) -> Dict[str, Any]:
        optimization_result = {
            "before": {
                "total": len(self._all_messages),
                "active": sum(1 for m in self._all_messages if getattr(m, "keep_in_context", True)),
                "archived": sum(1 for m in self._all_messages if m.stored),
                "tokens": sum(m.token_count for m in self._all_messages if getattr(m, "keep_in_context", True)),
            },
            "after": {}
        }
        
        for managed in self._all_messages:
            if managed.importance.category in [
                ImportanceCategory.LOW,
                ImportanceCategory.TRIVIAL
            ] and not managed.stored:
                stored = self.storage.archive_message(
                    managed.message,
                    managed.importance
                )
                managed.stored = stored
                managed.keep_in_context = False
        
        optimization_result["after"] = {
            "total": len(self._all_messages),
            "active": sum(1 for m in self._all_messages if getattr(m, "keep_in_context", True)),
            "archived": sum(1 for m in self._all_messages if m.stored),
            "tokens": sum(m.token_count for m in self._all_messages if getattr(m, "keep_in_context", True)),
        }
        
        return optimization_result
    
    def _update_stats(self):
        self._stats.total_messages = len(self._all_messages)
        self._stats.in_context_count = sum(
            1 for m in self._all_messages
            if getattr(m, "keep_in_context", True)
        )
        self._stats.archived_count = sum(
            1 for m in self._all_messages if m.stored
        )
        self._stats.last_updated = datetime.now()
        
        self._stats.estimated_tokens_used = sum(
            m.token_count for m in self._all_messages
            if getattr(m, "keep_in_context", True)
        )
        
        self._stats.estimated_tokens_saved = sum(
            m.token_count for m in self._all_messages if m.stored
        )
    
    def get_stats(self) -> ContextStats:
        return self._stats
    
    def get_storage_stats(self):
        return self.storage.get_stats()
    
    def get_archived_files(self):
        return self.storage.get_file_list()
    
    def search_archive(self, keyword: str, limit: int = 50) -> List[StoredMessage]:
        return self.storage.search_messages(keyword, limit)
    
    def get_messages_for_export(self) -> List[Dict[str, Any]]:
        return [m.message for m in self._all_messages]
    
    def get_managed_messages_for_export(self) -> List[Dict[str, Any]]:
        result = []
        for m in self._all_messages:
            result.append({
                "message": m.message,
                "importance": {
                    "score": m.importance.score,
                    "category": m.importance.category.value,
                    "reasoning": m.importance.reasoning,
                    "topics": m.importance.topics,
                },
                "decision": {
                    "keep_in_context": m.decision.keep_in_context,
                    "reason": m.decision.reason,
                    "suggested_action": m.decision.suggested_action,
                },
                "token_count": m.token_count,
                "keep_in_context": getattr(m, "keep_in_context", True),
            })
        return result
    
    def clear(self):
        self._all_messages.clear()
        self._stats = ContextStats(session_id=self.session_id)
    
    def get_message_count(self) -> int:
        return len(self._all_messages)
    
    def get_total_tokens(self) -> int:
        return sum(m.token_count for m in self._all_messages)
