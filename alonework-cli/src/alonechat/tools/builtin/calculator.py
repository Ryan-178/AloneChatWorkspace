import math
import re
from typing import Any, Dict

from alonechat.core.base_tool import BaseTool


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

    # 允许的操作符和函数白名单
    ALLOWED_OPERATORS = set("+-*/%^()., ")
    ALLOWED_NAMES = {
        k: v for k, v in math.__dict__.items() if not k.startswith("_")
    }
    ALLOWED_NAMES["pi"] = math.pi
    ALLOWED_NAMES["e"] = math.e

    def _sanitize_expression(self, expression: str) -> str:
        """清理并验证表达式，只允许安全的数学表达式"""
        # 移除所有空白字符用于检查
        stripped = expression.replace(" ", "").replace("\t", "").replace("\n", "")

        # 检查是否包含危险字符或模式
        dangerous_patterns = [
            r"__\w+",
            r"\bimport\b",
            r"\bexec\b",
            r"\beval\b",
            r"\bcompile\b",
            r"\bopen\b",
            r"\bfile\b",
            r"\bsubprocess\b",
            r"\bos\.",
            r"\bsys\.",
            r"\bclass\b",
            r"\blambda\b",
            r"\byield\b",
            r"\bglobal\b",
            r"\bnonlocal\b",
            r"\bassert\b",
            r"\braise\b",
            r"\btry\b",
            r"\bexcept\b",
            r"\bfinally\b",
            r"\bwith\b",
            r"\bdef\b",
            r"\bfor\b",
            r"\bwhile\b",
            r"\bif\b",
            r"\belif\b",
            r"\belse\b",
            r"\bpass\b",
            r"\bbreak\b",
            r"\bcontinue\b",
            r"\breturn\b",
            r"\bdel\b",
            r"\bprint\b",
            r"\binput\b",
            r"\bgetattr\b",
            r"\bsetattr\b",
            r"\bdelattr\b",
            r"\bhasattr\b",
            r"\bvars\b",
            r"\blocals\b",
            r"\bglobals\b",
            r"\bdir\b",
            r"\bchr\b",
            r"\bord\b",
            r"\bformat\b",
            r"\bjoin\b",
            r"\bsplit\b",
            r"\breplace\b",
            r"\bencode\b",
            r"\bdecode\b",
            r"\bhex\b",
            r"\boct\b",
            r"\bbin\b",
            r"\bascii\b",
            r"\brepr\b",
            r"\bstr\b",
            r"\bint\b",
            r"\bfloat\b",
            r"\blist\b",
            r"\bdict\b",
            r"\btuple\b",
            r"\bset\b",
            r"\bfrozenset\b",
            r"\bbytearray\b",
            r"\bbytes\b",
            r"\bmemoryview\b",
            r"\btype\b",
            r"\bisinstance\b",
            r"\bissubclass\b",
            r"\bcallable\b",
            r"\bstaticmethod\b",
            r"\bclassmethod\b",
            r"\bproperty\b",
            r"\bsuper\b",
            r"\bobject\b",
            r"\bnext\b",
            r"\biter\b",
            r"\ball\b",
            r"\bany\b",
            r"\bsum\b",
            r"\bmin\b",
            r"\bmax\b",
            r"\babs\b",
            r"\bround\b",
            r"\bdivmod\b",
            r"\bpow\b",
            r"\bcomplex\b",
            r"\bbool\b",
            r"\bfilter\b",
            r"\bmap\b",
            r"\bzip\b",
            r"\benumerate\b",
            r"\brange\b",
            r"\bsorted\b",
            r"\breversed\b",
            r"\bslice\b",
            r"\bhash\b",
            r"\bid\b",
            r"\blen\b",
            r"\bhelp\b",
            r"\bexit\b",
            r"\bquit\b",
            r"\bcopyright\b",
            r"\bcredits\b",
            r"\blicense\b",
            r"\bcompile\b",
            r"\beval\b",
            r"\bexec\b",
            r"\bapply\b",
            r"\bcoerce\b",
            r"\bintern\b",
            r"\breduce\b",
            r"\breload\b",
            r"\bxrange\b",
            r"\bunicode\b",
            r"\bbasestring\b",
            r"\bcmp\b",
            r"\bfile\b",
            r"\braw_input\b",
            r"\bexecfile\b",
            r"\b__import__\b",
            r"\b__builtins__\b",
            r"\b__globals__\b",
            r"\b__locals__\b",
            r"\b__closure__\b",
            r"\b__code__\b",
            r"\b__defaults__\b",
            r"\b__dict__\b",
            r"\b__doc__\b",
            r"\b__name__\b",
            r"\b__package__\b",
            r"\b__spec__\b",
            r"\b__annotations__\b",
            r"\b__kwdefaults__\b",
            r"\b__qualname__\b",
            r"\b__module__\b",
            r"\b__bases__\b",
            r"\b__class__\b",
            r"\b__self__\b",
            r"\b__func__\b",
            r"\b__get__\b",
            r"\b__set__\b",
            r"\b__delete__\b",
            r"\b__slots__\b",
            r"\b__weakref__\b",
            r"\b__prepare__\b",
            r"\b__instancecheck__\b",
            r"\b__subclasscheck__\b",
            r"\b__subclasses__\b",
            r"\b__mro__\b",
            r"\b__getitem__\b",
            r"\b__setitem__\b",
            r"\b__delitem__\b",
            r"\b__contains__\b",
            r"\b__iter__\b",
            r"\b__next__\b",
            r"\b__enter__\b",
            r"\b__exit__\b",
            r"\b__call__\b",
            r"\b__new__\b",
            r"\b__init__\b",
            r"\b__del__\b",
            r"\b__repr__\b",
            r"\b__str__\b",
            r"\b__format__\b",
            r"\b__bytes__\b",
            r"\b__hash__\b",
            r"\b__bool__\b",
            r"\b__eq__\b",
            r"\b__ne__\b",
            r"\b__lt__\b",
            r"\b__le__\b",
            r"\b__gt__\b",
            r"\b__ge__\b",
            r"\b__add__\b",
            r"\b__sub__\b",
            r"\b__mul__\b",
            r"\b__truediv__\b",
            r"\b__floordiv__\b",
            r"\b__mod__\b",
            r"\b__divmod__\b",
            r"\b__pow__\b",
            r"\b__lshift__\b",
            r"\b__rshift__\b",
            r"\b__and__\b",
            r"\b__xor__\b",
            r"\b__or__\b",
            r"\b__radd__\b",
            r"\b__rsub__\b",
            r"\b__rmul__\b",
            r"\b__rtruediv__\b",
            r"\b__rfloordiv__\b",
            r"\b__rmod__\b",
            r"\b__rdivmod__\b",
            r"\b__rpow__\b",
            r"\b__rlshift__\b",
            r"\b__rrshift__\b",
            r"\b__rand__\b",
            r"\b__rxor__\b",
            r"\b__ror__\b",
            r"\b__iadd__\b",
            r"\b__isub__\b",
            r"\b__imul__\b",
            r"\b__itruediv__\b",
            r"\b__ifloordiv__\b",
            r"\b__imod__\b",
            r"\b__ipow__\b",
            r"\b__ilshift__\b",
            r"\b__irshift__\b",
            r"\b__iand__\b",
            r"\b__ixor__\b",
            r"\b__ior__\b",
            r"\b__neg__\b",
            r"\b__pos__\b",
            r"\b__abs__\b",
            r"\b__invert__\b",
            r"\b__complex__\b",
            r"\b__int__\b",
            r"\b__float__\b",
            r"\b__index__\b",
            r"\b__round__\b",
            r"\b__trunc__\b",
            r"\b__floor__\b",
            r"\b__ceil__\b",
            r"\b__len__\b",
            r"\b__length_hint__\b",
            r"\b__getattr__\b",
            r"\b__getattribute__\b",
            r"\b__setattr__\b",
            r"\b__delattr__\b",
            r"\b__dir__\b",
            r"\b__get__\b",
            r"\b__set__\b",
            r"\b__delete__\b",
            r"\b__sizeof__\b",
            r"\b__reduce__\b",
            r"\b__reduce_ex__\b",
            r"\b__copy__\b",
            r"\b__deepcopy__\b",
            r"\b__getnewargs__\b",
            r"\b__getnewargs_ex__\b",
            r"\b__getstate__\b",
            r"\b__setstate__\b",
            r"\b__subclasshook__\b",
            r"\b__init_subclass__\b",
            r"\b__set_name__\b",
            r"\b__class_getitem__\b",
            r"\b__mro_entries__\b",
            r"\b__await__\b",
            r"\b__aiter__\b",
            r"\b__anext__\b",
            r"\b__aenter__\b",
            r"\b__aexit__\b",
            r"\b__fspath__\b",
            r"\b__match_args__\b",
            r"\b__typing_subst__\b",
            r"\b__typing_prepare_subst__\b",
            r"\b\{\{.*\}\}",
            r"\bf['\"]",
            r"\b\d+\*\*\d+\*\*\d+",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, stripped, re.IGNORECASE):
                raise ValueError(f"Disallowed pattern in expression: {pattern}")

        # 验证只允许数字、操作符、允许的函数名和常量
        # 提取所有标识符
        identifiers = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", expression)
        for ident in identifiers:
            if ident not in self.ALLOWED_NAMES:
                raise ValueError(f"Disallowed identifier in expression: {ident}")

        # 检查字符是否都在允许范围内
        for char in stripped:
            if not (char.isdigit() or char in self.ALLOWED_OPERATORS or char.isalpha() or char == "_"):
                raise ValueError(f"Disallowed character in expression: {char}")

        return expression

    def execute(self, expression: str) -> Any:
        sanitized = self._sanitize_expression(expression)

        # 使用 ast 模块安全地解析和计算表达式
        import ast

        try:
            tree = ast.parse(sanitized, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError("Only numeric constants are allowed")
            elif isinstance(node, ast.Num):  # Python < 3.8
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                elif isinstance(node.op, ast.Sub):
                    return left - right
                elif isinstance(node.op, ast.Mult):
                    return left * right
                elif isinstance(node.op, ast.Div):
                    if right == 0:
                        raise ValueError("Division by zero")
                    return left / right
                elif isinstance(node.op, ast.Mod):
                    return left % right
                elif isinstance(node.op, ast.Pow):
                    # 限制幂运算的大小以防止 DoS
                    if left > 10000 or right > 1000:
                        raise ValueError("Exponent too large")
                    return left ** right
                elif isinstance(node.op, ast.FloorDiv):
                    return left // right
                else:
                    raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            elif isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +operand
                elif isinstance(node.op, ast.USub):
                    return -operand
                else:
                    raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            elif isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name not in self.ALLOWED_NAMES:
                    raise ValueError(f"Disallowed function call: {func_name}")
                args = [_eval(arg) for arg in node.args]
                kwargs = {kw.arg: _eval(kw.value) for kw in node.keywords}
                return self.ALLOWED_NAMES[func_name](*args, **kwargs)
            elif isinstance(node, ast.Name):
                if node.id not in self.ALLOWED_NAMES:
                    raise ValueError(f"Disallowed name: {node.id}")
                return self.ALLOWED_NAMES[node.id]
            elif isinstance(node, ast.Subscript):
                raise ValueError("Subscript operations are not allowed")
            elif isinstance(node, ast.Attribute):
                raise ValueError("Attribute access is not allowed")
            else:
                raise ValueError(f"Unsupported expression type: {type(node).__name__}")

        return _eval(tree)
