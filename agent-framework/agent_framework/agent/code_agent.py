"""
CODE Agent - 面向开发者的编程任务Agent
"""
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from agent_framework.agent.react_agent import ReActAgent, AgentCallback
from agent_framework.core.base_agent import AgentResult, AgentEvent
from agent_framework.core.base_llm import Message
from agent_framework.core.task import Task, TaskDependency
from agent_framework.core.types import TaskStatus, TaskPriority, AgentMode
from agent_framework.tools.registry import ToolRegistry
from agent_framework.agent.code_prompts import (
    CODE_SYSTEM_PROMPT,
    CODE_GENERATION_TEMPLATE,
    DEBUG_TEMPLATE,
    REFACTOR_TEMPLATE,
    SEARCH_AGENT_PROMPT,
    PLAN_MODE_PROMPT,
)


class SearchSubAgent:
    """Search子Agent - 上下文隔离的代码搜索"""
    
    def __init__(self, llm, max_context_tokens: int = 32000):
        self.llm = llm
        self.max_context_tokens = max_context_tokens
        self.isolated_context: List[Message] = []
    
    async def search(self, query: str, project_path: str) -> str:
        """执行代码搜索，返回精炼结果"""
        self.isolated_context = [
            Message(role="system", content="You are a code search assistant. Help find and summarize relevant code.")
        ]
        
        files = self._scan_project(project_path)
        
        relevant = self._find_relevant(files, query)
        
        self.isolated_context.append(
            Message(role="user", content=f"Search query: {query}\n\nRelevant files:\n{relevant}")
        )
        
        summary = f"搜索结果：\n{relevant}\n\n建议：请查看上述文件以获取详细信息。"
        
        self.isolated_context.clear()
        
        return summary
    
    def _scan_project(self, project_path: str) -> List[Dict[str, Any]]:
        """扫描项目文件"""
        import os
        from pathlib import Path
        
        files = []
        code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"}
        
        try:
            root = Path(project_path)
            for file_path in root.rglob("*"):
                if file_path.is_file() and file_path.suffix in code_extensions:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read(5000)
                        files.append({
                            "path": str(file_path.relative_to(root)),
                            "content": content,
                            "size": file_path.stat().st_size,
                        })
                    except Exception:
                        pass
        except Exception:
            pass
        
        return files[:50]
    
    def _find_relevant(self, files: List[Dict[str, Any]], query: str) -> str:
        """查找相关代码"""
        query_lower = query.lower()
        keywords = query_lower.split()
        
        relevant_files = []
        for file_info in files:
            content_lower = file_info["content"].lower()
            score = sum(1 for kw in keywords if kw in content_lower)
            
            if score > 0:
                relevant_files.append((file_info["path"], score))
        
        relevant_files.sort(key=lambda x: x[1], reverse=True)
        
        if relevant_files:
            return "\n".join(f"- {path} (相关性: {score})" for path, score in relevant_files[:10])
        return "未找到相关文件"
    
    def clear_context(self) -> None:
        """清理上下文"""
        self.isolated_context.clear()


