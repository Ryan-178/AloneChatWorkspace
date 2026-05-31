import asyncio
import os
import tempfile
import sys
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

# Unix-specific modules, not available on Windows
if sys.platform != "win32":
    import resource
    import signal
else:
    resource = None
    signal = None


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False


class SubprocessSandbox:
    """
    子进程沙箱 - 安全的代码执行环境
    提供命令白名单、资源限制和路径限制
    """

    # 允许执行的命令白名单
    ALLOWED_COMMANDS = {
        "python", "python3", "node", "ruby", "perl",
        "ls", "cat", "echo", "head", "tail", "grep", "wc",
        "sort", "uniq", "cut", "tr", "sed", "awk",
        "find", "diff", "cmp", "file", "strings",
        "bc", "dc", "expr",
    }

    # 禁止执行的命令黑名单
    FORBIDDEN_COMMANDS = {
        "rm", "mv", "cp", "chmod", "chown", "sudo", "su",
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
        "pip", "pip3", "npm", "yarn", "gem", "cargo",
        "docker", "kubectl", "helm",
        "python -c", "python3 -c", "perl -e", "ruby -e",
    }

    def __init__(
        self,
        max_memory_mb: int = 128,
        max_cpu_time_seconds: int = 5,
        max_wall_time_seconds: int = 10,
        max_output_size: int = 1024 * 1024,  # 1MB
        allowed_working_dir: Optional[str] = None,
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time_seconds = max_cpu_time_seconds
        self.max_wall_time_seconds = max_wall_time_seconds
        self.max_output_size = max_output_size
        self.allowed_working_dir = allowed_working_dir or tempfile.mkdtemp(prefix="sandbox_")

        # 创建工作目录
        Path(self.allowed_working_dir).mkdir(parents=True, exist_ok=True)

    def _validate_command(self, command: List[str]) -> None:
        """验证命令是否在白名单中"""
        if not command:
            raise ValueError("Command cannot be empty")

        cmd = command[0]
        cmd_name = os.path.basename(cmd)

        # 检查是否在黑名单中
        full_cmd = " ".join(command[:2]) if len(command) > 1 else cmd
        for forbidden in self.FORBIDDEN_COMMANDS:
            if cmd_name == forbidden.split()[0] or full_cmd.startswith(forbidden):
                raise ValueError(f"Command '{forbidden}' is not allowed in sandbox")

        # 检查是否在白名单中
        if cmd_name not in self.ALLOWED_COMMANDS:
            raise ValueError(
                f"Command '{cmd_name}' is not in the allowed command whitelist. "
                f"Allowed commands: {', '.join(sorted(self.ALLOWED_COMMANDS))}"
            )

        # 检查是否包含危险参数
        dangerous_flags = {
            "-c", "--command", "-e", "--eval", "-exec",
            "--system", "--shell", "--sh",
        }
        for arg in command[1:]:
            if arg in dangerous_flags:
                raise ValueError(f"Dangerous flag '{arg}' is not allowed")

    def _setup_resource_limits(self):
        """设置资源限制（仅Unix）"""
        if resource is None:
            return
        # 限制 CPU 时间
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.max_cpu_time_seconds, self.max_cpu_time_seconds)
        )
        # 限制内存
        max_memory_bytes = self.max_memory_mb * 1024 * 1024
        resource.setrlimit(
            resource.RLIMIT_AS,
            (max_memory_bytes, max_memory_bytes)
        )
        # 限制输出文件大小
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (self.max_output_size, self.max_output_size)
        )
        # 限制子进程数量
        resource.setrlimit(
            resource.RLIMIT_NPROC,
            (10, 10)
        )
        # 限制打开文件数量
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (64, 64)
        )

    def _preexec_fn(self):
        """子进程启动前执行的函数（仅Unix）"""
        self._setup_resource_limits()
        # 切换到沙箱工作目录
        os.chdir(self.allowed_working_dir)

    async def execute(self, *command: str) -> SandboxResult:
        """
        在沙箱中执行命令
        """
        cmd_list = list(command)
        self._validate_command(cmd_list)

        try:
            # Windows doesn't support preexec_fn
            kwargs = {
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.PIPE,
                "cwd": self.allowed_working_dir,
                "env": {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": self.allowed_working_dir,
                    "TMPDIR": self.allowed_working_dir,
                },
            }
            if sys.platform != "win32":
                kwargs["preexec_fn"] = self._preexec_fn

            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(*cmd_list, **kwargs),
                timeout=self.max_wall_time_seconds,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.max_wall_time_seconds,
            )

            # 限制输出大小
            stdout_str = stdout.decode("utf-8", errors="replace")[:self.max_output_size]
            stderr_str = stderr.decode("utf-8", errors="replace")[:self.max_output_size]

            return SandboxResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=proc.returncode,
                timed_out=False,
            )

        except asyncio.TimeoutError:
            # 尝试终止进程
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            return SandboxResult(
                stdout="",
                stderr="Execution timed out",
                return_code=-1,
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                return_code=-1,
            )

    async def execute_python(self, code: str) -> SandboxResult:
        """
        安全地执行 Python 代码
        使用受限的 Python 解释器
        """
        # 检查代码中是否包含危险导入
        dangerous_imports = [
            "os", "sys", "subprocess", "socket", "urllib", "http",
            "ftplib", "telnetlib", "smtplib", "poplib", "imaplib",
            "shutil", "pathlib", "tempfile", "multiprocessing",
            "threading", "ctypes", "mmap", "pickle", "marshal",
            "compile", "exec", "eval", "__import__", "__builtins__",
        ]
        code_lower = code.lower()
        for imp in dangerous_imports:
            if f"import {imp}" in code_lower or f"from {imp}" in code_lower:
                return SandboxResult(
                    stdout="",
                    stderr=f"Import '{imp}' is not allowed in sandbox",
                    return_code=-1,
                )

        # 将代码写入临时文件
        code_file = Path(self.allowed_working_dir) / f"script_{os.urandom(8).hex()}.py"
        code_file.write_text(code, encoding="utf-8")

        try:
            result = await self.execute("python3", "-u", str(code_file))
        finally:
            # 清理临时文件
            try:
                code_file.unlink()
            except OSError:
                pass

        return result
