"""
CODE工具集 - Code Tools
面向开发者的编程工具
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
import subprocess
import os
import re

from agent_framework.core.base_tool import BaseTool, ToolResult


class CodeGeneratorTool(BaseTool):
    """代码生成工具"""
    
    name = "code_generator"
    description = "生成代码，支持多种编程语言"
    parameters = {
        "type": "object",
        "properties": {
            "language": {"type": "string", "description": "编程语言"},
            "description": {"type": "string", "description": "代码功能描述"},
            "output_path": {"type": "string", "description": "输出文件路径"},
        },
        "required": ["language", "description"],
    }
    
    def execute(self, language: str, description: str, output_path: Optional[str] = None) -> ToolResult:
        try:
            templates = {
                "python": 'def main():\n    """{}"""\n    pass\n\nif __name__ == "__main__":\n    main()',
                "javascript": '// {}\nfunction main() {{\n    // TODO: implement\n}}\n\nmain();',
                "typescript": '// {}\nfunction main(): void {{\n    // TODO: implement\n}}\n\nmain();',
                "java": 'public class Main {{\n    // {}\n    public static void main(String[] args) {{\n        // TODO: implement\n    }}\n}}',
            }
            
            code = templates.get(language.lower(), '// {}\n// TODO: implement').format(description)
            
            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                return ToolResult(success=True, data={"path": str(path), "code": code, "language": language})
            
            return ToolResult(success=True, data={"code": code, "language": language})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CodeExecutionTool(BaseTool):
    """代码执行工具"""
    
    name = "code_executor"
    description = "执行代码并返回结果"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的代码"},
            "language": {"type": "string", "description": "编程语言"},
            "timeout": {"type": "integer", "description": "执行超时时间(秒)"},
        },
        "required": ["code", "language"],
    }
    
    def execute(self, code: str, language: str, timeout: int = 30) -> ToolResult:
        try:
            if language.lower() == "python":
                result = subprocess.run(
                    ["python", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                    error=result.stderr if result.returncode != 0 else None,
                )
            else:
                return ToolResult(success=False, error=f"不支持的语言: {language}")
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"执行超时 ({timeout}秒)")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DebugAnalyzerTool(BaseTool):
    """调试分析工具"""
    
    name = "debug_analyzer"
    description = "分析错误信息，提供调试建议"
    parameters = {
        "type": "object",
        "properties": {
            "error_message": {"type": "string", "description": "错误信息"},
            "code_context": {"type": "string", "description": "相关代码上下文"},
        },
        "required": ["error_message"],
    }
    
    def execute(self, error_message: str, code_context: Optional[str] = None) -> ToolResult:
        try:
            error_types = {
                "TypeError": "类型错误：检查变量类型是否正确",
                "ValueError": "值错误：检查输入值是否在有效范围内",
                "KeyError": "键错误：检查字典键是否存在",
                "IndexError": "索引错误：检查数组索引是否越界",
                "AttributeError": "属性错误：检查对象是否具有该属性",
                "ImportError": "导入错误：检查模块是否安装",
                "SyntaxError": "语法错误：检查代码语法是否正确",
            }
            
            detected_type = None
            suggestion = None
            for error_type, desc in error_types.items():
                if error_type in error_message:
                    detected_type = error_type
                    suggestion = desc
                    break
            
            line_match = re.search(r"line (\d+)", error_message)
            line_number = int(line_match.group(1)) if line_match else None
            
            result = {
                "error_message": error_message,
                "error_type": detected_type or "Unknown",
                "suggestion": suggestion or "请检查错误信息并修复问题",
                "line_number": line_number,
            }
            
            if code_context:
                result["code_context"] = code_context
            
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class RefactorTool(BaseTool):
    """代码重构工具"""
    
    name = "code_refactor"
    description = "重构代码，优化代码结构"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "原始代码"},
            "refactor_type": {"type": "string", "enum": ["extract_method", "rename", "optimize"], "description": "重构类型"},
        },
        "required": ["code", "refactor_type"],
    }
    
    def execute(self, code: str, refactor_type: str) -> ToolResult:
        try:
            result = {"original_code": code, "refactor_type": refactor_type}
            
            if refactor_type == "optimize":
                optimized = code.replace("    ", "  ")
                result["refactored_code"] = optimized
                result["changes"] = ["优化缩进"]
            elif refactor_type == "rename":
                result["refactored_code"] = code
                result["changes"] = ["保持原样，需要指定重命名规则"]
            else:
                result["refactored_code"] = code
                result["changes"] = ["保持原样"]
            
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class TestGeneratorTool(BaseTool):
    """测试生成工具"""
    
    name = "test_generator"
    description = "生成测试用例"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "被测试代码"},
            "language": {"type": "string", "description": "编程语言"},
            "test_framework": {"type": "string", "description": "测试框架"},
        },
        "required": ["code", "language"],
    }
    
    def execute(self, code: str, language: str, test_framework: str = "pytest") -> ToolResult:
        try:
            func_match = re.search(r"def\s+(\w+)\s*\(", code)
            func_name = func_match.group(1) if func_match else "function"
            
            if language.lower() == "python":
                test_code = f'''import pytest
from module import {func_name}

def test_{func_name}_normal():
    """测试正常情况"""
    # Arrange
    # Act
    # Assert
    pass

def test_{func_name}_edge():
    """测试边界情况"""
    pass

def test_{func_name}_error():
    """测试错误情况"""
    pass
'''
            else:
                test_code = f"// Test for {func_name}\n// TODO: implement tests"
            
            return ToolResult(success=True, data={
                "test_code": test_code,
                "language": language,
                "test_framework": test_framework,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class LintTool(BaseTool):
    """代码检查工具"""
    
    name = "code_lint"
    description = "检查代码质量"
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "被检查代码"},
            "language": {"type": "string", "description": "编程语言"},
        },
        "required": ["code", "language"],
    }
    
    def execute(self, code: str, language: str) -> ToolResult:
        try:
            issues = []
            
            lines = code.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 100:
                    issues.append({"line": i, "type": "style", "message": "行长度超过100字符"})
                
                if language.lower() == "python":
                    if line.strip().startswith("print(") and "debug" in line.lower():
                        issues.append({"line": i, "type": "warning", "message": "可能存在调试代码"})
            
            return ToolResult(success=True, data={
                "issues": issues,
                "issue_count": len(issues),
                "language": language,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitTool(BaseTool):
    """Git操作工具"""
    
    name = "git_operation"
    description = "执行Git操作"
    parameters = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["status", "log", "diff", "branch"], "description": "Git操作类型"},
            "args": {"type": "array", "description": "操作参数"},
        },
        "required": ["operation"],
    }
    
    def execute(self, operation: str, args: Optional[List[str]] = None) -> ToolResult:
        try:
            cmd = ["git", operation]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "operation": operation,
                    "output": result.stdout,
                    "returncode": result.returncode,
                },
                error=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Git操作超时")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileSearchTool(BaseTool):
    """文件搜索工具"""
    
    name = "file_search"
    description = "在项目中搜索文件和代码"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "搜索模式"},
            "directory": {"type": "string", "description": "搜索目录"},
            "file_type": {"type": "string", "description": "文件类型"},
        },
        "required": ["pattern"],
    }
    
    def execute(self, pattern: str, directory: str = ".", file_type: Optional[str] = None) -> ToolResult:
        try:
            path = Path(directory)
            results = []
            
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    if file_type and file_path.suffix != file_type:
                        continue
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        if pattern.lower() in content.lower():
                            lines = content.split("\n")
                            matches = []
                            for i, line in enumerate(lines, 1):
                                if pattern.lower() in line.lower():
                                    matches.append({"line": i, "content": line.strip()})
                            
                            results.append({
                                "file": str(file_path.relative_to(path)),
                                "matches": matches[:5],
                            })
                    except Exception:
                        pass
            
            return ToolResult(success=True, data={
                "pattern": pattern,
                "results": results[:20],
                "total_matches": len(results),
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register_code_tools(registry) -> None:
    """注册所有CODE工具到工具注册表"""
    registry.register(CodeGeneratorTool())
    registry.register(CodeExecutionTool())
    registry.register(DebugAnalyzerTool())
    registry.register(RefactorTool())
    registry.register(TestGeneratorTool())
    registry.register(LintTool())
    registry.register(GitTool())
    registry.register(FileSearchTool())
