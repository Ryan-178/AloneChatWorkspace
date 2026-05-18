"""
/doctor 命令 - 检查安装健康状态 / Check installation health

增强功能 / Enhanced Features:
- 显示自动更新频道 / Show auto-update channel
- 显示可用PyPI版本 / Show available PyPI version
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

from alonechat import __version__ as cli_version


def _get_pypi_version() -> tuple[str | None, str | None]:
    """获取PyPI上的最新版本 / Get latest version from PyPI"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "alonechat-cli"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "Available versions:" in line:
                    versions = line.split("Available versions:")[1].strip()
                    latest = versions.split(",")[0].strip()
                    return latest, versions
        return None, None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None, None


def _check_pypi_version() -> dict:
    """检查PyPI版本 / Check PyPI version"""
    current = cli_version
    latest, all_versions = _get_pypi_version()

    if latest is None:
        return {
            "current": current,
            "latest": "未知 / Unknown",
            "update_available": False,
            "channel": "stable",
        }

    update_available = latest != current

    return {
        "current": current,
        "latest": latest,
        "all_versions": all_versions,
        "update_available": update_available,
    }


def _check_python_packages() -> list[tuple[str, bool, str]]:
    """检查关键Python包 / Check critical Python packages"""
    checks = []

    packages = [
        ("click", "click"),
        ("rich", "rich"),
        ("httpx", "httpx"),
        ("yaml", "PyYAML"),
    ]

    for mod_name, pkg_name in packages:
        try:
            mod = __import__(mod_name)
            version = getattr(mod, "__version__", "✓")
            checks.append((pkg_name, True, version))
        except ImportError:
            checks.append((pkg_name, False, "未安装 / Not installed"))

    return checks


def doctor_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    检查安装健康状态 / Check installation health

    增强显示 / Enhanced display:
    - 自动更新频道和可用版本 / Auto-update channel and available version
    - 关键依赖检查 / Critical dependency check

    用法 / Usage: /doctor
    """
    console.print("\n[bold cyan]AloneChat 健康检查 / Health Check[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("检查项 / Check", style="cyan")
    table.add_column("状态 / Status", style="green")
    table.add_column("详情 / Details")

    checks = []

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 10)
    checks.append((
        "Python 版本 / Python version",
        python_ok,
        python_version
    ))

    config_manager = obj.get("config_manager")
    if config_manager:
        config_exists = config_manager.config_path.exists()
        checks.append((
            "配置文件 / Config file",
            config_exists,
            str(config_manager.config_path) if config_exists else "未找到 / Not found"
        ))
    else:
        checks.append(("配置文件 / Config file", False, "不可用 / Unavailable"))

    session_dir = Path.home() / ".alonechat" / "sessions"
    session_dir_ok = session_dir.exists()
    checks.append((
        "会话目录 / Session directory",
        session_dir_ok,
        str(session_dir)
    ))

    for pkg_name, ok, version in _check_python_packages():
        checks.append((f"依赖 / Dependency: {pkg_name}", ok, version))

    pypi_info = _check_pypi_version()
    current_ver = pypi_info["current"]
    latest_ver = pypi_info["latest"]
    update_available = pypi_info["update_available"]

    checks.append((
        "安装版本 / Installed version",
        True,
        current_ver
    ))

    checks.append((
        "更新频道 / Update channel",
        True,
        f"PyPI (stable)"
    ))

    if update_available:
        checks.append((
            "可用更新 / Available update",
            False,
            f"[yellow]{latest_ver} (当前: {current_ver})[/yellow]"
        ))
    else:
        checks.append((
            "可用更新 / Available update",
            True,
            f"{latest_ver} (已是最新 / Already latest)"
        ))

    for name, ok, details in checks:
        status = "[green]✓ OK[/green]" if ok else "[red]✗ 失败[/red]"
        table.add_row(name, status, details)

    console.print(table)

    if update_available:
        console.print(Panel(
            f"[bold yellow]⚠ 有新版本可用 / New version available![/bold yellow]\n\n"
            f"当前版本 / Current: [cyan]{current_ver}[/cyan]\n"
            f"最新版本 / Latest: [green]{latest_ver}[/green]\n\n"
            f"更新命令 / Update command:\n"
            f"[dim]pip install --upgrade alonechat-cli[/dim]\n\n"
            f"可用版本 / Available versions:\n"
            f"[dim]{pypi_info.get('all_versions', 'N/A')}[/dim]",
            border_style="yellow"
        ))
        console.print()

    all_ok = all(check[1] for check in checks)
    if all_ok:
        console.print("[green]✓ 所有检查通过 / All checks passed[/green]")
    else:
        console.print("[yellow]⚠ 部分检查未通过 / Some checks failed[/yellow]")

    console.print()
