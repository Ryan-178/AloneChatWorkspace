"""
工具构建器 / Tool Builder

参考 claude-code-claude 的 buildTool 模式
Reference: claude-code-claude's buildTool pattern

提供工具构建工厂函数
Provides tool building factory functions
"""

from typing import Any, Callable, Dict, Optional, Type
from dataclasses import dataclass

from .tool import Tool, ToolResult, PermissionResult, ToolUseContext


@dataclass
class ToolDefaults:
    """
    工具默认值 / Tool Defaults
    
    提供工具方法的默认实现
    Provides default implementations for tool methods
    """
    is_enabled: Callable[[], bool] = lambda: True
    is_read_only: Callable[[Any], bool] = lambda _: False
    is_destructive: Callable[[Any], bool] = lambda _: False
    is_concurrency_safe: Callable[[Any], bool] = lambda _: False
    check_permissions: Callable[[Any, ToolUseContext], PermissionResult] = lambda _, __: PermissionResult.ALLOW
    user_facing_name: Callable[[Any], str] = lambda _: ""


# 全局默认值实例 / Global defaults instance
_tool_defaults = ToolDefaults()


def build_tool(tool_class: Type[Tool], **overrides) -> Type[Tool]:
    """
    构建工具类 / Build tool class
    
    为工具类填充默认方法实现
    Fills in default method implementations for tool class
    
    参考 claude-code-claude 的 buildTool 函数
    Reference: claude-code-claude's buildTool function
    
    默认值 / Defaults:
    - is_enabled: True
    - is_read_only: False (假设有写操作 / assumes writes)
    - is_destructive: False
    - is_concurrency_safe: False (假设不安全 / assumes not safe)
    - check_permissions: ALLOW (交给通用权限系统 / defers to general permission system)
    - user_facing_name: tool.name
    
    Args:
        tool_class: 工具类 / Tool class
        **overrides: 覆盖默认值 / Override defaults
        
    Returns:
        填充了默认值的工具类 / Tool class with defaults filled in
        
    使用示例 / Usage Example:
        class MyTool(Tool[dict, str]):
            @property
            def name(self) -> str:
                return "my_tool"
            
            @property
            def description(self) -> str:
                return "My tool"
            
            def input_schema(self) -> dict:
                return {"type": "object", "properties": {}}
            
            async def execute(self, input_data, context):
                return ToolResult(data="result")
        
        # 构建工具，填充默认值 / Build tool, fill in defaults
        BuiltMyTool = build_tool(MyTool)
    """
    # 保存原始方法 / Save original methods
    original_is_enabled = tool_class.is_enabled
    original_is_read_only = tool_class.is_read_only
    original_is_destructive = tool_class.is_destructive
    original_is_concurrency_safe = tool_class.is_concurrency_safe
    original_check_permissions = tool_class.check_permissions
    original_user_facing_name = tool_class.user_facing_name
    
    # 应用覆盖 / Apply overrides
    if 'is_enabled' in overrides:
        tool_class.is_enabled = overrides['is_enabled']
    elif not hasattr(tool_class, '_custom_is_enabled'):
        tool_class.is_enabled = _tool_defaults.is_enabled
    
    if 'is_read_only' in overrides:
        tool_class.is_read_only = overrides['is_read_only']
    elif not hasattr(tool_class, '_custom_is_read_only'):
        tool_class.is_read_only = _tool_defaults.is_read_only
    
    if 'is_destructive' in overrides:
        tool_class.is_destructive = overrides['is_destructive']
    elif not hasattr(tool_class, '_custom_is_destructive'):
        tool_class.is_destructive = _tool_defaults.is_destructive
    
    if 'is_concurrency_safe' in overrides:
        tool_class.is_concurrency_safe = overrides['is_concurrency_safe']
    elif not hasattr(tool_class, '_custom_is_concurrency_safe'):
        tool_class.is_concurrency_safe = _tool_defaults.is_concurrency_safe
    
    if 'check_permissions' in overrides:
        tool_class.check_permissions = overrides['check_permissions']
    elif not hasattr(tool_class, '_custom_check_permissions'):
        tool_class.check_permissions = _tool_defaults.check_permissions
    
    if 'user_facing_name' in overrides:
        tool_class.user_facing_name = overrides['user_facing_name']
    elif not hasattr(tool_class, '_custom_user_facing_name'):
        # 默认使用 name 属性 / Default to name property
        tool_class.user_facing_name = lambda _: tool_class.name
    
    return tool_class


