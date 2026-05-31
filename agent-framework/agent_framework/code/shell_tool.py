"""
ShellTool - 跨平台 Shell 命令执行工具
Cross-platform shell command execution tool.

Based on Codex's shell.rs pattern:
- Shell type detection (PowerShell, Cmd, Bash, Sh, Zsh)
- Command argument derivation per shell type
- Output capture with timeout
- CWD management
"""

import asyncio
import os
import platform
import shutil
import signal
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ShellType(str, Enum):
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"
    SH = "sh"
    ZSH = "zsh"


@dataclass
class ShellResult:
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: float = 0.0
    command: str = ""
    shell_type: ShellType = ShellType.CMD
    timed_out: bool = False
    truncated: bool = False


@dataclass
class ShellConfig:
    shell_type: Optional[ShellType] = None
    shell_path: Optional[str] = None
    timeout_ms: int = 30000
    max_output_bytes: int = 1024 * 1024
    use_login_shell: bool = False
    env: Optional[Dict[str, str]] = None


def detect_shell() -> Tuple[ShellType, str]:
    system = platform.system().lower()
    if system == "windows":
        pwsh = shutil.which("pwsh")
        if pwsh:
            return ShellType.POWERSHELL, pwsh
        powershell = shutil.which("powershell")
        if powershell:
            return ShellType.POWERSHELL, powershell
        return ShellType.CMD, "cmd.exe"
    else:
        zsh = shutil.which("zsh")
        if zsh:
            return ShellType.ZSH, zsh
        bash = shutil.which("bash")
        if bash:
            return ShellType.BASH, bash
        return ShellType.SH, "/bin/sh"


def derive_exec_args(
    shell_type: ShellType,
    shell_path: str,
    command: str,
    use_login_shell: bool = False,
) -> List[str]:
    if shell_type in (ShellType.ZSH, ShellType.BASH, ShellType.SH):
        arg = "-lc" if use_login_shell else "-c"
        return [shell_path, arg, command]
    elif shell_type == ShellType.POWERSHELL:
        args = [shell_path]
        if not use_login_shell:
            args.append("-NoProfile")
        args.extend(["-Command", command])
        return args
    elif shell_type == ShellType.CMD:
        return [shell_path, "/c", command]
    return [shell_path, "-c", command]


class ShellTool:
    """跨平台 Shell 命令执行工具"""

    def __init__(self, config: Optional[ShellConfig] = None):
        self.config = config or ShellConfig()
        if self.config.shell_type is None or self.config.shell_path is None:
            detected_type, detected_path = detect_shell()
            if self.config.shell_type is None:
                self.config.shell_type = detected_type
            if self.config.shell_path is None:
                self.config.shell_path = detected_path
        self._command_history: List[ShellResult] = []

    @property
    def shell_type(self) -> ShellType:
        return self.config.shell_type

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ShellResult:
        exec_args = derive_exec_args(
            self.config.shell_type,
            self.config.shell_path,
            command,
            self.config.use_login_shell,
        )
        exec_env = os.environ.copy()
        if self.config.env:
            exec_env.update(self.config.env)
        if env:
            exec_env.update(env)
        timeout_sec = (timeout_ms or self.config.timeout_ms) / 1000.0
        result = ShellResult(
            command=command,
            shell_type=self.config.shell_type,
        )
        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *exec_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=exec_env,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec,
                )
            except asyncio.TimeoutError:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except (asyncio.TimeoutError, ProcessLookupError):
                    process.kill()
                result.timed_out = True
                result.success = False
                result.exit_code = 124
                result.duration_ms = (time.time() - start_time) * 1000
                self._command_history.append(result)
                return result
            result.exit_code = process.returncode or 0
            result.success = process.returncode == 0
            max_bytes = self.config.max_output_bytes
            result.stdout = stdout_bytes.decode("utf-8", errors="replace")
            result.stderr = stderr_bytes.decode("utf-8", errors="replace")
            if len(result.stdout) > max_bytes:
                result.stdout = result.stdout[:max_bytes] + "\n... [truncated]"
                result.truncated = True
            if len(result.stderr) > max_bytes:
                result.stderr = result.stderr[:max_bytes] + "\n... [truncated]"
                result.truncated = True
        except FileNotFoundError:
            result.success = False
            result.exit_code = 127
            result.stderr = f"Shell not found: {self.config.shell_path}"
        except Exception as e:
            result.success = False
            result.exit_code = 1
            result.stderr = f"Execution error: {e}"
        result.duration_ms = (time.time() - start_time) * 1000
        self._command_history.append(result)
        return result

    async def execute_script(
        self,
        script: str,
        cwd: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> ShellResult:
        if self.config.shell_type == ShellType.POWERSHELL:
            return await self.execute(
                script, cwd=cwd, timeout_ms=timeout_ms
            )
        return await self.execute(script, cwd=cwd, timeout_ms=timeout_ms)

    def get_history(self) -> List[ShellResult]:
        return self._command_history.copy()

    def clear_history(self) -> None:
        self._command_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._command_history)
        succeeded = sum(1 for r in self._command_history if r.success)
        failed = total - succeeded
        avg_duration = (
            sum(r.duration_ms for r in self._command_history) / total
            if total > 0
            else 0.0
        )
        return {
            "total_commands": total,
            "succeeded": succeeded,
            "failed": failed,
            "avg_duration_ms": avg_duration,
            "shell_type": self.config.shell_type.value,
        }
