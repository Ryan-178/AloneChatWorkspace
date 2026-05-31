"""
成本追踪器 / Cost Tracker

多维度成本统计和追踪
Multi-dimensional cost statistics and tracking
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .types import (
    CostRecord,
    CostAlert,
    SessionCost,
    DailyCost,
    TokenUsage,
    CacheStats,
    CostPeriod,
)

logger = logging.getLogger(__name__)


class CostTracker:
    """
    成本追踪器 / Cost Tracker

    提供按轮次、会话、每日等多维度的成本统计
    Provides multi-dimensional cost statistics by turn, session, day, etc.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._records: Dict[str, CostRecord] = {}
        self._sessions: Dict[str, SessionCost] = {}
        self._daily_costs: Dict[str, DailyCost] = {}
        self._cache_stats = CacheStats()
        self._current_session_id: Optional[str] = None
        self._model_rates: Dict[str, Dict[str, float]] = {}
        self._alerts: List[CostAlert] = []
        self._alert_handlers: List[Callable[[CostAlert], None]] = []
        self._session_threshold: float = 1.0
        self._daily_threshold: float = 10.0
        self._tracking_enabled: bool = True

        if config_path:
            self._load_config(config_path)
        else:
            self._load_default_rates()

    def _load_default_rates(self) -> None:
        """
        加载默认价格费率 / Load default pricing rates
        """
        self._model_rates = {
            "deepseek-chat": {
                "input": 0.14,
                "output": 0.28,
                "cache": 0.014,
            },
            "deepseek-reasoner": {
                "input": 0.55,
                "output": 2.19,
                "cache": 0.055,
            },
            "gpt-4o": {
                "input": 5.0,
                "output": 15.0,
                "cache": 0.5,
            },
            "gpt-4o-mini": {
                "input": 0.15,
                "output": 0.6,
                "cache": 0.015,
            },
            "claude-3-5-sonnet": {
                "input": 3.0,
                "output": 15.0,
                "cache": 0.3,
            },
            "claude-3-haiku": {
                "input": 0.25,
                "output": 1.25,
                "cache": 0.025,
            },
        }

    def _load_config(self, config_path: str) -> None:
        """
        加载配置文件 / Load configuration file
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config:
                    cost_config = config.get("cost", {})
                    self._tracking_enabled = cost_config.get("tracking_enabled", True)
                    self._model_rates = cost_config.get("rates", {})
                    alerts_config = cost_config.get("alerts", {})
                    self._session_threshold = alerts_config.get("session_threshold", 1.0)
                    self._daily_threshold = alerts_config.get("daily_threshold", 10.0)
        except Exception as e:
            logger.warning(f"Failed to load cost config: {e}")
            self._load_default_rates()

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        开始新会话 / Start new session
        """
        sid = session_id or str(uuid.uuid4())
        self._sessions[sid] = SessionCost(
            session_id=sid,
            start_time=datetime.now(),
        )
        self._current_session_id = sid
        return sid

    def end_session(self, session_id: Optional[str] = None) -> Optional[SessionCost]:
        """
        结束会话 / End session
        """
        sid = session_id or self._current_session_id
        if sid and sid in self._sessions:
            session = self._sessions[sid]
            session.end_time = datetime.now()
            if sid == self._current_session_id:
                self._current_session_id = None
            return session
        return None

    def record_usage(
        self,
        usage: TokenUsage,
        model_id: str,
        session_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostRecord:
        """
        记录使用量 / Record usage
        """
        if not self._tracking_enabled:
            return CostRecord(
                id="",
                session_id="",
                model_id=model_id,
                usage=usage,
            )

        sid = session_id or self._current_session_id or "default"
        record_id = str(uuid.uuid4())

        rates = self._model_rates.get(model_id, {"input": 0, "output": 0, "cache": 0})
        input_cost = (usage.input_tokens / 1_000_000) * rates.get("input", 0)
        output_cost = (usage.output_tokens / 1_000_000) * rates.get("output", 0)
        cache_cost = (usage.cache_read_tokens / 1_000_000) * rates.get("cache", 0)
        total_cost = input_cost + output_cost + cache_cost

        record = CostRecord(
            id=record_id,
            session_id=sid,
            turn_id=turn_id,
            model_id=model_id,
            timestamp=datetime.now(),
            usage=usage,
            input_cost=input_cost,
            output_cost=output_cost,
            cache_cost=cache_cost,
            total_cost=total_cost,
            metadata=metadata or {},
        )

        self._records[record_id] = record

        if sid in self._sessions:
            self._sessions[sid].add_record(record)
        else:
            session = SessionCost(
                session_id=sid,
                start_time=datetime.now(),
            )
            session.add_record(record)
            self._sessions[sid] = session

        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self._daily_costs:
            self._daily_costs[today] = DailyCost(date=today)
        daily = self._daily_costs[today]
        daily.total_usage = daily.total_usage.add(usage)
        daily.total_cost += total_cost
        if model_id not in daily.model_costs:
            daily.model_costs[model_id] = 0.0
        daily.model_costs[model_id] += total_cost

        self._update_cache_stats(usage)

        self._check_alerts(sid, today)

        return record

    def _update_cache_stats(self, usage: TokenUsage) -> None:
        """
        更新缓存统计 / Update cache statistics
        """
        self._cache_stats.total_requests += 1
        if usage.cache_read_tokens > 0:
            self._cache_stats.cache_hits += 1
            self._cache_stats.tokens_saved += usage.cache_read_tokens
            rates = self._model_rates.get("default", {"cache": 0.014})
            self._cache_stats.cost_saved += (
                usage.cache_read_tokens / 1_000_000
            ) * rates.get("cache", 0.014)
        else:
            self._cache_stats.cache_misses += 1

    def _check_alerts(self, session_id: str, date: str) -> None:
        """
        检查是否触发警告 / Check if alerts should be triggered
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if session.total_cost >= self._session_threshold:
                alert = CostAlert(
                    alert_type="session_threshold",
                    threshold=self._session_threshold,
                    current_value=session.total_cost,
                    message=f"会话成本 ${session.total_cost:.4f} 已达到阈值 ${self._session_threshold:.4f}",
                )
                self._alerts.append(alert)
                self._notify_alert(alert)

        if date in self._daily_costs:
            daily = self._daily_costs[date]
            if daily.total_cost >= self._daily_threshold:
                alert = CostAlert(
                    alert_type="daily_threshold",
                    threshold=self._daily_threshold,
                    current_value=daily.total_cost,
                    message=f"每日成本 ${daily.total_cost:.4f} 已达到阈值 ${self._daily_threshold:.4f}",
                )
                self._alerts.append(alert)
                self._notify_alert(alert)

    def _notify_alert(self, alert: CostAlert) -> None:
        """
        通知警告 / Notify alert
        """
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def get_session_cost(self, session_id: Optional[str] = None) -> Optional[SessionCost]:
        """
        获取会话成本 / Get session cost
        """
        sid = session_id or self._current_session_id
        if sid:
            return self._sessions.get(sid)
        return None

    def get_daily_cost(self, date: Optional[str] = None) -> Optional[DailyCost]:
        """
        获取每日成本 / Get daily cost
        """
        d = date or datetime.now().strftime("%Y-%m-%d")
        return self._daily_costs.get(d)

    def get_cost_by_period(self, period: CostPeriod) -> Dict[str, Any]:
        """
        按周期获取成本 / Get cost by period
        """
        now = datetime.now()

        if period == CostPeriod.TURN:
            if self._current_session_id and self._current_session_id in self._sessions:
                session = self._sessions[self._current_session_id]
                if session.records:
                    last_record = session.records[-1]
                    return last_record.to_dict()
            return {}

        elif period == CostPeriod.SESSION:
            if self._current_session_id:
                session = self._sessions.get(self._current_session_id)
                if session:
                    return session.to_dict()
            return {}

        elif period == CostPeriod.DAY:
            today = now.strftime("%Y-%m-%d")
            daily = self._daily_costs.get(today)
            if daily:
                return daily.to_dict()
            return {}

        elif period == CostPeriod.WEEK:
            week_start = now - timedelta(days=now.weekday())
            week_costs = []
            for i in range(7):
                day = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                if day in self._daily_costs:
                    week_costs.append(self._daily_costs[day].to_dict())
            return {"days": week_costs}

        elif period == CostPeriod.MONTH:
            month_start = now.replace(day=1)
            month_costs = []
            current = month_start
            while current <= now:
                day_str = current.strftime("%Y-%m-%d")
                if day_str in self._daily_costs:
                    month_costs.append(self._daily_costs[day_str].to_dict())
                current += timedelta(days=1)
            return {"days": month_costs}

        return {}

    def get_all_sessions(self) -> List[SessionCost]:
        """
        获取所有会话成本 / Get all session costs
        """
        return list(self._sessions.values())

    def get_all_daily_costs(self, limit: int = 30) -> List[DailyCost]:
        """
        获取每日成本历史 / Get daily cost history
        """
        sorted_dates = sorted(self._daily_costs.keys(), reverse=True)[:limit]
        return [self._daily_costs[d] for d in sorted_dates]

    def get_cache_stats(self) -> CacheStats:
        """
        获取缓存统计 / Get cache statistics
        """
        return self._cache_stats

    def get_alerts(self, limit: int = 10) -> List[CostAlert]:
        """
        获取警告列表 / Get alert list
        """
        return self._alerts[-limit:]

    def add_alert_handler(self, handler: Callable[[CostAlert], None]) -> None:
        """
        添加警告处理器 / Add alert handler
        """
        self._alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[CostAlert], None]) -> None:
        """
        移除警告处理器 / Remove alert handler
        """
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取成本摘要 / Get cost summary
        """
        total_cost = sum(s.total_cost for s in self._sessions.values())
        total_usage = TokenUsage()
        for session in self._sessions.values():
            total_usage = total_usage.add(session.total_usage)

        return {
            "total_sessions": len(self._sessions),
            "total_records": len(self._records),
            "total_cost": total_cost,
            "total_usage": total_usage.to_dict(),
            "cache_stats": self._cache_stats.to_dict(),
            "current_session": self._current_session_id,
            "tracking_enabled": self._tracking_enabled,
        }

    def clear_history(self, before: Optional[datetime] = None) -> int:
        """
        清除历史记录 / Clear history
        """
        if before is None:
            count = len(self._records)
            self._records.clear()
            self._sessions.clear()
            self._daily_costs.clear()
            return count

        count = 0
        records_to_remove = [
            rid for rid, r in self._records.items()
            if r.timestamp < before
        ]
        for rid in records_to_remove:
            del self._records[rid]
            count += 1

        return count

    @property
    def is_tracking_enabled(self) -> bool:
        """检查追踪是否启用 / Check if tracking is enabled"""
        return self._tracking_enabled

    def set_tracking_enabled(self, enabled: bool) -> None:
        """设置追踪启用状态 / Set tracking enabled state"""
        self._tracking_enabled = enabled


_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker(config_path: Optional[str] = None) -> CostTracker:
    """
    获取全局成本追踪器 / Get global cost tracker
    """
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker(config_path)
    return _cost_tracker
