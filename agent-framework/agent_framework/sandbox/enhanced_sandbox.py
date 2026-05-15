"""
增强沙箱环境 - Enhanced Sandbox
支持项目文件夹隔离、文件权限控制、命令白名单等
"""
import asyncio
import os
import tempfile
import signal
from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from agent_framework.core.types import FilePermission, AgentMode


class SandboxResult:
    """沙箱执行结果"""
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False
    permission_denied: bool = False


class EnhancedSandbox:
    """
    增强沙箱 - 支持项目文件夹隔离和权限控制
    """
    
    DEFAULT_ALLOWED_COMMANDS = {
        "python", "python3", "node", "ruby", "perl",
        "ls", "cat", "echo", "head", "tail", "grep", "wc",
        "sort", "uniq", "cut", "tr", "sed", "awk",
        "find", "diff", "cmp", "file", "strings",
        "bc", "dc", "expr",
    }
    
    MTC_ALLOWED_COMMANDS = {
        "python", "python3",
        "ls", "cat", "echo", "head", "tail", "grep", "wc",
        "sort", "uniq", "cut", "tr",
    }
    
    CODE_ALLOWED_COMMANDS = {
        "python", "python3", "node", "npm", "npx", "yarn",
        "git", "pip", "pip3",
        "ls", "cat", "echo", "head", "tail", "grep", "wc",
        "sort", "uniq", "cut", "tr", "sed", "awk",
        "find", "diff", "cmp", "file",
        "make", "cmake",
        "pytest", "unittest",
        "ruff", "black", "mypy", "flake8",
    }
    
    FORBIDDEN_COMMANDS = {
        "rm", "mv", "chmod", "chown", "sudo", "su",
        "wget", "curl", "nc", "netcat", "telnet", "ssh", "scp",
        "bash", "sh", "zsh", "csh", "tcsh", "fish",
        "mkfs", "fdisk", "dd", "mount", "umount",
        "kill", "pkill", "killall",
        "reboot", "shutdown", "halt", "poweroff",
        "crontab", "at", "batch",
        "iptables", "nft", "ufw",
        "useradd", "userdel", "usermod", "groupadd", "groupdel",
        "passwd", "chpasswd",
        "apt", "apt-get", "yum", "dnf", "pacman", "brew",
        "docker", "kubectl", "helm",
    }
    
    def __init__(
        self,
        mode: AgentMode = AgentMode.MTC,
        project_folder: Optional[str] = None,
        max_memory_mb: int = 512,
        max_cpu_time_seconds: int = 30,
        max_wall_time_seconds: int = 60,
        max_output_size: int = 10 * 1024 * 1024,
        allowed_commands: Optional[Set[str]] = None,
        allowed_permissions: Optional[Set[FilePermission]] = None,
    ):
        self.mode = mode
        self.project_folder = project_folder or tempfile.mkdtemp(prefix=f"sandbox_{mode.value}_")
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time_seconds = max_cpu_time_seconds
        self.max_wall_time_seconds = max_wall_time_seconds
        self.max_output_size = max_output_size
        
        if allowed_commands:
            self.allowed_commands = allowed_commands
        elif mode == AgentMode.CODE:
            self.allowed_commands = self.CODE_ALLOWED_COMMANDS
        else:
            self.allowed_commands = self.MTC_ALLOWED_COMMANDS
        
        if allowed_permissions:
            self.allowed_permissions = allowed_permissions
        elif mode == AgentMode.CODE:
            self.allowed_permissions = {FilePermission.READ, FilePermission.WRITE, FilePermission.EXECUTE}
        else:
            self.allowed_permissions = {FilePermission.READ, FilePermission.WRITE}
        
        Path(self.project_folder).mkdir(parents=True, exist_ok=True)
        
        self._execution_history: List[Dict[str, Any]] = []
    
    def set_project_folder(self, folder: str) -> None:
        """设置项目文件夹隔离"""
        path = Path(folder).resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.project_folder = str(path)
    
    def validate_path(self, file_path: str) -> bool:
        """验证文件路径安全性（防止路径遍历攻击）"""
        try:
            path = Path(file_path).resolve()
            project_path = Path(self.project_folder).resolve()
            
            if ".." in str(path):
                return False
            
            try:
                path.relative_to(project_path)
                return True
            except ValueError:
                return False
        except Exception:
            return False
    
    def check_permission(self, permission: FilePermission) -> bool:
        """检查文件操作权限"""
        return permission in self.allowed_permissions
    
    def set_command_whitelist(self, commands: Set[str]) -> None:
        """设置命令白名单"""
        self.allowed_commands = commands - self.FORBIDDEN_COMMANDS
    
    def validate_command(self, command: List[str]) -> tuple[bool, str]:
        """验证命令是否在白名单"""
        if not command:
            return False, "命令为空"
        
        cmd = command[0]
        cmd_name = os.path.basename(cmd)
        
        for forbidden in self.FORBIDDEN_COMMANDS:
            if cmd_name == forbidden or cmd_name.startswith(forbidden):
                return False, f"禁止执行的命令: {forbidden}"
        
        if cmd_name not in self.allowed_commands:
            return False, f"命令 '{cmd_name}' 不在白名单中。允许的命令: {', '.join(sorted(self.allowed_commands))}"
        
        dangerous_flags = {
            "-c", "--command", "-e", "--eval", "-exec",
            "--system", "--shell", "--sh",
        }
        for arg in command[1:]:
            if arg in dangerous_flags:
                return False, f"禁止使用的参数: {arg}"
        
        return True, ""
    
    def set_resource_limits(self, memory_mb: int, cpu_seconds: int) -> None:
        """设置资源限制"""
        self.max_memory_mb = memory_mb
        self.max_cpu_time_seconds = cpu_seconds
    
    async def execute_with_timeout(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """带超时的执行"""
        timeout = timeout or self.max_wall_time_seconds
        
        is_valid, error_msg = self.validate_command(command)
        if not is_valid:
            return SandboxResult(
                stdout="",
                stderr=error_msg,
                return_code=-1,
                permission_denied=True,
            )
        
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_folder,
                    env=env or {
                        "PATH": "/usr/bin:/bin",
                        "HOME": self.project_folder,
                        "TMPDIR": self.project_folder,
                    },
                ),
                timeout=5,
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            
            stdout_str = stdout.decode("utf-8", errors="replace")[:self.max_output_size]
            stderr_str = stderr.decode("utf-8", errors="replace")[:self.max_output_size]
            
            self._execution_history.append({
                "command": " ".join(command),
                "return_code": proc.returncode,
                "success": proc.returncode == 0,
            })
            
            return SandboxResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=proc.returncode,
                timed_out=False,
            )
        
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return SandboxResult(
                stdout="",
                stderr=f"执行超时 ({timeout}秒)",
                return_code=-1,
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=f"执行错误: {str(e)}",
                return_code=-1,
            )
    
    def read_file(self, file_path: str) -> tuple[bool, str]:
        """安全读取文件"""
        if not self.validate_path(file_path):
            return False, f"路径不在项目文件夹内: {file_path}"
        
        if not self.check_permission(FilePermission.READ):
            return False, "没有读取权限"
        
        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return True, content
        except Exception as e:
            return False, str(e)
    
    def write_file(self, file_path: str, content: str) -> tuple[bool, str]:
        """安全写入文件"""
        if not self.validate_path(file_path):
            return False, f"路径不在项目文件夹内: {file_path}"
        
        if not self.check_permission(FilePermission.WRITE):
            return False, "没有写入权限"
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return True, str(path)
        except Exception as e:
            return False, str(e)
    
    def list_files(self, directory: Optional[str] = None) -> tuple[bool, List[Dict[str, Any]]]:
        """列出文件"""
        dir_path = directory or self.project_folder
        
        if not self.validate_path(dir_path):
            return False, []
        
        try:
            path = Path(dir_path)
            if not path.exists():
                return False, []
            
            files = []
            for f in path.iterdir():
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "is_dir": f.is_dir(),
                    "size": f.stat().st_size if f.is_file() else 0,
                })
            
            return True, files
        except Exception:
            return False, []
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self._execution_history
    
    def clear_history(self) -> None:
        """清空执行历史"""
        self._execution_history = []
    
    def get_sandbox_info(self) -> Dict[str, Any]:
        """获取沙箱信息"""
        return {
            "mode": self.mode.value,
            "project_folder": self.project_folder,
            "allowed_commands": list(self.allowed_commands),
            "allowed_permissions": [p.value for p in self.allowed_permissions],
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_time_seconds": self.max_cpu_time_seconds,
            "max_wall_time_seconds": self.max_wall_time_seconds,
        }


def create_mtc_sandbox(project_folder: Optional[str] = None) -> EnhancedSandbox:
    """创建MTC模式沙箱"""
    return EnhancedSandbox(
        mode=AgentMode.MTC,
        project_folder=project_folder,
        max_memory_mb=256,
        max_cpu_time_seconds=15,
        max_wall_time_seconds=30,
        allowed_permissions={FilePermission.READ, FilePermission.WRITE},
    )


def create_code_sandbox(project_folder: Optional[str] = None) -> EnhancedSandbox:
    """创建CODE模式沙箱"""
    return EnhancedSandbox(
        mode=AgentMode.CODE,
        project_folder=project_folder,
        max_memory_mb=512,
        max_cpu_time_seconds=30,
        max_wall_time_seconds=60,
        allowed_permissions={FilePermission.READ, FilePermission.WRITE, FilePermission.EXECUTE},
    )
