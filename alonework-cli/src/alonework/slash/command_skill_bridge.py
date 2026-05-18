"""
å½ä»¤æè½æ¡¥æ¥å¨ / Command Skill Bridge

å°ææ å½ä»¤ä¸æè½ç³»ç»ç»ä¸ / Unify slash commands and skills system

åè½ / Features:
- æè½å¯ä½ä¸ºææ å½ä»¤è°ç¨ / Skills can be invoked as slash commands
- ææ å½ä»¤å¯ä½ä¸ºæè½ç®¡ç?/ Slash commands can be managed as skills
- ç»ä¸çæ³¨åååç° / Unified registration and discovery
- ç®åå¿æºæ¨¡å?/ Simplified mental model

çæ¬ / Version: 2.1.3
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import asyncio


@dataclass
class UnifiedCommand:
    """
    ç»ä¸å½ä»¤å®ä¹ / Unified command definition
    
    åæ¶æ¯æææ å½ä»¤åæè½çå±æ?/ Supports both slash command and skill attributes
    """
    name: str
    description: str
    handler: Callable
    aliases: List[str] = field(default_factory=list)
    category: str = "general"
    usage: str = ""
    examples: List[str] = field(default_factory=list)
    
    is_skill: bool = False
    skill_id: Optional[str] = None
    skill_version: str = "1.0.0"
    skill_author: str = "system"
    skill_tags: List[str] = field(default_factory=list)
    skill_dependencies: List[str] = field(default_factory=list)
    
    input_types: List[str] = field(default_factory=list)
    output_types: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    
    enabled: bool = True
    
    def get_display_name(self) -> str:
        """è·åæ¾ç¤ºåç§° / Get display name"""
        return self.name
    
    def is_available(self) -> bool:
        """æ£æ¥æ¯å¦å¯ç?/ Check if available"""
        return self.enabled


class CommandSkillBridge:
    """
    å½ä»¤æè½æ¡¥æ¥å¨ / Command Skill Bridge
    
    ç»ä¸ç®¡çææ å½ä»¤åæè?/ Unified management of slash commands and skills
    
    ä½¿ç¨ç¤ºä¾ / Usage Example:
        bridge = CommandSkillBridge()
        
        # æ³¨åææ å½ä»¤
        bridge.register_command(slash_command)
        
        # æ³¨åæè½ï¼èªå¨è½¬æ¢ä¸ºå½ä»¤ï¼
        bridge.register_skill(skill)
        
        # ç»ä¸è°ç¨
        bridge.execute("compact", args=["--auto"])
        bridge.execute("data_analysis", args=["--type", "summary"])
    """
    
    def __init__(self):
        self._commands: Dict[str, UnifiedCommand] = {}
        self._aliases: Dict[str, str] = {}
        self._categories: Dict[str, List[str]] = {}
        self._skills_registry = None
        self._slash_registry = None
    
    def set_skills_registry(self, registry: Any) -> None:
        """è®¾ç½®æè½æ³¨åè¡¨ / Set skills registry"""
        self._skills_registry = registry
        self._sync_skills_to_commands()
    
    def set_slash_registry(self, registry: Any) -> None:
        """è®¾ç½®ææ å½ä»¤æ³¨åè¡?/ Set slash registry"""
        self._slash_registry = registry
        self._sync_slash_to_commands()
    
    def _sync_skills_to_commands(self) -> None:
        """åæ­¥æè½å°å½ä»¤ / Sync skills to commands"""
        if not self._skills_registry:
            return
        
        try:
            for skill_meta in self._skills_registry.list():
                self.register_skill(skill_meta)
        except Exception:
            pass
    
    def _sync_slash_to_commands(self) -> None:
        """åæ­¥ææ å½ä»¤ / Sync slash commands"""
        if not self._slash_registry:
            return
        
        try:
            for cmd in self._slash_registry.list_commands():
                self.register_slash_command(cmd)
        except Exception:
            pass
    
    def register_command(self, command: UnifiedCommand) -> None:
        """
        æ³¨åç»ä¸å½ä»¤ / Register unified command
        
        Args:
            command: ç»ä¸å½ä»¤å®ä¹ / Unified command definition
        """
        self._commands[command.name] = command
        
        for alias in command.aliases:
            self._aliases[alias] = command.name
        
        if command.category not in self._categories:
            self._categories[command.category] = []
        if command.name not in self._categories[command.category]:
            self._categories[command.category].append(command.name)
    
    def register_slash_command(self, slash_cmd: Any) -> None:
        """
        æ³¨åææ å½ä»¤ / Register slash command
        
        å°ææ å½ä»¤è½¬æ¢ä¸ºç»ä¸å½ä»¤æ ¼å¼ / Convert slash command to unified format
        """
        unified = UnifiedCommand(
            name=slash_cmd.name,
            description=slash_cmd.description,
            handler=slash_cmd.handler,
            aliases=getattr(slash_cmd, "aliases", []),
            category=getattr(slash_cmd, "category", "general"),
            usage=getattr(slash_cmd, "usage", ""),
            examples=getattr(slash_cmd, "examples", []),
            is_skill=False,
        )
        self.register_command(unified)
    
    def register_skill(self, skill_meta: Any) -> None:
        """
        æ³¨åæè?/ Register skill
        
        å°æè½è½¬æ¢ä¸ºç»ä¸å½ä»¤æ ¼å¼ / Convert skill to unified format
        """
        skill_name = getattr(skill_meta, "name", str(skill_meta))
        
        async def skill_handler(args: list, obj: dict, **kwargs) -> Any:
            return await self._execute_skill(skill_name, args, obj, kwargs)
        
        def sync_handler(args: list, obj: dict, **kwargs) -> Any:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(skill_handler(args, obj, **kwargs))
        
        unified = UnifiedCommand(
            name=skill_name,
            description=getattr(skill_meta, "description", ""),
            handler=sync_handler,
            aliases=[],
            category=getattr(skill_meta, "category", "skills"),
            is_skill=True,
            skill_id=getattr(skill_meta, "name", skill_name),
            skill_version=getattr(skill_meta, "version", "1.0.0"),
            skill_author=getattr(skill_meta, "author", "system"),
            skill_tags=getattr(skill_meta, "tags", []),
            skill_dependencies=getattr(skill_meta, "dependencies", []),
        )
        self.register_command(unified)
    
    async def _execute_skill(
        self, 
        skill_name: str, 
        args: list, 
        obj: dict, 
        kwargs: dict
    ) -> Any:
        """æ§è¡æè?/ Execute skill"""
        if not self._skills_registry:
            return None
        
        skill = self._skills_registry.get(skill_name)
        if not skill:
            return None
        
        context = {
            "args": args,
            "obj": obj,
            "kwargs": kwargs,
        }
        
        try:
            return await skill.execute(context)
        except Exception as e:
            return {"error": str(e)}
    
    def unregister(self, name: str) -> bool:
        """
        æ³¨éå½ä»¤ / Unregister command
        
        Args:
            name: å½ä»¤åç§°æå«å?/ Command name or alias
        
        Returns:
            æ¯å¦æå / Whether successful
        """
        actual_name = self._aliases.get(name, name)
        
        if actual_name not in self._commands:
            return False
        
        cmd = self._commands[actual_name]
        
        for alias in cmd.aliases:
            self._aliases.pop(alias, None)
        
        if cmd.category in self._categories:
            self._categories[cmd.category] = [
                n for n in self._categories[cmd.category] if n != actual_name
            ]
        
        del self._commands[actual_name]
        return True
    
    def get(self, name: str) -> Optional[UnifiedCommand]:
        """
        è·åå½ä»¤ / Get command
        
        Args:
            name: å½ä»¤åç§°æå«å?/ Command name or alias
        
        Returns:
            å½ä»¤å®ä¹ / Command definition
        """
        actual_name = self._aliases.get(name, name)
        return self._commands.get(actual_name)
    
    def has(self, name: str) -> bool:
        """æ£æ¥å½ä»¤æ¯å¦å­å?/ Check if command exists"""
        return name in self._commands or name in self._aliases
    
    def execute(
        self, 
        name: str, 
        args: List[str] = None, 
        obj: dict = None,
        **kwargs
    ) -> Any:
        """
        æ§è¡å½ä»¤ / Execute command
        
        ç»ä¸æ§è¡ææ å½ä»¤ææè?/ Unified execution of slash command or skill
        
        Args:
            name: å½ä»¤åç§° / Command name
            args: åæ°åè¡¨ / Arguments list
            obj: ä¸ä¸æå¯¹è±?/ Context object
            **kwargs: å¶ä»åæ° / Other arguments
        
        Returns:
            æ§è¡ç»æ / Execution result
        """
        command = self.get(name)
        
        if not command:
            raise ValueError(f"å½ä»¤ä¸å­å?/ Command not found: {name}")
        
        if not command.is_available():
            raise ValueError(f"å½ä»¤å·²ç¦ç?/ Command disabled: {name}")
        
        args = args or []
        obj = obj or {}
        
        return command.handler(args=args, obj=obj, **kwargs)
    
    def list_commands(
        self, 
        category: Optional[str] = None,
        include_skills: bool = True,
    ) -> List[UnifiedCommand]:
        """
        ååºææå½ä»?/ List all commands
        
        Args:
            category: åç±»è¿æ»¤ / Category filter
            include_skills: æ¯å¦åå«æè?/ Whether to include skills
        
        Returns:
            å½ä»¤åè¡¨ / Command list
        """
        if category:
            names = self._categories.get(category, [])
            commands = [self._commands[n] for n in names if n in self._commands]
        else:
            commands = list(self._commands.values())
        
        if not include_skills:
            commands = [c for c in commands if not c.is_skill]
        
        return commands
    
    def list_categories(self) -> List[str]:
        """ååºææåç±?/ List all categories"""
        return list(self._categories.keys())
    
    def search(self, query: str) -> List[UnifiedCommand]:
        """
        æç´¢å½ä»¤ / Search commands
        
        æåç§°ãæè¿°ãæ ç­¾æç´?/ Search by name, description, tags
        
        Args:
            query: æç´¢å³é®è¯?/ Search query
        
        Returns:
            å¹éçå½ä»¤åè¡?/ Matched commands
        """
        query_lower = query.lower()
        results = []
        
        for cmd in self._commands.values():
            if query_lower in cmd.name.lower():
                results.append(cmd)
            elif query_lower in cmd.description.lower():
                results.append(cmd)
            elif any(query_lower in tag.lower() for tag in cmd.skill_tags):
                results.append(cmd)
        
        return results
    
    def get_completions(self, prefix: str) -> List[str]:
        """
        è·åè¡¥å¨å»ºè®® / Get completion suggestions
        
        Args:
            prefix: åç¼ / Prefix
        
        Returns:
            è¡¥å¨å»ºè®®åè¡¨ / Completion suggestions
        """
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        è·åç»è®¡ä¿¡æ¯ / Get statistics
        
        Returns:
            ç»è®¡ä¿¡æ¯ / Statistics
        """
        total = len(self._commands)
        skills = sum(1 for c in self._commands.values() if c.is_skill)
        slash_commands = total - skills
        enabled = sum(1 for c in self._commands.values() if c.enabled)
        
        return {
            "total_commands": total,
            "slash_commands": slash_commands,
            "skills": skills,
            "enabled": enabled,
            "disabled": total - enabled,
            "categories": len(self._categories),
            "aliases": len(self._aliases),
        }
    
    def enable(self, name: str) -> bool:
        """å¯ç¨å½ä»¤ / Enable command"""
        cmd = self.get(name)
        if cmd:
            cmd.enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """ç¦ç¨å½ä»¤ / Disable command"""
        cmd = self.get(name)
        if cmd:
            cmd.enabled = False
            return True
        return False
    
    def to_slash_command(self, name: str) -> Optional[Any]:
        """
        è½¬æ¢ä¸ºææ å½ä»¤æ ¼å¼?/ Convert to slash command format
        
        ç¨äºä¸ç°æææ å½ä»¤ç³»ç»éæ?/ For integration with existing slash command system
        """
        cmd = self.get(name)
        if not cmd:
            return None
        
        from alonework.slash.registry import SlashCommand
        
        return SlashCommand(
            name=cmd.name,
            description=cmd.description,
            handler=cmd.handler,
            aliases=cmd.aliases,
            usage=cmd.usage,
            examples=cmd.examples,
            category=cmd.category,
        )


def create_bridge(
    skills_registry: Any = None,
    slash_registry: Any = None,
) -> CommandSkillBridge:
    """
    åå»ºå½ä»¤æè½æ¡¥æ¥å¨ / Create command skill bridge
    
    å·¥åå½æ°ï¼èªå¨åæ­¥ç°ææ³¨åè¡¨ / Factory function, auto sync existing registries
    
    Args:
        skills_registry: æè½æ³¨åè¡¨ / Skills registry
        slash_registry: ææ å½ä»¤æ³¨åè¡?/ Slash registry
    
    Returns:
        éç½®å¥½çæ¡¥æ¥å?/ Configured bridge
    """
    bridge = CommandSkillBridge()
    
    if skills_registry:
        bridge.set_skills_registry(skills_registry)
    
    if slash_registry:
        bridge.set_slash_registry(slash_registry)
    
    return bridge
