"""
/upgrade 命令 - 升级AloneWork CLI / Upgrade AloneWork CLI

版本 / Version: 2.1.80
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _get_current_version() -> str:
    """
    获取当前版本 / Get current version
    """
    try:
        from alonechat import __version__
        return __version__
    except ImportError:
        return "unknown"


def _check_pip_latest(package_name: str) -> str | None:
    """
    检查pip最新版本 / Check pip latest version
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", package_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if "(" in output:
                versions = output.split("(")[1].split(")")[0].split(", ")
                if versions:
                    return versions[0].strip()
    except Exception:
        pass
    return None


def _check_pyproject_version() -> str | None:
    """
    从pyproject.toml检查版本 / Check version from pyproject.toml
    """
    pyproject = Path(__file__).parents[4] / "pyproject.toml"
    if not pyproject.exists():
        pyproject = Path.cwd() / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.strip().startswith("version"):
                    return line.split("=")[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return None


def _get_changelog() -> str:
    """
    获取更新日志 / Get changelog
    """
    changelog = Path(__file__).parents[4] / "CHANGELOG.md"
    if not changelog.exists():
        changelog = Path.cwd() / "CHANGELOG.md"
    if changelog.exists():
        try:
            content = changelog.read_text(encoding="utf-8")
            lines = content.split("\n")[:30]
            return "\n".join(lines)
        except Exception:
            pass
    return ""


def upgrade_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    升级AloneWork CLI / Upgrade AloneWork CLI

    用法 / Usage:
        /upgrade                检查更新 / Check for updates
        /upgrade check          检查更新 / Check for updates
        /upgrade install        安装更新 / Install update
        /upgrade changelog      查看更新日志 / View changelog
        /upgrade info           版本信息 / Version info

    示例 / Examples:
        /upgrade
        /upgrade check
        /upgrade changelog
    """
    current_version = _get_current_version()

    if not args or args[0] == "check":
        console.print(f"[cyan]当前版本 / Current version: {current_version}[/cyan]")
        console.print("[dim]检查更新中... / Checking for updates...[/dim]")

        latest = _check_pip_latest("alonework-cli")
        pyproject_ver = _check_pyproject_version()

        table = Table(show_header=True, title="版本信息 / Version Info")
        table.add_column("项目 / Item", style="cyan")
        table.add_column("版本 / Version", style="green")

        table.add_row("当前版本 / Current", current_version)
        if pyproject_ver:
            table.add_row("项目版本 / Project", pyproject_ver)
        if latest:
            table.add_row("最新版本 / Latest", latest)
            if latest != current_version:
                table.add_row("状态 / Status", "[yellow]有更新可用 / Update available[/yellow]")
            else:
                table.add_row("状态 / Status", "[green]已是最新 / Up to date[/green]")
        else:
            table.add_row("状态 / Status", "[dim]无法检查 / Cannot check[/dim]")

        console.print(table)
        return

    if args[0] == "install":
        console.print("[cyan]正在升级... / Upgrading...[/cyan]")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "alonework-cli"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                console.print("[green]✓ 升级成功 / Upgrade successful[/green]")
                console.print(f"[dim]{result.stdout.strip()[-200:]}[/dim]")
            else:
                console.print(f"[red]升级失败 / Upgrade failed[/red]")
                console.print(f"[dim]{result.stderr.strip()[-200:]}[/dim]")
        except subprocess.TimeoutExpired:
            console.print("[red]升级超时 / Upgrade timeout[/red]")
        except Exception as e:
            console.print(f"[red]升级错误 / Upgrade error: {e}[/red]")
        return

    if args[0] == "changelog":
        changelog = _get_changelog()
        if changelog:
            console.print(Panel(changelog, title="更新日志 / Changelog", border_style="cyan"))
        else:
            console.print("[dim]未找到更新日志 / Changelog not found[/dim]")
            console.print("[dim]请查看 / Please visit: https://github.com/AlonechatWorkspace/AloneWork[/dim]")
        return

    if args[0] == "info":
        pyproject_ver = _check_pyproject_version()
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        console.print(Panel(
            f"[bold]AloneWork CLI 信息 / Info[/bold]\n\n"
            f"版本 / Version: {current_version}\n"
            f"项目版本 / Project version: {pyproject_ver or '-'}\n"
            f"Python: {python_ver}\n"
            f"路径 / Path: {sys.executable}\n"
            f"项目地址 / GitHub: https://github.com/AlonechatWorkspace/AloneWork\n"
            f"邮箱 / Email: aloneworkworkspace@163.com",
            border_style="cyan",
        ))
        return

    console.print(f"[red]未知操作 / Unknown action: {args[0]}[/red]")
    console.print("[dim]可用操作 / Available: check, install, changelog, info[/dim]")
