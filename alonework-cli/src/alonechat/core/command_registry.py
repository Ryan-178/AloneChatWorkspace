"""
命令注册表 / Command Registry

参考 claude-code-claude 的命令管理模式
Reference: claude-code-claude's command management pattern

管理命令注册、查找和懒加载
Manages command registration, lookup, and lazy loading
"""

import importlib
import logging
from typing import Any, Callable, Dict, List, Optional, Type

from .command import Command, CommandContext, CommandResult, Commands, CommandType

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    命令注册表 / Command Registry
    
    管理命令注册和查找，支持懒加载
    Manages command registration and lookup with lazy loading support
    
    使用示例 / Usage Example:
        registry = CommandRegistry()
        
        # 注册命令 / Register command
        registry.register(MyCommand())
        
        # 懒加载注册 / Lazy registration
        registry.register_lazy("my_command", "my_module.commands")
        
        # 获取命令 / Get command
        cmd = registry.get("my_command")
    """
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}
        self._lazy_modules: Dict[str, str] = {}
        self._factories: Dict[str, Callable[[], Command]] = {}
    
    def register(self, command: Command) -> None:
        """
        注册命令 / Register command
        
        Args:
            command: 命令实例 / Command instance
            
        Raises:
            ValueError: 如果命令名已存在 / If command name already exists
        """
        if command.name in self._commands:
            logger.warning(f"Command '{command.name}' already registered, overwriting")
        
        self._commands[command.name] = command
        
        # 注册别名 / Register aliases
        for alias in command.aliases:
            self._aliases[alias] = command.name
    
    def register_lazy(self, name: str, module_path: str, attr_name: Optional[str] = None) -> None:
        """
        懒加载注册 / Lazy registration
        
        延迟加载命令模块，直到首次使用
        Delays loading command module until first use
        
        Args:
            name: 命令名称 / Command name
            module_path: 模块路径 / Module path
            attr_name: 模块中的属性名（默认为 'command'）/ Attribute name in module (default: 'command')
        """
        self._lazy_modules[name] = (module_path, attr_name or 'command')
    
    def register_factory(self, name: str, factory: Callable[[], Command]) -> None:
        """
        工厂注册 / Factory registration
        
        使用工厂函数创建命令
        Create command using factory function
        
        Args:
            name: 命令名称 / Command name
            factory: 工厂函数 / Factory function
        """
        self._factories[name] = factory
    
    def get(self, name: str) -> Optional[Command]:
        """
        获取命令 / Get command
        
        Args:
            name: 命令名称或别名 / Command name or alias
            
        Returns:
            命令实例或 None / Command instance or None
        """
        # 移除斜杠前缀 / Remove slash prefix
        clean_name = name.lstrip('/')
        
        # 1. 直接查找 / Direct lookup
        if clean_name in self._commands:
            return self._commands[clean_name]
        
        # 2. 别名查找 / Alias lookup
        actual_name = self._aliases.get(clean_name)
        if actual_name and actual_name in self._commands:
            return self._commands[actual_name]
        
        # 3. 懒加载 / Lazy loading
        if clean_name in self._lazy_modules:
            return self._load_lazy_command(clean_name)
        
        # 4. 工厂创建 / Factory creation
        if clean_name in self._factories:
            return self._create_from_factory(clean_name)
        
        return None
    
    def _load_lazy_command(self, name: str) -> Optional[Command]:
        """
        加载懒加载命令 / Load lazy command
        
        Args:
            name: 命令名称 / Command name
            
        Returns:
            加载的命令或 None / Loaded command or None
        """
        if name not in self._lazy_modules:
            return None
        
        module_path, attr_name = self._lazy_modules[name]
        
        try:
            module = importlib.import_module(module_path)
            command = getattr(module, attr_name)
            
            if isinstance(command, Command):
                # 注册并移除懒加载记录 / Register and remove lazy record
                self.register(command)
                del self._lazy_modules[name]
                return command
            elif callable(command):
                # 如果是函数，调用它获取命令 / If function, call it to get command
                cmd = command()
                if isinstance(cmd, Command):
                    self.register(cmd)
                    del self._lazy_modules[name]
                    return cmd
            
            logger.error(f"Invalid command at {module_path}.{attr_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load lazy command '{name}': {e}")
            return None
    
    def _create_from_factory(self, name: str) -> Optional[Command]:
        """
        从工厂创建命令 / Create command from factory
        
        Args:
            name: 命令名称 / Command name
            
        Returns:
            创建的命令或 None / Created command or None
        """
        if name not in self._factories:
            return None
        
        try:
            factory = self._factories[name]
            command = factory()
            
            if isinstance(command, Command):
                self.register(command)
                del self._factories[name]
                return command
            
            logger.error(f"Factory for '{name}' did not return a Command instance")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create command '{name}' from factory: {e}")
            return None
    
    def list_commands(self, force_load: bool = False) -> Commands:
        """
        列出所有命令 / List all commands
        
        Args:
            force_load: 是否强制加载所有懒加载命令 / Whether to force load all lazy commands
            
        Returns:
            命令列表 / Command list
        """
        if force_load:
            # 加载所有懒加载命令 / Load all lazy commands
            for name in list(self._lazy_modules.keys()):
                self._load_lazy_command(name)
            for name in list(self._factories.keys()):
                self._create_from_factory(name)
        
        return list(self._commands.values())
    
    def list_enabled_commands(self) -> Commands:
        """
        列出所有启用的命令 / List all enabled commands
        
        Returns:
            启用的命令列表 / List of enabled commands
        """
        return [cmd for cmd in self.list_commands() if cmd.is_enabled()]
    
    def remove(self, name: str) -> bool:
        """
        移除命令 / Remove command
        
        Args:
            name: 命令名称 / Command name
            
        Returns:
            是否成功移除 / Whether successfully removed
        """
        clean_name = name.lstrip('/')
        
        if clean_name in self._commands:
            command = self._commands[clean_name]
            # 清除别名 / Clear aliases
            for alias in command.aliases:
                self._aliases.pop(alias, None)
            del self._commands[clean_name]
            return True
        
        return False
    
    def has_command(self, name: str) -> bool:
        """
        检查命令是否存在 / Check if command exists
        
        Args:
            name: 命令名称或别名 / Command name or alias
            
        Returns:
            是否存在 / Whether exists
        """
        return self.get(name) is not None
    
    def get_command_count(self) -> int:
        """
        获取命令数量 / Get command count
        
        Returns:
            已加载的命令数量 / Number of loaded commands
        """
        return len(self._commands)


# 全局命令注册表 / Global command registry
_global_command_registry = CommandRegistry()


def get_command_registry() -> CommandRegistry:
    """
    获取全局命令注册表 / Get global command registry
    
    Returns:
        全局命令注册表实例 / Global command registry instance
    """
    return _global_command_registry


async def execute_command(
    name: str,
    context: CommandContext,
    registry: Optional[CommandRegistry] = None
) -> CommandResult:
    """
    执行命令 / Execute command
    
    查找并执行命令
    Find and execute command
    
    Args:
        name: 命令名称 / Command name
        context: 命令上下文 / Command context
        registry: 命令注册表（默认使用全局）/ Command registry (default: global)
        
    Returns:
        执行结果 / Execution result
    """
    reg = registry or _global_command_registry
    command = reg.get(name)
    
    if command is None:
        return CommandResult(
            success=False,
            error=f"Command not found: {name}"
        )
    
    if not command.is_enabled():
        return CommandResult(
            success=False,
            error=f"Command disabled: {name}"
        )
    
    try:
        return await command.execute(context)
    except Exception as e:
        logger.error(f"Command '{name}' execution failed: {e}")
        return CommandResult(
            success=False,
            error=f"Command execution failed: {e}"
        )
