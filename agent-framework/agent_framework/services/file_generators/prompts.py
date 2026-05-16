"""
文件生成 Prompt 模板
从配置文件加载，替代硬编码
"""
from agent_framework.configs import get_prompts_config

_config = get_prompts_config()

FILE_GENERATION_PROMPTS = {
    "ppt": _config.get_file_generation_prompt("ppt"),
    "excel": _config.get_file_generation_prompt("excel"),
    "word": _config.get_file_generation_prompt("word"),
    "report": _config.get_file_generation_prompt("report"),
    "code": _config.get_file_generation_prompt("code"),
    "data_analysis": _config.get_file_generation_prompt("data_analysis"),
}


def reload_prompts():
    """重新加载提示词配置"""
    global FILE_GENERATION_PROMPTS, _config
    
    _config = get_prompts_config().reload()
    FILE_GENERATION_PROMPTS = {
        "ppt": _config.get_file_generation_prompt("ppt"),
        "excel": _config.get_file_generation_prompt("excel"),
        "word": _config.get_file_generation_prompt("word"),
        "report": _config.get_file_generation_prompt("report"),
        "code": _config.get_file_generation_prompt("code"),
        "data_analysis": _config.get_file_generation_prompt("data_analysis"),
    }
