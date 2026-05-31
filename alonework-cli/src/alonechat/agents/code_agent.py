"""
CODE Agent - 面向开发者的编程任务Agent - CODE Agent - Programming Task Agent for Developers
"""
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from alonechat.agents.react_agent import ReActAgent, AgentCallback
from alonechat.core.base_agent import AgentResult, AgentEvent
from alonechat.core.base_llm import Message
from alonechat.core.task import Task, TaskDependency
from alonechat.core.types import TaskStatus, TaskPriority, AgentMode
from alonechat.tools.registry import ToolRegistry
from alonechat.agents.code_prompts import (
    CODE_SYSTEM_PROMPT,
    CODE_GENERATION_TEMPLATE,
    DEBUG_TEMPLATE,
    REFACTOR_TEMPLATE,
    SEARCH_AGENT_PROMPT,
    PLAN_MODE_PROMPT,
)


class SearchSubAgent:
    """
    Search子Agent - Search Sub-Agent
    上下文隔离的代码搜索 - Context-isolated code search
    """
    
    def __init__(self, llm, max_context_tokens: int = 32000):
        """
        初始化搜索子Agent - Initialize search sub-agent
        
        Args:
            llm: 语言模型实例 / Language model instance
            max_context_tokens: 最大上下文token数 / Maximum context tokens
        """
        self.llm = llm
        self.max_context_tokens = max_context_tokens
        self.isolated_context: List[Message] = []
    
    async def search(self, query: str, project_path: str) -> str:
        """执行代码搜索，返回精炼结果 - Execute code search, return refined results"""
        self.isolated_context = [
            Message(role="system", content="You are a code search assistant. Help find and summarize relevant code.")
        ]
        
        files = self._scan_project(project_path)
        
        relevant = self._find_relevant(files, query)
        
        self.isolated_context.append(
            Message(role="user", content=f"Search query: {query}\n\nRelevant files:\n{relevant}")
        )
        
        summary = f"搜索结果 / Search Results：\n{relevant}\n\n建议 / Suggestion：请查看上述文件以获取详细信息 / Please check the above files for details。"
        
        self.isolated_context.clear()
        
        return summary
    
    def _scan_project(self, project_path: str) -> List[Dict[str, Any]]:
        """扫描项目文件 - Scan project files"""
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
        """查找相关代码 - Find relevant code"""
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
            return "\n".join(f"- {path} (相关性 / Relevance: {score})" for path, score in relevant_files[:10])
        return "未找到相关文件 / No relevant files found"
    
    def clear_context(self) -> None:
        """清理上下文 - Clear context"""
        self.isolated_context.clear()


