"""
test命令 - 自动测试

支持：
- 单元测试生成
- 测试执行
- 覆盖率统计
"""

import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax

console = Console()


def get_llm():
    """获取LLM实例"""
    try:
        from agent_framework.llm import LiteLLMProvider
        from agent_framework.config import config
        
        llm_config = config.llm
        return LiteLLMProvider(
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url
        )
    except Exception as e:
        console.print(f"[red]无法初始化LLM: {e}[/red]")
        console.print("[dim]请确保配置正确且agent-framework已安装[/dim]")
        raise


@click.command()
@click.option("--file", "-f", "source_file", help="要测试的源文件", type=click.Path(exists=True))
@click.option("--output", "-o", "output_dir", default="./tests", help="测试输出目录")
@click.option("--framework", default="pytest", help="测试框架 (pytest/jest/junit)")
@click.option("--run", "-r", "run_tests", is_flag=True, help="生成后立即运行测试")
@click.option("--coverage", is_flag=True, help="生成覆盖率报告")
@click.option("--types", "-t", multiple=True, default=["unit"], help="测试类型 (unit/integration/edge)")
@click.pass_obj
def test_command(obj: dict, source_file: str | None, output_dir: str, framework: str, run_tests: bool, coverage: bool, types: list[str]) -> None:
    """
    自动测试
    
    使用agent-framework的TestGenerator生成和执行测试
    
    示例：
    $ alonechat test --file my_code.py
    $ alonechat test --file my_code.py --run
    $ alonechat test --file my_code.py --framework pytest --coverage
    $ alonechat test --file app.js --framework jest
    """
    if not source_file:
        console.print(Panel.fit(
            "[bold cyan]自动测试[/bold cyan]\n\n"
            "使用agent-framework的TestGenerator生成和执行测试\n\n"
            "[dim]请使用 --file 指定要测试的文件[/dim]",
            border_style="cyan"
        ))
        console.print("\n[bold]示例：[/bold]")
        console.print("  $ alonechat test --file my_code.py")
        console.print("  $ alonechat test --file my_code.py --run")
        console.print("  $ alonechat test --file my_code.py --coverage")
        return
    
    source_path = Path(source_file)
    
    console.print(Panel.fit(
        f"[bold cyan]自动测试[/bold cyan]\n\n"
        f"源文件: {source_file}\n"
        f"输出目录: {output_dir}\n"
        f"测试框架: {framework}\n"
        f"测试类型: {', '.join(types)}\n"
        f"运行测试: {'是' if run_tests else '否'}\n"
        f"覆盖率: {'是' if coverage else '否'}",
        border_style="cyan"
    ))
    
    try:
        from agent_framework.services.test_generator import TestGenerator
        
        llm = get_llm()
        generator = TestGenerator(llm=llm)
        
        console.print("\n[bold]正在生成测试...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("生成中...", total=None)
            
            tests = generator.generate_tests(
                source_file=source_file,
                framework=framework,
                test_types=list(types)
            )
        
        console.print(f"\n[bold green]✓ 生成了 {len(tests)} 个测试用例[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("测试名称")
        table.add_column("类型", style="dim")
        table.add_column("描述", style="dim")
        
        for i, test in enumerate(tests, 1):
            table.add_row(
                str(i),
                test.get("name", ""),
                test.get("type", ""),
                test.get("description", "")[:50] + "..." if len(test.get("description", "")) > 50 else test.get("description", "")
            )
        
        console.print(table)
        
        console.print(f"\n[bold]写入测试文件...[/bold]")
        test_files = generator.write_tests(tests, output_dir)
        
        console.print(f"[green]✓ 已写入 {len(test_files)} 个测试文件：[/green]")
        for test_file in test_files:
            console.print(f"  • {test_file}")
        
        if run_tests or coverage:
            console.print(f"\n[bold]运行测试...[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("运行中...", total=None)
                
                result = generator.run_tests(
                    test_path=output_dir,
                    framework=framework,
                    coverage=coverage
                )
            
            console.print(f"\n[bold green]测试结果：[/bold green]\n")
            
            console.print(f"  总测试数: [cyan]{result.total_tests}[/cyan]")
            console.print(f"  通过: [green]{result.passed_tests}[/green]")
            console.print(f"  失败: [red]{result.failed_tests}[/red]")
            console.print(f"  跳过: [yellow]{result.skipped_tests}[/yellow]")
            
            if coverage and result.coverage:
                console.print(f"\n  覆盖率: [cyan]{result.coverage:.2f}%[/cyan]")
            
            if result.failed_tests > 0:
                console.print(f"\n[bold red]失败的测试：[/bold red]")
                for failure in result.failures:
                    console.print(f"  • {failure.get('test')}: {failure.get('message')}")
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
        console.print("[dim]请确保agent-framework在Python路径中[/dim]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
