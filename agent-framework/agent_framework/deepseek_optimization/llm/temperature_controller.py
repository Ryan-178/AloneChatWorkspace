"""
Temperature Controller
模型温度动态调整系统 - 根据场景、上下文、反馈自动调整温度参数
"""
import math
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque


class TaskType(str, Enum):
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    QUESTION_ANSWER = "question_answer"
    CHAT = "chat"
    REASONING = "reasoning"
    PLANNING = "planning"


class AdjustmentStrategy(str, Enum):
    TASK_BASED = "task_based"
    FEEDBACK_BASED = "feedback_based"
    CONTEXT_BASED = "context_based"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


@dataclass
class TemperatureRange:
    min_temp: float = 0.0
    max_temp: float = 2.0
    optimal: float = 0.7
    
    def clamp(self, value: float) -> float:
        return max(self.min_temp, min(self.max_temp, value))


@dataclass
class TemperatureAdjustment:
    from_temp: float
    to_temp: float
    reason: str
    strategy: AdjustmentStrategy
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def delta(self) -> float:
        return self.to_temp - self.from_temp


@dataclass
class FeedbackSignal:
    quality_score: float
    coherence_score: float
    creativity_score: float
    accuracy_score: float
    timestamp: float = field(default_factory=time.time)


TASK_TEMPERATURE_CONFIG: Dict[TaskType, TemperatureRange] = {
    TaskType.CREATIVE_WRITING: TemperatureRange(0.7, 1.5, 1.0),
    TaskType.CODE_GENERATION: TemperatureRange(0.0, 0.5, 0.2),
    TaskType.CODE_REVIEW: TemperatureRange(0.0, 0.3, 0.1),
    TaskType.ANALYSIS: TemperatureRange(0.1, 0.5, 0.3),
    TaskType.SUMMARIZATION: TemperatureRange(0.2, 0.6, 0.4),
    TaskType.TRANSLATION: TemperatureRange(0.1, 0.4, 0.2),
    TaskType.QUESTION_ANSWER: TemperatureRange(0.0, 0.7, 0.3),
    TaskType.CHAT: TemperatureRange(0.5, 1.0, 0.7),
    TaskType.REASONING: TemperatureRange(0.0, 0.4, 0.1),
    TaskType.PLANNING: TemperatureRange(0.1, 0.5, 0.3),
}


