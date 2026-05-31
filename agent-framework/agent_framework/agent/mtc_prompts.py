"""
MTC模式提示词模板 - MTC Mode Prompt Templates
面向非开发用户的通用办公任务提示词
从配置文件加载，替代硬编码
"""
from agent_framework.configs import get_prompts_config

_config = get_prompts_config()

MTC_SYSTEM_PROMPT = _config.mtc_system_prompt

INTENT_CLARIFICATION_TEMPLATE = _config.intent_clarification_template

TASK_PLANNING_TEMPLATE = _config.task_planning_template

OUTPUT_FORMAT_GUIDE = _config.output_format_guide

MTC_SKILLS_PROMPT = _config.mtc_skills_prompt


def reload_prompts():
    """重新加载提示词配置"""
    global MTC_SYSTEM_PROMPT, INTENT_CLARIFICATION_TEMPLATE, TASK_PLANNING_TEMPLATE
    global OUTPUT_FORMAT_GUIDE, MTC_SKILLS_PROMPT, _config
    
    _config = get_prompts_config().reload()
    MTC_SYSTEM_PROMPT = _config.mtc_system_prompt
    INTENT_CLARIFICATION_TEMPLATE = _config.intent_clarification_template
    TASK_PLANNING_TEMPLATE = _config.task_planning_template
    OUTPUT_FORMAT_GUIDE = _config.output_format_guide
    MTC_SKILLS_PROMPT = _config.mtc_skills_prompt
