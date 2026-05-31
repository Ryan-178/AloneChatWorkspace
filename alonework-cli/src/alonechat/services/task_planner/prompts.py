"""
任务规划 Prompt 模板
从配置文件加载，替代硬编码
"""
from alonechat.configs import get_prompts_config

_config = get_prompts_config()

TASK_DECOMPOSITION_PROMPT = _config.task_decomposition_prompt

TASK_EXECUTION_PROMPT = _config.task_execution_prompt


def reload_prompts():
    """重新加载提示词配置"""
    global TASK_DECOMPOSITION_PROMPT, TASK_EXECUTION_PROMPT, _config
    
    _config = get_prompts_config().reload()
    TASK_DECOMPOSITION_PROMPT = _config.task_decomposition_prompt
    TASK_EXECUTION_PROMPT = _config.task_execution_prompt
