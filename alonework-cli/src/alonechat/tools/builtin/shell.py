"""
Shell工具 - Shell Tool

安全的Shell命令执行工具
Safe Shell command execution tool

功能 / Features:
- 命令白名单/黑名单过滤
- 超时控制
- 输出捕获
- 工作目录指定
- 环境变量控制
"""

import subprocess
import shlex
import os
from typing import Any, Dict, Optional
from pathlib import Path

from alonechat.core.base_tool import BaseTool, ToolResult


DEFAULT_WHITELIST = [
    "ls", "cat", "grep", "find", "head", "tail", "wc", "sort", "uniq",
    "echo", "pwd", "which", "whereis", "type", "date", "whoami",
    "git", "python", "node", "npm", "pip", "cargo", "go",
]

DEFAULT_BLACKLIST = [
    "rm -rf", "rm -r", "sudo", "su", "chmod 777", "chown",
    "mkfs", "dd", "format", "del /", "rmdir /s",
    "> /dev/", "mv /*", "cp /*",
]


class ShellTool(BaseTool):
    """
    Shell命令执行工具 - Shell Command Execution Tool
    
    安全地执行Shell命令，支持白名单/黑名单过滤
    Safely execute Shell commands with whitelist/blacklist filtering
    
    属性 / Attributes:
        whitelist: 允许的命令前缀列表 / List of allowed command prefixes
        blacklist: 禁止的命令模式列表 / List of forbidden command patterns
        timeout: 默认超时时间(秒) / Default timeout in seconds
        max_output: 最大输出长度 / Maximum output length
    """
    
    name = "shell"
    description = "Execute shell commands safely. Supports whitelist/blacklist filtering and timeout control."
    category = "shell"
    permission_level = "execute"
    estimated_cost = 0.01
    
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)",
                "default": 30,
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for command execution",
            },
            "env": {
                "type": "object",
                "description": "Additional environment variables",
            },
            "capture_stderr": {
                "type": "boolean",
                "description": "Whether to capture stderr separately",
                "default": True,
            },
        },
        "required": ["command"],
    }
    
    def __init__(
        self,
        whitelist: Optional[list[str]] = None,
        blacklist: Optional[list[str]] = None,
        timeout: int = 30,
        max_output: int = 100000,
    ):
        """
        初始化Shell工具 / Initialize Shell tool
        
        Args:
            whitelist: 命令白名单 / Command whitelist
            blacklist: 命令黑名单 / Command blacklist
            timeout: 默认超时时间 / Default timeout
            max_output: 最大输出长度 / Maximum output length
        """
        self.whitelist = whitelist or DEFAULT_WHITELIST
        self.blacklist = blacklist or DEFAULT_BLACKLIST
        self.timeout = timeout
        self.max_output = max_output
    
    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        capture_stderr: bool = True,
    ) -> Dict[str, Any]:
        """
        执行Shell命令 / Execute shell command
        
        Args:
            command: 要执行的命令 / Command to execute
            timeout: 超时时间(秒) / Timeout in seconds
            cwd: 工作目录 / Working directory
            env: 额外环境变量 / Additional environment variables
            capture_stderr: 是否捕获stderr / Whether to capture stderr
        
        Returns:
            执行结果字典 / Execution result dictionary
        """
        validation_error = self._validate_command(command)
        if validation_error:
            return {
                "success": False,
                "error": validation_error,
                "stdout": "",
                "stderr": "",
                "return_code": -1,
            }
        
        actual_timeout = timeout or self.timeout
        actual_cwd = Path(cwd) if cwd else Path.cwd()
        
        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)
        
        try:
            if os.name == 'nt':
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(actual_cwd),
                    env=execution_env,
                    timeout=actual_timeout,
                    capture_output=True,
                    text=True,
                )
            else:
                try:
                    args = shlex.split(command)
                except ValueError:
                    args = command
                
                process = subprocess.run(
                    args if isinstance(args, list) else command,
                    shell=isinstance(args, str),
                    cwd=str(actual_cwd),
                    env=execution_env,
                    timeout=actual_timeout,
                    capture_output=True,
                    text=True,
                )
            
            stdout = self._truncate_output(process.stdout)
            stderr = self._truncate_output(process.stderr)
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "command": command,
                "cwd": str(actual_cwd),
                "timeout": actual_timeout,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {actual_timeout} seconds",
                "stdout": "",
                "stderr": "",
                "return_code": -1,
                "command": command,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "return_code": -1,
                "command": command,
            }
    
    def _validate_command(self, command: str) -> Optional[str]:
        """
        验证命令是否允许执行 / Validate if command is allowed
        
        Args:
            command: 要验证的命令 / Command to validate
        
        Returns:
            错误信息，None表示验证通过 / Error message, None means valid
        """
        command_lower = command.lower().strip()
        
        for pattern in self.blacklist:
            if pattern.lower() in command_lower:
                return f"Command contains forbidden pattern: {pattern}"
        
        first_word = command.split()[0] if command.split() else ""
        if first_word and self.whitelist:
            if first_word not in self.whitelist:
                return f"Command '{first_word}' is not in whitelist"
        
        return None
    
    def _truncate_output(self, output: str) -> str:
        """
        截断输出 / Truncate output
        
        Args:
            output: 原始输出 / Original output
        
        Returns:
            截断后的输出 / Truncated output
        """
        if len(output) > self.max_output:
            return output[:self.max_output] + f"\n... (truncated, {len(output)} total chars)"
        return output
    
    def is_safe_command(self, command: str) -> bool:
        """
        检查命令是否安全 / Check if command is safe
        
        Args:
            command: 要检查的命令 / Command to check
        
        Returns:
            是否安全 / Whether safe
        """
        return self._validate_command(command) is None
