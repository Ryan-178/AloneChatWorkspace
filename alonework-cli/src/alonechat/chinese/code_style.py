"""
中文代码风格模块 / Chinese Code Style Module

提供 / Provides:
- 命名建议 / Naming suggestions
- 注释生成 / Comment generation
- 文档生成 / Documentation generation
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class StyleSuggestion:
    """风格建议 / Style Suggestion"""
    original: str
    suggested: str
    reason: str
    category: str


class StyleConfigLoader:
    """风格配置加载器 / Style Config Loader"""
    
    _instance: Optional["StyleConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "configs" / "chinese_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"chinese": {"code_style": {}}}
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def get_instance(cls) -> "StyleConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


style_config = StyleConfigLoader.get_instance()


class NamingAdvisor:
    """
    命名顾问 / Naming Advisor
    
    提供命名建议 / Provide naming suggestions
    """
    
    def __init__(self):
        self._config = style_config.get("chinese.code_style.naming", {})
    
    def suggest_variable_name(
        self,
        description: str,
        language: str = "python",
    ) -> List[str]:
        """
        建议变量名 / Suggest variable name
        
        Args:
            description: 描述 / Description
            language: 语言 / Language
            
        Returns:
            建议列表 / Suggestion list
        """
        suggestions = []
        
        keywords = self._extract_keywords(description)
        
        style = self._config.get("variable.style", "snake_case")
        max_length = self._config.get("variable.max_length", 30)
        
        for keyword in keywords[:3]:
            name = self._apply_style(keyword, style)
            if len(name) <= max_length:
                suggestions.append(name)
        
        if not suggestions:
            suggestions.append("data")
        
        return suggestions
    
    def suggest_function_name(
        self,
        description: str,
        language: str = "python",
    ) -> List[str]:
        """
        建议函数名 / Suggest function name
        
        Args:
            description: 描述 / Description
            language: 语言 / Language
            
        Returns:
            建议列表 / Suggestion list
        """
        suggestions = []
        
        verb_prefixes = self._config.get("function.verb_prefix", [])
        style = self._config.get("function.style", "snake_case")
        max_length = self._config.get("function.max_length", 40)
        
        keywords = self._extract_keywords(description)
        
        detected_verb = None
        for prefix in verb_prefixes:
            if prefix in description.lower():
                detected_verb = prefix
                break
        
        if keywords:
            base_name = keywords[0] if not detected_verb else keywords[-1] if len(keywords) > 1 else keywords[0]
            
            if detected_verb:
                name = f"{detected_verb}_{base_name}"
            else:
                name = base_name
            
            name = self._apply_style(name, style)
            if len(name) <= max_length:
                suggestions.append(name)
            
            for prefix in verb_prefixes[:3]:
                full_name = self._apply_style(f"{prefix}_{base_name}", style)
                if len(full_name) <= max_length and full_name not in suggestions:
                    suggestions.append(full_name)
        
        if not suggestions:
            suggestions.append("process")
        
        return suggestions[:5]
    
    def suggest_class_name(
        self,
        description: str,
        language: str = "python",
    ) -> List[str]:
        """
        建议类名 / Suggest class name
        
        Args:
            description: 描述 / Description
            language: 语言 / Language
            
        Returns:
            建议列表 / Suggestion list
        """
        suggestions = []
        
        suffixes = self._config.get("class.suffix", [])
        style = self._config.get("class.style", "PascalCase")
        max_length = self._config.get("class.max_length", 40)
        
        keywords = self._extract_keywords(description)
        
        if keywords:
            base_name = keywords[0]
            name = self._apply_style(base_name, style)
            
            if len(name) <= max_length:
                suggestions.append(name)
            
            for suffix in suffixes[:3]:
                full_name = self._apply_style(f"{base_name}_{suffix}", style)
                if len(full_name) <= max_length and full_name not in suggestions:
                    suggestions.append(full_name)
        
        if not suggestions:
            suggestions.append("Handler")
        
        return suggestions[:5]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词 / Extract keywords"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        english_pattern = re.compile(r'[a-zA-Z]+')
        
        keywords = []
        
        for match in english_pattern.finditer(text):
            word = match.group().lower()
            if len(word) > 2:
                keywords.append(word)
        
        for match in chinese_pattern.finditer(text):
            word = match.group()
            if len(word) >= 2:
                keywords.append(self._chinese_to_pinyin(word))
        
        return keywords
    
    def _chinese_to_pinyin(self, text: str) -> str:
        """中文转拼音（简化版）/ Chinese to pinyin (simplified)"""
        common_words = {
            "用户": "user",
            "数据": "data",
            "文件": "file",
            "配置": "config",
            "日志": "log",
            "请求": "request",
            "响应": "response",
            "处理": "process",
            "管理": "manage",
            "服务": "service",
            "控制器": "controller",
            "模型": "model",
            "视图": "view",
            "缓存": "cache",
            "数据库": "database",
            "连接": "connection",
            "会话": "session",
            "消息": "message",
            "任务": "task",
            "结果": "result",
            "错误": "error",
            "状态": "status",
            "信息": "info",
            "列表": "list",
            "详情": "detail",
            "创建": "create",
            "更新": "update",
            "删除": "delete",
            "查询": "query",
            "保存": "save",
            "加载": "load",
            "解析": "parse",
            "格式": "format",
            "验证": "validate",
        }
        
        return common_words.get(text, "item")
    
    def _apply_style(self, name: str, style: str) -> str:
        """应用命名风格 / Apply naming style"""
        words = re.split(r'[_\s]+', name.lower())
        words = [w for w in words if w]
        
        if not words:
            return name
        
        if style == "snake_case":
            return "_".join(words)
        elif style == "camelCase":
            return words[0] + "".join(w.capitalize() for w in words[1:])
        elif style == "PascalCase":
            return "".join(w.capitalize() for w in words)
        elif style == "UPPER_SNAKE_CASE":
            return "_".join(w.upper() for w in words)
        else:
            return "_".join(words)


class CommentGenerator:
    """
    注释生成器 / Comment Generator
    
    生成中文注释 / Generate Chinese comments
    """
    
    def __init__(self):
        self._config = style_config.get("chinese.code_style.comment", {})
    
    def generate_function_docstring(
        self,
        name: str,
        description: str,
        params: Optional[Dict[str, str]] = None,
        returns: Optional[str] = None,
        language: str = "python",
    ) -> str:
        """
        生成函数文档字符串 / Generate function docstring
        
        Args:
            name: 函数名 / Function name
            description: 描述 / Description
            params: 参数 / Parameters
            returns: 返回值 / Return value
            language: 语言 / Language
            
        Returns:
            文档字符串 / Docstring
        """
        if language == "python":
            lines = [f'"""', description, ""]
            
            if params:
                lines.append("Args:")
                for param_name, param_desc in params.items():
                    lines.append(f"    {param_name}: {param_desc}")
                lines.append("")
            
            if returns:
                lines.append("Returns:")
                lines.append(f"    {returns}")
                lines.append("")
            
            lines.append('"""')
            
            return "\n".join(lines)
        else:
            lines = [f"/**", f" * {description}"]
            
            if params:
                lines.append(" *")
                for param_name, param_desc in params.items():
                    lines.append(f" * @param {param_name} {param_desc}")
            
            if returns:
                lines.append(f" * @return {returns}")
            
            lines.append(" */")
            
            return "\n".join(lines)
    
    def generate_class_docstring(
        self,
        name: str,
        description: str,
        attributes: Optional[Dict[str, str]] = None,
        language: str = "python",
    ) -> str:
        """
        生成类文档字符串 / Generate class docstring
        
        Args:
            name: 类名 / Class name
            description: 描述 / Description
            attributes: 属性 / Attributes
            language: 语言 / Language
            
        Returns:
            文档字符串 / Docstring
        """
        if language == "python":
            lines = [f'"""', description, ""]
            
            if attributes:
                lines.append("Attributes:")
                for attr_name, attr_desc in attributes.items():
                    lines.append(f"    {attr_name}: {attr_desc}")
                lines.append("")
            
            lines.append('"""')
            
            return "\n".join(lines)
        else:
            return f"/**\n * {description}\n */"
    
    def generate_inline_comment(
        self,
        code: str,
        explanation: str,
        language: str = "python",
    ) -> str:
        """
        生成行内注释 / Generate inline comment
        
        Args:
            code: 代码 / Code
            explanation: 解释 / Explanation
            language: 语言 / Language
            
        Returns:
            带注释的代码 / Code with comment
        """
        if language == "python":
            return f"{code}  # {explanation}"
        else:
            return f"{code}  // {explanation}"


