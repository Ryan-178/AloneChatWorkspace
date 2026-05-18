"""
éæagent-frameworkçCLIå½ä»¤

è¿äºå½ä»¤ç´æ¥è°ç¨agent-frameworkçåè½ï¼é¿åéå¤å¼å?"""

import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown

console = Console()


def get_llm():
    """è·åLLMå®ä¾"""
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
        console.print(f"[red]æ æ³åå§åLLM: {e}[/red]")
        console.print("[dim]è¯·ç¡®ä¿éç½®æ­£ç¡®ä¸agent-frameworkå·²å®è£[/dim]")
        raise


@click.group()
def agent_commands():
    """Agentç¸å³å½ä»¤ - è°ç¨agent-frameworkåè½"""
    pass


@agent_commands.command("task")
@click.argument("description")
@click.option("--execute", "-e", is_flag=True, help="ç«å³æ§è¡ä»»å¡")
@click.option("--workspace", "-w", default="./workspace", help="å·¥ä½ç©ºé´è·¯å¾")
@click.pass_obj
def task_command(obj: dict, description: str, execute: bool, workspace: str):
    """
    ä»»å¡è§ååæ§è¡?    
    ä½¿ç¨agent-frameworkçTaskPlannerè¿è¡ä»»å¡æè§£åæ§è¡?    
    ç¤ºä¾ï¼?    $ alonechat agent task "åædata.xlsxå¹¶çææ¥å?
    $ alonechat agent task "éæç¨æ·è®¤è¯æ¨¡å" --execute
    """
    console.print(Panel.fit(
        f"[bold cyan]ä»»å¡è§å[/bold cyan]\n\n"
        f"ä»»å¡æè¿°: {description}\n"
        f"æ§è¡æ¨¡å¼: {'ç«å³æ§è¡' if execute else 'ä»è§å?}\n"
        f"å·¥ä½ç©ºé´: {workspace}",
        border_style="cyan"
    ))
    
    try:
        from agent_framework.services.task_planner import TaskPlanner
        
        llm = get_llm()
        planner = TaskPlanner(llm=llm)
        
        console.print("\n[bold]æ­£å¨åæä»»å¡...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("æè§£ä»»å¡ä¸?..", total=None)
            
            async def decompose():
                return await planner.decompose_task(
                    user_request=description,
                    context={"workspace": workspace}
                )
            
            task_plan = asyncio.run(decompose())
        
        console.print("\n[bold green]ä»»å¡æè§£ç»æï¼[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("åºå·", style="cyan", width=6)
        table.add_column("ä»»å¡æè¿°")
        table.add_column("ä¾èµ", style="dim")
        
        for i, subtask in enumerate(task_plan.get("subtasks", []), 1):
            deps = ", ".join(subtask.get("dependencies", []))
            table.add_row(str(i), subtask.get("description", ""), deps or "-")
        
        console.print(table)
        
        if execute:
            console.print("\n[bold]å¼å§æ§è¡ä»»å?..[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("æ§è¡ä¸?..", total=None)
                
                async def execute_plan():
                    return await planner.execute_task_plan(
                        task_plan=task_plan,
                        workspace_id=workspace
                    )
                
                result = asyncio.run(execute_plan())
            
            console.print("\n[bold green]â?ä»»å¡æ§è¡å®æï¼[/bold green]")
            console.print(result)
        
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
        console.print("[dim]è¯·ç¡®ä¿agent-frameworkå¨Pythonè·¯å¾ä¸­[/dim]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("process")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="è¾åºæ ¼å¼ (text/markdown/json)")
@click.option("--save", "-s", help="ä¿å­å°æä»?)
@click.pass_obj
def process_command(obj: dict, file_path: str, output: str | None, save: str | None):
    """
    æä»¶å¤ç
    
    ä½¿ç¨agent-frameworkçFileProcessorså¤çåç§æä»¶æ ¼å¼
    
    ç¤ºä¾ï¼?    $ alonechat agent process document.pdf
    $ alonechat agent process report.docx --output markdown
    $ alonechat agent process data.xlsx --save output.txt
    """
    file_path = Path(file_path)
    suffix = file_path.suffix
    
    console.print(f"\n[bold]å¤çæä»¶: {file_path.name}[/bold]")
    console.print(f"æä»¶ç±»å: [cyan]{suffix}[/cyan]")
    console.print(f"æä»¶å¤§å°: [cyan]{file_path.stat().st_size / 1024:.2f} KB[/cyan]")
    
    try:
        from agent_framework.services.file_processors import get_processor
        
        processor = get_processor(suffix)
        
        console.print("\n[bold]æ­£å¨è§£ææä»¶...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("è§£æä¸?..", total=None)
            
            async def parse():
                return await processor.to_text(file_path)
            
            text = asyncio.run(parse())
        
        console.print("\n[bold green]è§£æç»æï¼[/bold green]")
        
        if save:
            Path(save).write_text(text, encoding="utf-8")
            console.print(f"[green]â?å·²ä¿å­å°: {save}[/green]")
        
        if output == "markdown":
            console.print(Markdown(text))
        elif output == "json":
            import json
            console.print_json(json.dumps({"content": text}, ensure_ascii=False))
        else:
            if len(text) > 1000:
                console.print(text[:1000] + "\n...")
                console.print(f"\n[dim]å?{len(text)} å­ç¬¦[/dim]")
            else:
                console.print(text)
        
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("fix")
@click.option("--error", "-e", help="éè¯¯ä¿¡æ¯")
@click.option("--file", "-f", "file_path", help="ä»£ç æä»¶è·¯å¾", type=click.Path(exists=True))
@click.option("--run-tests", is_flag=True, help="ä¿®å¤åè¿è¡æµè¯?)
@click.pass_obj
def fix_command(obj: dict, error: str | None, file_path: str | None, run_tests: bool):
    """
    éè¯¯ä¿®å¤
    
    ä½¿ç¨agent-frameworkçErrorFixerä¿®å¤ä»£ç éè¯¯
    
    ç¤ºä¾ï¼?    $ alonechat agent fix --error "TypeError: ..." --file my_code.py
    $ alonechat agent fix --file my_code.py --run-tests
    """
    if not file_path:
        console.print("[red]è¯·æä¾æä»¶è·¯å¾?(--file)[/red]")
        return
    
    console.print(f"\n[bold]åæéè¯¯...[/bold]")
    console.print(f"æä»¶: [cyan]{file_path}[/cyan]")
    if error:
        console.print(f"éè¯¯: [red]{error}[/red]")
    
    try:
        from agent_framework.services.error_fixer import ErrorFixer
        
        llm = get_llm()
        fixer = ErrorFixer(llm=llm)
        
        console.print("\n[bold]æ­£å¨ä¿®å¤...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("ä¿®å¤ä¸?..", total=None)
            
            if error:
                result = fixer.fix_runtime_error(file_path, error)
            else:
                result = fixer.fix_file(file_path, run_tests=run_tests)
        
        console.print("\n[bold green]ä¿®å¤ç»æï¼[/bold green]\n")
        
        if result.get("success"):
            console.print(f"[green]â?ä¿®å¤æå[/green]")
            
            if result.get("fixed_code"):
                console.print("\n[bold]ä¿®å¤åçä»£ç ï¼[/bold]\n")
                syntax = Syntax(
                    result["fixed_code"],
                    "python",
                    theme="monokai",
                    line_numbers=True
                )
                console.print(syntax)
                
                if click.confirm("\næ¯å¦ä¿å­ä¿®å¤åçä»£ç ï¼?):
                    Path(file_path).write_text(result["fixed_code"], encoding="utf-8")
                    console.print(f"[green]â?å·²ä¿å­å°: {file_path}[/green]")
        else:
            console.print(f"[red]â?ä¿®å¤å¤±è´¥: {result.get('message', 'æªç¥éè¯¯')}[/red]")
        
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("skill")
@click.argument("skill_name", required=False)
@click.option("--list", "-l", "list_skills", is_flag=True, help="ååºæææè?)
@click.option("--run", "-r", "run_skill", is_flag=True, help="è¿è¡æè?)
@click.option("--params", "-p", help="æè½åæ?(JSONæ ¼å¼)")
@click.pass_obj
def skill_command(obj: dict, skill_name: str | None, list_skills: bool, run_skill: bool, params: str | None):
    """
    Skillsç®¡ç
    
    ä½¿ç¨agent-frameworkçSkillsRegistryç®¡çæè?    
    ç¤ºä¾ï¼?    $ alonechat agent skill --list
    $ alonechat agent skill document_generation --run
    $ alonechat agent skill data_analysis --run --params '{"data": [...]}'
    """
    try:
        from agent_framework.tools.skills_registry import SkillsRegistry
        
        registry = SkillsRegistry()
        
        if list_skills:
            console.print("\n[bold cyan]å¯ç¨æè½åè¡¨ï¼[/bold cyan]\n")
            
            skills = registry.list_skills()
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("æè½åç§?, style="cyan")
            table.add_column("æè¿°")
            table.add_column("å·¥å·", style="dim")
            
            for skill in skills:
                tools = ", ".join(skill.get("tools", []))
                table.add_row(
                    skill.get("name", ""),
                    skill.get("description", ""),
                    tools or "-"
                )
            
            console.print(table)
        
        elif skill_name:
            if run_skill:
                console.print(f"\n[bold]è¿è¡æè? {skill_name}[/bold]")
                
                context = {}
                if params:
                    import json
                    context = json.loads(params)
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("æ§è¡ä¸?..", total=None)
                    
                    async def execute():
                        return await registry.execute(skill_name, context)
                    
                    result = asyncio.run(execute())
                
                console.print("\n[bold green]æ§è¡ç»æï¼[/bold green]")
                console.print(result)
            else:
                console.print(f"\n[bold]æè½ä¿¡æ? {skill_name}[/bold]")
                skill = registry.get_skill(skill_name)
                if skill:
                    console.print(f"  åç§°: [cyan]{skill.get('name')}[/cyan]")
                    console.print(f"  æè¿°: {skill.get('description')}")
                    console.print(f"  å·¥å·: {', '.join(skill.get('tools', []))}")
                else:
                    console.print(f"[red]æªæ¾å°æè? {skill_name}[/red]")
        
        else:
            console.print("[yellow]è¯·æå®æè½åç§°æä½¿ç¨ --list æ¥çæææè½[/yellow]")
    
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("rag")
@click.argument("action", type=click.Choice(["index", "search"]))
@click.argument("path_or_query")
@click.option("--k", default=5, help="è¿åç»ææ°é")
@click.pass_obj
def rag_command(obj: dict, action: str, path_or_query: str, k: int):
    """
    RAGæ£ç´?    
    ä½¿ç¨agent-frameworkçRAGåè½è¿è¡ä»£ç æ£ç´?    
    ç¤ºä¾ï¼?    $ alonechat agent rag index ./src
    $ alonechat agent rag search "ç¨æ·è®¤è¯é»è¾"
    $ alonechat agent rag search "æ¥è¯¢åå®¹" --k 10
    """
    try:
        from agent_framework.rag import RAGPipeline
        
        pipeline = RAGPipeline()
        
        if action == "index":
            console.print(f"\n[bold]ç´¢å¼ç®å½: {path_or_query}[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("ç´¢å¼ä¸?..", total=None)
                
                async def index():
                    return await pipeline.ingest(path_or_query)
                
                count = asyncio.run(index())
            
            console.print(f"[green]â?ç´¢å¼å®æï¼å±ç´¢å¼ {count} ä¸ªææ¡£[/green]")
        
        elif action == "search":
            console.print(f"\n[bold]æç´¢: {path_or_query}[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("æç´¢ä¸?..", total=None)
                
                async def search():
                    return await pipeline.retrieve(path_or_query, k=k)
                
                results = asyncio.run(search())
            
            console.print(f"\n[bold green]æ¾å° {len(results)} ä¸ªç»æï¼[/bold green]\n")
            
            for i, result in enumerate(results, 1):
                console.print(f"  [bold cyan]{i}. {result.get('source', 'æªç¥')}[/bold cyan]")
                console.print(f"     ç¸ä¼¼åº? {result.get('score', 0):.4f}")
                content = result.get('content', '')
                if len(content) > 100:
                    console.print(f"     [dim]{content[:100]}...[/dim]\n")
                else:
                    console.print(f"     [dim]{content}[/dim]\n")
    
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("generate")
@click.argument("type", type=click.Choice(["ppt", "excel", "report", "doc"]))
@click.option("--request", "-r", required=True, help="çæè¯·æ±æè¿°")
@click.option("--output", "-o", required=True, help="è¾åºæä»¶è·¯å¾")
@click.option("--data", "-d", help="æ°æ®æä»¶è·¯å¾ (JSON)")
@click.pass_obj
def generate_command(obj: dict, type: str, request: str, output: str, data: str | None):
    """
    æä»¶çæ
    
    ä½¿ç¨agent-frameworkçFileGeneratorsçæåç§æä»¶
    
    ç¤ºä¾ï¼?    $ alonechat agent generate ppt --request "äº§åä»ç»PPT" --output product.pptx
    $ alonechat agent generate excel --request "éå®æ°æ®æ¥è¡? --output sales.xlsx
    $ alonechat agent generate report --request "å­£åº¦æ¥å" --output report.docx
    """
    console.print(f"\n[bold]çæ{type.upper()}æä»¶[/bold]")
    console.print(f"è¯·æ±: [cyan]{request}[/cyan]")
    console.print(f"è¾åº: [cyan]{output}[/cyan]")
    
    try:
        from agent_framework.services.file_generators import FileGeneratorService
        
        llm = get_llm()
        service = FileGeneratorService(llm=llm)
        
        context = {}
        if data:
            import json
            context = json.loads(Path(data).read_text())
        
        console.print("\n[bold]æ­£å¨çæ...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("çæä¸?..", total=None)
            
            async def generate():
                if type == "ppt":
                    return await service.generate_ppt(request, context, output)
                elif type == "excel":
                    return await service.generate_excel(request, context, output)
                elif type == "report":
                    return await service.generate_word_report(request, context, output)
                elif type == "doc":
                    return await service.generate_word_report(request, context, output)
            
            result_path = asyncio.run(generate())
        
        console.print(f"\n[bold green]â?çæå®æï¼[/bold green]")
        console.print(f"æä»¶å·²ä¿å­å°: [cyan]{result_path}[/cyan]")
        
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")


@agent_commands.command("analyze")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="è¾åºæ ¼å¼ (text/markdown)")
@click.pass_obj
def analyze_command(obj: dict, file_path: str, output: str | None):
    """
    æ°æ®åæ
    
    ä½¿ç¨agent-frameworkåææ°æ®æä»¶
    
    ç¤ºä¾ï¼?    $ alonechat agent analyze data.xlsx
    $ alonechat agent analyze sales.csv --output markdown
    """
    file_path = Path(file_path)
    
    console.print(f"\n[bold]åææä»¶: {file_path.name}[/bold]")
    
    try:
        from agent_framework.services.file_generators import FileGeneratorService
        
        llm = get_llm()
        service = FileGeneratorService(llm=llm)
        
        # åè¯»åæä»?        from agent_framework.services.file_processors import get_processor
        processor = get_processor(file_path.suffix)
        data = asyncio.run(processor.to_text(file_path))
        
        console.print("\n[bold]æ­£å¨åæ...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("åæä¸?..", total=None)
            
            async def analyze():
                return await service.analyze_data(data, "åææ°æ®å¹¶ç»åºæ´å¯?)
            
            result = asyncio.run(analyze())
        
        console.print("\n[bold green]åæç»æï¼[/bold green]\n")
        
        if output == "markdown":
            console.print(Markdown(result))
        else:
            console.print(result)
        
    except ImportError:
        console.print("[red]éè¯¯: agent-frameworkæªå®è£[/red]")
    except Exception as e:
        console.print(f"[red]éè¯¯: {e}[/red]")
