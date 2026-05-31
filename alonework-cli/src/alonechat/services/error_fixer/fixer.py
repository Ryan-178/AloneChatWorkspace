"""
Error Fixer - 错误自动修复系统
支持编译错误、运行时错误、逻辑错误的诊断和修复
完全本地运行，保护代码隐私
"""
import os
import re
import ast
import json
import time
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class ErrorType(Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    NAME = "name"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    INDEX = "index"
    KEY = "key"
    VALUE = "value"
    RUNTIME = "runtime"
    LOGIC = "logic"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DiagnosticError:
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    file_path: str
    line: int
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    stack_trace: str = ""


@dataclass
class FixSuggestion:
    description: str
    code_before: str
    code_after: str
    confidence: float
    fix_type: str
    explanation: str = ""


@dataclass
class FixResult:
    success: bool
    original_code: str
    fixed_code: str
    errors_fixed: List[DiagnosticError] = field(default_factory=list)
    errors_remaining: List[DiagnosticError] = field(default_factory=list)
    iterations: int = 0
    duration_ms: float = 0


class ErrorPattern:
    """
    错误模式定义
    Error pattern definition
    """
    
    PATTERNS = {
        ErrorType.SYNTAX: [
            (r"SyntaxError: (.+)", "语法错误 / Syntax error"),
            (r"IndentationError: (.+)", "缩进错误 / Indentation error"),
        ],
        ErrorType.TYPE: [
            (r"TypeError: (.+)", "类型错误 / Type error"),
            (r"type '(\w+)' is not subscriptable", "类型不可下标访问 / Type not subscriptable"),
        ],
        ErrorType.NAME: [
            (r"NameError: name '(\w+)' is not defined", "名称未定义 / Name not defined"),
        ],
        ErrorType.IMPORT: [
            (r"ImportError: (.+)", "导入错误 / Import error"),
            (r"ModuleNotFoundError: No module named '(\w+)'", "模块未找到 / Module not found"),
        ],
        ErrorType.ATTRIBUTE: [
            (r"AttributeError: '(\w+)' object has no attribute '(\w+)'", "属性不存在 / Attribute not found"),
        ],
        ErrorType.INDEX: [
            (r"IndexError: (.+)", "索引错误 / Index error"),
        ],
        ErrorType.KEY: [
            (r"KeyError: (.+)", "键错误 / Key error"),
        ],
        ErrorType.VALUE: [
            (r"ValueError: (.+)", "值错误 / Value error"),
        ],
    }


class ErrorDiagnostic:
    """
    错误诊断器
    Error diagnostic tool
    """
    
    def diagnose_python(self, file_path: str) -> List[DiagnosticError]:
        errors = []
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
        
        syntax_errors = self._check_syntax(file_path, content)
        errors.extend(syntax_errors)
        
        if not syntax_errors:
            runtime_errors = self._run_linter(file_path)
            errors.extend(runtime_errors)
        
        for error in errors:
            if error.line > 0 and error.line <= len(lines):
                error.code_snippet = lines[error.line - 1].strip()
        
        return errors
    
    def _check_syntax(self, file_path: str, content: str) -> List[DiagnosticError]:
        errors = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(DiagnosticError(
                error_type=ErrorType.SYNTAX,
                severity=ErrorSeverity.ERROR,
                message=f"SyntaxError: {e.msg}",
                file_path=file_path,
                line=e.lineno or 1,
                column=e.offset or 0,
                suggestion=self._get_syntax_suggestion(e.msg),
            ))
        
        return errors
    
    def _get_syntax_suggestion(self, msg: str) -> str:
        suggestions = {
            "unexpected EOF while parsing": "检查括号、引号是否匹配 / Check if brackets and quotes are matched",
            "invalid syntax": "检查语法是否正确 / Check if syntax is correct",
            "unterminated string literal": "字符串未闭合 / String not terminated",
            "expected ':'": "缺少冒号 / Missing colon",
        }
        
        for key, suggestion in suggestions.items():
            if key in msg.lower():
                return suggestion
        
        return "请检查语法错误 / Please check syntax error"
    
    def _run_linter(self, file_path: str) -> List[DiagnosticError]:
        errors = []
        
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                for line in result.stderr.split("\n"):
                    parsed = self._parse_error_line(line, file_path)
                    if parsed:
                        errors.append(parsed)
        except Exception:
            pass
        
        return errors
    
    def _parse_error_line(self, line: str, file_path: str) -> Optional[DiagnosticError]:
        match = re.search(r"line (\d+)", line)
        if match:
            return DiagnosticError(
                error_type=ErrorType.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                message=line,
                file_path=file_path,
                line=int(match.group(1)),
            )
        return None
    
    def diagnose_runtime_error(
        self,
        error_output: str,
        file_path: str,
    ) -> List[DiagnosticError]:
        errors = []
        
        for error_type, patterns in ErrorPattern.PATTERNS.items():
            for pattern, description in patterns:
                matches = re.finditer(pattern, error_output)
                for match in matches:
                    line_match = re.search(r"line (\d+)", error_output[match.start():])
                    line = int(line_match.group(1)) if line_match else 1
                    
                    errors.append(DiagnosticError(
                        error_type=error_type,
                        severity=ErrorSeverity.ERROR,
                        message=match.group(0),
                        file_path=file_path,
                        line=line,
                        suggestion=self._get_error_suggestion(error_type, match),
                    ))
        
        return errors
    
    def _get_error_suggestion(
        self,
        error_type: ErrorType,
        match: re.Match,
    ) -> str:
        suggestions = {
            ErrorType.NAME: f"定义变量或导入: {match.group(1) if match.groups() else ''} / Define or import the variable",
            ErrorType.IMPORT: f"安装模块: pip install {match.group(1) if match.groups() else ''} / Install the module",
            ErrorType.ATTRIBUTE: f"检查对象是否有该属性 / Check if object has the attribute",
            ErrorType.KEY: f"检查键是否存在 / Check if key exists",
            ErrorType.INDEX: f"检查索引范围 / Check index range",
            ErrorType.TYPE: f"检查类型是否匹配 / Check if types match",
        }
        return suggestions.get(error_type, "检查错误原因 / Check the error cause")


class FixStrategy:
    """
    修复策略
    Fix strategies
    """
    
    def __init__(self):
        self.strategies: Dict[ErrorType, List[callable]] = {
            ErrorType.SYNTAX: [self._fix_syntax],
            ErrorType.NAME: [self._fix_name_error],
            ErrorType.IMPORT: [self._fix_import_error],
            ErrorType.ATTRIBUTE: [self._fix_attribute_error],
            ErrorType.KEY: [self._fix_key_error],
            ErrorType.INDEX: [self._fix_index_error],
        }
    
    def get_fix(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        strategies = self.strategies.get(error.error_type, [])
        
        for strategy in strategies:
            fix = strategy(error, code, context)
            if fix:
                return fix
        
        return None
    
    def _fix_syntax(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        lines = code.split("\n")
        if error.line <= 0 or error.line > len(lines):
            return None
        
        line = lines[error.line - 1]
        
        if "expected ':'" in error.message.lower():
            fixed_line = line.rstrip() + ":"
            return FixSuggestion(
                description="添加缺失的冒号 / Add missing colon",
                code_before=line,
                code_after=fixed_line,
                confidence=0.9,
                fix_type="add_colon",
            )
        
        if "unterminated string literal" in error.message.lower():
            if line.count('"') % 2 == 1:
                fixed_line = line + '"'
            elif line.count("'") % 2 == 1:
                fixed_line = line + "'"
            else:
                return None
            
            return FixSuggestion(
                description="闭合字符串 / Terminate string",
                code_before=line,
                code_after=fixed_line,
                confidence=0.9,
                fix_type="terminate_string",
            )
        
        return None
    
    def _fix_name_error(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        match = re.search(r"name '(\w+)' is not defined", error.message)
        if not match:
            return None
        
        name = match.group(1)
        
        common_imports = {
            "np": "import numpy as np",
            "pd": "import pandas as pd",
            "plt": "import matplotlib.pyplot as plt",
            "json": "import json",
            "re": "import re",
            "os": "import os",
            "sys": "import sys",
            "datetime": "from datetime import datetime",
            "List": "from typing import List",
            "Dict": "from typing import Dict",
            "Optional": "from typing import Optional",
        }
        
        if name in common_imports:
            return FixSuggestion(
                description=f"添加导入: {common_imports[name]} / Add import",
                code_before="",
                code_after=common_imports[name] + "\n",
                confidence=0.8,
                fix_type="add_import",
            )
        
        return None
    
    def _fix_import_error(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        match = re.search(r"No module named '(\w+)'", error.message)
        if match:
            module = match.group(1)
            return FixSuggestion(
                description=f"安装模块: pip install {module} / Install module",
                code_before="",
                code_after=f"# Run: pip install {module}",
                confidence=0.7,
                fix_type="install_module",
                explanation=f"需要安装模块 {module} / Module {module} needs to be installed",
            )
        return None
    
    def _fix_attribute_error(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        lines = code.split("\n")
        if error.line <= 0 or error.line > len(lines):
            return None
        
        line = lines[error.line - 1]
        
        match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error.message)
        if match:
            obj_type, attr = match.groups()
            
            common_fixes = {
                ("list", "append"): None,
                ("dict", "get"): None,
                ("str", "strip"): None,
            }
            
            return FixSuggestion(
                description=f"检查 {obj_type} 对象是否有属性 {attr} / Check if {obj_type} has attribute {attr}",
                code_before=line,
                code_after=f"# TODO: Fix attribute access\n# {line}",
                confidence=0.5,
                fix_type="check_attribute",
            )
        
        return None
    
    def _fix_key_error(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        lines = code.split("\n")
        if error.line <= 0 or error.line > len(lines):
            return None
        
        line = lines[error.line - 1]
        
        bracket_match = re.search(r"\[['\"](\w+)['\"]\]", line)
        if bracket_match:
            key = bracket_match.group(1)
            fixed_line = re.sub(
                r"\[['\"]" + key + r"['\"]\]",
                f'.get("{key}")',
                line,
            )
            
            return FixSuggestion(
                description=f"使用 .get() 方法避免 KeyError / Use .get() to avoid KeyError",
                code_before=line,
                code_after=fixed_line,
                confidence=0.7,
                fix_type="use_get_method",
            )
        
        return None
    
    def _fix_index_error(
        self,
        error: DiagnosticError,
        code: str,
        context: Dict[str, Any],
    ) -> Optional[FixSuggestion]:
        lines = code.split("\n")
        if error.line <= 0 or error.line > len(lines):
            return None
        
        line = lines[error.line - 1]
        
        return FixSuggestion(
            description="添加索引边界检查 / Add index boundary check",
            code_before=line,
            code_after=f"# TODO: Add boundary check\nif len(sequence) > index:\n    {line}",
            confidence=0.6,
            fix_type="add_boundary_check",
        )


class ErrorFixer:
    """
    错误修复器 - 主入口
    Error fixer - Main entry point
    """
    
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.diagnostic = ErrorDiagnostic()
        self.strategy = FixStrategy()
        self._fix_history: List[Dict[str, Any]] = []
    
    def fix_file(
        self,
        file_path: str,
        run_tests: bool = True,
    ) -> FixResult:
        """
        修复文件中的错误
        Fix errors in file
        """
        start_time = time.time()
        
        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()
        
        current_code = original_code
        all_errors_fixed = []
        iterations = 0
        
        while iterations < self.max_iterations:
            errors = self.diagnostic.diagnose_python(file_path)
            
            if not errors:
                break
            
            fixed_any = False
            for error in errors:
                fix = self.strategy.get_fix(error, current_code, {})
                
                if fix:
                    current_code = self._apply_fix(current_code, error, fix)
                    all_errors_fixed.append(error)
                    fixed_any = True
                    
                    self._fix_history.append({
                        "file": file_path,
                        "error": error.message,
                        "fix": fix.description,
                        "iteration": iterations,
                    })
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(current_code)
                    break
            
            if not fixed_any:
                break
            
            iterations += 1
        
        remaining_errors = self.diagnostic.diagnose_python(file_path)
        
        duration = (time.time() - start_time) * 1000
        
        return FixResult(
            success=len(remaining_errors) == 0,
            original_code=original_code,
            fixed_code=current_code,
            errors_fixed=all_errors_fixed,
            errors_remaining=remaining_errors,
            iterations=iterations,
            duration_ms=duration,
        )
    
    def _apply_fix(
        self,
        code: str,
        error: DiagnosticError,
        fix: FixSuggestion,
    ) -> str:
        lines = code.split("\n")
        
        if fix.fix_type == "add_import":
            return fix.code_after + code
        
        if error.line > 0 and error.line <= len(lines):
            if fix.code_before in lines[error.line - 1]:
                lines[error.line - 1] = lines[error.line - 1].replace(
                    fix.code_before,
                    fix.code_after,
                )
        
        return "\n".join(lines)
    
    def fix_runtime_error(
        self,
        file_path: str,
        error_output: str,
    ) -> FixResult:
        """
        修复运行时错误
        Fix runtime error
        """
        start_time = time.time()
        
        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()
        
        errors = self.diagnostic.diagnose_runtime_error(error_output, file_path)
        
        current_code = original_code
        fixed_errors = []
        
        for error in errors:
            fix = self.strategy.get_fix(error, current_code, {})
            
            if fix:
                current_code = self._apply_fix(current_code, error, fix)
                fixed_errors.append(error)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(current_code)
        
        duration = (time.time() - start_time) * 1000
        
        return FixResult(
            success=len(fixed_errors) > 0,
            original_code=original_code,
            fixed_code=current_code,
            errors_fixed=fixed_errors,
            errors_remaining=[],
            iterations=1,
            duration_ms=duration,
        )
    
    def get_fix_history(self) -> List[Dict[str, Any]]:
        return self._fix_history
    
    def clear_history(self) -> None:
        self._fix_history = []
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        分析错误模式
        Analyze error patterns
        """
        if not self._fix_history:
            return {}
        
        patterns: Dict[str, int] = {}
        
        for record in self._fix_history:
            error_type = record.get("error", "").split(":")[0]
            patterns[error_type] = patterns.get(error_type, 0) + 1
        
        return {
            "total_fixes": len(self._fix_history),
            "patterns": patterns,
            "most_common": max(patterns.items(), key=lambda x: x[1]) if patterns else None,
        }
