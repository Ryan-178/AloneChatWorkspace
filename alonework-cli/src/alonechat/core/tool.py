"""
工具接口定义 / Tool Interface Definition

参考 claude-code-claude 的 Tool 模式
Reference: claude-code-claude's Tool pattern

定义工具的基础接口和类型
Defines base tool interfaces and types
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, Awaitable, Callable, Dict, Generic, List, 
    Optional, TypeVar, Union
)
from enum import Enum


# 类型变量 / Type variables
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class PermissionResult(Enum):
    """
    权限检查结果 / Permission Check Result
    
    工具执行前的权限检查结果
    Result of permission check before tool execution
    """
    ALLOW = "allow"      # 允许执行 / Allow execution
    DENY = "deny"        # 拒绝执行 / Deny execution
    ASK = "ask"          # 需要用户确认 / Requires user confirmation


@dataclass
class ToolResult:
    """
    工具执行结果 / Tool Execution Result
    
    工具执行后的返回结果
    Return result after tool execution
    """
    data: Any                                    # 输出数据 / Output data
    error: Optional[str] = None                  # 错误信息 / Error message
    new_messages: List[Any] = field(default_factory=list)  # 新消息 / New messages
    is_error: bool = False                       # 是否为错误 / Whether is error


@dataclass
class ValidationResult:
    """
    输入验证结果 / Input Validation Result
    
    工具输入验证的结果
    Result of tool input validation
    """
    is_valid: bool                               # 是否有效 / Whether valid
    error_message: Optional[str] = None          # 错误信息 / Error message
    error_code: Optional[int] = None             # 错误代码 / Error code


@dataclass
class ToolProgress:
    """
    工具执行进度 / Tool Execution Progress
    
    工具执行过程中的进度信息
    Progress information during tool execution
    """
    tool_use_id: str                             # 工具调用 ID / Tool use ID
    progress: float = 0.0                        # 进度百分比 / Progress percentage (0-100)
    message: Optional[str] = None                # 进度消息 / Progress message
    data: Optional[Any] = None                   # 附加数据 / Additional data


# 进度回调类型 / Progress callback type
ToolProgressCallback = Callable[[ToolProgress], None]


@dataclass
class ToolUseContext:
    """
    工具使用上下文 / Tool Use Context
    
    工具执行时的上下文信息
    Context information during tool execution
    """
    abort_controller: Optional[Any] = None       # 中止控制器 / Abort controller
    get_app_state: Optional[Callable] = None     # 获取应用状态 / Get app state
    set_app_state: Optional[Callable] = None     # 设置应用状态 / Set app state
    messages: List[Any] = field(default_factory=list)  # 消息历史 / Message history
    agent_id: Optional[str] = None               # 代理 ID / Agent ID
    session_id: Optional[str] = None             # 会话 ID / Session ID


class Tool(ABC, Generic[InputT, OutputT]):
    """
    工具基类 / Tool Base Class
    
    所有工具必须继承此基类并实现抽象方法
    All tools must inherit from this base class and implement abstract methods
    
    使用示例 / Usage Example:
        class MyTool(Tool[dict, str]):
            @property
            def name(self) -> str:
                return "my_tool"
            
            @property
            def description(self) -> str:
                return "My custom tool"
            
            def input_schema(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            
            async def execute(self, input_data: dict, context: ToolUseContext) -> ToolResult:
                return ToolResult(data="result")
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        工具名称 / Tool name
        
        唯一标识工具的名称
        Unique name identifying the tool
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        工具描述 / Tool description
        
        工具功能的简短描述
        Short description of tool functionality
        """
        pass
    
    @property
    def aliases(self) -> List[str]:
        """
        工具别名 / Tool aliases
        
        工具的替代名称列表
        List of alternative names for the tool
        """
        return []
    
    @property
    def search_hint(self) -> Optional[str]:
        """
        搜索提示 / Search hint
        
        用于工具搜索的关键字提示
        Keyword hint for tool search
        """
        return None
    
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        输入模式 / Input schema
        
        JSON Schema 格式的输入定义
        Input definition in JSON Schema format
        
        Returns:
            JSON Schema 字典 / JSON Schema dictionary
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        input_data: InputT,
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        """
        执行工具 / Execute tool
        
        执行工具的主要逻辑
        Main logic for tool execution
        
        Args:
            input_data: 输入数据 / Input data
            context: 使用上下文 / Use context
            on_progress: 进度回调 / Progress callback
            
        Returns:
            执行结果 / Execution result
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        是否启用 / Whether enabled
        
        检查工具是否可用
        Check if tool is available
        
        Returns:
            是否启用 / Whether enabled
        """
        return True
    
    def is_read_only(self, input_data: InputT) -> bool:
        """
        是否只读 / Whether read-only
        
        检查工具是否只读操作
        Check if tool is read-only operation
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            是否只读 / Whether read-only
        """
        return False
    
    def is_destructive(self, input_data: InputT) -> bool:
        """
        是否破坏性操作 / Whether destructive
        
        检查工具是否执行破坏性操作（删除、覆盖等）
        Check if tool performs destructive operations (delete, overwrite, etc.)
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            是否破坏性 / Whether destructive
        """
        return False
    
    def is_concurrency_safe(self, input_data: InputT) -> bool:
        """
        是否并发安全 / Whether concurrency-safe
        
        检查工具是否可以并发执行
        Check if tool can be executed concurrently
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            是否并发安全 / Whether concurrency-safe
        """
        return False
    
    async def validate_input(
        self,
        input_data: InputT,
        context: ToolUseContext
    ) -> Optional[ValidationResult]:
        """
        验证输入 / Validate input
        
        验证工具输入是否有效
        Validate if tool input is valid
        
        Args:
            input_data: 输入数据 / Input data
            context: 使用上下文 / Use context
            
        Returns:
            验证结果，None 表示有效 / Validation result, None means valid
        """
        return None
    
    async def check_permissions(
        self,
        input_data: InputT,
        context: ToolUseContext
    ) -> PermissionResult:
        """
        检查权限 / Check permissions
        
        检查工具执行权限
        Check tool execution permissions
        
        Args:
            input_data: 输入数据 / Input data
            context: 使用上下文 / Use context
            
        Returns:
            权限结果 / Permission result
        """
        return PermissionResult.ALLOW
    
    def get_path(self, input_data: InputT) -> Optional[str]:
        """
        获取文件路径 / Get file path
        
        从输入中提取文件路径（如果适用）
        Extract file path from input (if applicable)
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            文件路径或 None / File path or None
        """
        return None
    
    def user_facing_name(self, input_data: Optional[InputT] = None) -> str:
        """
        用户可见名称 / User-facing name
        
        用于 UI 显示的工具名称
        Tool name for UI display
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            显示名称 / Display name
        """
        return self.name
    
    def get_activity_description(self, input_data: Optional[InputT] = None) -> Optional[str]:
        """
        活动描述 / Activity description
        
        用于进度显示的活动描述
        Activity description for progress display
        
        Args:
            input_data: 输入数据 / Input data
            
        Returns:
            活动描述或 None / Activity description or None
        """
        return None


# 工具列表类型 / Tool list type
Tools = List[Tool[Any, Any]]


def find_tool_by_name(tools: Tools, name: str) -> Optional[Tool[Any, Any]]:
    """
    按名称查找工具 / Find tool by name
    
    在工具列表中按名称或别名查找工具
    Find tool by name or alias in tool list
    
    Args:
        tools: 工具列表 / Tool list
        name: 工具名称 / Tool name
        
    Returns:
        找到的工具或 None / Found tool or None
    """
    for tool in tools:
        if tool.name == name or name in tool.aliases:
            return tool
    return None


def filter_enabled_tools(tools: Tools) -> Tools:
    """
    过滤启用的工具 / Filter enabled tools
    
    返回所有启用的工具
    Returns all enabled tools
    
    Args:
        tools: 工具列表 / Tool list
        
    Returns:
        启用的工具列表 / List of enabled tools
    """
    return [tool for tool in tools if tool.is_enabled()]
