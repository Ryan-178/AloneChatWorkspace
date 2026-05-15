"""
MTC Agent - More Than Coding Agent
面向非开发用户的通用办公任务Agent
"""
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from agent_framework.agent.react_agent import ReActAgent, AgentCallback
from agent_framework.core.base_agent import AgentResult, AgentEvent
from agent_framework.core.base_llm import Message
from agent_framework.core.task import Task, TaskDependency, Artifact
from agent_framework.core.types import TaskStatus, TaskPriority, AgentMode
from agent_framework.tools.registry import ToolRegistry
from agent_framework.agent.mtc_prompts import (
    MTC_SYSTEM_PROMPT,
    INTENT_CLARIFICATION_TEMPLATE,
    TASK_PLANNING_TEMPLATE,
    OUTPUT_FORMAT_GUIDE,
)


class IntentClarifier:
    """意图澄清系统 - 用于澄清模糊的用户需求"""
    
    def __init__(self, llm, max_questions: int = 3):
        self.llm = llm
        self.max_questions = max_questions
        self.collected_answers: Dict[str, Any] = {}
    
    def should_clarify(self, task: str) -> bool:
        """判断是否需要澄清意图"""
        clarification_keywords = [
            "帮我", "弄一下", "处理", "做个", "写个",
            "分析", "整理", "优化", "改进"
        ]
        vague_indicators = [
            len(task) < 20,
            not any(char.isdigit() for char in task),
            any(keyword in task for keyword in clarification_keywords) and len(task.split()) < 10
        ]
        return sum(vague_indicators) >= 2
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """分析用户请求意图"""
        return {
            "original_task": task,
            "needs_clarification": self.should_clarify(task),
            "task_length": len(task),
            "has_numbers": any(char.isdigit() for char in task),
        }
    
    def generate_questions(self, task: str) -> List[Dict[str, Any]]:
        """生成追问表单（最多3个问题）"""
        questions = []
        
        if self.should_clarify(task):
            questions.append({
                "id": "output_format",
                "type": "choice",
                "question": "您希望输出什么格式的文档？",
                "options": ["Markdown", "Word文档", "PDF", "Excel表格", "PPT演示文稿"],
                "required": True,
            })
            
            questions.append({
                "id": "detail_level",
                "type": "choice",
                "question": "您需要多详细的内容？",
                "options": ["简要概述", "标准详细", "非常详细"],
                "required": True,
            })
            
            questions.append({
                "id": "target_audience",
                "type": "text",
                "question": "这份文档的目标读者是谁？（可选）",
                "required": False,
            })
        
        return questions[:self.max_questions]
    
    def collect_answers(self, answers: Dict[str, Any]) -> None:
        """收集用户回答"""
        self.collected_answers.update(answers)
    
    def integrate(self, original_task: str) -> str:
        """整合回答为完整需求"""
        if not self.collected_answers:
            return original_task
        
        integrated = f"原始需求：{original_task}\n\n"
        integrated += "澄清信息：\n"
        
        for key, value in self.collected_answers.items():
            integrated += f"- {key}: {value}\n"
        
        return integrated
    
    def reset(self) -> None:
        """重置澄清状态"""
        self.collected_answers = {}


