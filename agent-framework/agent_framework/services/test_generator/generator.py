"""
Test Generator - 自动测试生成系统
支持 pytest, jest, junit 等多框架
完全本地运行，保护代码隐私
"""
import os
import ast
import re
import json
import subprocess
import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod


class TestFramework(Enum):
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    GO_TEST = "go_test"
    RUST_TEST = "rust_test"


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    EDGE_CASE = "edge_case"


@dataclass
class TestCase:
    name: str
    code: str
    test_type: TestType
    framework: TestFramework
    target_function: Optional[str] = None
    target_class: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    error_trace: Optional[str] = None
    coverage: Optional[float] = None


@dataclass
class TestSuiteResult:
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: float
    coverage_percent: float
    results: List[TestResult] = field(default_factory=list)


class CodeAnalyzer:
    """
    代码分析器 - 分析代码结构以生成测试
    Code Analyzer - Analyze code structure for test generation
    """
    
    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {"functions": [], "classes": []}
        
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._analyze_function(node)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)
        
        return {"functions": functions, "classes": classes}
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        params = []
        for arg in node.args.args:
            param_info = {"name": arg.arg}
            if arg.annotation:
                param_info["type"] = ast.unparse(arg.annotation)
            params.append(param_info)
        
        return_info = None
        if node.returns:
            return_info = ast.unparse(node.returns)
        
        docstring = ast.get_docstring(node)
        
        return {
            "name": node.name,
            "params": params,
            "return_type": return_info,
            "docstring": docstring,
            "lineno": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._analyze_function(item))
        
        return {
            "name": node.name,
            "methods": methods,
            "docstring": ast.get_docstring(node),
            "lineno": node.lineno,
        }