class PlanMode:
    """
    Plan Mode - 先规划后执行 - Plan Mode - Plan first, then execute
    """
    
    def __init__(self, llm):
        """初始化规划模式 - Initialize plan mode"""
        self.llm = llm
    
    async def create_plan(self, task: str) -> Dict[str, Any]:
        """创建执行计划 - Create execution plan"""
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
        """分析任务 - Analyze task"""
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
        """生成执行步骤 - Generate execution steps"""
        task_type = analysis["type"]
        
        if task_type == "generation":
            return [
                {"step": 1, "description": "理解需求和约束条件 / Understand requirements and constraints", "needs_search": False},
                {"step": 2, "description": "搜索相关代码和模式 / Search relevant code and patterns", "needs_search": True},
                {"step": 3, "description": "设计代码结构 / Design code structure", "needs_search": False},
                {"step": 4, "description": "生成代码实现 / Generate code implementation", "needs_search": False},
                {"step": 5, "description": "验证和测试 / Verify and test", "needs_search": False},
            ]
        elif task_type == "debug":
            return [
                {"step": 1, "description": "分析错误信息 / Analyze error message", "needs_search": False},
                {"step": 2, "description": "定位问题代码 / Locate problematic code", "needs_search": True},
                {"step": 3, "description": "识别根因 / Identify root cause", "needs_search": False},
                {"step": 4, "description": "实施修复 / Implement fix", "needs_search": False},
                {"step": 5, "description": "验证修复 / Verify fix", "needs_search": False},
            ]
        elif task_type == "refactor":
            return [
                {"step": 1, "description": "分析现有代码 / Analyze existing code", "needs_search": True},
                {"step": 2, "description": "识别重构点 / Identify refactoring points", "needs_search": False},
                {"step": 3, "description": "设计重构方案 / Design refactoring plan", "needs_search": False},
                {"step": 4, "description": "实施重构 / Implement refactoring", "needs_search": False},
                {"step": 5, "description": "验证行为不变 / Verify behavior unchanged", "needs_search": False},
            ]
        else:
            return [
                {"step": 1, "description": "分析任务 / Analyze task", "needs_search": False},
                {"step": 2, "description": "执行操作 / Execute operation", "needs_search": False},
                {"step": 3, "description": "验证结果 / Verify result", "needs_search": False},
            ]
    
    def _assess_risks(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """评估风险 - Assess risks"""
        return [
            {"risk": "代码变更可能影响其他模块 / Code changes may affect other modules", "mitigation": "运行完整测试套件 / Run full test suite"},
            {"risk": "性能可能退化 / Performance may degrade", "mitigation": "进行性能基准测试 / Run performance benchmarks"},
        ]
    
    def _estimate_time(self, steps: List[Dict[str, Any]]) -> str:
        """估算时间 - Estimate time"""
        step_count = len(steps)
        if step_count <= 3:
            return "5-10分钟 / 5-10 minutes"
        elif step_count <= 5:
            return "10-20分钟 / 10-20 minutes"
        else:
            return "20-30分钟 / 20-30 minutes"
    
    def format_plan_for_display(self, plan: Dict[str, Any]) -> str:
        """格式化计划用于展示 - Format plan for display"""
        output = f"## 执行计划 / Execution Plan\n\n"
        output += f"**任务 / Task**: {plan['task']}\n"
        output += f"**类型 / Type**: {plan['analysis']['type']}\n"
        output += f"**预计时间 / Estimated Time**: {plan['estimated_time']}\n\n"
        
        output += "### 执行步骤 / Execution Steps\n"
        for step in plan["steps"]:
            output += f"{step['step']}. {step['description']}"
            if step.get("needs_search"):
                output += " (需要搜索 / Needs search)"
            output += "\n"
        
        output += "\n### 风险评估 / Risk Assessment\n"
        for risk in plan["risks"]:
            output += f"- {risk['risk']}\n"
            output += f"  应对 / Mitigation: {risk['mitigation']}\n"
        
        return output


class CodeAgent(ReActAgent):
    """
    CODE模式Agent - CODE Mode Agent
    面向开发者的编程任务Agent - Programming task Agent for developers
    
    支持两种执行路径：
    1. CodexBridge: 通过 Codex CLI 二进制执行（更强大，支持沙箱）
    2. LLM ReAct: 通过 LLM ReAct 循环执行（纯 Python，更灵活）
    """
    
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
        use_codex_bridge: bool = False,
        codex_config: Optional[Any] = None,
    ):
        """
        初始化CODE Agent - Initialize CODE Agent
        
        Args:
            llm: 语言模型实例 / Language model instance
            tool_registry: 工具注册表 / Tool registry
            memory: 记忆模块 / Memory module
            max_iterations: 最大迭代次数 / Maximum iteration count
            name: Agent名称 / Agent name
            system_prompt: 系统提示词 / System prompt
            config: 配置对象 / Configuration object
            project_path: 项目路径 / Project path
            use_codex_bridge: 是否使用 CodexBridge / Whether to use CodexBridge
            codex_config: CodexBridge 配置 / CodexBridge configuration
        """
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
        
        self._codex_bridge: Optional[Any] = None
        if use_codex_bridge:
            try:
                from alonechat.code.codex_bridge import CodexBridge, CodexBridgeConfig
                if codex_config is not None:
                    self._codex_bridge = CodexBridge(codex_config)
                else:
                    self._codex_bridge = CodexBridge(CodexBridgeConfig(working_directory=self.project_path))
            except ImportError:
                self._codex_bridge = None
    
    def _default_system_prompt(self) -> str:
        """获取默认系统提示词 - Get default system prompt"""
        tools = self.tool_registry.list_tools()
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in tools
        ) if tools else "暂无可用工具 / No tools available"
        
        return CODE_SYSTEM_PROMPT.format(tools=tool_descriptions)
    
    def _load_tools(self) -> None:
        """加载CODE专用工具集 - Load CODE-specific tool set"""
        try:
            from alonechat.tools.code import register_code_tools
            register_code_tools(self.tool_registry)
        except ImportError:
            pass
    
    async def analyze_code(self, code: str) -> Dict[str, Any]:
        """代码分析功能 - Code analysis functionality"""
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
                "建议添加类型注解 / Suggest adding type annotations" if "def " in code and ":" not in code.split("def ")[1].split("\n")[0] else None,
                "建议添加文档注释 / Suggest adding docstrings" if '"""' not in code and "'''" not in code else None,
            ],
        }
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Optional[str] = None,
    ) -> str:
        """代码生成功能 - Code generation functionality"""
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
            messages.append(Message(role="user", content=f"上下文代码 / Context Code：\n{context}"))
        
        response = self.llm.chat(messages)
        return response.content
    
    async def debug_code(
        self,
        error_message: str,
        code_context: str,
    ) -> Dict[str, Any]:
        """调试支持功能 - Debug support functionality"""
        prompt = DEBUG_TEMPLATE.format(
            error_message=error_message,
            code_context=code_context,
            error_type="Unknown",
            error_location="待定位 / To be located",
            error_description=error_message,
            stack_trace="无堆栈信息 / No stack trace",
            call_chain="待分析 / To be analyzed",
            key_frames="待识别 / To be identified",
            direct_cause="待分析 / To be analyzed",
            root_cause="待分析 / To be analyzed",
            impact_scope="待评估 / To be assessed",
            solution_1="分析错误信息 / Analyze error message",
            solution_2="检查代码逻辑 / Check code logic",
            comparison="需要更多信息 / Need more information",
            test_case="待生成 / To be generated",
            verification_steps="待确定 / To be determined",
            problematic_code=code_context,
            fixed_code="待生成 / To be generated",
            fix_explanation="待分析 / To be analyzed",
            risk_warning="待评估 / To be assessed",
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
                "检查变量类型是否正确 / Check if variable types are correct",
                "验证输入数据格式 / Validate input data format",
                "检查边界条件处理 / Check boundary condition handling",
            ],
        }
    
    async def refactor_code(
        self,
        code: str,
        refactor_goal: str,
    ) -> Dict[str, Any]:
        """重构功能 - Refactoring functionality"""
        prompt = REFACTOR_TEMPLATE.format(
            refactor_goal=refactor_goal,
            current_code=code,
            before_code=code,
            issue_1="代码结构待优化 / Code structure needs optimization",
            issue_2="可能存在重复代码 / May have duplicate code",
            issue_3="命名可能不够清晰 / Naming may not be clear",
            after_code="重构后的代码 / Refactored code",
            improvement_1="提升代码可读性 / Improve code readability",
            improvement_2="减少代码重复 / Reduce code duplication",
            improvement_3="优化代码结构 / Optimize code structure",
            risk_1="行为可能改变 / Behavior may change",
            impact_1="中 / Medium",
            mitigation_1="运行测试验证 / Run tests to verify",
            risk_2="性能可能受影响 / Performance may be affected",
            impact_2="低 / Low",
            mitigation_2="进行性能测试 / Run performance tests",
            test_cases="待生成测试用例 / Test cases to be generated",
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
                "优化代码结构 / Optimize code structure",
                "提取公共方法 / Extract common methods",
                "改善命名 / Improve naming",
            ],
        }
    
    async def search_code(self, query: str) -> str:
        """使用Search子Agent搜索代码 - Search code using Search Sub-Agent"""
        if self.search_agent:
            return await self.search_agent.search(query, self.project_path)
        return "Search子Agent未启用 / Search Sub-Agent not enabled"
    
    async def create_execution_plan(self, task: str) -> Dict[str, Any]:
        """创建执行计划（Plan Mode） - Create execution plan (Plan Mode)"""
        if self.plan_mode:
            self.current_plan = await self.plan_mode.create_plan(task)
            return self.current_plan
        return {"error": "Plan Mode未启用 / Plan Mode not enabled"}
    
    def run(self, task: str) -> AgentResult:
        """执行任务（覆盖父类，添加代码上下文理解） - Execute task (override parent, add code context understanding)"""
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
        """流式执行任务 - Execute task with streaming"""
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
            content="执行完成 / Execution completed",
            metadata={"history_count": len(self.execution_history)}
        )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史 - Get execution history"""
        return self.execution_history
    
    async def execute_with_codex(
        self,
        prompt: str,
        cwd: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
    ) -> Any:
        """通过 CodexBridge 执行编码任务 - Execute coding task via CodexBridge"""
        if not self._codex_bridge:
            raise RuntimeError("CodexBridge not available. Set use_codex_bridge=True or install codex CLI.")
        
        work_dir = cwd or self.project_path
        
        if stream:
            return self._codex_bridge.exec_stream(prompt, cwd=work_dir, model=model)
        else:
            return await self._codex_bridge.exec(prompt, cwd=work_dir, model=model)

    async def review_with_codex(
        self,
        cwd: Optional[str] = None,
        target: Optional[str] = None,
    ) -> Any:
        """通过 CodexBridge 进行代码审查 - Review code via CodexBridge"""
        if not self._codex_bridge:
            raise RuntimeError("CodexBridge not available.")
        return await self._codex_bridge.review(cwd=cwd or self.project_path, target=target)

    async def apply_codex_changes(self, cwd: Optional[str] = None) -> Any:
        """应用 Codex 生成的代码变更 - Apply Codex-generated changes"""
        if not self._codex_bridge:
            raise RuntimeError("CodexBridge not available.")
        return await self._codex_bridge.apply(cwd=cwd or self.project_path)

    @property
    def has_codex(self) -> bool:
        """检查 CodexBridge 是否可用 - Check if CodexBridge is available"""
        return self._codex_bridge is not None

    def run(self, task: str) -> AgentResult:
        """执行任务 - Execute task"""
        start_time = time.time()
        
        result = super().run(task)
        
        self.execution_history.append({
            "task": task,
            "result": result.answer,
            "time_ms": result.total_time_ms,
            "timestamp": time.time(),
            "engine": "codex_bridge" if self._codex_bridge else "llm_react",
        })
        
        total_time_ms = (time.time() - start_time) * 1000
        result.total_time_ms = total_time_ms
        
        return result

    def cleanup(self) -> None:
        """清理资源 - Cleanup resources"""
        if self._codex_bridge:
            self._codex_bridge.cleanup()
        self.reset()

    def reset(self) -> None:
        """重置Agent状态 - Reset Agent state"""
        self.current_plan = None
        self.execution_history = []
        if self.search_agent:
            self.search_agent.clear_context()
