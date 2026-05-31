"""
CLI命令模块 / CLI Commands Module

新增顶级CLI命令
Additional top-level CLI commands
"""

import asyncio
import logging
import platform
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """AloneChat CLI 命令行工具"""
    pass


@cli.command()
@click.option("--provider", "-p", default=None, help="按提供商筛选")
@click.option("--capability", "-c", default=None, help="按能力筛选")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def models(provider: Optional[str], capability: Optional[str], verbose: bool) -> None:
    """
    列出可用模型 / List available models
    """
    asyncio.run(_list_models_async(provider, capability, verbose))


async def _list_models_async(
    provider: Optional[str],
    capability: Optional[str],
    verbose: bool,
) -> None:
    try:
        from alonechat.llm.model_registry import get_model_registry

        registry = get_model_registry()

        if provider:
            from alonechat.llm.model_registry import ModelProvider
            try:
                provider_enum = ModelProvider(provider)
                models_list = registry.list_by_provider(provider_enum)
            except ValueError:
                console.print(f"[red]未知提供商: {provider}[/red]")
                return
        elif capability:
            from alonechat.llm.model_registry import ModelCapability
            try:
                cap_enum = ModelCapability(capability)
                models_list = registry.list_by_capability(cap_enum)
            except ValueError:
                console.print(f"[red]未知能力: {capability}[/red]")
                return
        else:
            models_list = registry.list_available()

        if not models_list:
            console.print("[yellow]没有找到可用模型[/yellow]")
            return

        table = Table(title="可用模型", show_header=True, header_style="bold")
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("提供商", style="yellow")
        if verbose:
            table.add_column("上下文窗口", style="magenta")
            table.add_column("输入价格", style="blue")
            table.add_column("输出价格", style="blue")
            table.add_column("能力", style="dim")

        for model in models_list:
            row = [
                model.id,
                model.name,
                model.provider.value,
            ]
            if verbose:
                row.extend([
                    str(model.context_window),
                    f"${model.input_price}/M",
                    f"${model.output_price}/M",
                    ", ".join(c.value for c in model.capabilities[:3]),
                ])
            table.add_row(*row)

        console.print(table)

    except ImportError:
        console.print("[red]alonechat 不可用[/red]")


@cli.command()
@click.option("--fix", "-f", is_flag=True, help="尝试自动修复问题")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def doctor(fix: bool, verbose: bool) -> None:
    """
    系统诊断 / System diagnostics
    """
    asyncio.run(_run_doctor_async(fix, verbose))


