"""
generate命令 - 代码生成 / generate command - Code generation

支持 / Supports:
- 函数生成 / Function generation
- 类生成 / Class generation
- 模块生成 / Module generation
- 项目脚手架 / Project scaffolding
"""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter, DEEPSEEK_MODEL
from alonechat.code import CodeGenerator, CodeAnalyzer

console = Console()


@click.command()
@click.option("--type", "-t", "gen_type", help="生成类型 / Generation type", 
              type=click.Choice(["function", "class", "module", "project"]))
@click.option("--name", "-n", help="名称 / Name")
@click.option("--output", "-o", help="输出路径 / Output path", type=click.Path())
@click.option("--language", "-l", default="python", help="编程语言 / Programming language")
@click.option("--test", is_flag=True, help="同时生成测试 / Also generate tests")
@click.pass_obj
def generate_command(
    obj: dict,
    gen_type: str | None,
    name: str | None,
    output: str | None,
    language: str,
    test: bool,
) -> None:
    """
    生成代码 / Generate code
    
    支持生成函数、类、模块和项目脚手架 / Support generating functions, classes, modules and project scaffolding
    """
    console.print(Panel.fit(
        "[bold cyan]代码生成 / Code Generation[/bold cyan]\n\n"
        "支持生成 / Support generating:\n"
        "• 函数 (function)\n"
        "• 类 (class)\n"
        "• 模块 (module)\n"
        "• 项目 (project)\n\n"
        f"[dim]模型: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]思考模式: 已启用 (reasoning_effort=high)[/dim]",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]错误: 未找到配置文件 / Error: Config file not found[/red]")
        console.print("请先运行 / Please run: [cyan]alonechat init[/cyan]")
        return
    
    config = config_manager.load_config()
    
    if not gen_type:
        console.print("\n请选择生成类型 / Please select generation type:")
        console.print("  [1] 函数 (function)")
        console.print("  [2] 类 (class)")
        console.print("  [3] 模块 (module)")
        console.print("  [4] 项目 (project)")
        
        choice = Prompt.ask("请选择 / Please select", choices=["1", "2", "3", "4"], default="1")
        gen_type = ["function", "class", "module", "project"][int(choice) - 1]
    
    if not name:
        name = Prompt.ask(f"请输入{gen_type}名称 / Please enter {gen_type} name")
    
    description = Prompt.ask(f"请描述{gen_type}的功能 / Please describe the {gen_type}")
    
    console.print(f"\n[bold]正在生成{gen_type}... / Generating {gen_type}...[/bold]")
    console.print(f"[dim]使用模型 / Using model: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]")
    
    model_router = ModelRouter(config)
    generator = CodeGenerator(model_router=model_router, console=console)
    
    with console.status("[bold green]生成中... / Generating...[/bold green]"):
        if gen_type == "function":
            result = generator.generate_function(
                description=description,
                name=name,
                language=language,
            )
        elif gen_type == "class":
            result = generator.generate_class(
                description=description,
                name=name,
                language=language,
            )
        else:
            result = generator.generate_function(
                description=description,
                name=name,
                language=language,
            )
    
    console.print(f"\n[bold green]生成的代码 / Generated code:[/bold green]\n")
    
    if output:
        output_path = Path(output)
        output_path.write_text(result.code, encoding="utf-8")
        console.print(f"[green]✓ 代码已保存到 / Code saved to: {output_path}[/green]")
    else:
        syntax = Syntax(result.code, language, theme="monokai", line_numbers=True)
        console.print(syntax)
        
        if click.confirm("\n是否保存到文件？ / Save to file?"):
            ext_map = {
                "python": ".py",
                "javascript": ".js",
                "typescript": ".ts",
                "java": ".java",
                "go": ".go",
                "rust": ".rs",
            }
            ext = ext_map.get(language, ".txt")
            filename = Prompt.ask("文件名 / Filename", default=f"{name}{ext}")
            Path(filename).write_text(result.code, encoding="utf-8")
            console.print(f"[green]✓ 已保存到 / Saved to: {filename}[/green]")
    
    if test:
        console.print(f"\n[bold]正在生成测试... / Generating tests...[/bold]")
        
        with console.status("[bold green]生成测试中... / Generating tests...[/bold green]"):
            test_result = generator.generate_tests(result.code, language)
        
        console.print(f"\n[bold green]生成的测试 / Generated tests:[/bold green]\n")
        syntax = Syntax(test_result.code, language, theme="monokai", line_numbers=True)
        console.print(syntax)
        
        if click.confirm("\n是否保存测试文件？ / Save test file?"):
            test_filename = Prompt.ask("测试文件名 / Test filename", default=f"test_{name}.py")
            Path(test_filename).write_text(test_result.code, encoding="utf-8")
            console.print(f"[green]✓ 测试已保存到 / Test saved to: {test_filename}[/green]")
