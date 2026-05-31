import pytest

from agent_framework.tools.registry import ToolRegistry
from agent_framework.tools.builtin.calculator import CalculatorTool
from agent_framework.tools.builtin.current_time import CurrentTimeTool
from agent_framework.tools.builtin.web_search import WebSearchTool
from agent_framework.core.base_tool import BaseTool, ToolResult


class DummyTool(BaseTool):
    name = "dummy"
    description = "A dummy tool"
    parameters = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "string"},
        },
        "required": ["x"],
    }

    def execute(self, x: int, y: str = "default") -> str:
        return f"{y}:{x}"


class NoNameTool(BaseTool):
    name = ""
    description = "No name"
    parameters = {}

    def execute(self, **kwargs):
        return "ok"


class TestToolRegistry:
    def test_register_and_list(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        tools = reg.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "dummy"
        assert tools[0]["description"] == "A dummy tool"

    def test_duplicate_name_raises(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(DummyTool())

    def test_register_no_name_raises(self):
        reg = ToolRegistry()
        with pytest.raises(ValueError, match="must have a name"):
            reg.register(NoNameTool())

    def test_get_tool(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        t = reg.get_tool("dummy")
        assert t is not None
        assert t.name == "dummy"

    def test_get_tool_not_found(self):
        reg = ToolRegistry()
        assert reg.get_tool("missing") is None

    def test_execute_tool_success(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        result = reg.execute_tool("dummy", {"x": 42, "y": "hello"})
        assert result.success is True
        assert result.data == "hello:42"
        assert result.error is None

    def test_execute_tool_with_defaults(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        result = reg.execute_tool("dummy", {"x": 1})
        assert result.success is True
        assert result.data == "default:1"

    def test_execute_tool_missing_required(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        result = reg.execute_tool("dummy", {"y": "hello"})
        assert result.success is False
        assert "Missing required parameter" in result.error

    def test_execute_tool_unknown_param(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        result = reg.execute_tool("dummy", {"x": 1, "z": 2})
        assert result.success is False
        assert "Unknown parameter" in result.error

    def test_execute_tool_not_found(self):
        reg = ToolRegistry()
        result = reg.execute_tool("missing", {})
        assert result.success is False
        assert "not found" in result.error

    def test_execute_tool_exception(self):
        class BadTool(BaseTool):
            name = "bad"
            description = "Bad tool"
            parameters = {}

            def execute(self, **kwargs):
                raise RuntimeError("boom")

        reg = ToolRegistry()
        reg.register(BadTool())
        result = reg.execute_tool("bad", {})
        assert result.success is False
        assert "boom" in result.error

    def test_unregister(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        reg.unregister("dummy")
        assert reg.get_tool("dummy") is None

    def test_logs(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        reg.execute_tool("dummy", {"x": 1})
        logs = reg.get_logs()
        assert len(logs) == 1
        assert logs[0]["tool"] == "dummy"
        assert logs[0]["success"] is True
        assert "timestamp" in logs[0]
        reg.clear_logs()
        assert len(reg.get_logs()) == 0

    def test_type_validation_string(self):
        reg = ToolRegistry()
        reg.register(DummyTool())
        result = reg.execute_tool("dummy", {"x": "not_int", "y": "hello"})
        assert result.success is False
        assert "must be of type integer" in result.error

    def test_type_validation_number(self):
        class NumTool(BaseTool):
            name = "num"
            description = "Num tool"
            parameters = {
                "type": "object",
                "properties": {"val": {"type": "number"}},
            }

            def execute(self, val: float = 0.0):
                return val

        reg = ToolRegistry()
        reg.register(NumTool())
        result = reg.execute_tool("num", {"val": "abc"})
        assert result.success is False
        assert "must be of type number" in result.error

        result2 = reg.execute_tool("num", {"val": 3.14})
        assert result2.success is True


class TestCalculatorTool:
    def test_basic_math(self):
        t = CalculatorTool()
        result = t.execute(expression="2 + 3 * 4")
        assert result == 14

    def test_math_functions(self):
        t = CalculatorTool()
        result = t.execute(expression="sqrt(16) + sin(0)")
        assert result == 4.0

    def test_disallowed_name(self):
        t = CalculatorTool()
        with pytest.raises(ValueError, match="Disallowed name"):
            t.execute(expression="__import__('os')")

    def test_disallowed_os(self):
        t = CalculatorTool()
        with pytest.raises(ValueError):
            t.execute(expression="os.system('ls')")

    def test_constants(self):
        t = CalculatorTool()
        result = t.execute(expression="pi + e")
        assert result > 5


class TestCurrentTimeTool:
    def test_iso_format(self):
        t = CurrentTimeTool()
        result = t.execute()
        assert len(result) > 0

    def test_human_format(self):
        t = CurrentTimeTool()
        result = t.execute(format="human")
        assert len(result) > 0
        assert ":" in result

    def test_timezone_offset(self):
        t = CurrentTimeTool()
        result = t.execute(timezone_offset_hours=8)
        assert len(result) > 0


class TestWebSearchTool:
    def test_fallback_without_duckduckgo(self):
        t = WebSearchTool()
        result = t.execute(query="python", num_results=2)
        assert isinstance(result, list)

    def test_definition(self):
        t = WebSearchTool()
        assert t.name == "web_search"
        assert "search" in t.description.lower()
