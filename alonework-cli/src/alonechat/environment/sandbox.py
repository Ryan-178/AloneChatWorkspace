"""
安全沙箱模块 / Security Sandbox Module

提供行动验证和安全限制
Provides action validation and security restrictions
"""

from typing import Any
from dataclasses import dataclass, field
import re

from .action_env import Action, ActionType


@dataclass
class SandboxConfig:
    """
    沙箱配置 / Sandbox Configuration
    
    定义安全限制
    Defines security restrictions
    """
    enabled: bool = True
    timeout: int = 300
    memory_limit: str = "1GB"
    allowed_paths: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /",
        "sudo",
        "chmod 777",
        "mkfs",
        "dd if=/dev/zero",
    ])
    allowed_actions: list[str] = field(default_factory=lambda: [
        "tool_call",
        "code_generate",
        "file_operation",
        "api_call",
        "communicate",
        "observe",
        "reflect",
        "plan",
        "delegate",
    ])
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
            "memory_limit": self.memory_limit,
            "allowed_paths": self.allowed_paths,
            "blocked_commands": self.blocked_commands,
            "allowed_actions": self.allowed_actions,
        }


class Sandbox:
    """
    安全沙箱 / Security Sandbox
    
    提供行动验证和安全限制
    Provides action validation and security restrictions
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化沙箱 / Initialize sandbox
        
        Args:
            config: 配置字典 / Configuration dictionary
        """
        self.config = config or {}
        
        self._config = SandboxConfig(
            enabled=self.config.get("enabled", True),
            timeout=self.config.get("timeout", 300),
            memory_limit=self.config.get("memory_limit", "1GB"),
            allowed_paths=self.config.get("allowed_paths", []),
            blocked_commands=self.config.get("blocked_commands", [
                "rm -rf /",
                "sudo",
                "chmod 777",
            ]),
            allowed_actions=self.config.get("allowed_actions", [
                "tool_call",
                "code_generate",
                "file_operation",
                "api_call",
                "communicate",
                "observe",
                "reflect",
                "plan",
                "delegate",
            ]),
        )
    
    def is_valid_action(self, action: Action) -> bool:
        """
        验证行动是否合法 / Validate if action is valid
        
        Args:
            action: 行动对象 / Action object
            
        Returns:
            是否合法 / Whether valid
        """
        if not self._config.enabled:
            return True
        
        if not self._is_action_type_allowed(action):
            return False
        
        if action.type == ActionType.FILE_OPERATION:
            if not self._is_path_allowed(action):
                return False
        
        if action.type == ActionType.CODE_EXECUTE:
            if not self._is_code_safe(action):
                return False
        
        if action.type == ActionType.TOOL_CALL:
            if not self._is_tool_allowed(action):
                return False
        
        return True
    
    def _is_action_type_allowed(self, action: Action) -> bool:
        """
        检查行动类型是否允许 / Check if action type is allowed
        
        Args:
            action: 行动对象 / Action object
            
        Returns:
            是否允许 / Whether allowed
        """
        action_type = action.type.value
        return action_type in self._config.allowed_actions
    
    def _is_path_allowed(self, action: Action) -> bool:
        """
        检查路径是否允许 / Check if path is allowed
        
        Args:
            action: 行动对象 / Action object
            
        Returns:
            是否允许 / Whether allowed
        """
        path = action.params.get("path", "")
        
        if not self._config.allowed_paths:
            return True
        
        for allowed_path in self._config.allowed_paths:
            if path.startswith(allowed_path) or allowed_path in path:
                return True
        
        return False
    
    def _is_code_safe(self, action: Action) -> bool:
        """
        检查代码是否安全 / Check if code is safe
        
        Args:
            action: 行动对象 / Action object
            
        Returns:
            是否安全 / Whether safe
        """
        code = action.params.get("code", "")
        
        for blocked in self._config.blocked_commands:
            if blocked in code:
                return False
        
        dangerous_patterns = [
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"subprocess\.call\s*\(",
            r"os\.system\s*\(",
            r"open\s*\(['\"].*['\"],\s*['\"]w['\"]",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                return False
        
        return True
    
    def _is_tool_allowed(self, action: Action) -> bool:
        """
        检查工具是否允许 / Check if tool is allowed
        
        Args:
            action: 行动对象 / Action object
            
        Returns:
            是否允许 / Whether allowed
        """
        tool_name = action.name
        
        blocked_tools = [
            "system",
            "shell",
            "execute_shell",
        ]
        
        return tool_name not in blocked_tools
    
    def validate_params(
        self,
        action: Action,
        required_params: list[str],
    ) -> tuple[bool, str | None]:
        """
        验证参数 / Validate parameters
        
        Args:
            action: 行动对象 / Action object
            required_params: 必需参数列表 / List of required parameters
            
        Returns:
            (是否有效, 错误信息) / (is_valid, error_message)
        """
        for param in required_params:
            if param not in action.params:
                return False, f"Missing required parameter: {param}"
            
            if action.params[param] is None:
                return False, f"Parameter {param} cannot be None"
        
        return True, None
    
    def sanitize_input(self, input_str: str) -> str:
        """
        清理输入 / Sanitize input
        
        Args:
            input_str: 输入字符串 / Input string
            
        Returns:
            清理后的字符串 / Sanitized string
        """
        sanitized = input_str
        
        sanitized = re.sub(r'[<>"\'&]', '', sanitized)
        
        sanitized = sanitized[:10000]
        
        return sanitized
    
    def get_timeout(self) -> int:
        """获取超时时间 / Get timeout"""
        return self._config.timeout
    
    def get_memory_limit(self) -> str:
        """获取内存限制 / Get memory limit"""
        return self._config.memory_limit
    
    def get_config(self) -> dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config.to_dict()
    
    def add_allowed_path(self, path: str) -> None:
        """
        添加允许的路径 / Add allowed path
        
        Args:
            path: 路径 / Path
        """
        if path not in self._config.allowed_paths:
            self._config.allowed_paths.append(path)
    
    def remove_allowed_path(self, path: str) -> None:
        """
        移除允许的路径 / Remove allowed path
        
        Args:
            path: 路径 / Path
        """
        if path in self._config.allowed_paths:
            self._config.allowed_paths.remove(path)
    
    def add_blocked_command(self, command: str) -> None:
        """
        添加禁止的命令 / Add blocked command
        
        Args:
            command: 命令 / Command
        """
        if command not in self._config.blocked_commands:
            self._config.blocked_commands.append(command)