class TestGeneratorBase(ABC):
    """
    测试生成器基类
    Base class for test generators
    """
    
    @abstractmethod
    def generate_unit_tests(
        self, 
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        pass
    
    @abstractmethod
    def generate_integration_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        pass
    
    @abstractmethod
    def generate_edge_case_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        pass


class PytestGenerator(TestGeneratorBase):
    """
    Pytest 测试生成器
    Pytest test generator
    """
    
    def __init__(self):
        self.framework = TestFramework.PYTEST
    
    def generate_unit_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        tests = []
        module_name = Path(module_path).stem
        
        for func in code_analysis.get("functions", []):
            if func["name"].startswith("_"):
                continue
            
            test = self._generate_function_test(func, module_name, source_code)
            if test:
                tests.append(test)
        
        for cls in code_analysis.get("classes", []):
            class_tests = self._generate_class_tests(cls, module_name, source_code)
            tests.extend(class_tests)
        
        return tests
    
    def _generate_function_test(
        self,
        func_info: Dict[str, Any],
        module_name: str,
        source_code: str,
    ) -> Optional[TestCase]:
        func_name = func_info["name"]
        params = func_info.get("params", [])
        
        test_values = self._infer_test_values(params, func_info.get("docstring", ""))
        
        test_code = f'''def test_{func_name}():
    """Test for {func_name} - {func_name}的测试"""
    from {module_name} import {func_name}
    
    # Test case 1: Normal input / 测试用例1: 正常输入
    result = {func_name}({test_values["normal"]})
    assert result is not None
    
    # Test case 2: Edge case / 测试用例2: 边缘情况
    try:
        result = {func_name}({test_values["edge"]})
    except Exception as e:
        pass  # Expected exception / 预期异常'''
        
        return TestCase(
            name=f"test_{func_name}",
            code=test_code,
            test_type=TestType.UNIT,
            framework=self.framework,
            target_function=func_name,
            imports=[f"from {module_name} import {func_name}"],
        )
    
    def _generate_class_tests(
        self,
        class_info: Dict[str, Any],
        module_name: str,
        source_code: str,
    ) -> List[TestCase]:
        tests = []
        class_name = class_info["name"]
        
        init_test = TestCase(
            name=f"test_{class_name}_init",
            code=f'''def test_{class_name}_init():
    """Test {class_name} initialization - {class_name}初始化测试"""
    from {module_name} import {class_name}
    
    # Test instance creation / 测试实例创建
    instance = {class_name}()
    assert instance is not None''',
            test_type=TestType.UNIT,
            framework=self.framework,
            target_class=class_name,
            imports=[f"from {module_name} import {class_name}"],
        )
        tests.append(init_test)
        
        for method in class_info.get("methods", []):
            if method["name"].startswith("_") and method["name"] != "__init__":
                continue
            
            method_test = self._generate_method_test(
                class_name, method, module_name
            )
            if method_test:
                tests.append(method_test)
        
        return tests
    
    def _generate_method_test(
        self,
        class_name: str,
        method_info: Dict[str, Any],
        module_name: str,
    ) -> Optional[TestCase]:
        method_name = method_info["name"]
        test_name = f"test_{class_name}_{method_name}"
        
        return TestCase(
            name=test_name,
            code=f'''def {test_name}():
    """Test {class_name}.{method_name} - {class_name}.{method_name}测试"""
    from {module_name} import {class_name}
    
    instance = {class_name}()
    # Add specific test logic based on method signature
    # 根据方法签名添加具体测试逻辑''',
            test_type=TestType.UNIT,
            framework=self.framework,
            target_class=class_name,
            imports=[f"from {module_name} import {class_name}"],
        )
    
    def _infer_test_values(
        self,
        params: List[Dict[str, Any]],
        docstring: Optional[str],
    ) -> Dict[str, str]:
        normal_values = []
        edge_values = []
        
        for param in params:
            param_type = param.get("type", "")
            param_name = param["name"]
            
            if "int" in param_type.lower():
                normal_values.append("1")
                edge_values.append("0")
            elif "float" in param_type.lower():
                normal_values.append("1.0")
                edge_values.append("0.0")
            elif "str" in param_type.lower():
                normal_values.append('"test"')
                edge_values.append('""')
            elif "list" in param_type.lower():
                normal_values.append("[1, 2, 3]")
                edge_values.append("[]")
            elif "dict" in param_type.lower():
                normal_values.append('{"key": "value"}')
                edge_values.append("{}")
            elif "bool" in param_type.lower():
                normal_values.append("True")
                edge_values.append("False")
            else:
                normal_values.append("None")
                edge_values.append("None")
        
        return {
            "normal": ", ".join(normal_values) if normal_values else "",
            "edge": ", ".join(edge_values) if edge_values else "",
        }
    
    def generate_integration_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        tests = []
        module_name = Path(module_path).stem
        
        classes = code_analysis.get("classes", [])
        if len(classes) >= 2:
            integration_test = TestCase(
                name=f"test_{module_name}_integration",
                code=f'''def test_{module_name}_integration():
    """Integration test for {module_name} - {module_name}集成测试"""
    # Import all classes
    # 导入所有类
    from {module_name} import *
    
    # Test interactions between components
    # 测试组件之间的交互''',
                test_type=TestType.INTEGRATION,
                framework=self.framework,
            )
            tests.append(integration_test)
        
        return tests
    
    def generate_edge_case_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        tests = []
        module_name = Path(module_path).stem
        
        for func in code_analysis.get("functions", []):
            if func["name"].startswith("_"):
                continue
            
            edge_test = TestCase(
                name=f"test_{func['name']}_edge_cases",
                code=f'''import pytest
from {module_name} import {func['name']}

def test_{func['name']}_edge_cases():
    """Edge case tests for {func['name']} - {func['name']}边缘情况测试"""
    # Test with None
    # None值测试
    with pytest.raises(Exception):
        {func['name']}(None)
    
    # Test with empty input
    # 空输入测试
    try:
        result = {func['name']}()
    except TypeError:
        pass''',
                test_type=TestType.EDGE_CASE,
                framework=self.framework,
                target_function=func["name"],
            )
            tests.append(edge_test)
        
        return tests


class JestGenerator(TestGeneratorBase):
    """
    Jest 测试生成器 (JavaScript/TypeScript)
    Jest test generator
    """
    
    def __init__(self):
        self.framework = TestFramework.JEST
    
    def generate_unit_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        tests = []
        
        for func in code_analysis.get("functions", []):
            test = TestCase(
                name=f"{func['name']}.test",
                code=f'''describe('{func['name']}', () => {{
  it('should work correctly', () => {{
    // Test implementation
    // 测试实现
    const result = {func['name']}();
    expect(result).toBeDefined();
  }});

  it('should handle edge cases', () => {{
    // Edge case test
    // 边缘情况测试
    expect(() => {func['name']}(null)).toThrow();
  }});
}});''',
                test_type=TestType.UNIT,
                framework=self.framework,
                target_function=func["name"],
            )
            tests.append(test)
        
        return tests
    
    def generate_integration_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        return []
    
    def generate_edge_case_tests(
        self,
        code_analysis: Dict[str, Any],
        source_code: str,
        module_path: str,
    ) -> List[TestCase]:
        return []


class TestRunner:
    """
    测试运行器 - 本地执行测试
    Test Runner - Execute tests locally
    """
    
    def run_pytest(
        self,
        test_path: str,
        coverage: bool = True,
        timeout: int = 300,
    ) -> TestSuiteResult:
        cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
        
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=json"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(test_path).parent,
            )
            
            return self._parse_pytest_result(result, time.time() - start_time)
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=timeout * 1000,
                coverage_percent=0,
            )
        except Exception as e:
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=0,
                coverage_percent=0,
            )
    
    def _parse_pytest_result(
        self,
        result: subprocess.CompletedProcess,
        duration: float,
    ) -> TestSuiteResult:
        output = result.stdout + result.stderr
        
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        skipped_match = re.search(r"(\d+) skipped", output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        
        coverage = 0.0
        cov_match = re.search(r"TOTAL.*?(\d+)%", output)
        if cov_match:
            coverage = float(cov_match.group(1))
        
        return TestSuiteResult(
            total_tests=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration * 1000,
            coverage_percent=coverage,
        )
    
    def run_jest(
        self,
        test_path: str,
        coverage: bool = True,
        timeout: int = 300,
    ) -> TestSuiteResult:
        cmd = ["npx", "jest", test_path, "--verbose"]
        
        if coverage:
            cmd.append("--coverage")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            return self._parse_jest_result(result, time.time() - start_time)
        except Exception:
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=0,
                coverage_percent=0,
            )
    
    def _parse_jest_result(
        self,
        result: subprocess.CompletedProcess,
        duration: float,
    ) -> TestSuiteResult:
        output = result.stdout
        
        passed_match = re.search(r"Tests:\s+(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        skipped_match = re.search(r"(\d+) skipped", output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        
        coverage = 0.0
        
        return TestSuiteResult(
            total_tests=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration * 1000,
            coverage_percent=coverage,
        )


class TestGenerator:
    """
    统一测试生成器入口
    Unified test generator entry point
    """
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.generators: Dict[TestFramework, TestGeneratorBase] = {
            TestFramework.PYTEST: PytestGenerator(),
            TestFramework.JEST: JestGenerator(),
        }
        self.runner = TestRunner()
    
    def generate_tests(
        self,
        source_file: str,
        framework: TestFramework = TestFramework.PYTEST,
        test_types: Optional[List[TestType]] = None,
    ) -> List[TestCase]:
        """
        为源文件生成测试
        Generate tests for source file
        """
        test_types = test_types or [TestType.UNIT, TestType.EDGE_CASE]
        
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        code_analysis = self.analyzer.analyze_python_file(source_file)
        
        generator = self.generators.get(framework)
        if not generator:
            return []
        
        tests = []
        
        if TestType.UNIT in test_types:
            tests.extend(
                generator.generate_unit_tests(code_analysis, source_code, source_file)
            )
        
        if TestType.INTEGRATION in test_types:
            tests.extend(
                generator.generate_integration_tests(code_analysis, source_code, source_file)
            )
        
        if TestType.EDGE_CASE in test_types:
            tests.extend(
                generator.generate_edge_case_tests(code_analysis, source_code, source_file)
            )
        
        return tests
    
    def write_tests(
        self,
        tests: List[TestCase],
        output_dir: str,
    ) -> List[str]:
        """
        将测试写入文件
        Write tests to files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        written_files = []
        
        for test in tests:
            file_name = f"{test.name}.py" if test.framework == TestFramework.PYTEST else f"{test.name}.test.js"
            file_path = output_path / file_name
            
            content = self._build_test_file_content(test)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            written_files.append(str(file_path))
        
        return written_files
    
    def _build_test_file_content(self, test: TestCase) -> str:
        lines = [
            '"""',
            f'Auto-generated test: {test.name}',
            f'Target: {test.target_function or test.target_class or "module"}',
            f'Type: {test.test_type.value}',
            '"""',
            "",
        ]
        
        for imp in test.imports:
            lines.append(imp)
        
        if test.imports:
            lines.append("")
        
        if test.setup_code:
            lines.append(test.setup_code)
            lines.append("")
        
        lines.append(test.code)
        
        if test.teardown_code:
            lines.append("")
            lines.append(test.teardown_code)
        
        return "\n".join(lines)
    
    def run_tests(
        self,
        test_path: str,
        framework: TestFramework = TestFramework.PYTEST,
        coverage: bool = True,
    ) -> TestSuiteResult:
        """
        运行测试
        Run tests
        """
        if framework == TestFramework.PYTEST:
            return self.runner.run_pytest(test_path, coverage)
        elif framework == TestFramework.JEST:
            return self.runner.run_jest(test_path, coverage)
        else:
            return TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=0,
                coverage_percent=0,
            )
    
    def generate_and_run(
        self,
        source_file: str,
        output_dir: str,
        framework: TestFramework = TestFramework.PYTEST,
    ) -> Tuple[List[str], TestSuiteResult]:
        """
        生成并运行测试
        Generate and run tests
        """
        tests = self.generate_tests(source_file, framework)
        written_files = self.write_tests(tests, output_dir)
        
        if written_files:
            result = self.run_tests(output_dir, framework)
        else:
            result = TestSuiteResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_ms=0,
                coverage_percent=0,
            )
        
        return written_files, result
