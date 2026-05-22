"""
基础工具类 - Base Tool Classes

定义工具的基础抽象类和数据模型
Defines base abstract classes and data models for tools

工具分类 / Tool Categories:
- shell: Shell命令执行 / Shell command execution
- file: 文件操作 / File operations
- git: Git版本控制 / Git version control
- web: 网络操作 / Web operations
- code: 代码操作 / Code operations
- general: 通用工具 / General tools

权限级别 / Permission Levels:
- read: 只读操作 / Read-only operations
- write: 写入操作 / Write operations
- execute: 执行操作 / Execute operations
- dangerous: 危险操作 / Dangerous operations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ToolCategory(str, Enum):
    """
    工具分类枚举 - Tool Category Enum
    定义工具的分类，用于组织和筛选工具
    Defines tool categories for organization and filtering
    """
    SHELL = "shell"
    FILE = "file"
    GIT = "git"
    WEB = "web"
    CODE = "code"
    GENERAL = "general"


class PermissionLevel(str, Enum):
    """
    权限级别枚举 - Permission Level Enum
    定义工具操作所需的权限级别
    Defines permission level required for tool operations
    """
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DANGEROUS = "dangerous"


class ToolParameter(BaseModel):
    """
    工具参数模型 - Tool Parameter Model
    定义工具的单个参数
    Defines a single parameter for a tool
    """
    name: str = Field(..., description="参数名称 / Parameter name")
    type: str = Field(..., description="参数类型 / Parameter type")
    description: str = Field(..., description="参数描述 / Parameter description")
    required: bool = Field(default=True, description="是否必需 / Whether required")
    default: Optional[Any] = Field(default=None, description="默认值 / Default value")
    enum: Optional[List[Any]] = Field(default=None, description="枚举值列表 / Enum values list")


class ToolDef(BaseModel):
    """
    工具定义模型 - Tool Definition Model
    定义工具的完整信息
    Defines complete information for a tool
    """
    name: str = Field(..., description="工具名称 / Tool name")
    description: str = Field(..., description="工具描述 / Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数JSON Schema / Parameters JSON Schema")
    category: str = Field(default="general", description="工具分类 / Tool category")
    permission_level: str = Field(default="read", description="权限级别 / Permission level")
    estimated_cost: float = Field(default=0.0, description="预估成本 / Estimated cost")


class ToolResult(BaseModel):
    """
    工具执行结果模型 - Tool Execution Result Model
    表示工具执行后的返回结果
    Represents the result after tool execution
    """
    success: bool = Field(default=True, description="是否成功 / Whether successful")
    data: Any = Field(default=None, description="返回数据 / Returned data")
    error: Optional[str] = Field(default=None, description="错误信息 / Error message")
    execution_time_ms: float = Field(default=0.0, description="执行时间(毫秒) / Execution time in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳 / Timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据 / Additional metadata")


class BaseTool(ABC):
    """
    基础工具抽象类 - Base Tool Abstract Class
    
    所有工具必须继承此类并实现execute方法
    All tools must inherit this class and implement execute method
    
    属性 / Attributes:
        name: 工具名称 / Tool name
        description: 工具描述 / Tool description
        parameters: 参数JSON Schema / Parameters JSON Schema
        category: 工具分类 / Tool category
        permission_level: 权限级别 / Permission level
        estimated_cost: 预估成本 / Estimated cost
    """
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    category: str = "general"
    permission_level: str = "read"
    estimated_cost: float = 0.0
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        执行工具 / Execute tool
        
        子类必须实现此方法
        Subclasses must implement this method
        
        Args:
            **kwargs: 工具参数 / Tool parameters
        
        Returns:
            执行结果 / Execution result
        """
        pass
    
    def get_definition(self) -> ToolDef:
        """
        获取工具定义 / Get tool definition
        
        Returns:
            工具定义对象 / Tool definition object
        """
        return ToolDef(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            category=self.category,
            permission_level=self.permission_level,
            estimated_cost=self.estimated_cost,
        )
    
    def is_dangerous(self) -> bool:
        """
        检查是否为危险工具 / Check if tool is dangerous
        
        Returns:
            是否危险 / Whether dangerous
        """
        return self.permission_level == PermissionLevel.DANGEROUS.value
    
    def needs_confirmation(self) -> bool:
        """
        检查是否需要确认 / Check if confirmation is needed
        
        Returns:
            是否需要确认 / Whether confirmation is needed
        """
        return self.permission_level in [
            PermissionLevel.WRITE.value,
            PermissionLevel.EXECUTE.value,
            PermissionLevel.DANGEROUS.value,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典 / Convert to dictionary
        
        Returns:
            工具信息字典 / Tool info dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "permission_level": self.permission_level,
            "estimated_cost": self.estimated_cost,
            "is_dangerous": self.is_dangerous(),
            "needs_confirmation": self.needs_confirmation(),
        }
