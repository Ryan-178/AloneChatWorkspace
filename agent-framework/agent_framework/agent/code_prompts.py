"""
CODE模式提示词模板 - CODE Mode Prompt Templates
面向开发者的编程任务提示词
从配置文件加载，替代硬编码
"""
from agent_framework.configs import get_prompts_config

_config = get_prompts_config()

CODE_SYSTEM_PROMPT = _config.code_system_prompt

CODE_GENERATION_TEMPLATE = _config.code_generation_template

DEBUG_TEMPLATE = _config.debug_template

REFACTOR_TEMPLATE = _config.refactor_template

SEARCH_AGENT_PROMPT = _config.search_agent_prompt

PLAN_MODE_PROMPT = _config.plan_mode_prompt


def reload_prompts():
    """重新加载提示词配置"""
    global CODE_SYSTEM_PROMPT, CODE_GENERATION_TEMPLATE, DEBUG_TEMPLATE
    global REFACTOR_TEMPLATE, SEARCH_AGENT_PROMPT, PLAN_MODE_PROMPT, _config
    
    _config = get_prompts_config().reload()
    CODE_SYSTEM_PROMPT = _config.code_system_prompt
    CODE_GENERATION_TEMPLATE = _config.code_generation_template
    DEBUG_TEMPLATE = _config.debug_template
    REFACTOR_TEMPLATE = _config.refactor_template
    SEARCH_AGENT_PROMPT = _config.search_agent_prompt
    PLAN_MODE_PROMPT = _config.plan_mode_prompt
