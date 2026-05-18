"""
MTC模式测试
"""
import pytest
from unittest.mock import Mock, AsyncMock

from agent_framework.core.types import AgentMode, TaskStatus, TaskPriority
from agent_framework.core.task import Task, TaskDependency, Artifact, Reference
from agent_framework.agent.mtc_agent import MTCAgent, IntentClarifier, TaskPlanner
from agent_framework.agent.intent_clarifier import ClarificationQuestion
from agent_framework.tools.skills_registry import SkillsRegistry, register_builtin_skills


class TestMTCTypes:
    """测试MTC相关类型"""
    
    def test_agent_mode_enum(self):
        assert AgentMode.MTC.value == "MTC"
        assert AgentMode.CODE.value == "CODE"
    
    def test_task_status_enum(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_task_priority_enum(self):
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"


class TestTaskModels:
    """测试任务模型"""
    
    def test_task_creation(self):
        task = Task(description="测试任务")
        assert task.description == "测试任务"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.id is not None
        assert task.created_at is not None
    
    def test_task_with_dependencies(self):
        task1 = Task(description="任务1")
        task2 = Task(
            description="任务2",
            dependencies=[TaskDependency(task_id=task1.id, type="requires")]
        )
        assert len(task2.dependencies) == 1
        assert task2.dependencies[0].task_id == task1.id
    
    def test_artifact_creation(self):
        artifact = Artifact(
            name="test.txt",
            type="document",
            path="/tmp/test.txt",
            size=100,
        )
        assert artifact.name == "test.txt"
        assert artifact.type == "document"
    
    def test_reference_creation(self):
        ref = Reference(
            source="web",
            url="https://example.com",
            title="Example",
            relevance_score=0.9,
        )
        assert ref.source == "web"
        assert ref.relevance_score == 0.9


class TestIntentClarifier:
    """测试意图澄清系统"""
    
    def setup_method(self):
        self.clarifier = IntentClarifier(llm=Mock(), max_questions=3)
    
    def test_should_clarify_vague_request(self):
        assert self.clarifier.should_clarify("帮我弄一下")
        assert self.clarifier.should_clarify("做个报告")
    
    def test_should_not_clarify_specific_request(self):
        assert not self.clarifier.should_clarify("生成一份包含销售数据的季度报告，输出为PDF格式")
    
    def test_generate_questions(self):
        questions = self.clarifier.generate_questions("帮我写个文档")
        assert len(questions) > 0
        assert len(questions) <= 3
    
    def test_collect_answers(self):
        self.clarifier.questions = [
            ClarificationQuestion(question_id="format", question_text="格式?", question_type="choice")
        ]
        self.clarifier.collect_answers({"format": "PDF"})
        assert self.clarifier.collected_answers["format"] == "PDF"
    
    def test_integrate(self):
        self.clarifier.questions = [
            ClarificationQuestion(question_id="format", question_text="格式?", question_type="choice")
        ]
        self.clarifier.collect_answers({"format": "PDF"})
        integrated = self.clarifier.integrate("写个文档")
        assert "PDF" in integrated
        assert "写个文档" in integrated


class TestTaskPlanner:
    """测试任务规划器"""
    
    def setup_method(self):
        self.planner = TaskPlanner()
    
    def test_decompose_document_task(self):
        tasks = self.planner.decompose("写一份项目报告")
        assert len(tasks) > 1
        assert all(isinstance(t, Task) for t in tasks)
    
    def test_decompose_data_task(self):
        tasks = self.planner.decompose("分析销售数据")
        assert len(tasks) > 1
        assert any("数据" in t.description for t in tasks)
    
    def test_identify_dependencies(self):
        tasks = self.planner.decompose("写一份报告")
        deps = self.planner.identify_dependencies(tasks)
        assert isinstance(deps, dict)
    
    def test_build_dag(self):
        tasks = self.planner.decompose("写一份报告")
        dag = self.planner.build_dag(tasks)
        assert "nodes" in dag
        assert "edges" in dag
        assert dag["task_count"] == len(tasks)
    
    def test_get_execution_order(self):
        tasks = self.planner.decompose("写一份报告")
        order = self.planner.get_execution_order(tasks)
        assert len(order) > 0
        assert all(isinstance(layer, list) for layer in order)
    
    def test_estimate_complexity(self):
        assert self.planner.estimate_complexity("简单任务") == "low"
        assert self.planner.estimate_complexity("完整的详细分析报告") == "high"


class TestMTCAgent:
    """测试MTC Agent"""
    
    def setup_method(self):
        self.mock_llm = Mock()
        self.mock_llm.chat = Mock(return_value=Mock(content="测试响应"))
    
    def test_agent_initialization(self):
        agent = MTCAgent(llm=self.mock_llm)
        assert agent.mode == AgentMode.MTC
        assert agent.clarification_enabled is True
    
    def test_agent_system_prompt(self):
        agent = MTCAgent(llm=self.mock_llm)
        prompt = agent._default_system_prompt()
        assert "MTC" in prompt or "文档" in prompt or "办公" in prompt
    
    def test_clarify_intent(self):
        agent = MTCAgent(llm=self.mock_llm)
        result = agent.clarify_intent("帮我弄一下")
        assert "needs_clarification" in result
    
    def test_plan_task(self):
        agent = MTCAgent(llm=self.mock_llm)
        result = agent.plan_task("写一份详细的项目报告")
        assert "needs_planning" in result
        assert "complexity" in result


class TestSkillsRegistry:
    """测试Skills注册系统"""
    
    def setup_method(self):
        self.registry = SkillsRegistry()
    
    def test_register_builtin_skills(self):
        register_builtin_skills(self.registry)
        skills = self.registry.list()
        assert len(skills) > 0
        assert any(s.name == "document_generation" for s in skills)
    
    def test_get_skill(self):
        register_builtin_skills(self.registry)
        skill = self.registry.get("document_generation")
        assert skill is not None
        assert skill.metadata.name == "document_generation"
    
    def test_search_skills(self):
        register_builtin_skills(self.registry)
        results = self.registry.search("文档")
        assert len(results) > 0
    
    def test_get_categories(self):
        register_builtin_skills(self.registry)
        categories = self.registry.get_categories()
        assert len(categories) > 0


class TestSkillsExecution:
    """测试Skills执行"""
    
    def setup_method(self):
        self.registry = SkillsRegistry()
        register_builtin_skills(self.registry)
    
    @pytest.mark.asyncio
    async def test_document_generation_skill(self):
        skill = self.registry.get("document_generation")
        result = await skill.execute({
            "title": "测试文档",
            "content": "这是测试内容",
        })
        assert result["success"] is True
        assert "document" in result
    
    @pytest.mark.asyncio
    async def test_data_analysis_skill(self):
        skill = self.registry.get("data_analysis")
        result = await skill.execute({
            "data": [1, 2, 3, 4, 5],
            "analysis_type": "summary",
        })
        assert result["success"] is True
        assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_web_research_skill(self):
        skill = self.registry.get("web_research")
        result = await skill.execute({
            "query": "测试搜索",
            "num_results": 3,
        })
        assert result["success"] is True
        assert "results" in result
