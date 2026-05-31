"""
Enhanced sandbox with project folder isolation, file permission control, command whitelist
Loads configuration from YAML, supports MTC/CODE modes, wildcard command patterns
Production-ready with cross-platform support (Windows/Linux/macOS)
"""
from __future__ import annotations
import asyncio
import os
import platform
import tempfile
import shlex
from typing import List, Optional, Set, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from agent_framework.core.types import FilePermission, AgentMode
from agent_framework.configs import get_sandbox_config


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    timed_out: bool = False
    permission_denied: bool = False


def _load_sandbox_config():
    return get_sandbox_config()


def _get_platform() -> str:
    return platform.system().lower()


class EnhancedSandbox:
    """
    Enhanced sandbox with project folder isolation and permission control
    Supports MTC (non-developer) and CODE (developer) modes
    Cross-platform: Windows, Linux, macOS
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
        max_memory_mb: Optional[int] = None,
        max_cpu_time_seconds: Optional[int] = None,
        max_wall_time_seconds: Optional[int] = None,
        max_output_size: Optional[int] = None,
        allowed_commands: Optional[Set[str]] = None,
        allowed_permissions: Optional[Set[FilePermission]] = None,
    ):
        config = _load_sandbox_config()

        self.mode = mode
        self.project_folder = project_folder or tempfile.mkdtemp(prefix=f"sandbox_{mode.value}_")
        self.platform = _get_platform()

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

        self.allowed_command_patterns: Set[str] = set(config.default_config.get("allowed_patterns", []))

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
        path = Path(folder).resolve()
        path.mkdir(parents=True, exist_ok=True)
        self.project_folder = str(path)

    def validate_path(self, file_path: str) -> bool:
        try:
            path = Path(file_path).resolve()
            project_path = Path(self.project_folder).resolve()

            try:
                path.relative_to(project_path)
                return True
            except ValueError:
                return False
        except Exception:
            return False

    def check_permission(self, permission: FilePermission) -> bool:
        return permission in self.allowed_permissions

    def set_command_whitelist(self, commands: Set[str]) -> None:
        self.allowed_commands = commands - self.FORBIDDEN_COMMANDS

    def _match_command_pattern(self, cmd_name: str, full_command: str) -> bool:
        import fnmatch
        for pattern in self.allowed_command_patterns:
            if fnmatch.fnmatch(full_command, pattern):
                return True
            if fnmatch.fnmatch(cmd_name, pattern):
                return True
        return False

    def validate_command(self, command: List[str]) -> Tuple[bool, str]:
        if not command:
            return False, "Empty command"

        cmd = command[0]
        cmd_name = os.path.basename(cmd)

        full_command_str = " ".join(shlex.quote(c) if ' ' in c else c for c in command)

        for forbidden in self.FORBIDDEN_COMMANDS:
            if cmd_name == forbidden or cmd_name.startswith(forbidden):
                return False, f"Forbidden command: {forbidden}"

        if cmd_name in self.allowed_commands:
            pass
        elif self._match_command_pattern(cmd_name, full_command_str):
            pass
        else:
            allowed_list = ', '.join(sorted(self.allowed_commands))
            return False, f"Command '{cmd_name}' not in whitelist. Allowed: {allowed_list}"

        for arg in command[1:]:
            if arg in self.dangerous_flags:
                return False, f"Dangerous flag: {arg}"

        return True, ""

    def set_resource_limits(self, memory_mb: int, cpu_seconds: int) -> None:
        self.max_memory_mb = memory_mb
        self.max_cpu_time_seconds = cpu_seconds

    async def execute_with_timeout(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        timeout = timeout or self.max_wall_time_seconds

        is_valid, error_msg = self.validate_command(command)
        if not is_valid:
            return SandboxResult(
                stderr=error_msg,
                permission_denied=True,
            )

        exec_env = {}
        for k, v in self.default_env.items():
            resolved = v.replace("{project_folder}", self.project_folder)
            exec_env[k] = resolved
        if env:
            exec_env.update(env)

        try:
            creation_flags = 0
            if self.platform == "windows":
                creation_flags = 0x08000000

            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_folder,
                    env=exec_env,
                    creationflags=creation_flags,
                ),
                timeout=min(5, timeout),
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
                return_code=proc.returncode or 0,
                timed_out=False,
            )

        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return SandboxResult(
                stderr=f"Execution timeout ({timeout}s)",
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(
                stderr=f"Execution error: {str(e)}",
            )

    def read_file(self, file_path: str) -> Tuple[bool, str]:
        if not self.validate_path(file_path):
            return False, f"Path outside project folder: {file_path}"

        if not self.check_permission(FilePermission.READ):
            return False, "No read permission"

        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"File not found: {file_path}"

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return True, content
        except Exception as e:
            return False, str(e)

    def write_file(self, file_path: str, content: str) -> Tuple[bool, str]:
        if not self.validate_path(file_path):
            return False, f"Path outside project folder: {file_path}"

        if not self.check_permission(FilePermission.WRITE):
            return False, "No write permission"

        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return True, str(path)
        except Exception as e:
            return False, str(e)

    def list_files(self, directory: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
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
        return self._execution_history

    def clear_history(self) -> None:
        self._execution_history = []

    def get_sandbox_info(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "platform": self.platform,
            "project_folder": self.project_folder,
            "allowed_commands": list(self.allowed_commands),
            "allowed_permissions": [p.value for p in self.allowed_permissions],
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_time_seconds": self.max_cpu_time_seconds,
            "max_wall_time_seconds": self.max_wall_time_seconds,
            "execution_count": len(self._execution_history),
        }


def create_mtc_sandbox(project_folder: Optional[str] = None) -> EnhancedSandbox:
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
    EnhancedSandbox._config = get_sandbox_config().reload()
