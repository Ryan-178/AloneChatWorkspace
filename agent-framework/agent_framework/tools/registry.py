import time
import json
from typing import Any, Dict, List, Optional

from agent_framework.core.base_tool import BaseTool, ToolDef, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._logs: List[Dict[str, Any]] = []

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("Tool must have a name")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[ToolDef]:
        tool = self._tools.get(name)
        if tool is None:
            return None
        return tool.get_definition()

    def execute_tool(self, name: str, params: Dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            result = ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
            )
            self._log_execution(name, params, result)
            return result

        schema = tool.parameters
        validation_error = self._validate_params(params, schema)
        if validation_error:
            result = ToolResult(
                success=False,
                error=validation_error,
            )
            self._log_execution(name, params, result)
            return result

        start = time.time()
        try:
            data = tool.execute(**params)
            execution_time_ms = (time.time() - start) * 1000
            result = ToolResult(
                success=True,
                data=data,
                execution_time_ms=execution_time_ms,
            )
        except Exception as e:
            execution_time_ms = (time.time() - start) * 1000
            result = ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

        self._log_execution(name, params, result)
        return result

    def _validate_params(self, params: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        if not schema:
            return None

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for key in required:
            if key not in params:
                return f"Missing required parameter: '{key}'"

        for key, value in params.items():
            if key not in properties:
                return f"Unknown parameter: '{key}'"
            prop = properties[key]
            expected_type = prop.get("type")
            if expected_type and not self._check_type(value, expected_type):
                return f"Parameter '{key}' must be of type {expected_type}, got {type(value).__name__}"

        return None

    def _check_type(self, value: Any, expected: str) -> bool:
        type_map = {
            "string": (str,),
            "integer": (int,),
            "number": (int, float),
            "boolean": (bool,),
            "array": (list, tuple),
            "object": (dict,),
        }
        allowed = type_map.get(expected, ())
        return isinstance(value, allowed)

    def _log_execution(self, name: str, params: Dict[str, Any], result: ToolResult) -> None:
        self._logs.append({
            "tool": name,
            "params": params,
            "success": result.success,
            "data": result.data if result.success else None,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.timestamp.isoformat(),
        })

    def get_logs(self) -> List[Dict[str, Any]]:
        return list(self._logs)

    def clear_logs(self) -> None:
        self._logs.clear()
