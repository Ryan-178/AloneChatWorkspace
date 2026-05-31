"""
Bash 工具 / Bash Tool

执行 bash 命令
Execute bash commands
"""

import asyncio
import logging
import platform
import subprocess
from typing import Any, Dict, Optional

from ..core.tool import Tool, ToolResult, ToolUseContext, PermissionResult, ToolProgressCallback

logger = logging.getLogger(__name__)


class BashTool(Tool[Dict[str, str], str]):
    """
    Bash 工具 / Bash Tool
    
    执行 bash/shell 命令
    Execute bash/shell commands
    
    使用示例 / Usage Example:
        tool = BashTool()
        result = await tool.execute({"command": "ls -la"}, context)
    """
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return "Execute bash/shell commands"
    
    @property
    def aliases(self) -> list:
        return ["shell", "sh", "cmd"]
    
    @property
    def search_hint(self) -> str:
        return "run command shell execute terminal"
    
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for command execution"
                }
            },
            "required": ["command"]
        }
    
    async def execute(
        self,
        input_data: Dict[str, str],
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        command = input_data.get("command", "")
        timeout = input_data.get("timeout", 60)
        cwd = input_data.get("cwd")
        
        if not command:
            return ToolResult(data="", error="No command provided", is_error=True)
        
        try:
            # 确定 shell / Determine shell
            if platform.system() == "Windows":
                shell_cmd = ["cmd", "/c", command]
            else:
                shell_cmd = ["bash", "-c", command]
            
            # 执行命令 / Execute command
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    data="",
                    error=f"Command timed out after {timeout} seconds",
                    is_error=True
                )
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            if process.returncode != 0:
                return ToolResult(
                    data=stdout_str,
                    error=f"Command failed with exit code {process.returncode}: {stderr_str}",
                    is_error=True
                )
            
            return ToolResult(data=stdout_str)
            
        except Exception as e:
            logger.error(f"Bash execution failed: {e}")
            return ToolResult(data="", error=str(e), is_error=True)
    
    def is_read_only(self, input_data: Dict[str, str]) -> bool:
        # 简单的启发式判断 / Simple heuristic
        command = input_data.get("command", "").strip()
        read_only_commands = ["ls", "cat", "echo", "pwd", "whoami", "date", "grep", "find", "wc"]
        first_word = command.split()[0] if command.split() else ""
        return first_word in read_only_commands
    
    def is_destructive(self, input_data: Dict[str, str]) -> bool:
        command = input_data.get("command", "").strip()
        destructive_commands = ["rm", "rmdir", "del", "format", "mkfs", "dd"]
        first_word = command.split()[0] if command.split() else ""
        return first_word in destructive_commands
    
    async def check_permissions(
        self,
        input_data: Dict[str, str],
        context: ToolUseContext
    ) -> PermissionResult:
        # 破坏性命令需要确认 / Destructive commands need confirmation
        if self.is_destructive(input_data):
            return PermissionResult.ASK
        return PermissionResult.ALLOW
    
    def get_activity_description(self, input_data: Optional[Dict[str, str]] = None) -> Optional[str]:
        if input_data:
            command = input_data.get("command", "")
            if len(command) > 50:
                return f"Running: {command[:50]}..."
            return f"Running: {command}"
        return "Executing command"
