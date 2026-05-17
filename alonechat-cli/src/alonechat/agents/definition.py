"""
代理定义 / Agent Definition

定义子代理的结构和行为 / Defines structure and behavior of subagents
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AgentModel(Enum):
    """代理模型枚举 / Agent model enum"""
    SONNET = "sonnet"
    OPUS = "opus"
    HAIKU = "haiku"
    DEEPSEEK = "deepseek"


@dataclass
class AgentDefinition:
    """
    代理定义 / Agent Definition
    
    定义一个子代理的完整配置 / Defines complete configuration of a subagent
    """
    name: str
    description: str
    prompt: str
    tools: list[str] = field(default_factory=list)
    model: AgentModel = AgentModel.DEEPSEEK
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """转换为字典 / Convert to dict"""
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "tools": self.tools,
            "model": self.model.value,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentDefinition":
        """从字典创建 / Create from dict"""
        model_str = data.get("model", "deepseek")
        try:
            model = AgentModel(model_str.lower())
        except ValueError:
            model = AgentModel.DEEPSEEK
        
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            tools=data.get("tools", []),
            model=model,
            enabled=data.get("enabled", True),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> dict[str, "AgentDefinition"]:
        """
        从JSON字符串解析多个代理 / Parse multiple agents from JSON string
        
        用于 --agents 标志 / Used for --agents flag
        """
        import json
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return {}
        
        agents = {}
        for name, agent_data in data.items():
            agent_data["name"] = name
            agents[name] = cls.from_dict(agent_data)
        
        return agents


DEFAULT_AGENTS: dict[str, AgentDefinition] = {
    "code-reviewer": AgentDefinition(
        name="code-reviewer",
        description="代码审查专家，主动审查代码变更 / Expert code reviewer, proactively reviews code changes",
        prompt="你是一位高级代码审查专家。专注于代码质量、安全性和最佳实践。审查代码时提供具体的改进建议。",
        tools=["Read", "Grep", "Glob", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "debugger": AgentDefinition(
        name="debugger",
        description="调试专家，分析错误和测试失败 / Debugging specialist for errors and test failures",
        prompt="你是一位调试专家。分析错误，识别根本原因，并提供修复方案。使用系统化方法排查问题。",
        tools=["Read", "Grep", "Glob", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "test-writer": AgentDefinition(
        name="test-writer",
        description="测试编写专家，编写单元测试和集成测试 / Test writing specialist",
        prompt="你是一位测试编写专家。编写清晰、全面的测试用例，覆盖边界情况和错误处理。",
        tools=["Read", "Write", "Edit", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "doc-writer": AgentDefinition(
        name="doc-writer",
        description="文档编写专家，编写技术文档和注释 / Documentation specialist",
        prompt="你是一位技术文档专家。编写清晰、结构化的文档，包括API文档、使用指南和示例。",
        tools=["Read", "Write", "Edit"],
        model=AgentModel.DEEPSEEK,
    ),
}
