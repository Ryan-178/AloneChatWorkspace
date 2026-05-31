"""
CodeExecutionEngine - 代码执行引擎
Code execution engine that orchestrates shell, file editing, and patching.

Inspired by Codex's code-mode service and exec module:
- Session-based execution
- Tool call dispatching
- Output streaming
- Sandbox policy enforcement
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from alonechat.code.shell_tool import ShellTool, ShellConfig, ShellResult, ShellType
from alonechat.code.apply_patch import ApplyPatchTool, PatchResult


class SandboxPolicy(str, Enum):
    DANGER_FULL_ACCESS = "danger-full-access"
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"


@dataclass
class ExecutionResult:
    success: bool = False
    tool_name: str = ""
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionEvent:
    event_type: str = ""
    content: str = ""
    tool_name: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineConfig:
    working_directory: str = "."
    sandbox_policy: SandboxPolicy = SandboxPolicy.WORKSPACE_WRITE
    timeout_ms: int = 30000
    max_output_bytes: int = 1024 * 1024
    shell_config: Optional[ShellConfig] = None
    allowed_commands: List[str] = field(default_factory=list)
    denied_commands: List[str] = field(default_factory=list)
    auto_approve: bool = False


TOOL_DEFINITIONS = {
    "shell": {
        "name": "shell",
        "description": "Execute a shell command",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to execute"},
                "workdir": {"type": "string", "description": "Working directory (optional)"},
                "timeout_ms": {"type": "integer", "description": "Timeout in milliseconds (optional)"},
            },
            "required": ["command"],
        },
    },
    "apply_patch": {
        "name": "apply_patch",
        "description": "Apply a unified diff patch to files",
        "parameters": {
            "type": "object",
            "properties": {
                "patch": {"type": "string", "description": "The unified diff patch text"},
                "workdir": {"type": "string", "description": "Working directory for path resolution (optional)"},
            },
            "required": ["patch"],
        },
    },
    "file_read": {
        "name": "file_read",
        "description": "Read file contents",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "offset": {"type": "integer", "description": "Line offset (optional)"},
                "limit": {"type": "integer", "description": "Max lines to read (optional)"},
            },
            "required": ["path"],
        },
    },
    "file_write": {
        "name": "file_write",
        "description": "Write content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    "file_edit": {
        "name": "file_edit",
        "description": "Edit a file by replacing text",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_text": {"type": "string", "description": "Text to find and replace"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
}


class CodeExecutionEngine:
    """代码执行引擎 - 调度 shell、文件编辑、补丁等工具"""

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.config.working_directory = os.path.abspath(self.config.working_directory)
        self._shell = ShellTool(self.config.shell_config or ShellConfig(
            timeout_ms=self.config.timeout_ms,
            max_output_bytes=self.config.max_output_bytes,
        ))
        self._patcher = ApplyPatchTool(workdir=self.config.working_directory)
        self._event_handlers: List[Callable[[ExecutionEvent], None]] = []
        self._execution_history: List[ExecutionResult] = []

    def on_event(self, handler: Callable[[ExecutionEvent], None]) -> None:
        self._event_handlers.append(handler)

    def _emit(self, event: ExecutionEvent) -> None:
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return list(TOOL_DEFINITIONS.values())

    def _check_sandbox(self, tool_name: str, params: Dict[str, Any]) -> Optional[str]:
        if self.config.sandbox_policy == SandboxPolicy.DANGER_FULL_ACCESS:
            return None
        if tool_name == "shell":
            command = params.get("command", "")
            cmd_parts = command.split()
            if not cmd_parts:
                return None
            cmd_name = cmd_parts[0]
            if self.config.denied_commands and cmd_name in self.config.denied_commands:
                return f"Command '{cmd_name}' is denied by sandbox policy"
            if self.config.sandbox_policy == SandboxPolicy.READ_ONLY:
                write_commands = {"rm", "del", "rmdir", "mkdir", "touch", "mv", "cp", "echo", "write", "ni"}
                if cmd_name in write_commands:
                    return f"Read-only sandbox: command '{cmd_name}' is not allowed"
        return None

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> ExecutionResult:
        denial = self._check_sandbox(tool_name, params)
        if denial:
            return ExecutionResult(
                success=False,
                tool_name=tool_name,
                error=denial,
            )

        self._emit(ExecutionEvent(
            event_type="tool_start",
            tool_name=tool_name,
            content=f"Executing {tool_name}",
            metadata=params,
        ))

        start_time = time.time()
        result = ExecutionResult(tool_name=tool_name)

        try:
            if tool_name == "shell":
                result = await self._execute_shell(params)
            elif tool_name == "apply_patch":
                result = self._execute_apply_patch(params)
            elif tool_name == "file_read":
                result = self._execute_file_read(params)
            elif tool_name == "file_write":
                result = self._execute_file_write(params)
            elif tool_name == "file_edit":
                result = self._execute_file_edit(params)
            else:
                result.error = f"Unknown tool: {tool_name}"
        except Exception as e:
            result.success = False
            result.error = f"Tool execution error: {e}"

        result.duration_ms = (time.time() - start_time) * 1000
        self._execution_history.append(result)

        self._emit(ExecutionEvent(
            event_type="tool_complete",
            tool_name=tool_name,
            content=result.output if result.success else result.error,
            metadata={"success": result.success, "duration_ms": result.duration_ms},
        ))

        return result

    async def _execute_shell(self, params: Dict[str, Any]) -> ExecutionResult:
        command = params["command"]
        workdir = params.get("workdir", self.config.working_directory)
        timeout_ms = params.get("timeout_ms", self.config.timeout_ms)
        shell_result = await self._shell.execute(
            command, cwd=workdir, timeout_ms=timeout_ms
        )
        return ExecutionResult(
            success=shell_result.success,
            tool_name="shell",
            output=shell_result.stdout,
            error=shell_result.stderr,
            metadata={
                "exit_code": shell_result.exit_code,
                "timed_out": shell_result.timed_out,
                "shell_type": shell_result.shell_type.value,
            },
        )

    def _execute_apply_patch(self, params: Dict[str, Any]) -> ExecutionResult:
        patch_text = params["patch"]
        workdir = params.get("workdir", self.config.working_directory)
        patcher = ApplyPatchTool(workdir=workdir)
        patch_result = patcher.apply(patch_text)
        return ExecutionResult(
            success=patch_result.success,
            tool_name="apply_patch",
            output=patch_result.details,
            error="; ".join(patch_result.errors) if patch_result.errors else "",
            metadata={
                "applied_files": patch_result.applied_files,
                "change_count": len(patch_result.changes),
            },
        )

    def _execute_file_read(self, params: Dict[str, Any]) -> ExecutionResult:
        path = params["path"]
        if not os.path.isabs(path):
            path = os.path.join(self.config.working_directory, path)
        offset = params.get("offset", 0)
        limit = params.get("limit", 2000)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            selected = lines[offset:offset + limit]
            numbered = [f"{i + offset + 1}: {line}" for i, line in enumerate(selected)]
            return ExecutionResult(
                success=True,
                tool_name="file_read",
                output="".join(numbered),
                metadata={"total_lines": len(lines), "returned_lines": len(selected)},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                tool_name="file_read",
                error=str(e),
            )

    def _execute_file_write(self, params: Dict[str, Any]) -> ExecutionResult:
        path = params["path"]
        content = params["content"]
        if not os.path.isabs(path):
            path = os.path.join(self.config.working_directory, path)
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ExecutionResult(
                success=True,
                tool_name="file_write",
                output=f"Written {len(content)} bytes to {path}",
                metadata={"bytes_written": len(content)},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                tool_name="file_write",
                error=str(e),
            )

    def _execute_file_edit(self, params: Dict[str, Any]) -> ExecutionResult:
        path = params["path"]
        old_text = params["old_text"]
        new_text = params["new_text"]
        if not os.path.isabs(path):
            path = os.path.join(self.config.working_directory, path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count(old_text)
            if count == 0:
                return ExecutionResult(
                    success=False,
                    tool_name="file_edit",
                    error=f"Text not found in {path}",
                )
            new_content = content.replace(old_text, new_text, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return ExecutionResult(
                success=True,
                tool_name="file_edit",
                output=f"Replaced 1 occurrence in {path}",
                metadata={"occurrences_found": count},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                tool_name="file_edit",
                error=str(e),
            )

    async def execute_stream(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> AsyncGenerator[ExecutionEvent, None]:
        yield ExecutionEvent(
            event_type="tool_start",
            tool_name=tool_name,
            content=f"Starting {tool_name}",
        )
        result = await self.execute_tool(tool_name, params)
        if result.success:
            yield ExecutionEvent(
                event_type="tool_output",
                tool_name=tool_name,
                content=result.output,
                metadata=result.metadata,
            )
        else:
            yield ExecutionEvent(
                event_type="tool_error",
                tool_name=tool_name,
                content=result.error,
            )
        yield ExecutionEvent(
            event_type="tool_complete",
            tool_name=tool_name,
            content="",
            metadata={"success": result.success, "duration_ms": result.duration_ms},
        )

    def get_history(self) -> List[ExecutionResult]:
        return self._execution_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._execution_history)
        succeeded = sum(1 for r in self._execution_history if r.success)
        return {
            "total_executions": total,
            "succeeded": succeeded,
            "failed": total - succeeded,
            "shell_stats": self._shell.get_stats(),
        }
