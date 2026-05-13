"""
Gateway 工具系统
基于现有的BaseTool，提供工具注册表、内置工具和工具执行
"""
import time
import math
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from agent_framework.core.base_tool import BaseTool, ToolDef, ToolResult


# ==================== 内置工具 ====================

class CalculatorTool(BaseTool):
    """计算器工具"""
    name = "calculator"
    description = "Evaluate a mathematical expression. Supports basic arithmetic, math functions (sin, cos, log, sqrt, etc.), and constants (pi, e)."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate, e.g. '2 + 2 * 3' or 'sqrt(16) + sin(pi/2)'",
            },
        },
        "required": ["expression"],
    }

    def execute(self, expression: str) -> Any:
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("_")
        }
        allowed_names["pi"] = math.pi
        allowed_names["e"] = math.e

        code = compile(expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise ValueError(f"Disallowed name in expression: {name}")

        return eval(code, {"__builtins__": {}}, allowed_names)


class CurrentTimeTool(BaseTool):
    """获取当前时间工具"""
    name = "current_time"
    description = "Get the current date and time."
    parameters = {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Optional format string (strftime format)",
                "default": "%Y-%m-%d %H:%M:%S",
            },
            "timezone": {
                "type": "string",
                "description": "Optional timezone (not implemented yet, uses local time)",
                "default": "local",
            },
        },
        "required": [],
    }

    def execute(self, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "local") -> str:
        return datetime.now().strftime(format)


class WebSearchTool(BaseTool):
    """网络搜索工具（简单实现）"""
    name = "web_search"
    description = "Perform a web search (simulated for now)."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        # 简单模拟搜索
        results = [
            {
                "title": f"Search Result 1 for: {query}",
                "snippet": f"This is a simulated search result about {query}. In a real implementation, this would fetch from a search API.",
                "url": "https://example.com/result1",
            },
            {
                "title": f"Search Result 2 for: {query}",
                "snippet": f"Another simulated result. You could integrate with SerpAPI, Bing Search, or Google Search API.",
                "url": "https://example.com/result2",
            },
            {
                "title": f"Search Result 3 for: {query}",
                "snippet": "Remember to respect rate limits and terms of service when using real search APIs.",
                "url": "https://example.com/result3",
            },
        ]
        return results[:num_results]


# ==================== 工具注册表 ====================

class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.register(CalculatorTool())
        self.register(CurrentTimeTool())
        self.register(WebSearchTool())
    
    def register(self, tool: BaseTool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """获取一个工具"""
        return self._tools.get(name)
    
    def get_all(self) -> List[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_all_definitions(self) -> List[ToolDef]:
        """获取所有工具定义（用于传给LLM）"""
        return [tool.get_definition() for tool in self._tools.values()]
    
    def get_all_openai_format(self) -> List[Dict[str, Any]]:
        """获取OpenAI格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self._tools.values()
        ]
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具（异步版本）"""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
                execution_time_ms=0.0,
            )
        
        start_time = time.time()
        try:
            result = tool.execute(**kwargs)
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )


# 全局工具注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
