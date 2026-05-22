"""
反思机制模块 / Reflection Mechanism Module

实现Agent的自我反思和策略调整
Implements self-reflection and strategy adjustment for agents
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ReflectionResult:
    """
    反思结果 / Reflection Result
    
    包含反思的分析和建议
    Contains analysis and suggestions from reflection
    """
    reflection_id: str
    agent_id: str
    timestamp: str
    
    analysis: dict[str, Any]
    suggestions: list[str]
    strategy_adjustments: dict[str, Any]
    
    success_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "reflection_id": self.reflection_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "analysis": self.analysis,
            "suggestions": self.suggestions,
            "strategy_adjustments": self.strategy_adjustments,
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "metadata": self.metadata,
        }


class ReflectionEngine:
    """
    反思引擎 / Reflection Engine
    
    实现Agent的自我反思和策略调整
    Implements self-reflection and strategy adjustment for agents
    
    不做训练，只记录交互数据
    No training, only records interaction data
    """
    
    def __init__(
        self,
        model: Any = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化反思引擎 / Initialize reflection engine
        
        Args:
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        self.model = model
        self.config = config or {}
        
        self._history: list[ReflectionResult] = []
        self._success_patterns: dict[str, list[str]] = {}
        self._failure_patterns: dict[str, list[str]] = {}
        
        self.max_history = self.config.get("max_history", 100)
        self.reflection_depth = self.config.get("reflection_depth", 3)
    
    async def reflect(
        self,
        agent_id: str,
        recent_actions: list[dict[str, Any]],
        recent_results: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReflectionResult:
        """
        执行反思 / Perform reflection
        
        Args:
            agent_id: Agent标识 / Agent identifier
            recent_actions: 最近的行动 / Recent actions
            recent_results: 最近的结果 / Recent results
            context: 上下文 / Context
            
        Returns:
            反思结果 / Reflection result
        """
        from uuid import uuid4
        
        analysis = await self._analyze_performance(
            recent_actions, recent_results
        )
        
        suggestions = await self._generate_suggestions(
            analysis, recent_actions, recent_results
        )
        
        strategy_adjustments = await self._determine_strategy_adjustments(
            analysis, suggestions
        )
        
        success_patterns = self._extract_success_patterns(
            recent_actions, recent_results
        )
        
        failure_patterns = self._extract_failure_patterns(
            recent_actions, recent_results
        )
        
        result = ReflectionResult(
            reflection_id=str(uuid4()),
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            analysis=analysis,
            suggestions=suggestions,
            strategy_adjustments=strategy_adjustments,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            metadata={"context": context} if context else {},
        )
        
        self._history.append(result)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history // 2:]
        
        self._update_patterns(agent_id, success_patterns, failure_patterns)
        
        return result
    
    async def _analyze_performance(
        self,
        actions: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        分析性能 / Analyze performance
        
        Args:
            actions: 行动列表 / List of actions
            results: 结果列表 / List of results
            
        Returns:
            分析结果 / Analysis result
        """
        if not results:
            return {"status": "no_data"}
        
        success_count = sum(1 for r in results if r.get("success", False))
        total_count = len(results)
        success_rate = success_count / total_count if total_count > 0 else 0
        
        errors = [
            r.get("error", "") for r in results
            if not r.get("success", False) and r.get("error")
        ]
        
        error_types = {}
        for error in errors:
            error_type = self._classify_error(error)
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "success_rate": success_rate,
            "total_actions": total_count,
            "successful_actions": success_count,
            "failed_actions": total_count - success_count,
            "error_types": error_types,
            "common_errors": errors[:5] if errors else [],
        }
    
    async def _generate_suggestions(
        self,
        analysis: dict[str, Any],
        actions: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> list[str]:
        """
        生成建议 / Generate suggestions
        
        Args:
            analysis: 分析结果 / Analysis result
            actions: 行动列表 / List of actions
            results: 结果列表 / List of results
            
        Returns:
            建议列表 / List of suggestions
        """
        suggestions = []
        
        success_rate = analysis.get("success_rate", 0)
        
        if success_rate < 0.5:
            suggestions.append("Consider reviewing and adjusting the overall approach")
        
        error_types = analysis.get("error_types", {})
        if error_types:
            most_common_error = max(error_types, key=error_types.get)
            suggestions.append(f"Focus on addressing {most_common_error} errors")
        
        if len(actions) > 20:
            suggestions.append("Consider breaking down tasks into smaller subtasks")
        
        if success_rate > 0.8:
            suggestions.append("Current approach is working well, consider optimizing for efficiency")
        
        if self.model:
            prompt = f"""基于以下分析结果，提供改进建议：

分析结果: {json.dumps(analysis, ensure_ascii=False)}

请提供3-5条具体的改进建议。
"""
            try:
                if hasattr(self.model, 'chat'):
                    response = await self.model.chat(prompt)
                    if isinstance(response, str):
                        lines = response.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                suggestions.append(line.strip())
            except Exception:
                pass
        
        return suggestions[:10]
    
    async def _determine_strategy_adjustments(
        self,
        analysis: dict[str, Any],
        suggestions: list[str],
    ) -> dict[str, Any]:
        """
        确定策略调整 / Determine strategy adjustments
        
        Args:
            analysis: 分析结果 / Analysis result
            suggestions: 建议列表 / List of suggestions
            
        Returns:
            策略调整 / Strategy adjustments
        """
        adjustments = {}
        
        success_rate = analysis.get("success_rate", 0)
        
        if success_rate < 0.3:
            adjustments["approach"] = "conservative"
            adjustments["retry_count"] = 3
        elif success_rate < 0.6:
            adjustments["approach"] = "balanced"
            adjustments["retry_count"] = 2
        else:
            adjustments["approach"] = "aggressive"
            adjustments["retry_count"] = 1
        
        error_types = analysis.get("error_types", {})
        if error_types:
            adjustments["focus_areas"] = list(error_types.keys())
        
        return adjustments
    
    def _extract_success_patterns(
        self,
        actions: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> list[str]:
        """
        提取成功模式 / Extract success patterns
        
        Args:
            actions: 行动列表 / List of actions
            results: 结果列表 / List of results
            
        Returns:
            成功模式列表 / List of success patterns
        """
        patterns = []
        
        for i, result in enumerate(results):
            if result.get("success", False) and i < len(actions):
                action = actions[i]
                action_type = action.get("type", "unknown")
                patterns.append(f"success:{action_type}")
        
        return patterns
    
    def _extract_failure_patterns(
        self,
        actions: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> list[str]:
        """
        提取失败模式 / Extract failure patterns
        
        Args:
            actions: 行动列表 / List of actions
            results: 结果列表 / List of results
            
        Returns:
            失败模式列表 / List of failure patterns
        """
        patterns = []
        
        for i, result in enumerate(results):
            if not result.get("success", False) and i < len(actions):
                action = actions[i]
                action_type = action.get("type", "unknown")
                error = result.get("error", "")
                error_type = self._classify_error(error)
                patterns.append(f"failure:{action_type}:{error_type}")
        
        return patterns
    
    def _classify_error(self, error: str) -> str:
        """
        分类错误 / Classify error
        
        Args:
            error: 错误信息 / Error message
            
        Returns:
            错误类型 / Error type
        """
        error_lower = error.lower() if isinstance(error, str) else ""
        
        if "timeout" in error_lower:
            return "timeout"
        elif "permission" in error_lower:
            return "permission"
        elif "not found" in error_lower:
            return "not_found"
        elif "invalid" in error_lower:
            return "invalid"
        elif "error" in error_lower:
            return "general"
        else:
            return "unknown"
    
    def _update_patterns(
        self,
        agent_id: str,
        success_patterns: list[str],
        failure_patterns: list[str],
    ) -> None:
        """
        更新模式记录 / Update pattern records
        
        Args:
            agent_id: Agent标识 / Agent identifier
            success_patterns: 成功模式 / Success patterns
            failure_patterns: 失败模式 / Failure patterns
        """
        if agent_id not in self._success_patterns:
            self._success_patterns[agent_id] = []
        self._success_patterns[agent_id].extend(success_patterns)
        
        if agent_id not in self._failure_patterns:
            self._failure_patterns[agent_id] = []
        self._failure_patterns[agent_id].extend(failure_patterns)
        
        max_patterns = 100
        if len(self._success_patterns[agent_id]) > max_patterns:
            self._success_patterns[agent_id] = self._success_patterns[agent_id][-max_patterns:]
        if len(self._failure_patterns[agent_id]) > max_patterns:
            self._failure_patterns[agent_id] = self._failure_patterns[agent_id][-max_patterns:]
    
    def get_history(
        self,
        agent_id: str | None = None,
        limit: int = 10,
    ) -> list[ReflectionResult]:
        """
        获取反思历史 / Get reflection history
        
        Args:
            agent_id: Agent标识（可选）/ Agent identifier (optional)
            limit: 数量限制 / Limit
            
        Returns:
            反思结果列表 / List of reflection results
        """
        history = self._history
        
        if agent_id:
            history = [r for r in history if r.agent_id == agent_id]
        
        return history[-limit:]
    
    def get_patterns(
        self,
        agent_id: str,
    ) -> dict[str, list[str]]:
        """
        获取模式 / Get patterns
        
        Args:
            agent_id: Agent标识 / Agent identifier
            
        Returns:
            模式字典 / Patterns dictionary
        """
        return {
            "success": self._success_patterns.get(agent_id, []),
            "failure": self._failure_patterns.get(agent_id, []),
        }
