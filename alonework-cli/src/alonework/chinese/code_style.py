"""
ä¸­æä»£ç é£æ ¼æ¨¡å / Chinese Code Style Module

æä¾ / Provides:
- å½åå»ºè®® / Naming suggestions
- æ³¨éçæ / Comment generation
- ææ¡£çæ / Documentation generation
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class StyleSuggestion:
    """é£æ ¼å»ºè®® / Style Suggestion"""
    original: str
    suggested: str
    reason: str
    category: str


class StyleConfigLoader:
    """é£æ ¼éç½®å è½½å?/ Style Config Loader"""
    
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
    å½åé¡¾é® / Naming Advisor
    
    æä¾å½åå»ºè®® / Provide naming suggestions
    """
    
    def __init__(self):
        self._config = style_config.get("chinese.code_style.naming", {})
    
    def suggest_variable_name(
        self,
        description: str,
        language: str = "python",
    ) -> List[str]:
        """
        å»ºè®®åéå?/ Suggest variable name
        
        Args:
            description: æè¿° / Description
            language: è¯­è¨ / Language
            
        Returns:
            å»ºè®®åè¡¨ / Suggestion list
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
        å»ºè®®å½æ°å?/ Suggest function name
        
        Args:
            description: æè¿° / Description
            language: è¯­è¨ / Language
            
        Returns:
            å»ºè®®åè¡¨ / Suggestion list
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
        å»ºè®®ç±»å / Suggest class name
        
        Args:
            description: æè¿° / Description
            language: è¯­è¨ / Language
            
        Returns:
            å»ºè®®åè¡¨ / Suggestion list
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
        """æåå³é®è¯?/ Extract keywords"""
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
        """ä¸­æè½¬æ¼é³ï¼ç®åçï¼? Chinese to pinyin (simplified)"""
        common_words = {
            "ç¨æ·": "user",
            "æ°æ®": "data",
            "æä»¶": "file",
            "éç½®": "config",
            "æ¥å¿": "log",
            "è¯·æ±": "request",
            "ååº": "response",
            "å¤ç": "process",
            "ç®¡ç": "manage",
            "æå¡": "service",
            "æ§å¶å?: "controller",
            "æ¨¡å": "model",
            "è§å¾": "view",
            "ç¼å­": "cache",
            "æ°æ®åº?: "database",
            "è¿æ¥": "connection",
            "ä¼è¯": "session",
            "æ¶æ¯": "message",
            "ä»»å¡": "task",
            "ç»æ": "result",
            "éè¯¯": "error",
            "ç¶æ?: "status",
            "ä¿¡æ¯": "info",
            "åè¡¨": "list",
            "è¯¦æ": "detail",
            "åå»º": "create",
            "æ´æ°": "update",
            "å é¤": "delete",
            "æ¥è¯¢": "query",
            "ä¿å­": "save",
            "å è½½": "load",
            "è§£æ": "parse",
            "æ ¼å¼": "format",
            "éªè¯": "validate",
        }
        
        return common_words.get(text, "item")
    
    def _apply_style(self, name: str, style: str) -> str:
        """åºç¨å½åé£æ ¼ / Apply naming style"""
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
    æ³¨éçæå?/ Comment Generator
    
    çæä¸­ææ³¨é / Generate Chinese comments
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
        çæå½æ°ææ¡£å­ç¬¦ä¸?/ Generate function docstring
        
        Args:
            name: å½æ°å?/ Function name
            description: æè¿° / Description
            params: åæ° / Parameters
            returns: è¿åå?/ Return value
            language: è¯­è¨ / Language
            
        Returns:
            ææ¡£å­ç¬¦ä¸?/ Docstring
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
        çæç±»ææ¡£å­ç¬¦ä¸² / Generate class docstring
        
        Args:
            name: ç±»å / Class name
            description: æè¿° / Description
            attributes: å±æ?/ Attributes
            language: è¯­è¨ / Language
            
        Returns:
            ææ¡£å­ç¬¦ä¸?/ Docstring
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
        çæè¡åæ³¨é / Generate inline comment
        
        Args:
            code: ä»£ç  / Code
            explanation: è§£é / Explanation
            language: è¯­è¨ / Language
            
        Returns:
            å¸¦æ³¨éçä»£ç  / Code with comment
        """
        if language == "python":
            return f"{code}  # {explanation}"
        else:
            return f"{code}  // {explanation}"


class ChineseCodeStyle:
    """
    ä¸­æä»£ç é£æ ¼ç»¼åå·¥å· / Chinese Code Style Comprehensive Tool
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
        åæå¹¶å»ºè®?/ Analyze and suggest
        
        Args:
            code: ä»£ç  / Code
            language: è¯­è¨ / Language
            
        Returns:
            å»ºè®®åè¡¨ / Suggestion list
        """
        suggestions = []
        
        suggestions.extend(self._check_naming(code, language))
        suggestions.extend(self._check_comments(code, language))
        
        return suggestions
    
    def _check_naming(self, code: str, language: str) -> List[StyleSuggestion]:
        """æ£æ¥å½å?/ Check naming"""
        suggestions = []
        
        func_pattern = re.compile(r'def\s+(\w+)\s*\(')
        for match in func_pattern.finditer(code):
            name = match.group(1)
            
            if re.match(r'^[a-z]$', name):
                suggestions.append(StyleSuggestion(
                    original=name,
                    suggested=f"process_{name}",
                    reason="å½æ°åè¿äºç®ç­ï¼å»ºè®®ä½¿ç¨æ´å·æè¿°æ§çåç§°",
                    category="naming",
                ))
        
        return suggestions
    
    def _check_comments(self, code: str, language: str) -> List[StyleSuggestion]:
        """æ£æ¥æ³¨é?/ Check comments"""
        suggestions = []
        
        func_pattern = re.compile(r'def\s+\w+\s*\([^)]*\)\s*:')
        
        for match in func_pattern.finditer(code):
            start = match.end()
            
            remaining = code[start:].strip()
            
            if not remaining.startswith('"""') and not remaining.startswith("'''"):
                suggestions.append(StyleSuggestion(
                    original="",
                    suggested="æ·»å å½æ°ææ¡£å­ç¬¦ä¸?,
                    reason="å½æ°ç¼ºå°ææ¡£å­ç¬¦ä¸²è¯´æ?,
                    category="comment",
                ))
        
        return suggestions
