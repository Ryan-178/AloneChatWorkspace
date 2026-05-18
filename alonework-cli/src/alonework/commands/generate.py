"""
generateå½ä»¤ - ä»£ç çæ / generate command - Code generation

æ¯æ / Supports:
- å½æ°çæ / Function generation
- ç±»çæ?/ Class generation
- æ¨¡åçæ / Module generation
- é¡¹ç®èææ?/ Project scaffolding
"""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from alonework.config import ConfigManager
from alonework.models import ModelRouter, DEEPSEEK_MODEL
from alonework.code import CodeGenerator, CodeAnalyzer

console = Console()


@click.command()
@click.option("--type", "-t", "gen_type", help="çæç±»å / Generation type", 
              type=click.Choice(["function", "class", "module", "project"]))
@click.option("--name", "-n", help="åç§° / Name")
@click.option("--output", "-o", help="è¾åºè·¯å¾ / Output path", type=click.Path())
@click.option("--language", "-l", default="python", help="ç¼ç¨è¯­è¨ / Programming language")
@click.option("--test", is_flag=True, help="åæ¶çææµè¯ / Also generate tests")
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
    çæä»£ç  / Generate code
    
    æ¯æçæå½æ°ãç±»ãæ¨¡ååé¡¹ç®èææ?/ Support generating functions, classes, modules and project scaffolding
    """
    console.print(Panel.fit(
        "[bold cyan]ä»£ç çæ / Code Generation[/bold cyan]\n\n"
        "æ¯æçæ / Support generating:\n"
        "â?å½æ° (function)\n"
        "â?ç±?(class)\n"
        "â?æ¨¡å (module)\n"
        "â?é¡¹ç® (project)\n\n"
        f"[dim]æ¨¡å: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]æèæ¨¡å¼? å·²å¯ç?(reasoning_effort=high)[/dim]",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]éè¯¯: æªæ¾å°éç½®æä»?/ Error: Config file not found[/red]")
        console.print("è¯·åè¿è¡ / Please run: [cyan]alonechat init[/cyan]")
        return
    
    config = config_manager.load_config()
    
    if not gen_type:
        console.print("\nè¯·éæ©çæç±»å / Please select generation type:")
        console.print("  [1] å½æ° (function)")
        console.print("  [2] ç±?(class)")
        console.print("  [3] æ¨¡å (module)")
        console.print("  [4] é¡¹ç® (project)")
        
        choice = Prompt.ask("è¯·éæ© / Please select", choices=["1", "2", "3", "4"], default="1")
        gen_type = ["function", "class", "module", "project"][int(choice) - 1]
    
    if not name:
        name = Prompt.ask(f"è¯·è¾å¥{gen_type}åç§° / Please enter {gen_type} name")
    
    description = Prompt.ask(f"è¯·æè¿°{gen_type}çåè?/ Please describe the {gen_type}")
    
    console.print(f"\n[bold]æ­£å¨çæ{gen_type}... / Generating {gen_type}...[/bold]")
    console.print(f"[dim]ä½¿ç¨æ¨¡å / Using model: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]")
    
    model_router = ModelRouter(config)
    generator = CodeGenerator(model_router=model_router, console=console)
    
    with console.status("[bold green]çæä¸?.. / Generating...[/bold green]"):
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
    
    console.print(f"\n[bold green]çæçä»£ç ?/ Generated code:[/bold green]\n")
    
    if output:
        output_path = Path(output)
        output_path.write_text(result.code, encoding="utf-8")
        console.print(f"[green]â?ä»£ç å·²ä¿å­å° / Code saved to: {output_path}[/green]")
    else:
        syntax = Syntax(result.code, language, theme="monokai", line_numbers=True)
        console.print(syntax)
        
        if click.confirm("\næ¯å¦ä¿å­å°æä»¶ï¼ / Save to file?"):
            ext_map = {
                "python": ".py",
                "javascript": ".js",
                "typescript": ".ts",
                "java": ".java",
                "go": ".go",
                "rust": ".rs",
            }
            ext = ext_map.get(language, ".txt")
            filename = Prompt.ask("æä»¶å?/ Filename", default=f"{name}{ext}")
            Path(filename).write_text(result.code, encoding="utf-8")
            console.print(f"[green]â?å·²ä¿å­å° / Saved to: {filename}[/green]")
    
    if test:
        console.print(f"\n[bold]æ­£å¨çææµè¯... / Generating tests...[/bold]")
        
        with console.status("[bold green]çææµè¯ä¸?.. / Generating tests...[/bold green]"):
            test_result = generator.generate_tests(result.code, language)
        
        console.print(f"\n[bold green]çæçæµè¯?/ Generated tests:[/bold green]\n")
        syntax = Syntax(test_result.code, language, theme="monokai", line_numbers=True)
        console.print(syntax)
        
        if click.confirm("\næ¯å¦ä¿å­æµè¯æä»¶ï¼?/ Save test file?"):
            test_filename = Prompt.ask("æµè¯æä»¶å?/ Test filename", default=f"test_{name}.py")
            Path(test_filename).write_text(test_result.code, encoding="utf-8")
            console.print(f"[green]â?æµè¯å·²ä¿å­å° / Test saved to: {test_filename}[/green]")
