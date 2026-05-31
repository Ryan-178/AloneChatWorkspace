"""
CLI LSP集成 / CLI LSP Integration

集成LSP诊断到CLI环境
Integrates LSP diagnostics into CLI environment
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
logger = logging.getLogger(__name__)


class CLILSPIntegration:
    """
    CLI LSP集成 / CLI LSP Integration

    管理LSP诊断在CLI中的显示和交互
    Manages LSP diagnostics display and interaction in CLI
    """

    def __init__(self, root_path: Optional[str] = None):
        self._root_path = root_path
        self._diagnostics: Dict[str, List[Any]] = {}
        self._on_diagnostics_callback: Optional[Callable] = None
        self._enabled = True

    async def initialize(self, root_path: str) -> bool:
        """
        初始化LSP集成 / Initialize LSP integration
        """
        self._root_path = root_path
        try:
            from alonechat.lsp import LSPManager

            config_path = str(
                Path(__file__).parent.parent.parent.parent
                / "agent-framework"
                / "agent_framework"
                / "configs"
                / "lsp.yaml"
            )
            self._manager = LSPManager(config_path)
            await self._manager.start(root_path)
            self._manager.add_diagnostics_handler(self._on_diagnostics)
            return True
        except ImportError:
            logger.warning("alonechat.lsp not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize LSP: {e}")
            return False

    async def shutdown(self) -> None:
        """
        关闭LSP集成 / Shutdown LSP integration
        """
        if hasattr(self, "_manager"):
            await self._manager.stop()

    async def open_file(self, file_path: str) -> None:
        """
        打开文件进行诊断 / Open file for diagnostics
        """
        if not self._enabled or not hasattr(self, "_manager"):
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8")
            await self._manager.open_document(file_path, content)
        except Exception as e:
            logger.warning(f"Failed to open file for LSP: {e}")

    async def update_file(self, file_path: str, content: str, version: int = 1) -> None:
        """
        更新文件内容 / Update file content
        """
        if not self._enabled or not hasattr(self, "_manager"):
            return

        try:
            await self._manager.change_document(file_path, version, content)
        except Exception as e:
            logger.warning(f"Failed to update file for LSP: {e}")

    async def close_file(self, file_path: str) -> None:
        """
        关闭文件 / Close file
        """
        if not self._enabled or not hasattr(self, "_manager"):
            return

        try:
            await self._manager.close_document(file_path)
        except Exception as e:
            logger.warning(f"Failed to close file for LSP: {e}")

    def _on_diagnostics(self, language: str, uri: str, diagnostics: List[Any]) -> None:
        """
        处理诊断结果 / Handle diagnostics
        """
        self._diagnostics[uri] = diagnostics

        if self._on_diagnostics_callback:
            try:
                self._on_diagnostics_callback(uri, diagnostics)
            except Exception as e:
                logger.error(f"Error in diagnostics callback: {e}")

    def set_diagnostics_callback(self, callback: Callable) -> None:
        """
        设置诊断回调 / Set diagnostics callback
        """
        self._on_diagnostics_callback = callback

    def get_diagnostics(self, file_path: str) -> List[Any]:
        """
        获取文件诊断结果 / Get file diagnostics
        """
        uri = Path(file_path).as_uri()
        return self._diagnostics.get(uri, [])

    def get_all_diagnostics(self) -> Dict[str, List[Any]]:
        """
        获取所有诊断结果 / Get all diagnostics
        """
        return self._diagnostics.copy()

    def get_summary(self) -> Dict[str, int]:
        """
        获取诊断摘要 / Get diagnostics summary
        """
        errors = 0
        warnings = 0
        info = 0
        hints = 0

        for diagnostics in self._diagnostics.values():
            for d in diagnostics:
                severity = getattr(d, "severity", None)
                if severity:
                    if severity.value == 1:
                        errors += 1
                    elif severity.value == 2:
                        warnings += 1
                    elif severity.value == 3:
                        info += 1
                    else:
                        hints += 1

        return {
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "hints": hints,
            "total": errors + warnings + info + hints,
        }

    @property
    def is_enabled(self) -> bool:
        """检查是否启用 / Check if enabled"""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态 / Set enabled state"""
        self._enabled = enabled


