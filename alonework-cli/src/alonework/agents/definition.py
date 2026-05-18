"""
ä»£çå®ä¹ / Agent Definition

å®ä¹å­ä»£ççç»æåè¡ä¸?/ Defines structure and behavior of subagents
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AgentModel(Enum):
    """ä»£çæ¨¡åæä¸¾ / Agent model enum"""
    SONNET = "sonnet"
    OPUS = "opus"
    HAIKU = "haiku"
    DEEPSEEK = "deepseek"


@dataclass
class AgentDefinition:
    """
    ä»£çå®ä¹ / Agent Definition
    
    å®ä¹ä¸ä¸ªå­ä»£ççå®æ´éç½?/ Defines complete configuration of a subagent
    """
    name: str
    description: str
    prompt: str
    tools: list[str] = field(default_factory=list)
    model: AgentModel = AgentModel.DEEPSEEK
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """è½¬æ¢ä¸ºå­å?/ Convert to dict"""
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
        """ä»å­å¸åå»?/ Create from dict"""
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
        ä»JSONå­ç¬¦ä¸²è§£æå¤ä¸ªä»£ç?/ Parse multiple agents from JSON string
        
        ç¨äº --agents æ å¿ / Used for --agents flag
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
        description="ä»£ç å®¡æ¥ä¸å®¶ï¼ä¸»å¨å®¡æ¥ä»£ç åæ?/ Expert code reviewer, proactively reviews code changes",
        prompt="ä½ æ¯ä¸ä½é«çº§ä»£ç å®¡æ¥ä¸å®¶ãä¸æ³¨äºä»£ç è´¨éãå®å¨æ§åæä½³å®è·µãå®¡æ¥ä»£ç æ¶æä¾å·ä½çæ¹è¿å»ºè®®ã?,
        tools=["Read", "Grep", "Glob", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "debugger": AgentDefinition(
        name="debugger",
        description="è°è¯ä¸å®¶ï¼åæéè¯¯åæµè¯å¤±è´¥ / Debugging specialist for errors and test failures",
        prompt="ä½ æ¯ä¸ä½è°è¯ä¸å®¶ãåæéè¯¯ï¼è¯å«æ ¹æ¬åå ï¼å¹¶æä¾ä¿®å¤æ¹æ¡ãä½¿ç¨ç³»ç»åæ¹æ³ææ¥é®é¢ã?,
        tools=["Read", "Grep", "Glob", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "test-writer": AgentDefinition(
        name="test-writer",
        description="æµè¯ç¼åä¸å®¶ï¼ç¼åååæµè¯åéææµè¯ / Test writing specialist",
        prompt="ä½ æ¯ä¸ä½æµè¯ç¼åä¸å®¶ãç¼åæ¸æ°ãå¨é¢çæµè¯ç¨ä¾ï¼è¦çè¾¹çæåµåéè¯¯å¤çã?,
        tools=["Read", "Write", "Edit", "Bash"],
        model=AgentModel.DEEPSEEK,
    ),
    "doc-writer": AgentDefinition(
        name="doc-writer",
        description="ææ¡£ç¼åä¸å®¶ï¼ç¼åææ¯ææ¡£åæ³¨é / Documentation specialist",
        prompt="ä½ æ¯ä¸ä½ææ¯ææ¡£ä¸å®¶ãç¼åæ¸æ°ãç»æåçææ¡£ï¼åæ¬APIææ¡£ãä½¿ç¨æååç¤ºä¾ã?,
        tools=["Read", "Write", "Edit"],
        model=AgentModel.DEEPSEEK,
    ),
}
