"""
Promptå·¥ç¨æ¨¡å / Prompt Engineering Module

æä¾ / Provides:
- Promptæ¨¡æ¿ç®¡ç / Prompt template management
- ä¸­æä¼åPrompt / Chinese optimized prompts
- ä»£ç çæPrompt / Code generation prompts
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class PromptTemplate:
    """Promptæ¨¡æ¿ / Prompt Template"""
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    description: str = ""
    
    def render(self, **kwargs) -> str:
        """æ¸²ææ¨¡æ¿ / Render template"""
        result = self.template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        return result


class PromptConfigLoader:
    """Promptéç½®å è½½å?/ Prompt Config Loader"""
    
    _instance: Optional["PromptConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "configs" / "deepseek_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"prompts": {"system": {}, "templates": {}}}
    
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
    def get_instance(cls) -> "PromptConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


prompt_config = PromptConfigLoader.get_instance()


class PromptEngineer:
    """
    Promptå·¥ç¨å¸?/ Prompt Engineer
    
    ç®¡çåçæåç±»Prompt / Manage and generate various prompts
    """
    
    def __init__(self):
        self._config = prompt_config
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """å è½½æ¨¡æ¿ / Load templates"""
        templates = self._config.get("prompts.templates", {})
        
        for name, template_str in templates.items():
            variables = self._extract_variables(template_str)
            self._templates[name] = PromptTemplate(
                name=name,
                template=template_str,
                variables=variables,
            )
    
    def _extract_variables(self, template: str) -> List[str]:
        """æååé / Extract variables"""
        import re
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, template)))
    
    def get_system_prompt(self, prompt_type: str) -> str:
        """
        è·åç³»ç»Prompt / Get system prompt
        
        Args:
            prompt_type: Promptç±»å / Prompt type
            
        Returns:
            ç³»ç»Prompt / System prompt
        """
        return self._config.get(f"prompts.system.{prompt_type}", "")
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """
        æ¸²ææ¨¡æ¿ / Render template
        
        Args:
            template_name: æ¨¡æ¿åç§° / Template name
            **kwargs: æ¨¡æ¿åé / Template variables
            
        Returns:
            æ¸²æç»æ / Rendered result
        """
        if template_name in self._templates:
            return self._templates[template_name].render(**kwargs)
        return ""
    
    def build_code_generation_prompt(
        self,
        description: str,
        language: str = "python",
        code_type: str = "function",
        name: Optional[str] = None,
        params: Optional[str] = None,
        returns: Optional[str] = None,
    ) -> str:
        """
        æå»ºä»£ç çæPrompt / Build code generation prompt
        
        Args:
            description: åè½æè¿° / Function description
            language: ç¼ç¨è¯­è¨ / Programming language
            code_type: ä»£ç ç±»å / Code type
            name: åç§° / Name
            params: åæ° / Parameters
            returns: è¿åå?/ Return value
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_generation")
        
        if code_type == "function":
            template_prompt = self.render_template(
                "function_generation",
                name=name or "function_name",
                description=description,
                params=params or "æ?/ None",
                returns=returns or "æ?/ None",
                language=language,
            )
        elif code_type == "class":
            template_prompt = self.render_template(
                "class_generation",
                name=name or "ClassName",
                description=description,
                attributes=params or "æ?/ None",
                methods=returns or "æ?/ None",
                language=language,
            )
        else:
            template_prompt = f"è¯·çæ{language}ä»£ç ï¼\n{description}"
        
        return f"{system_prompt}\n\n{template_prompt}"
    
    def build_code_review_prompt(
        self,
        code: str,
        language: str = "python",
    ) -> str:
        """
        æå»ºä»£ç å®¡æ¥Prompt / Build code review prompt
        
        Args:
            code: ä»£ç åå®¹ / Code content
            language: ç¼ç¨è¯­è¨ / Programming language
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_review")
        
        return f"""{system_prompt}

è¯·å®¡æ¥ä»¥ä¸{language}ä»£ç ï¼?
```{language}
{code}
```

