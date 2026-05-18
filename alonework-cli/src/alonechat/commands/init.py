"""
init命令 - 初始化项目配置 / init command - Initialize project config

创建.alonechatrc配置文件，配置API密钥等 / Create .alonechatrc config file
"""

import os
import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from alonechat.config import ConfigManager

console = Console()

DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"


@click.command()
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有配置 / Force overwrite")
@click.option("--api-key", help="API密钥 / API key")
@click.pass_obj
def init_command(obj: dict, force: bool, api_key: str | None) -> None:
    """
    初始化AloneChat配置 / Initialize AloneChat config
    
    创建.alonechatrc配置文件，配置API密钥 / Create .alonechatrc config file
    """
    console.print(Panel.fit(
        "[bold cyan]AloneChat 配置初始化 / Config Initialization[/bold cyan]\n\n"
        "本工具将帮助您 / This tool will help you:\n"
        "1. 创建配置文件 (.alonechatrc) / Create config file\n"
        "2. 配置API密钥（本地加密存储） / Configure API key (encrypted locally)\n\n"
        "[dim]模型: DeepSeek V4 Flash[/dim]\n"
        "[dim]所有配置均存储在本地，确保隐私安全 / All configs stored locally[/dim]",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    config_path = config_manager.config_path
    
    if config_path.exists() and not force:
        if not Confirm.ask(f"配置文件 {config_path} 已存在，是否覆盖？ / Config exists, overwrite?"):
            console.print("[yellow]初始化已取消 / Initialization cancelled[/yellow]")
            return
    
    console.print("\n[bold]步骤 1/2: 配置文件位置 / Config file location[/bold]")
    console.print(f"配置文件将创建在 / Config will be created at: [cyan]{config_path}[/cyan]")
    
    console.print("\n[bold]步骤 2/2: API密钥配置 / API key configuration[/bold]")
    console.print("[dim]使用 DeepSeek V4 Flash 模型 / Using DeepSeek V4 Flash model[/dim]")
    
    env_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if api_key:
        final_api_key = api_key
    elif env_api_key:
        console.print(f"[green]检测到环境变量 DEEPSEEK_API_KEY / Detected env var[/green]")
        use_env = Confirm.ask("使用环境变量中的API密钥？ / Use API key from env?", default=True)
        if use_env:
            final_api_key = env_api_key
        else:
            final_api_key = Prompt.ask(
                "\n请输入API密钥 / Enter API key",
                password=True,
                default=""
            )
    else:
        final_api_key = Prompt.ask(
            "\n请输入API密钥 / Enter API key",
            password=True,
            default=""
        )
    
    if not final_api_key:
        console.print("[red]错误: API密钥不能为空 / Error: API key cannot be empty[/red]")
        return
    
    console.print("\n[bold]正在创建配置文件... / Creating config file...[/bold]")
    
    config_data = {
        "version": "2.0",
        "model": {
            "provider": "deepseek",
            "name": DEEPSEEK_MODEL,
            "api_base": DEEPSEEK_API_BASE,
        },
        "context": {
            "max_tokens": 1000000,
            "compression_enabled": True
        },
        "privacy": {
            "code_local": True,
            "encryption_enabled": True,
            "log_enabled": False
        }
    }
    
    config_manager.save_config(config_data)
    
    encrypted_key = config_manager.encrypt_api_key(final_api_key)
    key_file = config_path.parent / ".alonechat_key"
    key_file.write_text(encrypted_key, encoding="utf-8")
    
    console.print("\n[bold green]✓ 配置初始化完成！ / Config initialized![/bold green]")
    console.print(f"\n配置文件已创建 / Config created: [cyan]{config_path}[/cyan]")
    console.print(f"API密钥已加密存储 / API key encrypted: [cyan]{key_file}[/cyan]")
    console.print(f"模型 / Model: [cyan]DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/cyan]")
    
    console.print("\n[bold]下一步 / Next steps:[/bold]")
    console.print("  $ alonechat chat        # 启动交互式对话 / Start interactive chat")
    console.print("  $ alonechat generate    # 生成代码 / Generate code")
    console.print("  $ alonechat commit      # 智能提交 / Smart commit")
    console.print("  $ alonechat --help      # 查看所有命令 / View all commands")
