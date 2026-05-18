"""
test鍛戒护 - 鑷姩娴嬭瘯

鏀寔锛?- 鍗曞厓娴嬭瘯鐢熸垚
- 娴嬭瘯鎵ц
- 瑕嗙洊鐜囩粺璁?"""

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
    """鑾峰彇LLM瀹炰緥"""
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
        console.print(f"[red]鏃犳硶鍒濆鍖朙LM: {e}[/red]")
        console.print("[dim]璇风‘淇濋厤缃纭笖agent-framework宸插畨瑁匸/dim]")
        raise


@click.command()
@click.option("--file", "-f", "source_file", help="瑕佹祴璇曠殑婧愭枃浠?, type=click.Path(exists=True))
@click.option("--output", "-o", "output_dir", default="./tests", help="娴嬭瘯杈撳嚭鐩綍")
@click.option("--framework", default="pytest", help="娴嬭瘯妗嗘灦 (pytest/jest/junit)")
@click.option("--run", "-r", "run_tests", is_flag=True, help="鐢熸垚鍚庣珛鍗宠繍琛屾祴璇?)
@click.option("--coverage", is_flag=True, help="鐢熸垚瑕嗙洊鐜囨姤鍛?)
@click.option("--types", "-t", multiple=True, default=["unit"], help="娴嬭瘯绫诲瀷 (unit/integration/edge)")
@click.pass_obj
def test_command(obj: dict, source_file: str | None, output_dir: str, framework: str, run_tests: bool, coverage: bool, types: list[str]) -> None:
    """
    鑷姩娴嬭瘯
    
    浣跨敤agent-framework鐨凾estGenerator鐢熸垚鍜屾墽琛屾祴璇?    
    绀轰緥锛?    $ alonechat test --file my_code.py
    $ alonechat test --file my_code.py --run
    $ alonechat test --file my_code.py --framework pytest --coverage
    $ alonechat test --file app.js --framework jest
    """
    if not source_file:
        console.print(Panel.fit(
            "[bold cyan]鑷姩娴嬭瘯[/bold cyan]\n\n"
            "浣跨敤agent-framework鐨凾estGenerator鐢熸垚鍜屾墽琛屾祴璇昞n\n"
            "[dim]璇蜂娇鐢?--file 鎸囧畾瑕佹祴璇曠殑鏂囦欢[/dim]",
            border_style="cyan"
        ))
        console.print("\n[bold]绀轰緥锛歔/bold]")
        console.print("  $ alonechat test --file my_code.py")
        console.print("  $ alonechat test --file my_code.py --run")
        console.print("  $ alonechat test --file my_code.py --coverage")
        return
    
    source_path = Path(source_file)
    
    console.print(Panel.fit(
        f"[bold cyan]鑷姩娴嬭瘯[/bold cyan]\n\n"
        f"婧愭枃浠? {source_file}\n"
        f"杈撳嚭鐩綍: {output_dir}\n"
        f"娴嬭瘯妗嗘灦: {framework}\n"
        f"娴嬭瘯绫诲瀷: {', '.join(types)}\n"
        f"杩愯娴嬭瘯: {'鏄? if run_tests else '鍚?}\n"
        f"瑕嗙洊鐜? {'鏄? if coverage else '鍚?}",
        border_style="cyan"
    ))
    
    try:
        from agent_framework.services.test_generator import TestGenerator
        
        llm = get_llm()
        generator = TestGenerator(llm=llm)
        
        console.print("\n[bold]姝ｅ湪鐢熸垚娴嬭瘯...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("鐢熸垚涓?..", total=None)
            
            tests = generator.generate_tests(
                source_file=source_file,
                framework=framework,
                test_types=list(types)
            )
        
        console.print(f"\n[bold green]鉁?鐢熸垚浜?{len(tests)} 涓祴璇曠敤渚媅/bold green]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("搴忓彿", style="cyan", width=6)
        table.add_column("娴嬭瘯鍚嶇О")
        table.add_column("绫诲瀷", style="dim")
        table.add_column("鎻忚堪", style="dim")
        
        for i, test in enumerate(tests, 1):
            table.add_row(
                str(i),
                test.get("name", ""),
                test.get("type", ""),
                test.get("description", "")[:50] + "..." if len(test.get("description", "")) > 50 else test.get("description", "")
            )
        
        console.print(table)
        
        console.print(f"\n[bold]鍐欏叆娴嬭瘯鏂囦欢...[/bold]")
        test_files = generator.write_tests(tests, output_dir)
        
        console.print(f"[green]鉁?宸插啓鍏?{len(test_files)} 涓祴璇曟枃浠讹細[/green]")
        for test_file in test_files:
            console.print(f"  鈥?{test_file}")
        
        if run_tests or coverage:
            console.print(f"\n[bold]杩愯娴嬭瘯...[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("杩愯涓?..", total=None)
                
                result = generator.run_tests(
                    test_path=output_dir,
                    framework=framework,
                    coverage=coverage
                )
            
            console.print(f"\n[bold green]娴嬭瘯缁撴灉锛歔/bold green]\n")
            
            console.print(f"  鎬绘祴璇曟暟: [cyan]{result.total_tests}[/cyan]")
            console.print(f"  閫氳繃: [green]{result.passed_tests}[/green]")
            console.print(f"  澶辫触: [red]{result.failed_tests}[/red]")
            console.print(f"  璺宠繃: [yellow]{result.skipped_tests}[/yellow]")
            
            if coverage and result.coverage:
                console.print(f"\n  瑕嗙洊鐜? [cyan]{result.coverage:.2f}%[/cyan]")
            
            if result.failed_tests > 0:
                console.print(f"\n[bold red]澶辫触鐨勬祴璇曪細[/bold red]")
                for failure in result.failures:
                    console.print(f"  鈥?{failure.get('test')}: {failure.get('message')}")
        
    except ImportError:
        console.print("[red]閿欒: agent-framework鏈畨瑁匸/red]")
        console.print("[dim]璇风‘淇漚gent-framework鍦≒ython璺緞涓璠/dim]")
    except Exception as e:
        console.print(f"[red]閿欒: {e}[/red]")