class ChineseCodeStyle:
    """
    中文代码风格综合工具 / Chinese Code Style Comprehensive Tool
    """
    
    def __init__(self):
        self.naming_advisor = NamingAdvisor()
        self.comment_generator = CommentGenerator()
    
    def analyze_and_suggest(
        self,
        code: str,
        language: str = "python",
    ) -> List[StyleSuggestion]:
        """
        分析并建议 / Analyze and suggest
        
        Args:
            code: 代码 / Code
            language: 语言 / Language
            
        Returns:
            建议列表 / Suggestion list
        """
        suggestions = []
        
        suggestions.extend(self._check_naming(code, language))
        suggestions.extend(self._check_comments(code, language))
        
        return suggestions
    
    def _check_naming(self, code: str, language: str) -> List[StyleSuggestion]:
        """检查命名 / Check naming"""
        suggestions = []
        
        func_pattern = re.compile(r'def\s+(\w+)\s*\(')
        for match in func_pattern.finditer(code):
            name = match.group(1)
            
            if re.match(r'^[a-z]$', name):
                suggestions.append(StyleSuggestion(
                    original=name,
                    suggested=f"process_{name}",
                    reason="函数名过于简短，建议使用更具描述性的名称",
                    category="naming",
                ))
        
        return suggestions
    
    def _check_comments(self, code: str, language: str) -> List[StyleSuggestion]:
        """检查注释 / Check comments"""
        suggestions = []
        
        func_pattern = re.compile(r'def\s+\w+\s*\([^)]*\)\s*:')
        
        for match in func_pattern.finditer(code):
            start = match.end()
            
            remaining = code[start:].strip()
            
            if not remaining.startswith('"""') and not remaining.startswith("'''"):
                suggestions.append(StyleSuggestion(
                    original="",
                    suggested="添加函数文档字符串",
                    reason="函数缺少文档字符串说明",
                    category="comment",
                ))
        
        return suggestions
