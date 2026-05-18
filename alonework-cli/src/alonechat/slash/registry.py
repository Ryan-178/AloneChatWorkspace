"""
Slash命令注册表 / Slash Command Registry

管理所有slash命令的注册和查找 / Manages registration and lookup of slash commands
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class SlashCommand:
    """Slash命令数据类 / Slash Command Data Class"""
    name: str
    description: str
    handler: Callable
    aliases: list[str] = field(default_factory=list)
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    category: str = "general"


class SlashCommandRegistry:
    """Slash命令注册表 / Slash Command Registry"""
    
    def __init__(self):
        self._commands: dict[str, SlashCommand] = {}
        self._aliases: dict[str, str] = {}
        self._categories: dict[str, list[str]] = {}
    
    def register(self, command: SlashCommand) -> None:
        """注册命令 / Register command"""
        self._commands[command.name] = command
        
        for alias in command.aliases:
            self._aliases[alias] = command.name
        
        if command.category not in self._categories:
            self._categories[command.category] = []
        if command.name not in self._categories[command.category]:
            self._categories[command.category].append(command.name)
    
    def unregister(self, name: str) -> bool:
        """注销命令 / Unregister command"""
        if name in self._commands:
            cmd = self._commands[name]
            for alias in cmd.aliases:
                self._aliases.pop(alias, None)
            if cmd.category in self._categories:
                self._categories[cmd.category] = [
                    n for n in self._categories[cmd.category] if n != name
                ]
            del self._commands[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[SlashCommand]:
        """获取命令 / Get command"""
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands.get(self._aliases[name])
        return None
    
    def has(self, name: str) -> bool:
        """检查命令是否存在 / Check if command exists"""
        return name in self._commands or name in self._aliases
    
    def list_commands(self, category: Optional[str] = None) -> list[SlashCommand]:
        """列出所有命令 / List all commands"""
        if category:
            names = self._categories.get(category, [])
            return [self._commands[n] for n in names if n in self._commands]
        return list(self._commands.values())
    
    def list_categories(self) -> list[str]:
        """列出所有分类 / List all categories"""
        return list(self._categories.keys())
    
    def search(self, query: str) -> list[SlashCommand]:
        """搜索命令 / Search commands"""
        query = query.lower()
        results = []
        for cmd in self._commands.values():
            if query in cmd.name.lower() or query in cmd.description.lower():
                results.append(cmd)
        return results
    
    def get_completions(self, prefix: str) -> list[str]:
        """获取补全建议 / Get completion suggestions"""
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        
        prefix_name = prefix[1:].lower()
        completions = []
        
        for cmd in self._commands.values():
            if cmd.name.startswith(prefix_name):
                completions.append(f"/{cmd.name}")
            for alias in cmd.aliases:
                if alias.startswith(prefix_name):
                    completions.append(f"/{alias}")
        
        return completions
