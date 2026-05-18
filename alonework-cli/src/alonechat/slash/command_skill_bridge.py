"""
命令技能桥接器 / Command Skill Bridge

将斜杠命令与技能系统统一 / Unify slash commands and skills system

功能 / Features:
- 技能可作为斜杠命令调用 / Skills can be invoked as slash commands
- 斜杠命令可作为技能管理 / Slash commands can be managed as skills
- 统一的注册和发现 / Unified registration and discovery
- 简化心智模型 / Simplified mental model

版本 / Version: 2.1.3
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import asyncio


@dataclass
class UnifiedCommand:
    """
    统一命令定义 / Unified command definition
    
    同时支持斜杠命令和技能的属性 / Supports both slash command and skill attributes
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
        """获取显示名称 / Get display name"""
        return self.name
    
    def is_available(self) -> bool:
        """检查是否可用 / Check if available"""
        return self.enabled


class CommandSkillBridge:
    """
    命令技能桥接器 / Command Skill Bridge
    
    统一管理斜杠命令和技能 / Unified management of slash commands and skills
    
    使用示例 / Usage Example:
        bridge = CommandSkillBridge()
        
        # 注册斜杠命令
        bridge.register_command(slash_command)
        
        # 注册技能（自动转换为命令）
        bridge.register_skill(skill)
        
        # 统一调用
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
        """设置技能注册表 / Set skills registry"""
        self._skills_registry = registry
        self._sync_skills_to_commands()
    
    def set_slash_registry(self, registry: Any) -> None:
        """设置斜杠命令注册表 / Set slash registry"""
        self._slash_registry = registry
        self._sync_slash_to_commands()
    
    def _sync_skills_to_commands(self) -> None:
        """同步技能到命令 / Sync skills to commands"""
        if not self._skills_registry:
            return
        
        try:
            for skill_meta in self._skills_registry.list():
                self.register_skill(skill_meta)
        except Exception:
            pass
    
    def _sync_slash_to_commands(self) -> None:
        """同步斜杠命令 / Sync slash commands"""
        if not self._slash_registry:
            return
        
        try:
            for cmd in self._slash_registry.list_commands():
                self.register_slash_command(cmd)
        except Exception:
            pass
    
    def register_command(self, command: UnifiedCommand) -> None:
        """
        注册统一命令 / Register unified command
        
        Args:
            command: 统一命令定义 / Unified command definition
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
        注册斜杠命令 / Register slash command
        
        将斜杠命令转换为统一命令格式 / Convert slash command to unified format
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
        注册技能 / Register skill
        
        将技能转换为统一命令格式 / Convert skill to unified format
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
        """执行技能 / Execute skill"""
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
        注销命令 / Unregister command
        
        Args:
            name: 命令名称或别名 / Command name or alias
        
        Returns:
            是否成功 / Whether successful
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
        获取命令 / Get command
        
        Args:
            name: 命令名称或别名 / Command name or alias
        
        Returns:
            命令定义 / Command definition
        """
        actual_name = self._aliases.get(name, name)
        return self._commands.get(actual_name)
    
    def has(self, name: str) -> bool:
        """检查命令是否存在 / Check if command exists"""
        return name in self._commands or name in self._aliases
    
    def execute(
        self, 
        name: str, 
        args: List[str] = None, 
        obj: dict = None,
        **kwargs
    ) -> Any:
        """
        执行命令 / Execute command
        
        统一执行斜杠命令或技能 / Unified execution of slash command or skill
        
        Args:
            name: 命令名称 / Command name
            args: 参数列表 / Arguments list
            obj: 上下文对象 / Context object
            **kwargs: 其他参数 / Other arguments
        
        Returns:
            执行结果 / Execution result
        """
        command = self.get(name)
        
        if not command:
            raise ValueError(f"命令不存在 / Command not found: {name}")
        
        if not command.is_available():
            raise ValueError(f"命令已禁用 / Command disabled: {name}")
        
        args = args or []
        obj = obj or {}
        
        return command.handler(args=args, obj=obj, **kwargs)
    
    def list_commands(
        self, 
        category: Optional[str] = None,
        include_skills: bool = True,
    ) -> List[UnifiedCommand]:
        """
        列出所有命令 / List all commands
        
        Args:
            category: 分类过滤 / Category filter
            include_skills: 是否包含技能 / Whether to include skills
        
        Returns:
            命令列表 / Command list
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
        """列出所有分类 / List all categories"""
        return list(self._categories.keys())
    
    def search(self, query: str) -> List[UnifiedCommand]:
        """
        搜索命令 / Search commands
        
        按名称、描述、标签搜索 / Search by name, description, tags
        
        Args:
            query: 搜索关键词 / Search query
        
        Returns:
            匹配的命令列表 / Matched commands
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
        获取补全建议 / Get completion suggestions
        
        Args:
            prefix: 前缀 / Prefix
        
        Returns:
            补全建议列表 / Completion suggestions
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
        获取统计信息 / Get statistics
        
        Returns:
            统计信息 / Statistics
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
        """启用命令 / Enable command"""
        cmd = self.get(name)
        if cmd:
            cmd.enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用命令 / Disable command"""
        cmd = self.get(name)
        if cmd:
            cmd.enabled = False
            return True
        return False
    
    def to_slash_command(self, name: str) -> Optional[Any]:
        """
        转换为斜杠命令格式 / Convert to slash command format
        
        用于与现有斜杠命令系统集成 / For integration with existing slash command system
        """
        cmd = self.get(name)
        if not cmd:
            return None
        
        from alonechat.slash.registry import SlashCommand
        
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
    创建命令技能桥接器 / Create command skill bridge
    
    工厂函数，自动同步现有注册表 / Factory function, auto sync existing registries
    
    Args:
        skills_registry: 技能注册表 / Skills registry
        slash_registry: 斜杠命令注册表 / Slash registry
    
    Returns:
        配置好的桥接器 / Configured bridge
    """
    bridge = CommandSkillBridge()
    
    if skills_registry:
        bridge.set_skills_registry(skills_registry)
    
    if slash_registry:
        bridge.set_slash_registry(slash_registry)
    
    return bridge