def create_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    execute_fn: Callable,
    **kwargs
) -> Tool:
    """
    动态创建工具 / Dynamically create tool
    
    通过函数动态创建工具实例
    Create tool instance dynamically via function
    
    Args:
        name: 工具名称 / Tool name
        description: 工具描述 / Tool description
        input_schema: 输入模式 / Input schema
        execute_fn: 执行函数 / Execute function
        **kwargs: 其他属性 / Other properties
        
    Returns:
        工具实例 / Tool instance
        
    使用示例 / Usage Example:
        async def my_execute(input_data, context, on_progress=None):
            return ToolResult(data="result")
        
        tool = create_tool(
            name="my_tool",
            description="My tool",
            input_schema={"type": "object", "properties": {}},
            execute_fn=my_execute
        )
    """
    class DynamicTool(Tool[dict, Any]):
        @property
        def tool_name(self) -> str:
            return name
        
        @property
        def tool_description(self) -> str:
            return description
        
        def tool_input_schema(self) -> Dict[str, Any]:
            return input_schema
        
        async def execute(self, input_data, context, on_progress=None):
            return await execute_fn(input_data, context, on_progress)
    
    # 设置属性 / Set attributes
    DynamicTool.name = property(lambda self: name)
    DynamicTool.description = property(lambda self: description)
    DynamicTool.input_schema = lambda self: input_schema
    
    # 应用额外属性 / Apply additional properties
    for key, value in kwargs.items():
        if hasattr(DynamicTool, key):
            setattr(DynamicTool, key, value)
    
    return build_tool(DynamicTool)


class ToolRegistry:
    """
    工具注册表 / Tool Registry
    
    管理工具注册和查找
    Manages tool registration and lookup
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(self, tool: Tool) -> None:
        """
        注册工具 / Register tool
        
        Args:
            tool: 工具实例 / Tool instance
        """
        self._tools[tool.name] = tool
        for alias in tool.aliases:
            self._aliases[alias] = tool.name
    
    def get(self, name: str) -> Optional[Tool]:
        """
        获取工具 / Get tool
        
        Args:
            name: 工具名称或别名 / Tool name or alias
            
        Returns:
            工具实例或 None / Tool instance or None
        """
        # 先查找直接名称 / First try direct name
        if name in self._tools:
            return self._tools[name]
        
        # 再查找别名 / Then try alias
        actual_name = self._aliases.get(name)
        if actual_name:
            return self._tools.get(actual_name)
        
        return None
    
    def list_tools(self) -> list[Tool]:
        """
        列出所有工具 / List all tools
        
        Returns:
            工具列表 / Tool list
        """
        return list(self._tools.values())
    
    def remove(self, name: str) -> bool:
        """
        移除工具 / Remove tool
        
        Args:
            name: 工具名称 / Tool name
            
        Returns:
            是否成功移除 / Whether successfully removed
        """
        if name in self._tools:
            tool = self._tools[name]
            # 清除别名 / Clear aliases
            for alias in tool.aliases:
                self._aliases.pop(alias, None)
            del self._tools[name]
            return True
        return False


# 全局工具注册表 / Global tool registry
_global_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表 / Get global tool registry
    
    Returns:
        全局工具注册表实例 / Global tool registry instance
    """
    return _global_tool_registry
