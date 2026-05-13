import math
from typing import Any, Dict

from agent_framework.core.base_tool import BaseTool


class CalculatorTool(BaseTool):
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

        result = eval(code, {"__builtins__": {}}, allowed_names)
        return result
