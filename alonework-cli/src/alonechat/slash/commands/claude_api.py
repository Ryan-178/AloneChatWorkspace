"""
/claude-api 命令 - 通过 Claude API 构建应用 / Build apps with Claude API

管理Claude API配置和技能 / Manage Claude API configuration and skills
版本 / Version: 2.1.69
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
import json

console = Console()


def claude_api_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    通过 Claude API 构建应用 / Build apps with Claude API
    
    用法 / Usage:
        /claude-api                   显示API状态 / Show API status
        /claude-api config            配置API参数 / Configure API
        /claude-api skill <name>      使用API技能 / Use API skill
        /claude-api list              列出可用技能 / List available skills
        /claude-api test              测试API连接 / Test API connection
    
    示例 / Examples:
        /claude-api                   查看状态 / View status
        /claude-api config            配置API / Configure API
        /claude-api list              列出技能 / List skills
        /claude-api test              测试连接 / Test connection
    """
    config_dir = Path.home() / ".alonechat" / "claude-api"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    skills_file = config_dir / "skills.json"
    
    def _load_config() -> dict:
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "api_key": "",
            "model": "claude-3-opus-20240229",
            "max_tokens": 4096,
            "temperature": 0.7,
            "endpoint": "https://api.anthropic.com/v1",
        }
    
    def _save_config(config: dict) -> None:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _load_skills() -> list[dict]:
        if skills_file.exists():
            try:
                with open(skills_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return [
            {"name": "chat", "description": "对话补全 / Chat completion", "endpoint": "/messages"},
            {"name": "stream", "description": "流式对话 / Stream chat", "endpoint": "/messages?stream=true"},
            {"name": "analyze", "description": "文本分析 / Text analysis", "endpoint": "/messages"},
            {"name": "code", "description": "代码生成 / Code generation", "endpoint": "/messages"},
            {"name": "summarize", "description": "摘要生成 / Summarization", "endpoint": "/messages"},
        ]
    
    def _save_skills(skills: list[dict]) -> None:
        with open(skills_file, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
    
    config = _load_config()
    
    if not args:
        has_key = bool(config.get("api_key"))
        console.print(Panel(
            f"[bold cyan]Claude API 状态 / Status[/bold cyan]\n\n"
            f"[dim]API密钥 / API Key: {'[green]已配置 / Configured[/green]' if has_key else '[yellow]未配置 / Not configured[/yellow]'}[/dim]\n"
            f"[dim]模型 / Model: {config.get('model', '未设置 / Not set')}[/dim]\n"
            f"[dim]端点 / Endpoint: {config.get('endpoint', '-')}[/dim]\n"
            f"[dim]最大Token / Max tokens: {config.get('max_tokens', '-')}[/dim]\n"
            f"[dim]温度 / Temperature: {config.get('temperature', '-')}[/dim]",
            title="Claude API",
            border_style="cyan"
        ))
        
        if not has_key:
            console.print("\n[yellow]提示: 使用 /claude-api config 配置API密钥 / Use /claude-api config to set API key[/yellow]")
        return
    
    subcommand = args[0]
    
    if subcommand == "config":
        console.print("[bold cyan]Claude API 配置 / Configuration[/bold cyan]\n")
        
        current_key = config.get("api_key", "")
        api_key = Prompt.ask(
            "[cyan]API密钥 / API Key[/cyan]",
            default="****" if current_key else "",
            password=True,
        )
        if api_key and api_key != "****":
            config["api_key"] = api_key
        
        model = Prompt.ask(
            "[cyan]模型 / Model[/cyan]",
            default=config.get("model", "claude-3-opus-20240229"),
        )
        config["model"] = model
        
        max_tokens_str = Prompt.ask(
            "[cyan]最大Token / Max tokens[/cyan]",
            default=str(config.get("max_tokens", 4096)),
        )
        try:
            config["max_tokens"] = int(max_tokens_str)
        except ValueError:
            console.print("[yellow]无效数字，使用默认值 / Invalid number, using default[/yellow]")
        
        temperature_str = Prompt.ask(
            "[cyan]温度 / Temperature (0.0-1.0)[/cyan]",
            default=str(config.get("temperature", 0.7)),
        )
        try:
            config["temperature"] = float(temperature_str)
        except ValueError:
            console.print("[yellow]无效数字，使用默认值 / Invalid number, using default[/yellow]")
        
        _save_config(config)
        console.print(f"\n[green]✓ 配置已保存 / Config saved to {config_file}[/green]")
        return
    
    if subcommand == "list":
        skills = _load_skills()
        
        table = Table(title="Claude API 技能 / Skills", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description")
        table.add_column("端点 / Endpoint", style="dim")
        
        for skill in skills:
            table.add_row(skill["name"], skill["description"], skill.get("endpoint", "-"))
        
        console.print(table)
        
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("\n[yellow]提示: 请先配置API密钥 / Please configure API key first: /claude-api config[/yellow]")
        return
    
    if subcommand == "test":
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("[red]请先配置API密钥 / Please configure API key first: /claude-api config[/red]")
            return
        
        console.print("[yellow]测试API连接中... / Testing API connection...[/yellow]")
        
        try:
            import httpx
            headers = {
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            data = {
                "model": config["model"],
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "ping"}],
            }
            response = httpx.post(
                f"{config['endpoint']}/messages",
                headers=headers,
                json=data,
                timeout=10,
            )
            
            if response.status_code == 200:
                console.print(f"[green]✓ API连接成功 / API connection successful[/green]")
            elif response.status_code == 401:
                console.print("[red]✗ API密钥无效 / Invalid API key[/red]")
            else:
                console.print(f"[red]✗ 连接失败 / Connection failed: HTTP {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]✗ 连接异常 / Connection error: {e}[/red]")
        return
    
    if subcommand == "skill" and len(args) >= 2:
        skill_name = args[1]
        skill_args = args[2:]
        skills = _load_skills()
        
        skill = next((s for s in skills if s["name"] == skill_name), None)
        if not skill:
            console.print(f"[red]技能未找到 / Skill not found: {skill_name}[/red]")
            console.print("[dim]使用 /claude-api list 查看可用技能[/dim]")
            return
        
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("[red]请先配置API密钥 / Please configure API key first: /claude-api config[/red]")
            return
        
        console.print(f"[green]✓ 技能已选择 / Skill selected: {skill_name}[/green]")
        console.print(f"[dim]{skill['description']}[/dim]")
        
        if skill_args:
            console.print(f"[dim]参数 / Args: {' '.join(skill_args)}[/dim]")
        
        console.print("\n[dim]提示: 此技能将在下次对话中使用 / This skill will be used in next conversation[/dim]")
        return
    
    console.print(f"[red]未知子命令 / Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]可用子命令: config, list, test, skill[/dim]")
