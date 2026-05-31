"""
配置加载器 - Configuration Loader
从YAML文件加载配置，替代硬编码
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


_config_cache: Dict[str, Any] = {}


def get_config_dir() -> Path:
    """获取配置文件目录"""
    return Path(__file__).parent


def load_yaml_config(filename: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        filename: 配置文件名
        use_cache: 是否使用缓存
        
    Returns:
        配置字典
    """
    if use_cache and filename in _config_cache:
        return _config_cache[filename]
    
    config_path = get_config_dir() / filename
    if not config_path.exists():
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    if use_cache:
        _config_cache[filename] = config
    
    return config


def reload_config(filename: str) -> Dict[str, Any]:
    """重新加载配置文件"""
    if filename in _config_cache:
        del _config_cache[filename]
    return load_yaml_config(filename, use_cache=True)


def clear_cache() -> None:
    """清空配置缓存"""
    global _config_cache
    _config_cache = {}


class PromptsConfig:
    """提示词配置"""
    
    _instance: Optional["PromptsConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("prompts.yaml")
        return cls._instance
    
    @property
    def code_system_prompt(self) -> str:
        return self._config.get("code_system_prompt", "")
    
    @property
    def code_generation_template(self) -> str:
        return self._config.get("code_generation_template", "")
    
    @property
    def debug_template(self) -> str:
        return self._config.get("debug_template", "")
    
    @property
    def refactor_template(self) -> str:
        return self._config.get("refactor_template", "")
    
    @property
    def search_agent_prompt(self) -> str:
        return self._config.get("search_agent_prompt", "")
    
    @property
    def plan_mode_prompt(self) -> str:
        return self._config.get("plan_mode_prompt", "")
    
    @property
    def mtc_system_prompt(self) -> str:
        return self._config.get("mtc_system_prompt", "")
    
    @property
    def intent_clarification_template(self) -> str:
        return self._config.get("intent_clarification_template", "")
    
    @property
    def task_planning_template(self) -> str:
        return self._config.get("task_planning_template", "")
    
    @property
    def output_format_guide(self) -> str:
        return self._config.get("output_format_guide", "")
    
    @property
    def mtc_skills_prompt(self) -> str:
        return self._config.get("mtc_skills_prompt", "")
    
    @property
    def task_decomposition_prompt(self) -> str:
        return self._config.get("task_decomposition_prompt", "")
    
    @property
    def task_execution_prompt(self) -> str:
        return self._config.get("task_execution_prompt", "")
    
    def get_file_generation_prompt(self, file_type: str) -> str:
        """获取文件生成提示词"""
        file_gen = self._config.get("file_generation", {})
        return file_gen.get(file_type, "")
    
    @classmethod
    def reload(cls) -> "PromptsConfig":
        """重新加载配置"""
        reload_config("prompts.yaml")
        cls._instance = None
        return cls()


class ModelsConfig:
    """模型配置"""
    
    _instance: Optional["ModelsConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("models.yaml")
        return cls._instance
    
    @property
    def deepseek_models(self) -> Dict[str, Any]:
        return self._config.get("models", {}).get("deepseek", {})
    
    @property
    def openai_models(self) -> Dict[str, Any]:
        return self._config.get("models", {}).get("openai", {})
    
    @property
    def embedding_models(self) -> Dict[str, Any]:
        return self._config.get("models", {}).get("embedding", {})
    
    @property
    def kv_cache_config(self) -> Dict[str, Any]:
        return self._config.get("kv_cache", {})
    
    def get_deepseek_model(self, model_name: str) -> Dict[str, Any]:
        """获取DeepSeek模型配置"""
        return self.deepseek_models.get(model_name, {})
    
    def get_openai_model(self, model_name: str) -> Dict[str, Any]:
        """获取OpenAI模型配置"""
        return self.openai_models.get(model_name, {})
    
    def get_model_pricing(self, provider: str, model_name: str) -> Dict[str, float]:
        """获取模型定价"""
        if provider == "deepseek":
            model_config = self.get_deepseek_model(model_name)
        elif provider == "openai":
            model_config = self.get_openai_model(model_name)
        else:
            return {}
        return model_config.get("pricing", {})
    
    def get_context_window(self, provider: str, model_name: str) -> int:
        """获取上下文窗口大小"""
        if provider == "deepseek":
            model_config = self.get_deepseek_model(model_name)
        elif provider == "openai":
            model_config = self.get_openai_model(model_name)
        else:
            return 4096
        return model_config.get("context_window", 4096)
    
    @classmethod
    def reload(cls) -> "ModelsConfig":
        """重新加载配置"""
        reload_config("models.yaml")
        cls._instance = None
        return cls()


class SandboxConfig:
    """沙箱配置"""
    
    _instance: Optional["SandboxConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("sandbox.yaml")
        return cls._instance
    
    @property
    def default_config(self) -> Dict[str, Any]:
        return self._config.get("default", {})
    
    @property
    def mtc_config(self) -> Dict[str, Any]:
        return self._config.get("mtc", {})
    
    @property
    def code_config(self) -> Dict[str, Any]:
        return self._config.get("code", {})
    
    @property
    def forbidden_commands(self) -> list:
        return self._config.get("forbidden_commands", [])
    
    @property
    def dangerous_flags(self) -> list:
        return self._config.get("dangerous_flags", [])
    
    @property
    def default_env(self) -> Dict[str, str]:
        return self._config.get("default_env", {})
    
    def get_mtc_allowed_commands(self) -> set:
        """获取MTC模式允许的命令"""
        return set(self.mtc_config.get("allowed_commands", []))
    
    def get_code_allowed_commands(self) -> set:
        """获取CODE模式允许的命令"""
        return set(self.code_config.get("allowed_commands", []))
    
    def get_mtc_permissions(self) -> set:
        """获取MTC模式权限"""
        from agent_framework.core.types import FilePermission
        permissions = self.mtc_config.get("allowed_permissions", [])
        result = set()
        for p in permissions:
            if p == "read":
                result.add(FilePermission.READ)
            elif p == "write":
                result.add(FilePermission.WRITE)
            elif p == "execute":
                result.add(FilePermission.EXECUTE)
        return result
    
    def get_code_permissions(self) -> set:
        """获取CODE模式权限"""
        from agent_framework.core.types import FilePermission
        permissions = self.code_config.get("allowed_permissions", [])
        result = set()
        for p in permissions:
            if p == "read":
                result.add(FilePermission.READ)
            elif p == "write":
                result.add(FilePermission.WRITE)
            elif p == "execute":
                result.add(FilePermission.EXECUTE)
        return result
    
    @classmethod
    def reload(cls) -> "SandboxConfig":
        """重新加载配置"""
        reload_config("sandbox.yaml")
        cls._instance = None
        return cls()


class IntentClarificationConfig:
    """意图澄清配置"""
    
    _instance: Optional["IntentClarificationConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("intent_clarification.yaml")
        return cls._instance
    
    @property
    def clarification_config(self) -> Dict[str, Any]:
        return self._config.get("clarification", {})
    
    @property
    def max_questions(self) -> int:
        return self.clarification_config.get("max_questions", 3)
    
    @property
    def vague_keywords(self) -> list:
        return self.clarification_config.get("vague_keywords", [])
    
    @property
    def specific_indicators(self) -> Dict[str, Any]:
        return self.clarification_config.get("specific_indicators", {})
    
    @property
    def vague_indicators(self) -> Dict[str, Any]:
        return self.clarification_config.get("vague_indicators", {})
    
    @property
    def question_templates(self) -> Dict[str, Any]:
        return self._config.get("question_templates", {})
    
    @property
    def task_keywords(self) -> Dict[str, Any]:
        return self._config.get("task_keywords", {})
    
    def get_questions_for_task_type(self, task_type: str) -> list:
        """获取特定任务类型的问题模板"""
        return self.question_templates.get(task_type, [])
    
    @classmethod
    def reload(cls) -> "IntentClarificationConfig":
        """重新加载配置"""
        reload_config("intent_clarification.yaml")
        cls._instance = None
        return cls()


class SkillsConfig:
    """技能配置"""
    
    _instance: Optional["SkillsConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("skills.yaml")
        return cls._instance
    
    @property
    def skills(self) -> Dict[str, Any]:
        return self._config.get("skills", {})
    
    @property
    def categories(self) -> Dict[str, Any]:
        return self._config.get("categories", {})
    
    def get_skill_config(self, skill_name: str) -> Dict[str, Any]:
        """获取技能配置"""
        return self.skills.get(skill_name, {})
    
    def get_skill_templates(self, skill_name: str) -> Dict[str, str]:
        """获取技能模板"""
        skill_config = self.get_skill_config(skill_name)
        return skill_config.get("templates", {})
    
    def get_category_skills(self, category: str) -> list:
        """获取分类下的技能列表"""
        cat_config = self.categories.get(category, {})
        return cat_config.get("skills", [])
    
    @classmethod
    def reload(cls) -> "SkillsConfig":
        """重新加载配置"""
        reload_config("skills.yaml")
        cls._instance = None
        return cls()


def get_prompts_config() -> PromptsConfig:
    """获取提示词配置"""
    return PromptsConfig()


def get_models_config() -> ModelsConfig:
    """获取模型配置"""
    return ModelsConfig()


def get_sandbox_config() -> SandboxConfig:
    """获取沙箱配置"""
    return SandboxConfig()


def get_intent_config() -> IntentClarificationConfig:
    """获取意图澄清配置"""
    return IntentClarificationConfig()


class PermissionsConfig:
    """权限规则配置"""
    
    _instance: Optional["PermissionsConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("permissions.yaml")
        return cls._instance
    
    @property
    def allowed_tools(self) -> list:
        return self._config.get("allowed_tools", [])
    
    @property
    def denied_tools(self) -> list:
        return self._config.get("denied_tools", [])
    
    @property
    def rules(self) -> list:
        return self._config.get("rules", [])
    
    @property
    def default_mode(self) -> str:
        return self._config.get("default_mode", "default")
    
    @property
    def tool_redirect_patterns(self) -> dict:
        return self._config.get("tool_redirect_patterns", {})
    
    def get(self, key: str, default=None):
        return self._config.get(key, default)
    
    @classmethod
    def reload(cls) -> "PermissionsConfig":
        reload_config("permissions.yaml")
        cls._instance = None
        return cls()


def get_skills_config() -> SkillsConfig:
    """获取技能配置"""
    return SkillsConfig()


def get_permissions_config() -> PermissionsConfig:
    """获取权限规则配置"""
    return PermissionsConfig()
