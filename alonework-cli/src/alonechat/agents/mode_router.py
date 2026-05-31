"""
Mode Router - 模式路由器 - Mode Router
根据用户选择和任务特征智能路由到CODE或WORK模式
Intelligently routes to CODE or WORK mode based on user choice and task characteristics
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from alonechat.agents.mode_manager import (
    AgentModeManager,
    ExecutionMode,
    ModeConfig,
    ModeSwitchEvent,
)
from alonechat.core.base_agent import AgentResult


class TaskCategory(str, Enum):
    """
    任务类别枚举 - Task Category Enum
    分类任务类型以辅助模式选择
    Classify task types to assist mode selection
    """
    CODE_GENERATION = "code_generation"
    CODE_DEBUG = "code_debug"
    CODE_REFACTOR = "code_refactor"
    CODE_REVIEW = "code_review"
    DOCUMENT_WRITING = "document_writing"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    TRANSLATION = "translation"
    GENERAL = "general"


@dataclass
class RoutingResult:
    """
    路由结果 - Routing Result
    包含路由决策的详细信息
    Contains detailed information about routing decision
    """
    mode: ExecutionMode
    category: TaskCategory
    confidence: float
    reasons: List[str]
    task_features: Dict[str, Any]


@dataclass
class RouterConfig:
    """
    路由器配置 - Router Configuration
    """
    enable_auto_routing: bool = True
    code_mode_threshold: float = 0.6
    work_mode_threshold: float = 0.6
    prefer_user_choice: bool = True


class ModeRouter:
    """
    模式路由器 - Mode Router
    智能分析任务并路由到合适的执行模式
    Intelligently analyzes tasks and routes to appropriate execution mode
    
    路由策略 / Routing Strategy:
    1. 用户显式选择 > 自动检测
       User explicit choice > Auto detection
    2. 代码相关任务 -> CODE模式
       Code-related tasks -> CODE mode
    3. 文档/办公任务 -> WORK模式
       Document/office tasks -> WORK mode
    """
    
    CODE_PATTERNS = {
        TaskCategory.CODE_GENERATION: [
            r"写.*函数", r"实现.*功能", r"创建.*类", r"编写.*代码",
            r"generate.*code", r"implement.*function", r"create.*class",
            r"添加.*方法", r"开发.*模块", r"build.*feature",
        ],
        TaskCategory.CODE_DEBUG: [
            r"debug", r"修复.*bug", r"解决.*错误", r"fix.*error",
            r"调试", r"排查.*问题", r"troubleshoot",
        ],
        TaskCategory.CODE_REFACTOR: [
            r"重构", r"优化.*代码", r"refactor", r"improve.*code",
            r"清理.*代码", r"重写", r"rewrite",
        ],
        TaskCategory.CODE_REVIEW: [
            r"代码.*审查", r"review.*code", r"检查.*代码",
            r"code.*review", r"分析.*代码质量",
        ],
    }
    
    WORK_PATTERNS = {
        TaskCategory.DOCUMENT_WRITING: [
            r"写.*文档", r"撰写.*报告", r"生成.*文档", r"创建.*PPT",
            r"write.*document", r"create.*report", r"制作.*演示",
            r"整理.*资料", r"总结.*内容",
        ],
        TaskCategory.DATA_ANALYSIS: [
            r"分析.*数据", r"统计.*报表", r"处理.*Excel",
            r"analyze.*data", r"数据.*分析", r"生成.*图表",
        ],
        TaskCategory.RESEARCH: [
            r"调研", r"搜索.*信息", r"查找.*资料", r"research",
            r"收集.*信息", r"了解.*情况",
        ],
        TaskCategory.TRANSLATION: [
            r"翻译", r"translate", r"转换.*语言",
        ],
    }
    
    CODE_KEYWORDS = [
        "代码", "编程", "程序", "函数", "类", "模块", "API",
        "git", "commit", "push", "pull", "branch", "merge",
        "test", "测试", "unit", "集成", "lint", "format",
        "debug", "调试", "错误", "异常", "bug", "fix",
        "refactor", "重构", "优化", "性能",
        "import", "export", "package", "dependency",
        "python", "javascript", "typescript", "java", "go", "rust",
        "实现", "算法", "排序", "搜索", "接口", "方法",
        "implement", "algorithm", "sort", "search", "interface",
        "编写", "开发", "编写代码", "写代码",
    ]
    
    WORK_KEYWORDS = [
        "文档", "报告", "文章", "PPT", "Excel", "表格",
        "分析", "统计", "数据", "图表", "可视化",
        "调研", "搜索", "查找", "收集",
        "翻译", "转换", "整理", "总结",
        "会议", "演示", "汇报", "方案",
    ]
    
    def __init__(
        self,
        mode_manager: Optional[AgentModeManager] = None,
        config: Optional[RouterConfig] = None,
    ):
        """
        初始化路由器 - Initialize router
        
        Args:
            mode_manager: 模式管理器实例 / Mode manager instance
            config: 路由器配置 / Router configuration
        """
        self.mode_manager = mode_manager
        self.config = config or RouterConfig()
    
    def analyze_task(self, task: str) -> Tuple[TaskCategory, float, List[str]]:
        """
        分析任务特征 - Analyze task characteristics
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            (任务类别, 置信度, 匹配原因) / (category, confidence, reasons)
        """
        task_lower = task.lower()
        reasons = []
        
        for category, patterns in self.CODE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    reasons.append(f"匹配代码模式: {pattern} / Matched code pattern")
                    return category, 0.9, reasons
        
        for category, patterns in self.WORK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, task_lower):
                    reasons.append(f"匹配工作模式: {pattern} / Matched work pattern")
                    return category, 0.9, reasons
        
        code_score = sum(1 for kw in self.CODE_KEYWORDS if kw in task_lower)
        work_score = sum(1 for kw in self.WORK_KEYWORDS if kw in task_lower)
        
        total = code_score + work_score
        if total == 0:
            return TaskCategory.GENERAL, 0.5, ["无明确特征 / No clear features"]
        
        if code_score > work_score:
            confidence = code_score / total
            reasons.append(f"代码关键词得分: {code_score} / Code keyword score")
            return TaskCategory.CODE_GENERATION, confidence, reasons
        else:
            confidence = work_score / total
            reasons.append(f"工作关键词得分: {work_score} / Work keyword score")
            return TaskCategory.DOCUMENT_WRITING, confidence, reasons
    
    def route(
        self,
        task: str,
        user_choice: Optional[ExecutionMode] = None,
    ) -> RoutingResult:
        """
        路由任务到合适的模式 - Route task to appropriate mode
        
        Args:
            task: 任务描述 / Task description
            user_choice: 用户显式选择的模式 / User explicitly chosen mode
            
        Returns:
            路由结果 / Routing result
        """
        category, confidence, reasons = self.analyze_task(task)
        
        task_features = {
            "length": len(task),
            "has_code_block": "```" in task,
            "has_file_path": "/" in task or "\\" in task,
            "has_url": "http" in task.lower(),
        }
        
        if user_choice is not None and self.config.prefer_user_choice:
            reasons.insert(0, "用户显式选择 / User explicit choice")
            return RoutingResult(
                mode=user_choice,
                category=category,
                confidence=1.0,
                reasons=reasons,
                task_features=task_features,
            )
        
        if not self.config.enable_auto_routing:
            current_mode = self.mode_manager.current_mode if self.mode_manager else ExecutionMode.WORK
            return RoutingResult(
                mode=current_mode,
                category=category,
                confidence=confidence,
                reasons=["使用当前模式 / Using current mode"],
                task_features=task_features,
            )
        
        code_categories = {
            TaskCategory.CODE_GENERATION,
            TaskCategory.CODE_DEBUG,
            TaskCategory.CODE_REFACTOR,
            TaskCategory.CODE_REVIEW,
        }
        
        if category in code_categories:
            mode = ExecutionMode.CODE
            if confidence >= self.config.code_mode_threshold:
                reasons.append("高置信度代码任务 / High confidence code task")
        else:
            mode = ExecutionMode.WORK
            if confidence >= self.config.work_mode_threshold:
                reasons.append("高置信度工作任务 / High confidence work task")
        
        return RoutingResult(
            mode=mode,
            category=category,
            confidence=confidence,
            reasons=reasons,
            task_features=task_features,
        )
    
    def execute(
        self,
        task: str,
        user_choice: Optional[ExecutionMode] = None,
    ) -> AgentResult:
        """
        路由并执行任务 - Route and execute task
        
        Args:
            task: 任务描述 / Task description
            user_choice: 用户选择的模式 / User chosen mode
            
        Returns:
            执行结果 / Execution result
        """
        if self.mode_manager is None:
            raise RuntimeError("ModeManager未设置 / ModeManager not set")
        
        routing = self.route(task, user_choice)
        
        if routing.mode != self.mode_manager.current_mode:
            self.mode_manager.switch_mode(
                routing.mode,
                reason=f"自动路由: {routing.category.value} / Auto routing"
            )
        
        return self.mode_manager.run(task)
    
    def get_routing_info(self, task: str) -> Dict[str, Any]:
        """
        获取路由信息（不执行） - Get routing info (without execution)
        
        Args:
            task: 任务描述 / Task description
            
        Returns:
            路由详细信息 / Detailed routing information
        """
        routing = self.route(task)
        return {
            "recommended_mode": routing.mode.value,
            "category": routing.category.value,
            "confidence": routing.confidence,
            "reasons": routing.reasons,
            "task_features": routing.task_features,
        }


def create_router(
    llm: Any = None,
    initial_mode: str = "work",
    enable_auto_routing: bool = True,
) -> ModeRouter:
    """
    创建路由器的便捷函数 - Convenience function to create router
    
    Args:
        llm: 语言模型实例 / Language model instance
        initial_mode: 初始模式 / Initial mode
        enable_auto_routing: 是否启用自动路由 / Whether to enable auto routing
        
    Returns:
        ModeRouter实例 / ModeRouter instance
    """
    from alonechat.agents.mode_manager import create_mode_manager
    
    mode_manager = create_mode_manager(
        llm=llm,
        mode=initial_mode,
        auto_detect_mode=enable_auto_routing,
    )
    
    router_config = RouterConfig(enable_auto_routing=enable_auto_routing)
    
    return ModeRouter(mode_manager=mode_manager, config=router_config)
