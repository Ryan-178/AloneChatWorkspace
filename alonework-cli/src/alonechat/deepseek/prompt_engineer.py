"""
Prompt工程模块 / Prompt Engineering Module

提供 / Provides:
- Prompt模板管理 / Prompt template management
- 中文优化Prompt / Chinese optimized prompts
- 代码生成Prompt / Code generation prompts
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class PromptTemplate:
    """Prompt模板 / Prompt Template"""
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    description: str = ""
    
    def render(self, **kwargs) -> str:
        """渲染模板 / Render template"""
        result = self.template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        return result


class PromptConfigLoader:
    """Prompt配置加载器 / Prompt Config Loader"""
    
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
    Prompt工程师 / Prompt Engineer
    
    管理和生成各类Prompt / Manage and generate various prompts
    """
    
    def __init__(self):
        self._config = prompt_config
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """加载模板 / Load templates"""
        templates = self._config.get("prompts.templates", {})
        
        for name, template_str in templates.items():
            variables = self._extract_variables(template_str)
            self._templates[name] = PromptTemplate(
                name=name,
                template=template_str,
                variables=variables,
            )
    
    def _extract_variables(self, template: str) -> List[str]:
        """提取变量 / Extract variables"""
        import re
        pattern = r'\{(\w+)\}'
        return list(set(re.findall(pattern, template)))
    
    def get_system_prompt(self, prompt_type: str) -> str:
        """
        获取系统Prompt / Get system prompt
        
        Args:
            prompt_type: Prompt类型 / Prompt type
            
        Returns:
            系统Prompt / System prompt
        """
        return self._config.get(f"prompts.system.{prompt_type}", "")
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """
        渲染模板 / Render template
        
        Args:
            template_name: 模板名称 / Template name
            **kwargs: 模板变量 / Template variables
            
        Returns:
            渲染结果 / Rendered result
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
        构建代码生成Prompt / Build code generation prompt
        
        Args:
            description: 功能描述 / Function description
            language: 编程语言 / Programming language
            code_type: 代码类型 / Code type
            name: 名称 / Name
            params: 参数 / Parameters
            returns: 返回值 / Return value
            
        Returns:
            完整Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_generation")
        
        if code_type == "function":
            template_prompt = self.render_template(
                "function_generation",
                name=name or "function_name",
                description=description,
                params=params or "无 / None",
                returns=returns or "无 / None",
                language=language,
            )
        elif code_type == "class":
            template_prompt = self.render_template(
                "class_generation",
                name=name or "ClassName",
                description=description,
                attributes=params or "无 / None",
                methods=returns or "无 / None",
                language=language,
            )
        else:
            template_prompt = f"请生成{language}代码：\n{description}"
        
        return f"{system_prompt}\n\n{template_prompt}"
    
    def build_code_review_prompt(
        self,
        code: str,
        language: str = "python",
    ) -> str:
        """
        构建代码审查Prompt / Build code review prompt
        
        Args:
            code: 代码内容 / Code content
            language: 编程语言 / Programming language
            
        Returns:
            完整Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_review")
        
        return f"""{system_prompt}

请审查以下{language}代码：

```{language}
{code}
```

请提供：
1. 代码质量评分 (1-10)
2. 发现的问题
3. 改进建议
4. 最佳实践建议"""
    
    def build_code_explanation_prompt(
        self,
        code: str,
        language: str = "python",
    ) -> str:
        """
        构建代码解释Prompt / Build code explanation prompt
        
        Args:
            code: 代码内容 / Code content
            language: 编程语言 / Programming language
            
        Returns:
            完整Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("code_explanation")
        
        return f"""{system_prompt}

请解释以下{language}代码：

```{language}
{code}
```

请用中文解释：
1. 代码功能
2. 关键逻辑
3. 使用的技术
4. 潜在问题"""
    
    def build_test_generation_prompt(
        self,
        code: str,
        language: str = "python",
        test_framework: Optional[str] = None,
    ) -> str:
        """
        构建测试生成Prompt / Build test generation prompt
        
        Args:
            code: 代码内容 / Code content
            language: 编程语言 / Programming language
            test_framework: 测试框架 / Test framework
            
        Returns:
            完整Prompt / Complete prompt
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
        构建中文优化Prompt / Build Chinese optimized prompt
        
        Args:
            user_input: 用户输入 / User input
            task_type: 任务类型 / Task type
            
        Returns:
            完整Prompt / Complete prompt
        """
        system_prompt = self.get_system_prompt("chinese_optimization")
        
        return f"""{system_prompt}

用户需求：{user_input}

请用中文回答，确保：
1. 准确理解用户意图
2. 提供清晰的解释
3. 使用规范的中文表达
4. 代码注释使用中文"""
    
    def build_refactoring_prompt(
        self,
        code: str,
        language: str = "python",
        goals: Optional[List[str]] = None,
    ) -> str:
        """
        构建重构Prompt / Build refactoring prompt
        
        Args:
            code: 代码内容 / Code content
            language: 编程语言 / Programming language
            goals: 重构目标 / Refactoring goals
            
        Returns:
            完整Prompt / Complete prompt
        """
        goals = goals or ["提高可读性", "优化性能", "减少重复"]
        
        return f"""请重构以下{language}代码：

```{language}
{code}
```

重构目标：
{chr(10).join(f'- {g}' for g in goals)}

要求：
1. 保持功能不变
2. 提高代码质量
3. 添加中文注释
4. 遵循最佳实践"""
    
    def build_error_fix_prompt(
        self,
        code: str,
        error_message: str,
        language: str = "python",
    ) -> str:
        """
        构建错误修复Prompt / Build error fix prompt
        
        Args:
            code: 代码内容 / Code content
            error_message: 错误信息 / Error message
            language: 编程语言 / Programming language
            
        Returns:
            完整Prompt / Complete prompt
        """
        return f"""请修复以下{language}代码中的错误：

代码：
```{language}
{code}
```

错误信息：
{error_message}

请：
1. 分析错误原因
2. 提供修复方案
3. 输出修复后的代码
4. 解释修复内容"""
