import subprocess
import tempfile
import os
import time
from typing import Any, Dict, List, Optional

from agent_framework.core.base_tool import ToolResult


class SubprocessSandbox:
    def __init__(
        self,
        timeout_seconds: int = 30,
        memory_limit_mb: Optional[int] = None,
        network_access: bool = False,
        allowed_commands: Optional[List[str]] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.network_access = network_access
        self.allowed_commands = set(allowed_commands) if allowed_commands else None

    def run(self, command: List[str], env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None) -> ToolResult:
        if self.allowed_commands is not None:
            cmd_name = command[0] if command else ""
            if cmd_name not in self.allowed_commands:
                return ToolResult(
                    success=False,
                    error=f"Command '{cmd_name}' is not in the allowed commands list",
                )

        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        if not self.network_access:
            run_env["HTTP_PROXY"] = ""
            run_env["HTTPS_PROXY"] = ""
            run_env["http_proxy"] = ""
            run_env["https_proxy"] = ""

        start = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=run_env,
                cwd=cwd,
            )
            execution_time_ms = (time.time() - start) * 1000
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={"stdout": result.stdout, "stderr": result.stderr},
                    execution_time_ms=execution_time_ms,
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Exit code {result.returncode}: {result.stderr}",
                    data={"stdout": result.stdout, "stderr": result.stderr},
                    execution_time_ms=execution_time_ms,
                )
        except subprocess.TimeoutExpired:
            execution_time_ms = (time.time() - start) * 1000
            return ToolResult(
                success=False,
                error=f"Command timed out after {self.timeout_seconds} seconds",
                execution_time_ms=execution_time_ms,
            )
        except Exception as e:
            execution_time_ms = (time.time() - start) * 1000
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