è¯·æä¾ï¼
1. ä»£ç è´¨éè¯å (1-10)
2. åç°çé®é¢?3. æ¹è¿å»ºè®®
4. æä½³å®è·µå»ºè®?""
    
    def build_code_explanation_prompt(
        self,
        code: str,
        language: str = "python",
    ) -> str:
        """
        æå»ºä»£ç è§£éPrompt / Build code explanation prompt
        
        Args:
            code: ä»£ç åå®¹ / Code content
            language: ç¼ç¨è¯­è¨ / Programming language
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_explanation")
        
        return f"""{system_prompt}

è¯·è§£éä»¥ä¸{language}ä»£ç ï¼?
```{language}
{code}
```

è¯·ç¨ä¸­æè§£éï¼?1. ä»£ç åè½
2. å³é®é»è¾
3. ä½¿ç¨çææ?4. æ½å¨é®é¢"""
    
    def build_test_generation_prompt(
        self,
        code: str,
        language: str = "python",
        test_framework: Optional[str] = None,
    ) -> str:
        """
        æå»ºæµè¯çæPrompt / Build test generation prompt
        
        Args:
            code: ä»£ç åå®¹ / Code content
            language: ç¼ç¨è¯­è¨ / Programming language
            test_framework: æµè¯æ¡æ¶ / Test framework
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "go": "go test",
        }
        
        if test_framework is None:
            test_framework = framework_map.get(language, "pytest")
        
        return self.render_template(
            "test_generation",
            language=language,
            code=code,
            test_framework=test_framework,
        )
    
    def build_chinese_optimized_prompt(
        self,
        user_input: str,
        task_type: str = "general",
    ) -> str:
        """
        æå»ºä¸­æä¼åPrompt / Build Chinese optimized prompt
        
        Args:
            user_input: ç¨æ·è¾å¥ / User input
            task_type: ä»»å¡ç±»å / Task type
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("chinese_optimization")
        
        return f"""{system_prompt}

ç¨æ·éæ±ï¼{user_input}

è¯·ç¨ä¸­æåç­ï¼ç¡®ä¿ï¼
1. åç¡®çè§£ç¨æ·æå¾
2. æä¾æ¸æ°çè§£é?3. ä½¿ç¨è§èçä¸­æè¡¨è¾?4. ä»£ç æ³¨éä½¿ç¨ä¸­æ"""
    
    def build_refactoring_prompt(
        self,
        code: str,
        language: str = "python",
        goals: Optional[List[str]] = None,
    ) -> str:
        """
        æå»ºéæPrompt / Build refactoring prompt
        
        Args:
            code: ä»£ç åå®¹ / Code content
            language: ç¼ç¨è¯­è¨ / Programming language
            goals: éæç®æ  / Refactoring goals
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        goals = goals or ["æé«å¯è¯»æ?, "ä¼åæ§è½", "åå°éå¤"]
        
        return f"""è¯·éæä»¥ä¸{language}ä»£ç ï¼?
```{language}
{code}
```

éæç®æ ï¼?{chr(10).join(f'- {g}' for g in goals)}

è¦æ±ï¼?1. ä¿æåè½ä¸å
2. æé«ä»£ç è´¨é
3. æ·»å ä¸­ææ³¨é
4. éµå¾ªæä½³å®è·?""
    
    def build_error_fix_prompt(
        self,
        code: str,
        error_message: str,
        language: str = "python",
    ) -> str:
        """
        æå»ºéè¯¯ä¿®å¤Prompt / Build error fix prompt
        
        Args:
            code: ä»£ç åå®¹ / Code content
            error_message: éè¯¯ä¿¡æ¯ / Error message
            language: ç¼ç¨è¯­è¨ / Programming language
            
        Returns:
            å®æ´Prompt / Complete prompt
        """
        return f"""è¯·ä¿®å¤ä»¥ä¸{language}ä»£ç ä¸­çéè¯¯ï¼?
ä»£ç ï¼?```{language}
{code}
```

éè¯¯ä¿¡æ¯ï¼?{error_message}

è¯·ï¼
1. åæéè¯¯åå 
2. æä¾ä¿®å¤æ¹æ¡
3. è¾åºä¿®å¤åçä»£ç 
4. è§£éä¿®å¤åå®¹"""
