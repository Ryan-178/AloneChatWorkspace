"""
集成agent-framework的CLI命令

这些命令直接调用agent-framework的功能，避免重复开发
"""

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


@click.group()
def agent_commands():
    """Agent相关命令 - 调用agent-framework功能"""
    pass


@agent_commands.command("task")
@click.argument("description")
@click.option("--execute", "-e", is_flag=True, help="立即执行任务")
@click.option("--workspace", "-w", default="./workspace", help="工作空间路径")
@click.pass_obj
def task_command(obj: dict, description: str, execute: bool, workspace: str):
    """
    任务规划和执行
    
    使用agent-framework的TaskPlanner进行任务拆解和执行
    
    示例：
    $ alonechat agent task "分析data.xlsx并生成报告"
    $ alonechat agent task "重构用户认证模块" --execute
    """
    console.print(Panel.fit(
        f"[bold cyan]任务规划[/bold cyan]\n\n"
        f"任务描述: {description}\n"
        f"执行模式: {'立即执行' if execute else '仅规划'}\n"
        f"工作空间: {workspace}",
        border_style="cyan"
    ))
    
    try:
        from agent_framework.services.task_planner import TaskPlanner
        
        llm = get_llm()
        planner = TaskPlanner(llm=llm)
        
        console.print("\n[bold]正在分析任务...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("拆解任务中...", total=None)
            
            async def decompose():
                return await planner.decompose_task(
                    user_request=description,
                    context={"workspace": workspace}
                )
            
            task_plan = asyncio.run(decompose())
        
        console.print("\n[bold green]任务拆解结果：[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("任务描述")
        table.add_column("依赖", style="dim")
        
        for i, subtask in enumerate(task_plan.get("subtasks", []), 1):
            deps = ", ".join(subtask.get("dependencies", []))
            table.add_row(str(i), subtask.get("description", ""), deps or "-")
        
        console.print(table)
        
        if execute:
            console.print("\n[bold]开始执行任务...[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("执行中...", total=None)
                
                async def execute_plan():
                    return await planner.execute_task_plan(
                        task_plan=task_plan,
                        workspace_id=workspace
                    )
                
                result = asyncio.run(execute_plan())
            
            console.print("\n[bold green]✓ 任务执行完成！[/bold green]")
            console.print(result)
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
        console.print("[dim]请确保agent-framework在Python路径中[/dim]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("process")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="输出格式 (text/markdown/json)")
@click.option("--save", "-s", help="保存到文件")
@click.pass_obj
def process_command(obj: dict, file_path: str, output: str | None, save: str | None):
    """
    文件处理
    
    使用agent-framework的FileProcessors处理各种文件格式
    
    示例：
    $ alonechat agent process document.pdf
    $ alonechat agent process report.docx --output markdown
    $ alonechat agent process data.xlsx --save output.txt
    """
    file_path = Path(file_path)
    suffix = file_path.suffix
    
    console.print(f"\n[bold]处理文件: {file_path.name}[/bold]")
    console.print(f"文件类型: [cyan]{suffix}[/cyan]")
    console.print(f"文件大小: [cyan]{file_path.stat().st_size / 1024:.2f} KB[/cyan]")
    
    try:
        from agent_framework.services.file_processors import get_processor
        
        processor = get_processor(suffix)
        
        console.print("\n[bold]正在解析文件...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("解析中...", total=None)
            
            async def parse():
                return await processor.to_text(file_path)
            
            text = asyncio.run(parse())
        
        console.print("\n[bold green]解析结果：[/bold green]")
        
        if save:
            Path(save).write_text(text, encoding="utf-8")
            console.print(f"[green]✓ 已保存到: {save}[/green]")
        
        if output == "markdown":
            console.print(Markdown(text))
        elif output == "json":
            import json
            console.print_json(json.dumps({"content": text}, ensure_ascii=False))
        else:
            if len(text) > 1000:
                console.print(text[:1000] + "\n...")
                console.print(f"\n[dim]共 {len(text)} 字符[/dim]")
            else:
                console.print(text)
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("fix")
@click.option("--error", "-e", help="错误信息")
@click.option("--file", "-f", "file_path", help="代码文件路径", type=click.Path(exists=True))
@click.option("--run-tests", is_flag=True, help="修复后运行测试")
@click.pass_obj
def fix_command(obj: dict, error: str | None, file_path: str | None, run_tests: bool):
    """
    错误修复
    
    使用agent-framework的ErrorFixer修复代码错误
    
    示例：
    $ alonechat agent fix --error "TypeError: ..." --file my_code.py
    $ alonechat agent fix --file my_code.py --run-tests
    """
    if not file_path:
        console.print("[red]请提供文件路径 (--file)[/red]")
        return
    
    console.print(f"\n[bold]分析错误...[/bold]")
    console.print(f"文件: [cyan]{file_path}[/cyan]")
    if error:
        console.print(f"错误: [red]{error}[/red]")
    
    try:
        from agent_framework.services.error_fixer import ErrorFixer
        
        llm = get_llm()
        fixer = ErrorFixer(llm=llm)
        
        console.print("\n[bold]正在修复...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("修复中...", total=None)
            
            if error:
                result = fixer.fix_runtime_error(file_path, error)
            else:
                result = fixer.fix_file(file_path, run_tests=run_tests)
        
        console.print("\n[bold green]修复结果：[/bold green]\n")
        
        if result.get("success"):
            console.print(f"[green]✓ 修复成功[/green]")
            
            if result.get("fixed_code"):
                console.print("\n[bold]修复后的代码：[/bold]\n")
                syntax = Syntax(
                    result["fixed_code"],
                    "python",
                    theme="monokai",
                    line_numbers=True
                )
                console.print(syntax)
                
                if click.confirm("\n是否保存修复后的代码？"):
                    Path(file_path).write_text(result["fixed_code"], encoding="utf-8")
                    console.print(f"[green]✓ 已保存到: {file_path}[/green]")
        else:
            console.print(f"[red]✗ 修复失败: {result.get('message', '未知错误')}[/red]")
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("skill")
@click.argument("skill_name", required=False)
@click.option("--list", "-l", "list_skills", is_flag=True, help="列出所有技能")
@click.option("--run", "-r", "run_skill", is_flag=True, help="运行技能")
@click.option("--params", "-p", help="技能参数 (JSON格式)")
@click.pass_obj
def skill_command(obj: dict, skill_name: str | None, list_skills: bool, run_skill: bool, params: str | None):
    """
    Skills管理
    
    使用agent-framework的SkillsRegistry管理技能
    
    示例：
    $ alonechat agent skill --list
    $ alonechat agent skill document_generation --run
    $ alonechat agent skill data_analysis --run --params '{"data": [...]}'
    """
    try:
        from agent_framework.tools.skills_registry import SkillsRegistry
        
        registry = SkillsRegistry()
        
        if list_skills:
            console.print("\n[bold cyan]可用技能列表：[/bold cyan]\n")
            
            skills = registry.list_skills()
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("技能名称", style="cyan")
            table.add_column("描述")
            table.add_column("工具", style="dim")
            
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
                console.print(f"\n[bold]运行技能: {skill_name}[/bold]")
                
                context = {}
                if params:
                    import json
                    context = json.loads(params)
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("执行中...", total=None)
                    
                    async def execute():
                        return await registry.execute(skill_name, context)
                    
                    result = asyncio.run(execute())
                
                console.print("\n[bold green]执行结果：[/bold green]")
                console.print(result)
            else:
                console.print(f"\n[bold]技能信息: {skill_name}[/bold]")
                skill = registry.get_skill(skill_name)
                if skill:
                    console.print(f"  名称: [cyan]{skill.get('name')}[/cyan]")
                    console.print(f"  描述: {skill.get('description')}")
                    console.print(f"  工具: {', '.join(skill.get('tools', []))}")
                else:
                    console.print(f"[red]未找到技能: {skill_name}[/red]")
        
        else:
            console.print("[yellow]请指定技能名称或使用 --list 查看所有技能[/yellow]")
    
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("rag")
@click.argument("action", type=click.Choice(["index", "search"]))
@click.argument("path_or_query")
@click.option("--k", default=5, help="返回结果数量")
@click.pass_obj
def rag_command(obj: dict, action: str, path_or_query: str, k: int):
    """
    RAG检索
    
    使用agent-framework的RAG功能进行代码检索
    
    示例：
    $ alonechat agent rag index ./src
    $ alonechat agent rag search "用户认证逻辑"
    $ alonechat agent rag search "查询内容" --k 10
    """
    try:
        from agent_framework.rag import RAGPipeline
        
        pipeline = RAGPipeline()
        
        if action == "index":
            console.print(f"\n[bold]索引目录: {path_or_query}[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("索引中...", total=None)
                
                async def index():
                    return await pipeline.ingest(path_or_query)
                
                count = asyncio.run(index())
            
            console.print(f"[green]✓ 索引完成！共索引 {count} 个文档[/green]")
        
        elif action == "search":
            console.print(f"\n[bold]搜索: {path_or_query}[/bold]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("搜索中...", total=None)
                
                async def search():
                    return await pipeline.retrieve(path_or_query, k=k)
                
                results = asyncio.run(search())
            
            console.print(f"\n[bold green]找到 {len(results)} 个结果：[/bold green]\n")
            
            for i, result in enumerate(results, 1):
                console.print(f"  [bold cyan]{i}. {result.get('source', '未知')}[/bold cyan]")
                console.print(f"     相似度: {result.get('score', 0):.4f}")
                content = result.get('content', '')
                if len(content) > 100:
                    console.print(f"     [dim]{content[:100]}...[/dim]\n")
                else:
                    console.print(f"     [dim]{content}[/dim]\n")
    
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("generate")
@click.argument("type", type=click.Choice(["ppt", "excel", "report", "doc"]))
@click.option("--request", "-r", required=True, help="生成请求描述")
@click.option("--output", "-o", required=True, help="输出文件路径")
@click.option("--data", "-d", help="数据文件路径 (JSON)")
@click.pass_obj
def generate_command(obj: dict, type: str, request: str, output: str, data: str | None):
    """
    文件生成
    
    使用agent-framework的FileGenerators生成各种文件
    
    示例：
    $ alonechat agent generate ppt --request "产品介绍PPT" --output product.pptx
    $ alonechat agent generate excel --request "销售数据报表" --output sales.xlsx
    $ alonechat agent generate report --request "季度报告" --output report.docx
    """
    console.print(f"\n[bold]生成{type.upper()}文件[/bold]")
    console.print(f"请求: [cyan]{request}[/cyan]")
    console.print(f"输出: [cyan]{output}[/cyan]")
    
    try:
        from agent_framework.services.file_generators import FileGeneratorService
        
        llm = get_llm()
        service = FileGeneratorService(llm=llm)
        
        context = {}
        if data:
            import json
            context = json.loads(Path(data).read_text())
        
        console.print("\n[bold]正在生成...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("生成中...", total=None)
            
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
        
        console.print(f"\n[bold green]✓ 生成完成！[/bold green]")
        console.print(f"文件已保存到: [cyan]{result_path}[/cyan]")
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@agent_commands.command("analyze")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="输出格式 (text/markdown)")
@click.pass_obj
def analyze_command(obj: dict, file_path: str, output: str | None):
    """
    数据分析
    
    使用agent-framework分析数据文件
    
    示例：
    $ alonechat agent analyze data.xlsx
    $ alonechat agent analyze sales.csv --output markdown
    """
    file_path = Path(file_path)
    
    console.print(f"\n[bold]分析文件: {file_path.name}[/bold]")
    
    try:
        from agent_framework.services.file_generators import FileGeneratorService
        
        llm = get_llm()
        service = FileGeneratorService(llm=llm)
        
        # 先读取文件
        from agent_framework.services.file_processors import get_processor
        processor = get_processor(file_path.suffix)
        data = asyncio.run(processor.to_text(file_path))
        
        console.print("\n[bold]正在分析...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("分析中...", total=None)
            
            async def analyze():
                return await service.analyze_data(data, "分析数据并给出洞察")
            
            result = asyncio.run(analyze())
        
        console.print("\n[bold green]分析结果：[/bold green]\n")
        
        if output == "markdown":
            console.print(Markdown(result))
        else:
            console.print(result)
        
    except ImportError:
        console.print("[red]错误: agent-framework未安装[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
