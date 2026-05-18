"""
ä»£çç®¡çå?/ Agent Manager

ç®¡çä»£ççæ³¨åãæ¥æ¾åéç½® / Manages agent registration, lookup and configuration
"""

import json
from pathlib import Path
from typing import Optional
from rich.console import Console

from alonework.agents.definition import AgentDefinition, DEFAULT_AGENTS

console = Console()


class AgentManager:
    """ä»£çç®¡çå?/ Agent Manager"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".alonechat"
        self.config_dir = config_dir
        self.config_file = config_dir / "agents.json"
        
        self._agents: dict[str, AgentDefinition] = {}
        self._load_default_agents()
        self._load_user_agents()
    
    def _load_default_agents(self) -> None:
        """å è½½é»è®¤ä»£ç / Load default agents"""
        self._agents.update(DEFAULT_AGENTS)
    
    def _load_user_agents(self) -> None:
        """å è½½ç¨æ·å®ä¹çä»£ç?/ Load user-defined agents"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, agent_data in data.items():
                    agent_data["name"] = name
                    self._agents[name] = AgentDefinition.from_dict(agent_data)
            except Exception:
                pass
    
    def _save_user_agents(self) -> None:
        """ä¿å­ç¨æ·ä»£ç / Save user agents"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        user_agents = {
            name: agent.to_dict()
            for name, agent in self._agents.items()
            if name not in DEFAULT_AGENTS
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(user_agents, f, ensure_ascii=False, indent=2)
    
    def register(self, agent: AgentDefinition) -> None:
        """æ³¨åä»£ç / Register agent"""
        self._agents[agent.name] = agent
        self._save_user_agents()
        console.print(f"[green]â?å·²æ³¨åä»£ç?/ Agent registered: {agent.name}[/green]")
    
    def unregister(self, name: str) -> bool:
        """æ³¨éä»£ç / Unregister agent"""
        if name in self._agents:
            del self._agents[name]
            self._save_user_agents()
            console.print(f"[green]â?å·²æ³¨éä»£ç / Agent unregistered: {name}[/green]")
            return True
        return False
    
    def get(self, name: str) -> Optional[AgentDefinition]:
        """è·åä»£ç / Get agent"""
        return self._agents.get(name)
    
    def list_agents(self) -> list[AgentDefinition]:
        """ååºææä»£ç?/ List all agents"""
        return list(self._agents.values())
    
    def enable(self, name: str) -> bool:
        """å¯ç¨ä»£ç / Enable agent"""
        agent = self.get(name)
        if agent:
            agent.enabled = True
            self._save_user_agents()
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """ç¦ç¨ä»£ç / Disable agent"""
        agent = self.get(name)
        if agent:
            agent.enabled = False
            self._save_user_agents()
            return True
        return False
    
    def load_from_json(self, json_str: str) -> list[str]:
        """
        ä»JSONå­ç¬¦ä¸²å è½½ä»£ç?/ Load agents from JSON string
        
        ç¨äº --agents æ å¿ / Used for --agents flag
        """
        agents = AgentDefinition.from_json(json_str)
        loaded_names = []
        
        for name, agent in agents.items():
            self._agents[name] = agent
            loaded_names.append(name)
        
        return loaded_names
    
    def get_agent_info(self, name: str) -> dict:
        """è·åä»£çä¿¡æ¯ / Get agent info"""
        agent = self.get(name)
        if agent is None:
            return {"exists": False}
        
        return {
            "exists": True,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model.value,
            "tools": agent.tools,
            "enabled": agent.enabled,
        }
