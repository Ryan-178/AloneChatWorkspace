"""
增强沙箱环境 - Enhanced Sandbox
支持项目文件夹隔离、文件权限控制、命令白名单等
从配置文件加载，替代硬编码
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
from agent_framework.configs import get_sandbox_config


class SandboxResult:
    """沙箱执行结果"""
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False
    permission_denied: bool = False


def _load_sandbox_config():
    """加载沙箱配置"""
    return get_sandbox_config()


class EnhancedSandbox:
    """
    增强沙箱 - 支持项目文件夹隔离和权限控制
    """

    _config = _load_sandbox_config()
    
    DEFAULT_ALLOWED_COMMANDS = _config.get_mtc_allowed_commands()
    
    MTC_ALLOWED_COMMANDS = _config.get_mtc_allowed_commands()
    
    CODE_ALLOWED_COMMANDS = _config.get_code_allowed_commands()
    
    FORBIDDEN_COMMANDS = set(_config.forbidden_commands)
    
    def __init__(
        self,
        mode: AgentMode = AgentMode.MTC,
        project_folder: Optional[str] = None,
        max_memory_mb: int = None,
        max_cpu_time_seconds: int = None,
        max_wall_time_seconds: int = None,
        max_output_size: int = None,
        allowed_commands: Optional[Set[str]] = None,
        allowed_permissions: Optional[Set[FilePermission]] = None,
    ):
        config = _load_sandbox_config()
        
        self.mode = mode
        self.project_folder = project_folder or tempfile.mkdtemp(prefix=f"sandbox_{mode.value}_")
        
        mtc_cfg = config.mtc_config
        code_cfg = config.code_config
        
        if max_memory_mb is None:
            self.max_memory_mb = mtc_cfg.get("max_memory_mb", 256) if mode == AgentMode.MTC else code_cfg.get("max_memory_mb", 512)
        else:
            self.max_memory_mb = max_memory_mb
            
        if max_cpu_time_seconds is None:
            self.max_cpu_time_seconds = mtc_cfg.get("max_cpu_time_seconds", 15) if mode == AgentMode.MTC else code_cfg.get("max_cpu_time_seconds", 30)
        else:
            self.max_cpu_time_seconds = max_cpu_time_seconds
            
        if max_wall_time_seconds is None:
            self.max_wall_time_seconds = mtc_cfg.get("max_wall_time_seconds", 30) if mode == AgentMode.MTC else code_cfg.get("max_wall_time_seconds", 60)
        else:
            self.max_wall_time_seconds = max_wall_time_seconds
            
        if max_output_size is None:
            self.max_output_size = mtc_cfg.get("max_output_size", 10485760) if mode == AgentMode.MTC else code_cfg.get("max_output_size", 10485760)
        else:
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
            self.allowed_permissions = config.get_code_permissions()
        else:
            self.allowed_permissions = config.get_mtc_permissions()
        
        self.dangerous_flags = set(config.dangerous_flags)
        self.default_env = config.default_env
        
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
        
        for arg in command[1:]:
            if arg in self.dangerous_flags:
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
        
        exec_env = dict(self.default_env)
        exec_env["HOME"] = self.project_folder
        exec_env["TMPDIR"] = self.project_folder
        if env:
            exec_env.update(env)
        
        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_folder,
                    env=exec_env,
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
    config = _load_sandbox_config()
    mtc_cfg = config.mtc_config
    
    return EnhancedSandbox(
        mode=AgentMode.MTC,
        project_folder=project_folder,
        max_memory_mb=mtc_cfg.get("max_memory_mb", 256),
        max_cpu_time_seconds=mtc_cfg.get("max_cpu_time_seconds", 15),
        max_wall_time_seconds=mtc_cfg.get("max_wall_time_seconds", 30),
        allowed_permissions=config.get_mtc_permissions(),
    )


def create_code_sandbox(project_folder: Optional[str] = None) -> EnhancedSandbox:
    """创建CODE模式沙箱"""
    config = _load_sandbox_config()
    code_cfg = config.code_config
    
    return EnhancedSandbox(
        mode=AgentMode.CODE,
        project_folder=project_folder,
        max_memory_mb=code_cfg.get("max_memory_mb", 512),
        max_cpu_time_seconds=code_cfg.get("max_cpu_time_seconds", 30),
        max_wall_time_seconds=code_cfg.get("max_wall_time_seconds", 60),
        allowed_permissions=config.get_code_permissions(),
    )


def reload_sandbox_config():
    """重新加载沙箱配置"""
    global EnhancedSandbox
    EnhancedSandbox._config = get_sandbox_config().reload()
