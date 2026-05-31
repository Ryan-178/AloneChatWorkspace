"""
Slash命令注册表 / Slash Command Registry

管理所有slash命令的注册和查找 / Manages registration and lookup of slash commands

对齐 claude-code-claude 的命令类型系统 / Aligns with claude-code-claude's command type system
版本 / Version: 2.1.80
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class SlashCommand:
    """
    Slash命令数据类 / Slash Command Data Class

    对齐 claude-code-claude 的 CommandBase 类型
    Aligns with claude-code-claude's CommandBase type

    命令类型 / Command Types:
    - local: 本地执行，返回文本 / Local execution, returns text
    - prompt: 展开为模型提示 / Expands to model prompt
    - interactive: 交互式命令 / Interactive command
    """
    name: str
    description: str
    handler: Callable
    type: str = "local"
    aliases: list[str] = field(default_factory=list)
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    category: str = "general"
    is_hidden: bool = False
    is_enabled: bool = True
    source: str = "builtin"
    version: str = ""
    when_to_use: str = ""
    argument_hint: str = ""
    disable_model_invocation: bool = False
    user_invocable: bool = True
    immediate: bool = False
    is_sensitive: bool = False
    supports_non_interactive: bool = True
    progress_message: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    effort: str = ""


class SlashCommandRegistry:
    """
    Slash命令注册表 / Slash Command Registry

    对齐 claude-code-claude 的命令管理架构
    - 支持命令类型过滤
    - 支持可用性检查
    - 支持来源过滤
    - 支持动态技能发现

    Aligns with claude-code-claude's command management architecture
    - Command type filtering
    - Availability checking
    - Source filtering
    - Dynamic skill discovery
    """

    def __init__(self):
        self._commands: dict[str, SlashCommand] = {}
        self._aliases: dict[str, str] = {}
        self._categories: dict[str, list[str]] = {}
        self._dynamic_commands: dict[str, SlashCommand] = {}

    def register(self, command: SlashCommand) -> None:
        """注册命令 / Register command"""
        if not command.is_enabled:
            return

        self._commands[command.name] = command

        for alias in command.aliases:
            self._aliases[alias] = command.name

        if command.category not in self._categories:
            self._categories[command.category] = []
        if command.name not in self._categories[command.category]:
            self._categories[command.category].append(command.name)

    def register_dynamic(self, command: SlashCommand) -> None:
        """
        注册动态命令 / Register dynamic command

        动态命令在运行时发现，如技能目录中的命令
        Dynamic commands are discovered at runtime, e.g., from skills directory
        """
        self._dynamic_commands[command.name] = command
        self.register(command)

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
            self._dynamic_commands.pop(name, None)
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

    def list_commands(
        self,
        category: Optional[str] = None,
        command_type: Optional[str] = None,
        source: Optional[str] = None,
        include_hidden: bool = False,
    ) -> list[SlashCommand]:
        """
        列出命令 / List commands

        Args:
            category: 按分类过滤 / Filter by category
            command_type: 按类型过滤 / Filter by type
            source: 按来源过滤 / Filter by source
            include_hidden: 是否包含隐藏命令 / Include hidden commands
        """
        commands = list(self._commands.values())

        if not include_hidden:
            commands = [c for c in commands if not c.is_hidden]

        if category:
            commands = [c for c in commands if c.category == category]

        if command_type:
            commands = [c for c in commands if c.type == command_type]

        if source:
            commands = [c for c in commands if c.source == source]

        return commands

    def list_categories(self) -> list[str]:
        """列出所有分类 / List all categories"""
        return list(self._categories.keys())

    def search(self, query: str) -> list[SlashCommand]:
        """搜索命令 / Search commands"""
        query = query.lower()
        results = []
        for cmd in self._commands.values():
            if (query in cmd.name.lower()
                    or query in cmd.description.lower()
                    or query in cmd.when_to_use.lower()
                    or any(query in alias for alias in cmd.aliases)):
                results.append(cmd)
        return results

    def get_completions(self, prefix: str) -> list[str]:
        """获取补全建议 / Get completion suggestions"""
        if not prefix.startswith("/"):
            prefix = "/" + prefix

        prefix_name = prefix[1:].lower()
        completions = []

        for cmd in self._commands.values():
            if cmd.is_hidden:
                continue
            if cmd.name.startswith(prefix_name):
                completions.append(f"/{cmd.name}")
            for alias in cmd.aliases:
                if alias.startswith(prefix_name):
                    completions.append(f"/{alias}")

        return sorted(completions)

    def get_commands_by_type(self, command_type: str) -> list[SlashCommand]:
        """
        按类型获取命令 / Get commands by type

        对齐 claude-code-claude 的命令类型过滤
        """
        return [c for c in self._commands.values() if c.type == command_type]

    def get_model_invocable_commands(self) -> list[SlashCommand]:
        """
        获取模型可调用的命令 / Get model-invocable commands

        对齐 claude-code-claude 的 getSkillToolCommands
        """
        return [
            c for c in self._commands.values()
            if c.type == "prompt" and not c.disable_model_invocation
        ]

    def clear_dynamic_cache(self) -> None:
        """
        清除动态命令缓存 / Clear dynamic command cache

        对齐 claude-code-claude 的 clearCommandsCache
        """
        self._dynamic_commands.clear()
