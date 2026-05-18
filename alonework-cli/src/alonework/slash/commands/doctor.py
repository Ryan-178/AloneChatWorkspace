"""
/doctor å½ä»¤ - æ£æ¥å®è£å¥åº·ç¶æ?/ Check installation health

å¢å¼ºåè½ / Enhanced Features:
- æ¾ç¤ºèªå¨æ´æ°é¢é / Show auto-update channel
- æ¾ç¤ºå¯ç¨PyPIçæ¬ / Show available PyPI version
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

from alonework import __version__ as cli_version


def _get_pypi_version() -> tuple[str | None, str | None]:
    """è·åPyPIä¸çææ°çæ?/ Get latest version from PyPI"""
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
    """æ£æ¥PyPIçæ¬ / Check PyPI version"""
    current = cli_version
    latest, all_versions = _get_pypi_version()

    if latest is None:
        return {
            "current": current,
            "latest": "æªç¥ / Unknown",
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
    """æ£æ¥å³é®Pythonå?/ Check critical Python packages"""
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
            version = getattr(mod, "__version__", "â?)
            checks.append((pkg_name, True, version))
        except ImportError:
            checks.append((pkg_name, False, "æªå®è£?/ Not installed"))

    return checks


def doctor_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    æ£æ¥å®è£å¥åº·ç¶æ?/ Check installation health

    å¢å¼ºæ¾ç¤º / Enhanced display:
    - èªå¨æ´æ°é¢éåå¯ç¨çæ?/ Auto-update channel and available version
    - å³é®ä¾èµæ£æ?/ Critical dependency check

    ç¨æ³ / Usage: /doctor
    """
    console.print("\n[bold cyan]AloneChat å¥åº·æ£æ?/ Health Check[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("æ£æ¥é¡¹ / Check", style="cyan")
    table.add_column("ç¶æ?/ Status", style="green")
    table.add_column("è¯¦æ / Details")

    checks = []

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 10)
    checks.append((
        "Python çæ¬ / Python version",
        python_ok,
        python_version
    ))

    config_manager = obj.get("config_manager")
    if config_manager:
        config_exists = config_manager.config_path.exists()
        checks.append((
            "éç½®æä»¶ / Config file",
            config_exists,
            str(config_manager.config_path) if config_exists else "æªæ¾å?/ Not found"
        ))
    else:
        checks.append(("éç½®æä»¶ / Config file", False, "ä¸å¯ç?/ Unavailable"))

    session_dir = Path.home() / ".alonechat" / "sessions"
    session_dir_ok = session_dir.exists()
    checks.append((
        "ä¼è¯ç®å½ / Session directory",
        session_dir_ok,
        str(session_dir)
    ))

    for pkg_name, ok, version in _check_python_packages():
        checks.append((f"ä¾èµ / Dependency: {pkg_name}", ok, version))

    pypi_info = _check_pypi_version()
    current_ver = pypi_info["current"]
    latest_ver = pypi_info["latest"]
    update_available = pypi_info["update_available"]

    checks.append((
        "å®è£çæ¬ / Installed version",
        True,
        current_ver
    ))

    checks.append((
        "æ´æ°é¢é / Update channel",
        True,
        f"PyPI (stable)"
    ))

    if update_available:
        checks.append((
            "å¯ç¨æ´æ° / Available update",
            False,
            f"[yellow]{latest_ver} (å½å: {current_ver})[/yellow]"
        ))
    else:
        checks.append((
            "å¯ç¨æ´æ° / Available update",
            True,
            f"{latest_ver} (å·²æ¯ææ?/ Already latest)"
        ))

    for name, ok, details in checks:
        status = "[green]â?OK[/green]" if ok else "[red]â?å¤±è´¥[/red]"
        table.add_row(name, status, details)

    console.print(table)

    if update_available:
        console.print(Panel(
            f"[bold yellow]â?ææ°çæ¬å¯ç¨ / New version available![/bold yellow]\n\n"
            f"å½åçæ¬ / Current: [cyan]{current_ver}[/cyan]\n"
            f"ææ°çæ?/ Latest: [green]{latest_ver}[/green]\n\n"
            f"æ´æ°å½ä»¤ / Update command:\n"
            f"[dim]pip install --upgrade alonechat-cli[/dim]\n\n"
            f"å¯ç¨çæ¬ / Available versions:\n"
            f"[dim]{pypi_info.get('all_versions', 'N/A')}[/dim]",
            border_style="yellow"
        ))
        console.print()

    all_ok = all(check[1] for check in checks)
    if all_ok:
        console.print("[green]â?æææ£æ¥éè¿ / All checks passed[/green]")
    else:
        console.print("[yellow]â?é¨åæ£æ¥æªéè¿ / Some checks failed[/yellow]")

    console.print()