class PlanMode:
    """Plan Mode - 先规划后执行"""
    
    def __init__(self, llm):
        self.llm = llm
    
    async def create_plan(self, task: str) -> Dict[str, Any]:
        """创建执行计划"""
        analysis = self._analyze_task(task)
        
        steps = self._generate_steps(analysis)
        
        risks = self._assess_risks(steps)
        
        return {
            "task": task,
            "analysis": analysis,
            "steps": steps,
            "risks": risks,
            "estimated_time": self._estimate_time(steps),
        }
    
    def _analyze_task(self, task: str) -> Dict[str, Any]:
        """分析任务"""
        task_lower = task.lower()
        
        task_type = "general"
        if "生成" in task or "创建" in task:
            task_type = "generation"
        elif "修复" in task or "调试" in task or "bug" in task_lower:
            task_type = "debug"
        elif "重构" in task or "优化" in task:
            task_type = "refactor"
        elif "测试" in task:
            task_type = "test"
        
        return {
            "type": task_type,
            "complexity": "medium",
            "keywords": task.split()[:5],
        }
    
    def _generate_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成执行步骤"""
        task_type = analysis["type"]
        
        if task_type == "generation":
            return [
                {"step": 1, "description": "理解需求和约束条件", "needs_search": False},
                {"step": 2, "description": "搜索相关代码和模式", "needs_search": True},
                {"step": 3, "description": "设计代码结构", "needs_search": False},
                {"step": 4, "description": "生成代码实现", "needs_search": False},
                {"step": 5, "description": "验证和测试", "needs_search": False},
            ]
        elif task_type == "debug":
            return [
                {"step": 1, "description": "分析错误信息", "needs_search": False},
                {"step": 2, "description": "定位问题代码", "needs_search": True},
                {"step": 3, "description": "识别根因", "needs_search": False},
                {"step": 4, "description": "实施修复", "needs_search": False},
                {"step": 5, "description": "验证修复", "needs_search": False},
            ]
        elif task_type == "refactor":
            return [
                {"step": 1, "description": "分析现有代码", "needs_search": True},
                {"step": 2, "description": "识别重构点", "needs_search": False},
                {"step": 3, "description": "设计重构方案", "needs_search": False},
                {"step": 4, "description": "实施重构", "needs_search": False},
                {"step": 5, "description": "验证行为不变", "needs_search": False},
            ]
        else:
            return [
                {"step": 1, "description": "分析任务", "needs_search": False},
                {"step": 2, "description": "执行操作", "needs_search": False},
                {"step": 3, "description": "验证结果", "needs_search": False},
            ]
    
    def _assess_risks(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """评估风险"""
        return [
            {"risk": "代码变更可能影响其他模块", "mitigation": "运行完整测试套件"},
            {"risk": "性能可能退化", "mitigation": "进行性能基准测试"},
        ]
    
    def _estimate_time(self, steps: List[Dict[str, Any]]) -> str:
        """估算时间"""
        step_count = len(steps)
        if step_count <= 3:
            return "5-10分钟"
        elif step_count <= 5:
            return "10-20分钟"
        else:
            return "20-30分钟"
    
    def format_plan_for_display(self, plan: Dict[str, Any]) -> str:
        """格式化计划用于展示"""
        output = f"## 执行计划\n\n"
        output += f"**任务**: {plan['task']}\n"
        output += f"**类型**: {plan['analysis']['type']}\n"
        output += f"**预计时间**: {plan['estimated_time']}\n\n"
        
        output += "### 执行步骤\n"
        for step in plan["steps"]:
            output += f"{step['step']}. {step['description']}"
            if step.get("needs_search"):
                output += " (需要搜索)"
            output += "\n"
        
        output += "\n### 风险评估\n"
        for risk in plan["risks"]:
            output += f"- {risk['risk']}\n"
            output += f"  应对: {risk['mitigation']}\n"
        
        return output


class CodeAgent(ReActAgent):
    """CODE模式Agent - 面向开发者的编程任务Agent"""
    
    def __init__(
        self,
        llm,
        tool_registry: Optional[ToolRegistry] = None,
        memory=None,
        max_iterations: int = 10,
        name: str = "code_agent",
        system_prompt: Optional[str] = None,
        config=None,
        project_path: Optional[str] = None,
    ):
        super().__init__(llm, tool_registry, memory, max_iterations, name, system_prompt)
        
        self.mode = AgentMode.CODE
        self.config = config
        self.project_path = project_path or "."
        
        enable_search = True if config is None else config.mode.code_config.enable_search_agent
        enable_plan = True if config is None else config.mode.code_config.enable_plan_mode
        max_tokens = 128000 if config is None else config.mode.code_config.max_context_tokens
        
        self.search_agent = SearchSubAgent(llm, max_tokens) if enable_search else None
        self.plan_mode = PlanMode(llm) if enable_plan else None
        
        self.current_plan: Optional[Dict[str, Any]] = None
        self.execution_history: List[Dict[str, Any]] = []
    
    def _default_system_prompt(self) -> str:
        tools = self.tool_registry.list_tools()
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in tools
        ) if tools else "暂无可用工具"
        
        return CODE_SYSTEM_PROMPT.format(tools=tool_descriptions)
    
    def _load_tools(self) -> None:
        """加载CODE专用工具集"""
        try:
            from agent_framework.tools.code import register_code_tools
            register_code_tools(self.tool_registry)
        except ImportError:
            pass
    
    async def analyze_code(self, code: str) -> Dict[str, Any]:
        """代码分析功能"""
        analysis = {
            "lines": len(code.split("\n")),
            "chars": len(code),
            "functions": code.count("def ") + code.count("function "),
            "classes": code.count("class "),
            "imports": code.count("import "),
        }
        
        return {
            "analysis": analysis,
            "suggestions": [
                "建议添加类型注解" if "def " in code and ":" not in code.split("def ")[1].split("\n")[0] else None,
                "建议添加文档注释" if '"""' not in code and "'''" not in code else None,
            ],
        }
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Optional[str] = None,
    ) -> str:
        """代码生成功能"""
        prompt = CODE_GENERATION_TEMPLATE.format(
            user_request=description,
            language=language,
            file_path="generated_code.py",
            description=description,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]
        
        if context:
            messages.append(Message(role="user", content=f"上下文代码：\n{context}"))
        
        response = self.llm.chat(messages)
        return response.content
    
    async def debug_code(
        self,
        error_message: str,
        code_context: str,
    ) -> Dict[str, Any]:
        """调试支持功能"""
        prompt = DEBUG_TEMPLATE.format(
            error_message=error_message,
            code_context=code_context,
            error_type="Unknown",
            error_location="待定位",
            error_description=error_message,
            stack_trace="无堆栈信息",
            call_chain="待分析",
            key_frames="待识别",
            direct_cause="待分析",
            root_cause="待分析",
            impact_scope="待评估",
            solution_1="分析错误信息",
            solution_2="检查代码逻辑",
            comparison="需要更多信息",
            test_case="待生成",
            verification_steps="待确定",
            problematic_code=code_context,
            fixed_code="待生成",
            fix_explanation="待分析",
            risk_warning="待评估",
        )
        
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]
        
        response = self.llm.chat(messages)
        
        return {
            "analysis": response.content,
            "error_message": error_message,
            "suggestions": [
                "检查变量类型是否正确",
                "验证输入数据格式",
                "检查边界条件处理",
            ],
        }
    
    async def refactor_code(
        self,
        code: str,
        refactor_goal: str,
    ) -> Dict[str, Any]:
        """重构功能"""
        prompt = REFACTOR_TEMPLATE.format(
            refactor_goal=refactor_goal,
            current_code=code,
            before_code=code,
            issue_1="代码结构待优化",
            issue_2="可能存在重复代码",
            issue_3="命名可能不够清晰",
            after_code="重构后的代码",
            improvement_1="提升代码可读性",
            improvement_2="减少代码重复",
            improvement_3="优化代码结构",
            risk_1="行为可能改变",
            impact_1="中",
            mitigation_1="运行测试验证",
            risk_2="性能可能受影响",
            impact_2="低",
            mitigation_2="进行性能测试",
            test_cases="待生成测试用例",
        )
        
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]
        
        response = self.llm.chat(messages)
        
        return {
            "refactored_code": response.content,
            "original_code": code,
            "goal": refactor_goal,
            "changes": [
                "优化代码结构",
                "提取公共方法",
                "改善命名",
            ],
        }
    
    async def search_code(self, query: str) -> str:
        """使用Search子Agent搜索代码"""
        if self.search_agent:
            return await self.search_agent.search(query, self.project_path)
        return "Search子Agent未启用"
    
    async def create_execution_plan(self, task: str) -> Dict[str, Any]:
        """创建执行计划（Plan Mode）"""
        if self.plan_mode:
            self.current_plan = await self.plan_mode.create_plan(task)
            return self.current_plan
        return {"error": "Plan Mode未启用"}
    
    def run(self, task: str) -> AgentResult:
        """执行任务（覆盖父类，添加代码上下文理解）"""
        start_time = time.time()
        
        result = super().run(task)
        
        self.execution_history.append({
            "task": task,
            "result": result.answer,
            "time_ms": result.total_time_ms,
            "timestamp": time.time(),
        })
        
        total_time_ms = (time.time() - start_time) * 1000
        result.total_time_ms = total_time_ms
        
        return result
    
    async def run_stream(self, task: str) -> AsyncGenerator[AgentEvent, None]:
        """流式执行任务"""
        if self.plan_mode:
            plan = await self.create_execution_plan(task)
            yield AgentEvent(
                type="plan_created",
                content=self.plan_mode.format_plan_for_display(plan),
                metadata={"plan": plan}
            )
        
        async for event in super().run_stream(task):
            yield event
        
        yield AgentEvent(
            type="execution_completed",
            content="执行完成",
            metadata={"history_count": len(self.execution_history)}
        )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history
    
    def reset(self) -> None:
        """重置Agent状态"""
        self.current_plan = None
        self.execution_history = []
        if self.search_agent:
            self.search_agent.clear_context()
