"""
代码生成模块 / Code Generation Module

提供 / Provides:
- 多语言代码生成 / Multi-language code generation
- 函数生成 / Function generation
- 类生成 / Class generation
- 测试生成 / Test generation
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import yaml

from rich.console import Console

from alonechat.models import ModelRouter
from alonechat.deepseek import PromptEngineer, MegaContextManager
from alonechat.chinese import ChineseNLP, NamingAdvisor


@dataclass
class GeneratedCode:
    """生成代码结果 / Generated Code Result"""
    code: str
    language: str
    file_path: Optional[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    imports: Optional[List[str]] = None


class CodeConfigLoader:
    """代码配置加载器 / Code Config Loader"""
    
    _instance: Optional["CodeConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "configs" / "code_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"code": {"languages": {}}}
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_language_config(self, language: str) -> Dict[str, Any]:
        """获取语言配置 / Get language config"""
        return self.get(f"code.languages.{language}", {})
    
    @classmethod
    def get_instance(cls) -> "CodeConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


code_config = CodeConfigLoader.get_instance()


class CodeGenerator:
    """
    代码生成器 / Code Generator
    
    支持多种编程语言 / Support multiple programming languages
    """
    
    def __init__(
        self,
        model_router: Optional[ModelRouter] = None,
        console: Optional[Console] = None,
    ):
        self.model_router = model_router
        self.console = console or Console()
        self.prompt_engineer = PromptEngineer()
        self.naming_advisor = NamingAdvisor()
        self.chinese_nlp = ChineseNLP()
    
    def detect_language(self, file_path: str) -> str:
        """
        检测语言 / Detect language
        
        Args:
            file_path: 文件路径 / File path
            
        Returns:
            语言名称 / Language name
        """
        ext = Path(file_path).suffix.lower()
        
        languages = code_config.get("code.languages", {})
        
        for lang, config in languages.items():
            if ext in config.get("extensions", []):
                return lang
        
        return "python"
    
    def generate_function(
        self,
        description: str,
        name: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        returns: Optional[str] = None,
        language: str = "python",
    ) -> GeneratedCode:
        """
        生成函数 / Generate function
        
        Args:
            description: 功能描述 / Function description
            name: 函数名 / Function name
            params: 参数 / Parameters
            returns: 返回值 / Return value
            language: 语言 / Language
            
        Returns:
            生成结果 / Generation result
        """
        if name is None:
            suggestions = self.naming_advisor.suggest_function_name(description, language)
            name = suggestions[0] if suggestions else "process"
        
        prompt = self.prompt_engineer.build_code_generation_prompt(
            description=description,
            language=language,
            code_type="function",
            name=name,
            params=str(params) if params else None,
            returns=returns,
        )
        
        if self.model_router:
            response = self.model_router.chat(
                model="deepseek",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            code = self._extract_code(response)
        else:
            code = self._generate_function_template(name, params, returns, language, description)
        
        return GeneratedCode(
            code=code,
            language=language,
        )
    
    def generate_class(
        self,
        description: str,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
        methods: Optional[List[str]] = None,
        language: str = "python",
    ) -> GeneratedCode:
        """
        生成类 / Generate class
        
        Args:
            description: 功能描述 / Class description
            name: 类名 / Class name
            attributes: 属性 / Attributes
            methods: 方法 / Methods
            language: 语言 / Language
            
        Returns:
            生成结果 / Generation result
        """
        if name is None:
            suggestions = self.naming_advisor.suggest_class_name(description, language)
            name = suggestions[0] if suggestions else "Handler"
        
        prompt = self.prompt_engineer.build_code_generation_prompt(
            description=description,
            language=language,
            code_type="class",
            name=name,
            params=str(attributes) if attributes else None,
            returns=str(methods) if methods else None,
        )
        
        if self.model_router:
            response = self.model_router.chat(
                model="deepseek",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            code = self._extract_code(response)
        else:
            code = self._generate_class_template(name, attributes, methods, language, description)
        
        return GeneratedCode(
            code=code,
            language=language,
        )
    
    def generate_tests(
        self,
        code: str,
        language: str = "python",
    ) -> GeneratedCode:
        """
        生成测试 / Generate tests
        
        Args:
            code: 代码 / Code
            language: 语言 / Language
            
        Returns:
            测试代码 / Test code
        """
        lang_config = code_config.get_language_config(language)
        test_framework = lang_config.get("test_framework", "pytest")
        
        prompt = self.prompt_engineer.build_test_generation_prompt(
            code=code,
            language=language,
            test_framework=test_framework,
        )
        
        if self.model_router:
            response = self.model_router.chat(
                model="deepseek",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            test_code = self._extract_code(response)
        else:
            test_code = self._generate_test_template(code, language, test_framework)
        
        return GeneratedCode(
            code=test_code,
            language=language,
        )
    
    def _extract_code(self, response: str) -> str:
        """提取代码块 / Extract code block"""
        code_block_pattern = re.compile(r'```[\w]*\n(.*?)```', re.DOTALL)
        
        matches = code_block_pattern.findall(response)
        
        if matches:
            return matches[0].strip()
        
        return response.strip()
    
    def _generate_function_template(
        self,
        name: str,
        params: Optional[Dict[str, str]],
        returns: Optional[str],
        language: str,
        description: str,
    ) -> str:
        """生成函数模板 / Generate function template"""
        if language == "python":
            param_str = ", ".join(params.keys()) if params else ""
            return f'''def {name}({param_str}):
    """
    {description}
    """
    pass
'''
        elif language in ("javascript", "typescript"):
            param_str = ", ".join(params.keys()) if params else ""
            return f'''/**
 * {description}
 */
function {name}({param_str}) {{
    // TODO: 实现
}}
'''
        else:
            return f"// Function: {name}\n// {description}"
    
    def _generate_class_template(
        self,
        name: str,
        attributes: Optional[Dict[str, str]],
        methods: Optional[List[str]],
        language: str,
        description: str,
    ) -> str:
        """生成类模板 / Generate class template"""
        if language == "python":
            attr_lines = []
            if attributes:
                for attr_name, attr_desc in attributes.items():
                    attr_lines.append(f"        self.{attr_name} = None  # {attr_desc}")
            
            method_lines = ["    def __init__(self):"]
            if attr_lines:
                method_lines.extend(attr_lines)
            else:
                method_lines.append("        pass")
            
            if methods:
                for method in methods:
                    method_lines.append(f"\n    def {method}(self):")
                    method_lines.append('        """TODO: 实现"""')
                    method_lines.append("        pass")
            
            return f'''class {name}:
    """
    {description}
    """
{chr(10).join(method_lines)}
'''
        elif language in ("javascript", "typescript"):
            return f'''/**
 * {description}
 */
class {name} {{
    constructor() {{
        // TODO: 初始化
    }}
}}
'''
        else:
            return f"// Class: {name}\n// {description}"
    
    def _generate_test_template(
        self,
        code: str,
        language: str,
        test_framework: str,
    ) -> str:
        """生成测试模板 / Generate test template"""
        if language == "python":
            return '''import pytest

def test_function():
    """测试函数"""
    # TODO: 添加测试用例
    assert True
'''
        elif language in ("javascript", "typescript"):
            return '''describe('Test Suite', () => {
    test('test case', () => {
        // TODO: 添加测试用例
        expect(true).toBe(true);
    });
});
'''
        else:
            return f"// Test file for {test_framework}"


class CodeAnalyzer:
    """
    代码分析器 / Code Analyzer
    
    分析代码结构和质量 / Analyze code structure and quality
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.chinese_nlp = ChineseNLP()
    
    def analyze_structure(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        分析结构 / Analyze structure
        
        Args:
            code: 代码 / Code
            language: 语言 / Language
            
        Returns:
            结构信息 / Structure info
        """
        result = {
            "language": language,
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "lines": len(code.split("\n")),
            "characters": len(code),
        }
        
        if language == "python":
            result.update(self._analyze_python(code))
        elif language in ("javascript", "typescript"):
            result.update(self._analyze_javascript(code))
        
        return result
    
    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """分析Python代码 / Analyze Python code"""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
        }
        
        import_pattern = re.compile(r'^(?:import|from)\s+(\S+)', re.MULTILINE)
        for match in import_pattern.finditer(code):
            result["imports"].append(match.group(1))
        
        func_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\)')
        for match in func_pattern.finditer(code):
            result["functions"].append({
                "name": match.group(1),
                "params": match.group(2),
            })
        
        class_pattern = re.compile(r'class\s+(\w+)(?:\(([^)]*)\))?:')
        for match in class_pattern.finditer(code):
            result["classes"].append({
                "name": match.group(1),
                "base": match.group(2) or "",
            })
        
        return result
    
    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """分析JavaScript代码 / Analyze JavaScript code"""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
        }
        
        import_pattern = re.compile(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]')
        for match in import_pattern.finditer(code):
            result["imports"].append(match.group(1))
        
        func_pattern = re.compile(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()')
        for match in func_pattern.finditer(code):
            name = match.group(1) or match.group(2)
            if name:
                result["functions"].append({"name": name})
        
        class_pattern = re.compile(r'class\s+(\w+)')
        for match in class_pattern.finditer(code):
            result["classes"].append({"name": match.group(1)})
        
        return result
    
    def calculate_complexity(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """
        计算复杂度 / Calculate complexity
        
        Args:
            code: 代码 / Code
            language: 语言 / Language
            
        Returns:
            复杂度信息 / Complexity info
        """
        lines = code.split("\n")
        
        cyclomatic = 1
        
        control_keywords = [
            r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b',
            r'\bwhile\b', r'\band\b', r'\bor\b', r'\btry\b',
            r'\bexcept\b', r'\bwith\b',
        ]
        
        for keyword in control_keywords:
            cyclomatic += len(re.findall(keyword, code))
        
        cognitive = cyclomatic
        
        nesting = 0
        max_nesting = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            current_nesting = indent // 4
            if current_nesting > max_nesting:
                max_nesting = current_nesting
        
        return {
            "cyclomatic": cyclomatic,
            "cognitive": cognitive,
            "max_nesting": max_nesting,
            "lines_of_code": len([l for l in lines if l.strip()]),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
        }
