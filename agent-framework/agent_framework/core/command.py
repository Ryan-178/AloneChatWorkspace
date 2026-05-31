"""
命令接口定义 / Command Interface Definition

参考 claude-code-claude 的 Command 模式
Reference: claude-code-claude's Command pattern

定义命令的基础接口和类型
Defines base command interfaces and types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from enum import Enum


class CommandType(Enum):
    """
    命令类型 / Command Type
    
    命令的执行方式
    How the command is executed
    """
    LOCAL = "local"            # 本地执行，返回文本 / Local execution, returns text
    LOCAL_JSX = "local-jsx"    # 本地执行，返回 UI / Local execution, returns UI
    PROMPT = "prompt"          # 提示命令，发送给模型 / Prompt command, sent to model


class CommandSource(Enum):
    """
    命令来源 / Command Source
    
    命令的来源渠道
    Source channel of the command
    """
    BUILTIN = "builtin"        # 内置命令 / Built-in command
    PLUGIN = "plugin"          # 插件命令 / Plugin command
    SKILL = "skill"            # 技能命令 / Skill command
    MCP = "mcp"               # MCP 命令 / MCP command
    USER = "user"             # 用户定义 / User defined


@dataclass
class CommandResult:
    """
    命令执行结果 / Command Execution Result
    
    命令执行后的返回结果
    Return result after command execution
    """
    success: bool                                    # 是否成功 / Whether successful
    output: Optional[str] = None                     # 输出文本 / Output text
    error: Optional[str] = None                      # 错误信息 / Error message
    data: Optional[Any] = None                       # 附加数据 / Additional data
    display_type: str = "text"                       # 显示类型 / Display type (text, json, markdown)


@dataclass
class CommandContext:
    """
    命令上下文 / Command Context
    
    命令执行时的上下文信息
    Context information during command execution
    """
    args: str = ""                                   # 命令参数 / Command arguments
    verbose: bool = False                            # 详细模式 / Verbose mode
    session_id: Optional[str] = None                 # 会话 ID / Session ID
    cwd: Optional[str] = None                        # 当前目录 / Current directory
    config: Optional[Any] = None                     # 配置对象 / Config object
    extra: Dict[str, Any] = field(default_factory=dict)  # 额外数据 / Extra data


class Command(ABC):
    """
    命令基类 / Command Base Class
    
    所有命令必须继承此基类并实现抽象方法
    All commands must inherit from this base class and implement abstract methods
    
    使用示例 / Usage Example:
        class MyCommand(Command):
            @property
            def name(self) -> str:
                return "my_command"
            
            @property
            def description(self) -> str:
                return "My custom command"
            
            async def execute(self, context: CommandContext) -> CommandResult:
                return CommandResult(success=True, output="Done!")
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        命令名称 / Command name
        
        唯一标识命令的名称（不含斜杠前缀）
        Unique name identifying the command (without slash prefix)
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        命令描述 / Command description
        
        命令功能的简短描述
        Short description of command functionality
        """
        pass
    
    @property
    def command_type(self) -> CommandType:
        """
        命令类型 / Command type
        
        命令的执行方式
        How the command is executed
        """
        return CommandType.LOCAL
    
    @property
    def source(self) -> CommandSource:
        """
        命令来源 / Command source
        
        命令的来源渠道
        Source channel of the command
        """
        return CommandSource.BUILTIN
    
    @property
    def aliases(self) -> List[str]:
        """
        命令别名 / Command aliases
        
        命令的替代名称列表
        List of alternative names for the command
        """
        return []
    
    @property
    def usage(self) -> Optional[str]:
        """
        用法说明 / Usage info
        
        命令的用法说明
        Usage information for the command
        """
        return None
    
    @property
    def examples(self) -> List[str]:
        """
        使用示例 / Usage examples
        
        命令的使用示例列表
        List of usage examples for the command
        """
        return []
    
    def is_enabled(self) -> bool:
        """
        是否启用 / Whether enabled
        
        检查命令是否可用
        Check if command is available
        
        Returns:
            是否启用 / Whether enabled
        """
        return True
    
    def requires_session(self) -> bool:
        """
        是否需要会话 / Whether requires session
        
        检查命令是否需要活跃会话
        Check if command requires active session
        
        Returns:
            是否需要会话 / Whether requires session
        """
        return False
    
    @abstractmethod
    async def execute(self, context: CommandContext) -> CommandResult:
        """
        执行命令 / Execute command
        
        执行命令的主要逻辑
        Main logic for command execution
        
        Args:
            context: 命令上下文 / Command context
            
        Returns:
            执行结果 / Execution result
        """
        pass


# 命令列表类型 / Command list type
Commands = List[Command]


def find_command_by_name(commands: Commands, name: str) -> Optional[Command]:
    """
    按名称查找命令 / Find command by name
    
    在命令列表中按名称或别名查找命令
    Find command by name or alias in command list
    
    Args:
        commands: 命令列表 / Command list
        name: 命令名称（可带斜杠前缀）/ Command name (may have slash prefix)
        
    Returns:
        找到的命令或 None / Found command or None
    """
    # 移除斜杠前缀 / Remove slash prefix
    clean_name = name.lstrip('/')
    
    for cmd in commands:
        if cmd.name == clean_name or clean_name in cmd.aliases:
            return cmd
    return None


def filter_enabled_commands(commands: Commands) -> Commands:
    """
    过滤启用的命令 / Filter enabled commands
    
    返回所有启用的命令
    Returns all enabled commands
    
    Args:
        commands: 命令列表 / Command list
        
    Returns:
        启用的命令列表 / List of enabled commands
    """
    return [cmd for cmd in commands if cmd.is_enabled()]


def format_command_help(command: Command) -> str:
    """
    格式化命令帮助 / Format command help
    
    生成命令的帮助文本
    Generate help text for command
    
    Args:
        command: 命令实例 / Command instance
        
    Returns:
        帮助文本 / Help text
    """
    lines = [f"/{command.name} - {command.description}"]
    
    if command.aliases:
        lines.append(f"  别名 / Aliases: {', '.join(command.aliases)}")
    
    if command.usage:
        lines.append(f"  用法 / Usage: {command.usage}")
    
    if command.examples:
        lines.append("  示例 / Examples:")
        for example in command.examples:
            lines.append(f"    {example}")
    
    return "\n".join(lines)