class TemperatureController:
    """
    模型温度动态调整控制器
    
    支持多种调整策略:
    - TASK_BASED: 根据任务类型预设温度
    - FEEDBACK_BASED: 根据反馈信号动态调整
    - CONTEXT_BASED: 根据上下文复杂度调整
    - ADAPTIVE: 自适应学习最优温度
    - HYBRID: 混合多种策略
    """
    
    DEFAULT_RANGE = TemperatureRange(0.0, 2.0, 0.7)
    HISTORY_SIZE = 100
    SMOOTHING_FACTOR = 0.3
    
    def __init__(
        self,
        strategy: AdjustmentStrategy = AdjustmentStrategy.HYBRID,
        initial_temperature: float = 0.7,
        learning_rate: float = 0.1,
        adaptation_enabled: bool = True,
    ):
        self.strategy = strategy
        self.current_temperature = initial_temperature
        self.learning_rate = learning_rate
        self.adaptation_enabled = adaptation_enabled
        
        self._adjustment_history: deque = deque(maxlen=self.HISTORY_SIZE)
        self._feedback_history: deque = deque(maxlen=self.HISTORY_SIZE)
        self._task_performance: Dict[TaskType, List[float]] = {}
        self._context_cache: Dict[str, float] = {}
        
        self._strategy_handlers: Dict[AdjustmentStrategy, Callable] = {
            AdjustmentStrategy.TASK_BASED: self._adjust_by_task,
            AdjustmentStrategy.FEEDBACK_BASED: self._adjust_by_feedback,
            AdjustmentStrategy.CONTEXT_BASED: self._adjust_by_context,
            AdjustmentStrategy.ADAPTIVE: self._adjust_adaptive,
            AdjustmentStrategy.HYBRID: self._adjust_hybrid,
        }
    
    def get_temperature(
        self,
        task_type: Optional[TaskType] = None,
        context: Optional[str] = None,
        feedback: Optional[FeedbackSignal] = None,
    ) -> float:
        """
        获取当前推荐的温度值
        """
        handler = self._strategy_handlers.get(self.strategy)
        if handler is None:
            return self.current_temperature
        
        new_temp = handler(task_type, context, feedback)
        new_temp = self._smooth_transition(new_temp)
        
        if new_temp != self.current_temperature:
            adjustment = TemperatureAdjustment(
                from_temp=self.current_temperature,
                to_temp=new_temp,
                reason=f"Strategy: {self.strategy.value}",
                strategy=self.strategy,
            )
            self._adjustment_history.append(adjustment)
            self.current_temperature = new_temp
        
        return self.current_temperature
    
    def update_feedback(self, feedback: FeedbackSignal) -> None:
        """
        更新反馈信号，用于自适应调整
        """
        self._feedback_history.append(feedback)
        
        if self.adaptation_enabled and len(self._feedback_history) >= 3:
            self._adapt_from_feedback()
    
    def set_task_type(self, task_type: TaskType) -> float:
        """
        根据任务类型设置温度
        """
        config = TASK_TEMPERATURE_CONFIG.get(task_type, self.DEFAULT_RANGE)
        new_temp = config.optimal
        
        adjustment = TemperatureAdjustment(
            from_temp=self.current_temperature,
            to_temp=new_temp,
            reason=f"Task type: {task_type.value}",
            strategy=AdjustmentStrategy.TASK_BASED,
            metadata={"task_type": task_type.value},
        )
        self._adjustment_history.append(adjustment)
        self.current_temperature = new_temp
        
        return self.current_temperature
    
    def adjust_for_context_complexity(
        self,
        context: str,
        token_count: Optional[int] = None,
    ) -> float:
        """
        根据上下文复杂度调整温度
        
        复杂度因素:
        - Token数量
        - 代码块数量
        - 特殊字符密度
        - 语言混合程度
        """
        complexity = self._calculate_context_complexity(context, token_count)
        
        if complexity < 0.3:
            target_temp = 0.7
        elif complexity < 0.6:
            target_temp = 0.5
        else:
            target_temp = 0.3
        
        new_temp = self._smooth_transition(target_temp)
        
        adjustment = TemperatureAdjustment(
            from_temp=self.current_temperature,
            to_temp=new_temp,
            reason=f"Context complexity: {complexity:.2f}",
            strategy=AdjustmentStrategy.CONTEXT_BASED,
            metadata={"complexity": complexity},
        )
        self._adjustment_history.append(adjustment)
        self.current_temperature = new_temp
        
        return self.current_temperature
    
    def _adjust_by_task(
        self,
        task_type: Optional[TaskType],
        context: Optional[str],
        feedback: Optional[FeedbackSignal],
    ) -> float:
        if task_type is None:
            return self.current_temperature
        
        config = TASK_TEMPERATURE_CONFIG.get(task_type, self.DEFAULT_RANGE)
        return config.optimal
    
    def _adjust_by_feedback(
        self,
        task_type: Optional[TaskType],
        context: Optional[str],
        feedback: Optional[FeedbackSignal],
    ) -> float:
        if feedback is None:
            return self.current_temperature
        
        quality = feedback.quality_score
        creativity = feedback.creativity_score
        accuracy = feedback.accuracy_score
        
        if accuracy < 0.5:
            adjustment = -0.2 * (1 - accuracy)
        elif creativity < 0.5 and quality > 0.7:
            adjustment = 0.1 * creativity
        else:
            adjustment = 0.05 * (quality - 0.5)
        
        return self.current_temperature + adjustment * self.learning_rate
    
    def _adjust_by_context(
        self,
        task_type: Optional[TaskType],
        context: Optional[str],
        feedback: Optional[FeedbackSignal],
    ) -> float:
        if context is None:
            return self.current_temperature
        
        complexity = self._calculate_context_complexity(context)
        
        if complexity > 0.7:
            return 0.2
        elif complexity > 0.5:
            return 0.4
        elif complexity > 0.3:
            return 0.6
        else:
            return 0.8
    
    def _adjust_adaptive(
        self,
        task_type: Optional[TaskType],
        context: Optional[str],
        feedback: Optional[FeedbackSignal],
    ) -> float:
        if task_type and task_type in self._task_performance:
            performances = self._task_performance[task_type]
            if performances:
                avg_performance = sum(performances) / len(performances)
                
                if avg_performance > 0.8:
                    return self.current_temperature
                elif avg_performance > 0.6:
                    return self.current_temperature - 0.05
                else:
                    return self.current_temperature - 0.1
        
        return self.current_temperature
    
    def _adjust_hybrid(
        self,
        task_type: Optional[TaskType],
        context: Optional[str],
        feedback: Optional[FeedbackSignal],
    ) -> float:
        weights = {
            "task": 0.4,
            "context": 0.3,
            "feedback": 0.3,
        }
        
        temps = []
        
        if task_type:
            task_temp = self._adjust_by_task(task_type, None, None)
            temps.append(("task", task_temp, weights["task"]))
        
        if context:
            ctx_temp = self._adjust_by_context(None, context, None)
            temps.append(("context", ctx_temp, weights["context"]))
        
        if feedback:
            fb_temp = self._adjust_by_feedback(None, None, feedback)
            temps.append(("feedback", fb_temp, weights["feedback"]))
        
        if not temps:
            return self.current_temperature
        
        total_weight = sum(w for _, _, w in temps)
        weighted_temp = sum(t * w for _, t, w in temps) / total_weight
        
        return weighted_temp
    
    def _calculate_context_complexity(
        self,
        context: str,
        token_count: Optional[int] = None,
    ) -> float:
        if not context:
            return 0.0
        
        cache_key = hash(context[:500])
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        
        factors = []
        
        length = len(context)
        length_factor = min(1.0, length / 10000)
        factors.append(length_factor)
        
        code_blocks = context.count('```')
        code_factor = min(1.0, code_blocks / 10)
        factors.append(code_factor * 1.5)
        
        special_chars = sum(1 for c in context if c in '{}[]<>/\\|@#$%^&*')
        special_factor = min(1.0, special_chars / max(length, 1) * 10)
        factors.append(special_factor)
        
        import re
        languages = len(re.findall(r'```(\w+)', context))
        lang_factor = min(1.0, languages / 5)
        factors.append(lang_factor)
        
        complexity = sum(factors) / len(factors)
        complexity = max(0.0, min(1.0, complexity))
        
        self._context_cache[cache_key] = complexity
        return complexity
    
    def _smooth_transition(self, target: float) -> float:
        """
        平滑温度过渡，避免突变
        """
        diff = target - self.current_temperature
        smoothed_diff = diff * self.SMOOTHING_FACTOR
        return self.current_temperature + smoothed_diff
    
    def _adapt_from_feedback(self) -> None:
        """
        从历史反馈中学习
        """
        if len(self._feedback_history) < 3:
            return
        
        recent = list(self._feedback_history)[-5:]
        avg_quality = sum(f.quality_score for f in recent) / len(recent)
        avg_accuracy = sum(f.accuracy_score for f in recent) / len(recent)
        
        if avg_accuracy < 0.6:
            self.current_temperature = max(0.0, self.current_temperature - 0.1)
        elif avg_quality > 0.8 and avg_accuracy > 0.8:
            pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取温度控制器统计信息
        """
        history = list(self._adjustment_history)
        
        return {
            "current_temperature": self.current_temperature,
            "strategy": self.strategy.value,
            "adjustment_count": len(history),
            "recent_adjustments": [
                {
                    "from": adj.from_temp,
                    "to": adj.to_temp,
                    "delta": adj.delta,
                    "reason": adj.reason,
                    "timestamp": adj.timestamp,
                }
                for adj in history[-10:]
            ],
            "feedback_count": len(self._feedback_history),
            "adaptation_enabled": self.adaptation_enabled,
        }
    
    def reset(self, initial_temperature: float = 0.7) -> None:
        """
        重置控制器状态
        """
        self.current_temperature = initial_temperature
        self._adjustment_history.clear()
        self._feedback_history.clear()
        self._task_performance.clear()
        self._context_cache.clear()


class TemperatureManager:
    """
    温度管理器 - 管理多个控制器的生命周期
    """
    
    def __init__(self):
        self._controllers: Dict[str, TemperatureController] = {}
        self._default_controller: Optional[TemperatureController] = None
    
    def get_controller(
        self,
        name: str = "default",
        strategy: AdjustmentStrategy = AdjustmentStrategy.HYBRID,
        **kwargs
    ) -> TemperatureController:
        """
        获取或创建温度控制器
        """
        if name not in self._controllers:
            controller = TemperatureController(strategy=strategy, **kwargs)
            self._controllers[name] = controller
            if self._default_controller is None:
                self._default_controller = controller
        return self._controllers[name]
    
    def get_default(self) -> TemperatureController:
        """
        获取默认控制器
        """
        if self._default_controller is None:
            self._default_controller = TemperatureController()
            self._controllers["default"] = self._default_controller
        return self._default_controller
    
    def remove_controller(self, name: str) -> bool:
        """
        移除控制器
        """
        if name in self._controllers:
            controller = self._controllers.pop(name)
            if controller is self._default_controller:
                self._default_controller = None
            return True
        return False
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有控制器统计信息
        """
        return {
            name: controller.get_statistics()
            for name, controller in self._controllers.items()
        }