class TaskPlanner:
    """任务规划器 - 将复杂任务分解为子任务"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def decompose(self, task: str) -> List[Task]:
        """将复杂任务分解为子任务列表"""
        subtasks = []
        
        task_lower = task.lower()
        
        if "文档" in task or "报告" in task or "写" in task:
            subtasks = [
                Task(
                    description="分析需求和目标",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="收集相关信息和数据",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="生成文档大纲",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    description="填充文档内容",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    description="格式化和优化输出",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.LOW,
                ),
            ]
        elif "数据" in task or "分析" in task:
            subtasks = [
                Task(
                    description="加载数据源",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="数据清洗和预处理",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="统计分析和计算",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    description="生成可视化图表",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    description="输出分析报告",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.LOW,
                ),
            ]
        elif "调研" in task or "搜索" in task:
            subtasks = [
                Task(
                    description="提取关键词和搜索策略",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="执行信息搜索",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    description="筛选和整理信息",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
                Task(
                    description="生成调研报告",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.LOW,
                ),
            ]
        else:
            subtasks = [
                Task(
                    description=f"执行任务：{task}",
                    status=TaskStatus.PENDING,
                    priority=TaskPriority.MEDIUM,
                ),
            ]
        
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies.append(
                TaskDependency(task_id=subtasks[i-1].id, type="requires")
            )
        
        return subtasks
    
    def identify_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """识别任务间依赖关系"""
        dependencies = {}
        for task in tasks:
            dep_ids = [dep.task_id for dep in task.dependencies]
            if dep_ids:
                dependencies[task.id] = dep_ids
        return dependencies
    
    def build_dag(self, tasks: List[Task]) -> Dict[str, Any]:
        """构建任务DAG图"""
        nodes = {task.id: task for task in tasks}
        edges = []
        
        for task in tasks:
            for dep in task.dependencies:
                edges.append((dep.task_id, task.id))
        
        return {
            "nodes": nodes,
            "edges": edges,
            "task_count": len(tasks),
        }
    
    def get_execution_order(self, tasks: List[Task]) -> List[List[Task]]:
        """获取执行顺序（拓扑排序，返回分层结果）"""
        if not tasks:
            return []
        
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: 0 for task in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in in_degree:
                    in_degree[task.id] += 1
        
        layers = []
        remaining = set(task.id for task in tasks)
        
        while remaining:
            ready = [tid for tid in remaining if in_degree[tid] == 0]
            
            if not ready:
                ready = [list(remaining)[0]]
            
            layer = [task_map[tid] for tid in ready]
            layers.append(layer)
            
            for tid in ready:
                remaining.remove(tid)
                for task in tasks:
                    if any(dep.task_id == tid for dep in task.dependencies):
                        in_degree[task.id] -= 1
        
        return layers
    
    def estimate_complexity(self, task: str) -> str:
        """估算任务复杂度"""
        complexity_indicators = {
            "high": ["完整", "详细", "全面", "多个", "复杂", "系统"],
            "medium": ["分析", "报告", "整理", "优化"],
            "low": ["简单", "快速", "简要", "概述"],
        }
        
        task_lower = task.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                return level
        
        return "medium"


class MTCAgent(ReActAgent):
    """MTC模式Agent - 面向非开发用户的通用办公任务Agent"""
    
    def __init__(
        self,
        llm,
        tool_registry: Optional[ToolRegistry] = None,
        memory=None,
        max_iterations: int = 10,
        name: str = "mtc_agent",
        system_prompt: Optional[str] = None,
        config=None,
    ):
        super().__init__(llm, tool_registry, memory, max_iterations, name, system_prompt)
        
        self.mode = AgentMode.MTC
        self.config = config
        
        self.intent_clarifier = IntentClarifier(
            llm=llm,
            max_questions=3 if config is None else config.mode.mtc_config.max_clarification_questions
        )
        self.task_planner = TaskPlanner(llm=llm)
        
        self.current_tasks: List[Task] = []
        self.artifacts: List[Artifact] = []
        self.clarification_enabled = True if config is None else config.mode.mtc_config.intent_clarification_enabled
    
    def _default_system_prompt(self) -> str:
        tools = self.tool_registry.list_tools()
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in tools
        ) if tools else "暂无可用工具"
        
        return MTC_SYSTEM_PROMPT.format(tools=tool_descriptions)
    
    def _load_tools(self) -> None:
        """加载MTC专用工具集"""
        try:
            from agent_framework.tools.mtc import register_mtc_tools
            register_mtc_tools(self.tool_registry)
        except ImportError:
            pass
    
    def clarify_intent(self, task: str) -> Dict[str, Any]:
        """意图澄清逻辑"""
        if not self.clarification_enabled:
            return {"needs_clarification": False, "task": task}
        
        analysis = self.intent_clarifier.analyze(task)
        
        if not analysis["needs_clarification"]:
            return {"needs_clarification": False, "task": task}
        
        questions = self.intent_clarifier.generate_questions(task)
        
        return {
            "needs_clarification": True,
            "task": task,
            "questions": questions,
            "analysis": analysis,
        }
    
    def collect_clarification_answers(self, answers: Dict[str, Any]) -> None:
        """收集澄清回答"""
        self.intent_clarifier.collect_answers(answers)
    
    def plan_task(self, task: str) -> Dict[str, Any]:
        """任务规划逻辑"""
        complexity = self.task_planner.estimate_complexity(task)
        
        if complexity == "low":
            return {
                "needs_planning": False,
                "task": task,
                "complexity": complexity,
            }
        
        subtasks = self.task_planner.decompose(task)
        self.current_tasks = subtasks
        
        execution_order = self.task_planner.get_execution_order(subtasks)
        dag = self.task_planner.build_dag(subtasks)
        
        return {
            "needs_planning": True,
            "task": task,
            "complexity": complexity,
            "subtasks": [t.model_dump() for t in subtasks],
            "execution_order": [[t.model_dump() for t in layer] for layer in execution_order],
            "dag": dag,
        }
    
    def get_task_progress(self) -> Dict[str, Any]:
        """获取任务进度"""
        if not self.current_tasks:
            return {"progress": 0, "tasks": []}
        
        total = len(self.current_tasks)
        completed = sum(1 for t in self.current_tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.current_tasks if t.status == TaskStatus.IN_PROGRESS)
        
        return {
            "progress": completed / total if total > 0 else 0,
            "completed": completed,
            "in_progress": in_progress,
            "total": total,
            "tasks": [t.model_dump() for t in self.current_tasks],
        }
    
    def add_artifact(self, artifact: Artifact) -> None:
        """添加产出物"""
        self.artifacts.append(artifact)
    
    def get_artifacts(self) -> List[Artifact]:
        """获取所有产出物"""
        return self.artifacts
    
    def run(self, task: str) -> AgentResult:
        """执行任务（覆盖父类，添加意图澄清和任务规划步骤）"""
        start_time = time.time()
        
        clarified_task = task
        if self.clarification_enabled:
            clarification = self.clarify_intent(task)
            if clarification["needs_clarification"]:
                clarified_task = self.intent_clarifier.integrate(task)
        
        planning = self.plan_task(clarified_task)
        
        if planning["needs_planning"]:
            for layer in self.task_planner.get_execution_order(self.current_tasks):
                for subtask in layer:
                    subtask.status = TaskStatus.IN_PROGRESS
                    
                    result = super().run(subtask.description)
                    
                    if result.answer:
                        subtask.status = TaskStatus.COMPLETED
                    else:
                        subtask.status = TaskStatus.FAILED
            
            final_result = super().run(clarified_task)
        else:
            final_result = super().run(clarified_task)
        
        total_time_ms = (time.time() - start_time) * 1000
        final_result.total_time_ms = total_time_ms
        
        return final_result
    
    async def run_stream(self, task: str) -> AsyncGenerator[AgentEvent, None]:
        """流式执行任务"""
        clarified_task = task
        if self.clarification_enabled:
            clarification = self.clarify_intent(task)
            if clarification["needs_clarification"]:
                yield AgentEvent(
                    type="clarification_needed",
                    content="需要澄清意图",
                    metadata={"questions": clarification["questions"]}
                )
                clarified_task = self.intent_clarifier.integrate(task)
        
        planning = self.plan_task(clarified_task)
        if planning["needs_planning"]:
            yield AgentEvent(
                type="plan_created",
                content="任务计划已创建",
                metadata={"subtasks": planning["subtasks"]}
            )
        
        async for event in super().run_stream(clarified_task):
            yield event
        
        yield AgentEvent(
            type="task_completed",
            content="任务完成",
            metadata={"artifacts": [a.model_dump() for a in self.artifacts]}
        )
    
    def reset(self) -> None:
        """重置Agent状态"""
        self.current_tasks = []
        self.artifacts = []
        self.intent_clarifier.reset()
