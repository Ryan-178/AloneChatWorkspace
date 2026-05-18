"""
ä»£ç çææ¨¡å / Code Generation Module

æä¾ / Provides:
- å¤è¯­è¨ä»£ç çæ / Multi-language code generation
- å½æ°çæ / Function generation
- ç±»çæ?/ Class generation
- æµè¯çæ / Test generation
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import yaml

from rich.console import Console

from alonework.models import ModelRouter
from alonework.deepseek import PromptEngineer, MegaContextManager
from alonework.chinese import ChineseNLP, NamingAdvisor


@dataclass
class GeneratedCode:
    """çæä»£ç ç»æ / Generated Code Result"""
    code: str
    language: str
    file_path: Optional[str] = None
    tests: Optional[str] = None
    documentation: Optional[str] = None
    imports: Optional[List[str]] = None


class CodeConfigLoader:
    """ä»£ç éç½®å è½½å?/ Code Config Loader"""
    
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
        """è·åè¯­è¨éç½® / Get language config"""
        return self.get(f"code.languages.{language}", {})
    
    @classmethod
    def get_instance(cls) -> "CodeConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


code_config = CodeConfigLoader.get_instance()


class CodeGenerator:
    """
    ä»£ç çæå?/ Code Generator
    
    æ¯æå¤ç§ç¼ç¨è¯­è¨ / Support multiple programming languages
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
        æ£æµè¯­è¨ / Detect language
        
        Args:
            file_path: æä»¶è·¯å¾ / File path
            
        Returns:
            è¯­è¨åç§° / Language name
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
        çæå½æ° / Generate function
        
        Args:
            description: åè½æè¿° / Function description
            name: å½æ°å?/ Function name
            params: åæ° / Parameters
            returns: è¿åå?/ Return value
            language: è¯­è¨ / Language
            
        Returns:
            çæç»æ / Generation result
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
        çæç±?/ Generate class
        
        Args:
            description: åè½æè¿° / Class description
            name: ç±»å / Class name
            attributes: å±æ?/ Attributes
            methods: æ¹æ³ / Methods
            language: è¯­è¨ / Language
            
        Returns:
            çæç»æ / Generation result
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
        çææµè¯ / Generate tests
        
        Args:
            code: ä»£ç  / Code
            language: è¯­è¨ / Language
            
        Returns:
            æµè¯ä»£ç  / Test code
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
        """æåä»£ç å?/ Extract code block"""
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
        """çæå½æ°æ¨¡æ¿ / Generate function template"""
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
    // TODO: å®ç°
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
        """çæç±»æ¨¡æ?/ Generate class template"""
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
                    method_lines.append('        """TODO: å®ç°"""')
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
        // TODO: åå§å?    }}
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
        """çææµè¯æ¨¡æ¿ / Generate test template"""
        if language == "python":
            return '''import pytest

def test_function():
    """æµè¯å½æ°"""
    # TODO: æ·»å æµè¯ç¨ä¾
    assert True
'''
        elif language in ("javascript", "typescript"):
            return '''describe('Test Suite', () => {
    test('test case', () => {
        // TODO: æ·»å æµè¯ç¨ä¾
        expect(true).toBe(true);
    });
});
'''
        else:
            return f"// Test file for {test_framework}"


class CodeAnalyzer:
    """
    ä»£ç åæå?/ Code Analyzer
    
    åæä»£ç ç»æåè´¨é?/ Analyze code structure and quality
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
        åæç»æ / Analyze structure
        
        Args:
            code: ä»£ç  / Code
            language: è¯­è¨ / Language
            
        Returns:
            ç»æä¿¡æ¯ / Structure info
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
        """åæPythonä»£ç  / Analyze Python code"""
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
        """åæJavaScriptä»£ç  / Analyze JavaScript code"""
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
        è®¡ç®å¤æåº?/ Calculate complexity
        
        Args:
            code: ä»£ç  / Code
            language: è¯­è¨ / Language
            
        Returns:
            å¤æåº¦ä¿¡æ?/ Complexity info
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
