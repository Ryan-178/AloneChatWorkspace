"""
代理管理器 / Agent Manager

管理代理的注册、查找和配置 / Manages agent registration, lookup and configuration
"""

import json
from pathlib import Path
from typing import Optional
from rich.console import Console

from alonechat.agents.definition import AgentDefinition, DEFAULT_AGENTS

console = Console()


class AgentManager:
    """代理管理器 / Agent Manager"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".alonechat"
        self.config_dir = config_dir
        self.config_file = config_dir / "agents.json"
        
        self._agents: dict[str, AgentDefinition] = {}
        self._load_default_agents()
        self._load_user_agents()
    
    def _load_default_agents(self) -> None:
        """加载默认代理 / Load default agents"""
        self._agents.update(DEFAULT_AGENTS)
    
    def _load_user_agents(self) -> None:
        """加载用户定义的代理 / Load user-defined agents"""
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
        """保存用户代理 / Save user agents"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        user_agents = {
            name: agent.to_dict()
            for name, agent in self._agents.items()
            if name not in DEFAULT_AGENTS
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(user_agents, f, ensure_ascii=False, indent=2)
    
    def register(self, agent: AgentDefinition) -> None:
        """注册代理 / Register agent"""
        self._agents[agent.name] = agent
        self._save_user_agents()
        console.print(f"[green]✓ 已注册代理 / Agent registered: {agent.name}[/green]")
    
    def unregister(self, name: str) -> bool:
        """注销代理 / Unregister agent"""
        if name in self._agents:
            del self._agents[name]
            self._save_user_agents()
            console.print(f"[green]✓ 已注销代理 / Agent unregistered: {name}[/green]")
            return True
        return False
    
    def get(self, name: str) -> Optional[AgentDefinition]:
        """获取代理 / Get agent"""
        return self._agents.get(name)
    
    def list_agents(self) -> list[AgentDefinition]:
        """列出所有代理 / List all agents"""
        return list(self._agents.values())
    
    def enable(self, name: str) -> bool:
        """启用代理 / Enable agent"""
        agent = self.get(name)
        if agent:
            agent.enabled = True
            self._save_user_agents()
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用代理 / Disable agent"""
        agent = self.get(name)
        if agent:
            agent.enabled = False
            self._save_user_agents()
            return True
        return False
    
    def load_from_json(self, json_str: str) -> list[str]:
        """
        从JSON字符串加载代理 / Load agents from JSON string
        
        用于 --agents 标志 / Used for --agents flag
        """
        agents = AgentDefinition.from_json(json_str)
        loaded_names = []
        
        for name, agent in agents.items():
            self._agents[name] = agent
            loaded_names.append(name)
        
        return loaded_names
    
    def get_agent_info(self, name: str) -> dict:
        """获取代理信息 / Get agent info"""
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
