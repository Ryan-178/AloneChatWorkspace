"""
模式管理器 - Mode Manager

管理交互模式的切换和工具执行权限检查
Manages interaction mode switching and tool execution permission checking

交互模式说明 / Interaction Mode Description:
- PLAN: 只读探索模式，只允许读取和搜索工具 / Read-only exploration mode, only read and search tools allowed
- AGENT: 默认交互模式，危险工具需要用户确认 / Default interaction mode, dangerous tools require user confirmation
- YOLO: 自动批准模式，所有工具自动执行 / Auto-approve mode, all tools execute automatically
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from pathlib import Path

from agent_framework.core.types import InteractionMode, ModeConfig


class ModeManager(ABC):
    """
    模式管理器基类 - Base Mode Manager
    
    管理交互模式的生命周期和工具执行权限
    Manages interaction mode lifecycle and tool execution permissions
    
    子类需要实现 / Subclasses need to implement:
    - request_approval(): 请求用户批准工具执行 / Request user approval for tool execution
    - notify_mode_change(): 通知模式变化 / Notify mode change
    """
    
    def __init__(self, config: Optional[ModeConfig] = None):
        """
        初始化模式管理器 / Initialize mode manager
        
        Args:
            config: 模式配置，如果为None则使用默认AGENT模式 / Mode config, uses default AGENT mode if None
        """
        self._config = config or ModeConfig()
        self._mode = self._config.mode
        self._on_mode_change_callbacks: list[Callable[[InteractionMode, InteractionMode], Awaitable[None]]] = []
    
    @property
    def mode(self) -> InteractionMode:
        """获取当前模式 / Get current mode"""
        return self._mode
    
    @property
    def config(self) -> ModeConfig:
        """获取当前配置 / Get current config"""
        return self._config
    
    def get_mode(self) -> InteractionMode:
        """
        获取当前交互模式 / Get current interaction mode
        
        Returns:
            当前交互模式 / Current interaction mode
        """
        return self._mode
    
    def set_mode(self, mode: InteractionMode | str) -> bool:
        """
        设置交互模式 / Set interaction mode
        
        Args:
            mode: 新的交互模式（枚举或字符串）/ New interaction mode (enum or string)
        
        Returns:
            是否成功切换 / Whether switch was successful
        """
        if isinstance(mode, str):
            try:
                mode = InteractionMode(mode.lower())
            except ValueError:
                return False
        
        if mode == self._mode:
            return True
        
        old_mode = self._mode
        self._mode = mode
        
        self._update_config_for_mode()
        
        self.notify_mode_change(old_mode, mode)
        
        return True
    
    def _update_config_for_mode(self) -> None:
        """
        根据当前模式更新配置 / Update config based on current mode
        
        不同模式有不同的默认行为 / Different modes have different default behaviors
        """
        if self._mode == InteractionMode.PLAN:
            self._config.auto_approve_tools = False
            self._config.allowed_tools = ["read", "search", "list", "file_read", "file_search"]
            self._config.require_confirmation = []
        elif self._mode == InteractionMode.AGENT:
            self._config.auto_approve_tools = False
            self._config.allowed_tools = []
            self._config.require_confirmation = ["shell", "file_write", "file_delete", "file_edit"]
        elif self._mode == InteractionMode.YOLO:
            self._config.auto_approve_tools = True
            self._config.allowed_tools = []
            self._config.require_confirmation = []
    
    def check_tool_permission(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """
        检查工具是否有权限执行 / Check if tool has permission to execute
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        
        Returns:
            是否有权限 / Whether has permission
        """
        if self._mode == InteractionMode.YOLO:
            return True
        
        if self._mode == InteractionMode.PLAN:
            allowed = self._config.allowed_tools
            if allowed and tool_name not in allowed:
                return False
        
        return True
    
    def needs_confirmation(self, tool_name: str) -> bool:
        """
        检查工具是否需要用户确认 / Check if tool needs user confirmation
        
        Args:
            tool_name: 工具名称 / Tool name
        
        Returns:
            是否需要确认 / Whether needs confirmation
        """
        if self._config.auto_approve_tools:
            return False
        
        return tool_name in self._config.require_confirmation
    
    @abstractmethod
    async def request_approval(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """
        请求用户批准工具执行 / Request user approval for tool execution
        
        子类必须实现此方法，提供具体的用户交互方式
        Subclasses must implement this method with specific user interaction
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        
        Returns:
            用户是否批准 / Whether user approved
        """
        pass
    
    def notify_mode_change(self, old_mode: InteractionMode, new_mode: InteractionMode) -> None:
        """
        通知模式变化 / Notify mode change
        
        子类可以重写此方法提供额外的通知行为
        Subclasses can override this for additional notification behavior
        
        Args:
            old_mode: 旧模式 / Old mode
            new_mode: 新模式 / New mode
        """
        pass
    
    def register_mode_change_callback(
        self, 
        callback: Callable[[InteractionMode, InteractionMode], Awaitable[None]]
    ) -> None:
        """
        注册模式变化回调 / Register mode change callback
        
        Args:
            callback: 回调函数，接收(old_mode, new_mode) / Callback function, receives (old_mode, new_mode)
        """
        self._on_mode_change_callbacks.append(callback)
    
    def unregister_mode_change_callback(
        self, 
        callback: Callable[[InteractionMode, InteractionMode], Awaitable[None]]
    ) -> None:
        """
        注销模式变化回调 / Unregister mode change callback
        
        Args:
            callback: 要注销的回调函数 / Callback to unregister
        """
        if callback in self._on_mode_change_callbacks:
            self._on_mode_change_callbacks.remove(callback)
    
    def get_mode_description(self) -> str:
        """
        获取当前模式的描述 / Get description of current mode
        
        Returns:
            模式描述 / Mode description
        """
        descriptions = {
            InteractionMode.PLAN: "只读探索模式 - 仅允许读取和搜索操作 / Read-only exploration mode - Only read and search operations allowed",
            InteractionMode.AGENT: "交互模式 - 危险操作需要确认 / Interaction mode - Dangerous operations require confirmation",
            InteractionMode.YOLO: "自动批准模式 - 所有操作自动执行 / Auto-approve mode - All operations execute automatically",
        }
        return descriptions.get(self._mode, "未知模式 / Unknown mode")
    
    def get_mode_icon(self) -> str:
        """
        获取当前模式的图标 / Get icon of current mode
        
        Returns:
            模式图标 / Mode icon
        """
        icons = {
            InteractionMode.PLAN: "🔍",
            InteractionMode.AGENT: "🤖",
            InteractionMode.YOLO: "🚀",
        }
        return icons.get(self._mode, "❓")
    
    def get_mode_color(self) -> str:
        """
        获取当前模式的颜色 / Get color of current mode
        
        Returns:
            模式颜色（用于UI显示）/ Mode color (for UI display)
        """
        colors = {
            InteractionMode.PLAN: "blue",
            InteractionMode.AGENT: "green",
            InteractionMode.YOLO: "yellow",
        }
        return colors.get(self._mode, "white")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典 / Convert to dictionary
        
        Returns:
            包含模式信息的字典 / Dictionary containing mode info
        """
        return {
            "mode": self._mode.value,
            "auto_approve_tools": self._config.auto_approve_tools,
            "require_confirmation": self._config.require_confirmation,
            "allowed_tools": self._config.allowed_tools,
            "description": self.get_mode_description(),
            "icon": self.get_mode_icon(),
            "color": self.get_mode_color(),
        }