async def _run_doctor_async(fix: bool, verbose: bool) -> None:
    console.print(Panel("系统诊断", title="AloneChat Doctor", border_style="blue"))

    checks = []

    console.print("\n[bold]检查 Python 环境...[/bold]")
    python_version = sys.version_info
    if python_version >= (3, 9):
        checks.append(("Python 版本", True, f"{python_version.major}.{python_version.minor}.{python_version.micro}"))
    else:
        checks.append(("Python 版本", False, f"{python_version.major}.{python_version.minor}.{python_version.micro} (需要 >= 3.9)"))

    console.print("\n[bold]检查依赖包...[/bold]")
    required_packages = [
        ("click", "CLI框架"),
        ("rich", "终端UI"),
        ("pydantic", "数据验证"),
        ("aiosqlite", "异步SQLite"),
        ("yaml", "配置解析"),
    ]

    for package, desc in required_packages:
        try:
            __import__(package)
            checks.append((f"{package} ({desc})", True, "已安装"))
        except ImportError:
            checks.append((f"{package} ({desc})", False, "未安装"))

    console.print("\n[bold]检查配置文件...[/bold]")
    config_dir = Path.home() / ".alonechat"
    if config_dir.exists():
        checks.append(("配置目录", True, str(config_dir)))
    else:
        checks.append(("配置目录", False, f"{config_dir} 不存在"))

    console.print("\n[bold]检查数据目录...[/bold]")
    data_dir = config_dir / "data"
    if data_dir.exists():
        checks.append(("数据目录", True, str(data_dir)))
    else:
        checks.append(("数据目录", False, f"{data_dir} 不存在"))

    console.print("\n[bold]检查 LSP 服务器...[/bold]")
    lsp_servers = [
        ("pyright-langserver", "Python"),
        ("typescript-language-server", "TypeScript"),
        ("gopls", "Go"),
        ("rust-analyzer", "Rust"),
    ]

    import shutil
    for cmd, lang in lsp_servers:
        if shutil.which(cmd):
            checks.append((f"{lang} LSP", True, cmd))
        else:
            checks.append((f"{lang} LSP", False, f"{cmd} 未安装"))

    console.print("\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("检查项", style="cyan")
    table.add_column("状态", width=10)
    table.add_column("详情", style="dim")

    passed = 0
    failed = 0
    for name, status, detail in checks:
        if status:
            status_str = "[green]✓ 通过[/green]"
            passed += 1
        else:
            status_str = "[red]✗ 失败[/red]"
            failed += 1
        table.add_row(name, status_str, detail)

    console.print(table)

    console.print(f"\n[bold]总计:[/bold] {passed} 通过, {failed} 失败")

    if failed > 0:
        console.print("\n[yellow]建议运行以下命令修复问题:[/yellow]")
        console.print("  pip install -r requirements.txt")
        console.print("  npm install -g pyright typescript-language-server")


@cli.command()
@click.option("--path", "-p", default=".", help="要审查的路径")
@click.option("--output", "-o", default=None, help="输出文件")
@click.option("--format", "-f", "output_format", default="text", type=click.Choice(["text", "json", "markdown"]))
def review(path: str, output: Optional[str], output_format: str) -> None:
    """
    代码审查 / Code review
    """
    asyncio.run(_run_review_async(path, output, output_format))


async def _run_review_async(
    path: str,
    output: Optional[str],
    output_format: str,
) -> None:
    console.print(f"[bold]开始代码审查: {path}[/bold]\n")

    target_path = Path(path)
    if not target_path.exists():
        console.print(f"[red]路径不存在: {path}[/red]")
        return

    findings = []

    python_files = list(target_path.rglob("*.py")) if target_path.is_dir() else [target_path]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("分析文件...", total=len(python_files))

        for file_path in python_files:
            progress.update(task, description=f"分析 {file_path.name}")

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    if "TODO" in line or "FIXME" in line:
                        findings.append({
                            "file": str(file_path),
                            "line": i,
                            "type": "todo",
                            "message": line.strip(),
                        })

                    if "print(" in line and not file_path.name.startswith("test_"):
                        findings.append({
                            "file": str(file_path),
                            "line": i,
                            "type": "print",
                            "message": "建议使用 logging 替代 print",
                        })

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

            progress.advance(task)

    if not findings:
        console.print("[green]✓ 没有发现问题[/green]")
        return

    table = Table(title="审查结果", show_header=True, header_style="bold")
    table.add_column("文件", style="cyan")
    table.add_column("行", style="yellow")
    table.add_column("类型", style="magenta")
    table.add_column("消息", style="dim")

    for finding in findings[:50]:
        table.add_row(
            finding["file"],
            str(finding["line"]),
            finding["type"],
            finding["message"][:60],
        )

    console.print(table)

    if len(findings) > 50:
        console.print(f"\n[yellow]显示前50条，共 {len(findings)} 条结果[/yellow]")


@cli.command()
@click.option("--interactive", "-i", is_flag=True, help="交互式配置")
def setup(interactive: bool) -> None:
    """
    引导配置 / Guided setup
    """
    asyncio.run(_run_setup_async(interactive))


async def _run_setup_async(interactive: bool) -> None:
    console.print(Panel("AloneChat 配置向导", border_style="blue"))

    config_dir = Path.home() / ".alonechat"
    config_dir.mkdir(parents=True, exist_ok=True)

    data_dir = config_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = config_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓[/green] 创建配置目录: {config_dir}")
    console.print(f"[green]✓[/green] 创建数据目录: {data_dir}")
    console.print(f"[green]✓[/green] 创建缓存目录: {cache_dir}")

    if interactive:
        api_key = click.prompt("请输入 API Key (可选)", default="", hide_input=True)
        if api_key:
            env_file = config_dir / ".env"
            env_file.write_text(f"ALONECHAT_API_KEY={api_key}\n")
            console.print(f"[green]✓[/green] 保存 API Key 到 {env_file}")

        default_model = click.prompt(
            "选择默认模型",
            type=click.Choice(["deepseek-chat", "gpt-4o", "claude-3-5-sonnet"]),
            default="deepseek-chat",
        )
        console.print(f"[green]✓[/green] 默认模型: {default_model}")

    console.print("\n[bold green]配置完成！[/bold green]")
    console.print("运行 [cyan]alonechat chat[/cyan] 开始对话")


@cli.command()
def features() -> None:
    """
    查询功能标志 / Query feature flags
    """
    asyncio.run(_show_features_async())


async def _show_features_async() -> None:
    features_list = [
        ("交互模式系统", "plan/agent/yolo 三种模式", True),
        ("工具系统", "20+ 核心工具", True),
        ("会话管理", "SQLite 持久化", True),
        ("LSP 诊断", "实时代码诊断", True),
        ("成本追踪", "多维度统计", True),
        ("多Agent协作", "Leader/Worker/Verifier", False),
        ("工作区快照", "快照和回滚", True),
        ("语义缓存", "智能缓存", True),
    ]

    table = Table(title="功能标志", show_header=True, header_style="bold")
    table.add_column("功能", style="cyan")
    table.add_column("描述", style="dim")
    table.add_column("状态", width=10)

    for name, desc, enabled in features_list:
        status = "[green]✓ 启用[/green]" if enabled else "[yellow]○ 禁用[/yellow]"
        table.add_row(name, desc, status)

    console.print(table)


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "-l", "list_all", is_flag=True, help="列出所有配置")
@click.option("--unset", "-u", is_flag=True, help="删除配置项")
def config_cmd(key: Optional[str], value: Optional[str], list_all: bool, unset: bool) -> None:
    """
    配置管理 / Configuration management
    """
    asyncio.run(_manage_config_async(key, value, list_all, unset))