def display_diagnostics(
    file_path: str,
    diagnostics: List[Any],
    show_details: bool = True,
) -> None:
    """
    显示诊断结果 / Display diagnostics
    """
    if not diagnostics:
        console.print(f"[green]✓[/green] {file_path} - 没有问题")
        return

    errors = []
    warnings = []
    info = []
    hints = []

    for d in diagnostics:
        severity = getattr(d, "severity", None)
        if severity:
            if severity.value == 1:
                errors.append(d)
            elif severity.value == 2:
                warnings.append(d)
            elif severity.value == 3:
                info.append(d)
            else:
                hints.append(d)

    total = len(diagnostics)
    summary = f"[red]{len(errors)} 错误[/red], [yellow]{len(warnings)} 警告[/yellow], [blue]{len(info)} 信息[/blue], [dim]{len(hints)} 提示[/dim]"

    console.print(f"\n[bold]{file_path}[/bold] ({total} 问题)")
    console.print(summary)

    if show_details:
        table = Table(show_header=True, header_style="bold")
        table.add_column("行", style="cyan", width=6)
        table.add_column("列", style="cyan", width=6)
        table.add_column("类型", width=8)
        table.add_column("消息")

        for d in diagnostics:
            range_obj = getattr(d, "range", None)
            if range_obj:
                line = range_obj.start.line + 1
                col = range_obj.start.character + 1
            else:
                line = 1
                col = 1

            severity = getattr(d, "severity", None)
            if severity:
                if severity.value == 1:
                    severity_str = "[red]错误[/red]"
                elif severity.value == 2:
                    severity_str = "[yellow]警告[/yellow]"
                elif severity.value == 3:
                    severity_str = "[blue]信息[/blue]"
                else:
                    severity_str = "[dim]提示[/dim]"
            else:
                severity_str = "[red]错误[/red]"

            message = getattr(d, "message", str(d))
            source = getattr(d, "source", None)
            if source:
                message = f"[{source}] {message}"

            table.add_row(str(line), str(col), severity_str, message)

        console.print(table)


def display_diagnostics_summary(diagnostics_by_file: Dict[str, List[Any]]) -> None:
    """
    显示诊断摘要 / Display diagnostics summary
    """
    total_errors = 0
    total_warnings = 0
    total_info = 0
    total_hints = 0

    for diagnostics in diagnostics_by_file.values():
        for d in diagnostics:
            severity = getattr(d, "severity", None)
            if severity:
                if severity.value == 1:
                    total_errors += 1
                elif severity.value == 2:
                    total_warnings += 1
                elif severity.value == 3:
                    total_info += 1
                else:
                    total_hints += 1

    total = total_errors + total_warnings + total_info + total_hints

    if total == 0:
        console.print(Panel(
            "[green]✓ 没有发现问题[/green]",
            title="诊断摘要",
            border_style="green",
        ))
        return

    content = Text()
    content.append(f"共 {total} 个问题\n\n", style="bold")
    content.append(f"  错误: {total_errors}\n", style="red")
    content.append(f"  警告: {total_warnings}\n", style="yellow")
    content.append(f"  信息: {total_info}\n", style="blue")
    content.append(f"  提示: {total_hints}", style="dim")

    console.print(Panel(content, title="诊断摘要", border_style="yellow" if total_errors > 0 else "green"))


def format_diagnostic_for_context(diagnostics: List[Any]) -> str:
    """
    格式化诊断结果用于上下文注入 / Format diagnostics for context injection
    """
    if not diagnostics:
        return ""

    lines = ["当前文件存在以下问题："]

    for d in diagnostics[:10]:
        range_obj = getattr(d, "range", None)
        if range_obj:
            line = range_obj.start.line + 1
            col = range_obj.start.character + 1
        else:
            line = 1
            col = 1

        severity = getattr(d, "severity", None)
        if severity:
            severity_str = severity.to_str()
        else:
            severity_str = "error"

        message = getattr(d, "message", str(d))
        source = getattr(d, "source", None)
        if source:
            lines.append(f"  - 第{line}行第{col}列 [{severity_str}] [{source}]: {message}")
        else:
            lines.append(f"  - 第{line}行第{col}列 [{severity_str}]: {message}")

    if len(diagnostics) > 10:
        lines.append(f"  ... 还有 {len(diagnostics) - 10} 个问题")

    return "\n".join(lines)
