"""
CODE模式测试
"""
import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from agent_framework.core.types import AgentMode, FilePermission
from agent_framework.agent.code_agent import CodeAgent, SearchSubAgent, PlanMode
from agent_framework.sandbox.enhanced_sandbox import (
    EnhancedSandbox,
    create_mtc_sandbox,
    create_code_sandbox,
)


class TestCodeAgent:
    """测试CODE Agent"""
    
    def setup_method(self):
        self.mock_llm = Mock()
        self.mock_llm.chat = Mock(return_value=Mock(content="测试代码响应"))
    
    def test_agent_initialization(self):
        agent = CodeAgent(llm=self.mock_llm)
        assert agent.mode == AgentMode.CODE
    
    def test_agent_system_prompt(self):
        agent = CodeAgent(llm=self.mock_llm)
        prompt = agent._default_system_prompt()
        assert "CODE" in prompt or "代码" in prompt or "开发" in prompt
    
    def test_search_agent_initialization(self):
        agent = CodeAgent(llm=self.mock_llm)
        assert agent.search_agent is not None
    
    def test_plan_mode_initialization(self):
        agent = CodeAgent(llm=self.mock_llm)
        assert agent.plan_mode is not None


class TestSearchSubAgent:
    """测试Search子Agent"""
    
    def setup_method(self):
        self.mock_llm = Mock()
        self.search_agent = SearchSubAgent(self.mock_llm)
    
    @pytest.mark.asyncio
    async def test_search(self):
        result = await self.search_agent.search("test query", ".")
        assert isinstance(result, str)
    
    def test_clear_context(self):
        self.search_agent.isolated_context = [Mock()]
        self.search_agent.clear_context()
        assert len(self.search_agent.isolated_context) == 0


class TestPlanMode:
    """测试Plan Mode"""
    
    def setup_method(self):
        self.mock_llm = Mock()
        self.plan_mode = PlanMode(self.mock_llm)
    
    @pytest.mark.asyncio
    async def test_create_plan(self):
        plan = await self.plan_mode.create_plan("实现一个新功能")
        assert "task" in plan
        assert "steps" in plan
        assert "risks" in plan
    
    def test_format_plan_for_display(self):
        plan = {
            "task": "测试任务",
            "analysis": {"type": "generation"},
            "steps": [{"step": 1, "description": "步骤1", "needs_search": False}],
            "risks": [{"risk": "风险1", "mitigation": "应对1"}],
            "estimated_time": "10分钟",
        }
        formatted = self.plan_mode.format_plan_for_display(plan)
        assert "测试任务" in formatted
        assert "步骤1" in formatted


class TestEnhancedSandbox:
    """测试增强沙箱"""
    
    def test_mtc_sandbox_creation(self):
        sandbox = create_mtc_sandbox()
        assert sandbox.mode == AgentMode.MTC
        assert FilePermission.READ in sandbox.allowed_permissions
        assert FilePermission.WRITE in sandbox.allowed_permissions
    
    def test_code_sandbox_creation(self):
        sandbox = create_code_sandbox()
        assert sandbox.mode == AgentMode.CODE
        assert FilePermission.EXECUTE in sandbox.allowed_permissions
    
    def test_validate_path_within_project(self):
        sandbox = create_mtc_sandbox()
        is_valid = sandbox.validate_path(f"{sandbox.project_folder}/test.txt")
        assert is_valid
    
    def test_validate_path_outside_project(self):
        sandbox = create_mtc_sandbox()
        is_valid = sandbox.validate_path("/etc/passwd")
        assert not is_valid
    
    def test_validate_path_traversal_attack(self):
        sandbox = create_mtc_sandbox()
        is_valid = sandbox.validate_path(f"{sandbox.project_folder}/../../../etc/passwd")
        assert not is_valid
    
    def test_validate_allowed_command(self):
        sandbox = create_code_sandbox()
        is_valid, _ = sandbox.validate_command(["python", "--version"])
        assert is_valid
    
    def test_validate_forbidden_command(self):
        sandbox = create_code_sandbox()
        is_valid, error = sandbox.validate_command(["rm", "-rf", "/"])
        assert not is_valid
        assert "禁止" in error
    
    def test_validate_command_not_in_whitelist(self):
        sandbox = create_mtc_sandbox()
        is_valid, error = sandbox.validate_command(["docker", "ps"])
        assert not is_valid
        assert "白名单" in error
    
    def test_check_permission(self):
        sandbox = create_mtc_sandbox()
        assert sandbox.check_permission(FilePermission.READ)
        assert sandbox.check_permission(FilePermission.WRITE)
    
    def test_set_command_whitelist(self):
        sandbox = create_mtc_sandbox()
        sandbox.set_command_whitelist({"python", "node"})
        is_valid, _ = sandbox.validate_command(["python", "script.py"])
        assert is_valid
    
    def test_read_file(self):
        sandbox = create_mtc_sandbox()
        success, content = sandbox.read_file(f"{sandbox.project_folder}/nonexistent.txt")
        assert not success
    
    def test_write_file(self):
        sandbox = create_mtc_sandbox()
        success, path = sandbox.write_file(
            f"{sandbox.project_folder}/test.txt",
            "测试内容"
        )
        assert success
    
    def test_list_files(self):
        sandbox = create_mtc_sandbox()
        success, files = sandbox.list_files()
        assert success
    
    def test_get_sandbox_info(self):
        sandbox = create_code_sandbox()
        info = sandbox.get_sandbox_info()
        assert info["mode"] == "CODE"
        assert "allowed_commands" in info


class TestSandboxSecurity:
    """测试沙箱安全性"""
    
    def test_no_dangerous_commands_in_mtc(self):
        sandbox = create_mtc_sandbox()
        dangerous_commands = ["rm", "sudo", "bash", "wget", "curl"]
        for cmd in dangerous_commands:
            is_valid, _ = sandbox.validate_command([cmd])
            assert not is_valid
    
    def test_no_dangerous_commands_in_code(self):
        sandbox = create_code_sandbox()
        dangerous_commands = ["rm", "sudo", "wget", "curl"]
        for cmd in dangerous_commands:
            is_valid, _ = sandbox.validate_command([cmd])
            assert not is_valid
    
    def test_path_traversal_protection(self):
        sandbox = create_mtc_sandbox()
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/shadow",
            "C:\\Windows\\System32",
        ]
        for path in malicious_paths:
            is_valid = sandbox.validate_path(path)
            assert not is_valid


class TestCodeTools:
    """测试CODE工具"""
    
    def test_code_generator_tool(self):
        from agent_framework.tools.code.code_tools import CodeGeneratorTool
        
        tool = CodeGeneratorTool()
        result = tool.execute(
            language="python",
            description="测试函数",
        )
        assert result.success
        assert "code" in result.data
    
    def test_debug_analyzer_tool(self):
        from agent_framework.tools.code.code_tools import DebugAnalyzerTool
        
        tool = DebugAnalyzerTool()
        result = tool.execute(
            error_message="TypeError: 'NoneType' object is not iterable",
        )
        assert result.success
        assert result.data["error_type"] == "TypeError"
    
    def test_lint_tool(self):
        from agent_framework.tools.code.code_tools import LintTool
        
        tool = LintTool()
        long_line = "x = " + "1 + " * 50
        result = tool.execute(
            code=long_line,
            language="python",
        )
        assert result.success
        assert len(result.data["issues"]) > 0