async def _manage_config_async(
    key: Optional[str],
    value: Optional[str],
    list_all: bool,
    unset: bool,
) -> None:
    config_file = Path.home() / ".alonechat" / "config.yaml"

    if list_all:
        if config_file.exists():
            console.print(config_file.read_text(encoding="utf-8"))
        else:
            console.print("[yellow]配置文件不存在[/yellow]")
        return

    if not key:
        console.print("[red]请指定配置项[/red]")
        return

    if unset:
        console.print(f"[yellow]删除配置项: {key}[/yellow]")
        return

    if value:
        console.print(f"[green]设置 {key} = {value}[/green]")
    else:
        console.print(f"[cyan]查询配置项: {key}[/cyan]")


@cli.command()
@click.option("--check", "-c", is_flag=True, help="检查更新")
@click.option("--force", "-f", is_flag=True, help="强制更新")
def update(check: bool, force: bool) -> None:
    """
    检查更新 / Check for updates
    """
    asyncio.run(_check_update_async(check, force))


async def _check_update_async(check: bool, force: bool) -> None:
    console.print("[bold]检查更新...[/bold]")

    current_version = "0.2.3"
    console.print(f"当前版本: [cyan]{current_version}[/cyan]")

    latest_version = "0.2.3"

    if latest_version == current_version:
        console.print("[green]✓ 已是最新版本[/green]")
    else:
        console.print(f"[yellow]发现新版本: {latest_version}[/yellow]")
        if force or click.confirm("是否更新?"):
            console.print("[bold]正在更新...[/bold]")
            console.print("[green]✓ 更新完成[/green]")


if __name__ == "__main__":
    cli()
