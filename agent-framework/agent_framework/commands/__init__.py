"""
CLI命令基类和共享工具 / CLI Command Base and Shared Utilities

提供命令实现的通用基类和辅助函数
Provides common base class and helper functions for command implementation
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

T = TypeVar("T")

console = Console()
logger = logging.getLogger(__name__)


class BaseCommand(ABC, Generic[T]):
    """
    命令基类 / Base Command Class

    提供命令实现的通用模式
    Provides common patterns for command implementation
    """

    name: str = ""
    description: str = ""
    aliases: List[str] = []

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._console = console

    @abstractmethod
    async def execute(self, *args, **kwargs) -> T:
        """
        执行命令 / Execute command
        """
        pass

    def run_async(self, *args, **kwargs) -> T:
        """
        同步运行异步命令 / Run async command synchronously
        """
        return asyncio.run(self.execute(*args, **kwargs))

    def log(self, message: str, level: str = "info") -> None:
        """
        记录日志 / Log message
        """
        if self.verbose:
            getattr(logger, level)(message)

    def print(self, message: str, style: Optional[str] = None) -> None:
        """
        打印消息 / Print message
        """
        self._console.print(message, style=style)

    def print_error(self, message: str) -> None:
        """
        打印错误 / Print error
        """
        self._console.print(f"[red]错误:[/red] {message}")

    def print_success(self, message: str) -> None:
        """
        打印成功 / Print success
        """
        self._console.print(f"[green]成功:[/green] {message}")

    def print_warning(self, message: str) -> None:
        """
        打印警告 / Print warning
        """
        self._console.print(f"[yellow]警告:[/yellow] {message}")

    def create_table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        show_header: bool = True,
    ) -> Table:
        """
        创建表格 / Create table
        """
        table = Table(title=title, show_header=show_header)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        return table

    def with_progress(
        self,
        description: str,
        task: Any,
    ) -> Progress:
        """
        创建进度条 / Create progress bar
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console,
        )


class AsyncCommand(click.Command):
    """
    异步命令支持 / Async Command Support

    包装asyncio命令为click命令
    Wraps asyncio commands as click commands
    """

    def __init__(self, name: str, callback: Any, **kwargs):
        super().__init__(name, callback=callback, **kwargs)

    def invoke(self, ctx: click.Context) -> Any:
        """
        调用命令 / Invoke command
        """
        callback = self.callback
        if asyncio.iscoroutinefunction(callback):
            return asyncio.run(callback(**ctx.params))
        return super().invoke(ctx)


class AsyncGroup(click.Group):
    """
    异步命令组支持 / Async Group Support
    """

    def command(
        self,
        name: Optional[str] = None,
        **kwargs
    ) -> click.decorators.FC:
        """
        装饰器：注册命令 / Decorator: register command
        """
        def decorator(f: Any) -> AsyncCommand:
            cmd_name = name or f.__name__
            cmd = AsyncCommand(cmd_name, callback=f, **kwargs)
            self.add_command(cmd)
            return cmd
        return decorator


def run_async(f: Any) -> Any:
    """
    装饰器：运行异步函数 / Decorator: run async function
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))
    return wrapper


def confirm_action(message: str, default: bool = False) -> bool:
    """
    确认操作 / Confirm action
    """
    return click.confirm(message, default=default)


def prompt_input(message: str, default: Optional[str] = None) -> str:
    """
    提示输入 / Prompt input
    """
    return click.prompt(message, default=default)


def format_file_size(size: int) -> str:
    """
    格式化文件大小 / Format file size
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    格式化持续时间 / Format duration
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳 / Format timestamp
    """
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_config_path() -> Path:
    """
    获取配置路径 / Get config path
    """
    config_home = Path.home() / ".alonechat"
    config_home.mkdir(parents=True, exist_ok=True)
    return config_home


def get_data_path() -> Path:
    """
    获取数据路径 / Get data path
    """
    data_home = Path.home() / ".alonechat" / "data"
    data_home.mkdir(parents=True, exist_ok=True)
    return data_home


def get_cache_path() -> Path:
    """
    获取缓存路径 / Get cache path
    """
    cache_home = Path.home() / ".alonechat" / "cache"
    cache_home.mkdir(parents=True, exist_ok=True)
    return cache_home
