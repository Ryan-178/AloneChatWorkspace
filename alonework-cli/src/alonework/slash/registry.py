"""
Slashå½ä»¤æ³¨åè¡?/ Slash Command Registry

ç®¡çææslashå½ä»¤çæ³¨ååæ¥æ¾ / Manages registration and lookup of slash commands
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class SlashCommand:
    """Slashå½ä»¤æ°æ®ç±?/ Slash Command Data Class"""
    name: str
    description: str
    handler: Callable
    aliases: list[str] = field(default_factory=list)
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    category: str = "general"


class SlashCommandRegistry:
    """Slashå½ä»¤æ³¨åè¡?/ Slash Command Registry"""
    
    def __init__(self):
        self._commands: dict[str, SlashCommand] = {}
        self._aliases: dict[str, str] = {}
        self._categories: dict[str, list[str]] = {}
    
    def register(self, command: SlashCommand) -> None:
        """æ³¨åå½ä»¤ / Register command"""
        self._commands[command.name] = command
        
        for alias in command.aliases:
            self._aliases[alias] = command.name
        
        if command.category not in self._categories:
            self._categories[command.category] = []
        if command.name not in self._categories[command.category]:
            self._categories[command.category].append(command.name)
    
    def unregister(self, name: str) -> bool:
        """æ³¨éå½ä»¤ / Unregister command"""
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
        """è·åå½ä»¤ / Get command"""
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands.get(self._aliases[name])
        return None
    
    def has(self, name: str) -> bool:
        """æ£æ¥å½ä»¤æ¯å¦å­å?/ Check if command exists"""
        return name in self._commands or name in self._aliases
    
    def list_commands(self, category: Optional[str] = None) -> list[SlashCommand]:
        """ååºææå½ä»?/ List all commands"""
        if category:
            names = self._categories.get(category, [])
            return [self._commands[n] for n in names if n in self._commands]
        return list(self._commands.values())
    
    def list_categories(self) -> list[str]:
        """ååºææåç±?/ List all categories"""
        return list(self._categories.keys())
    
    def search(self, query: str) -> list[SlashCommand]:
        """æç´¢å½ä»¤ / Search commands"""
        query = query.lower()
        results = []
        for cmd in self._commands.values():
            if query in cmd.name.lower() or query in cmd.description.lower():
                results.append(cmd)
        return results
    
    def get_completions(self, prefix: str) -> list[str]:
        """è·åè¡¥å¨å»ºè®® / Get completion suggestions"""
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
