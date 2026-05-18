"""
/claude-api å½ä»¤ - éè¿ Claude API æå»ºåºç¨ / Build apps with Claude API

ç®¡çClaude APIéç½®åæè?/ Manage Claude API configuration and skills
çæ¬ / Version: 2.1.69
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
    éè¿ Claude API æå»ºåºç¨ / Build apps with Claude API
    
    ç¨æ³ / Usage:
        /claude-api                   æ¾ç¤ºAPIç¶æ?/ Show API status
        /claude-api config            éç½®APIåæ° / Configure API
        /claude-api skill <name>      ä½¿ç¨APIæè?/ Use API skill
        /claude-api list              ååºå¯ç¨æè?/ List available skills
        /claude-api test              æµè¯APIè¿æ¥ / Test API connection
    
    ç¤ºä¾ / Examples:
        /claude-api                   æ¥çç¶æ?/ View status
        /claude-api config            éç½®API / Configure API
        /claude-api list              ååºæè?/ List skills
        /claude-api test              æµè¯è¿æ¥ / Test connection
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
            {"name": "chat", "description": "å¯¹è¯è¡¥å¨ / Chat completion", "endpoint": "/messages"},
            {"name": "stream", "description": "æµå¼å¯¹è¯ / Stream chat", "endpoint": "/messages?stream=true"},
            {"name": "analyze", "description": "ææ¬åæ / Text analysis", "endpoint": "/messages"},
            {"name": "code", "description": "ä»£ç çæ / Code generation", "endpoint": "/messages"},
            {"name": "summarize", "description": "æè¦çæ / Summarization", "endpoint": "/messages"},
        ]
    
    def _save_skills(skills: list[dict]) -> None:
        with open(skills_file, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
    
    config = _load_config()
    
    if not args:
        has_key = bool(config.get("api_key"))
        console.print(Panel(
            f"[bold cyan]Claude API ç¶æ?/ Status[/bold cyan]\n\n"
            f"[dim]APIå¯é¥ / API Key: {'[green]å·²éç½?/ Configured[/green]' if has_key else '[yellow]æªéç½?/ Not configured[/yellow]'}[/dim]\n"
            f"[dim]æ¨¡å / Model: {config.get('model', 'æªè®¾ç½?/ Not set')}[/dim]\n"
            f"[dim]ç«¯ç¹ / Endpoint: {config.get('endpoint', '-')}[/dim]\n"
            f"[dim]æå¤§Token / Max tokens: {config.get('max_tokens', '-')}[/dim]\n"
            f"[dim]æ¸©åº¦ / Temperature: {config.get('temperature', '-')}[/dim]",
            title="Claude API",
            border_style="cyan"
        ))
        
        if not has_key:
            console.print("\n[yellow]æç¤º: ä½¿ç¨ /claude-api config éç½®APIå¯é¥ / Use /claude-api config to set API key[/yellow]")
        return
    
    subcommand = args[0]
    
    if subcommand == "config":
        console.print("[bold cyan]Claude API éç½® / Configuration[/bold cyan]\n")
        
        current_key = config.get("api_key", "")
        api_key = Prompt.ask(
            "[cyan]APIå¯é¥ / API Key[/cyan]",
            default="****" if current_key else "",
            password=True,
        )
        if api_key and api_key != "****":
            config["api_key"] = api_key
        
        model = Prompt.ask(
            "[cyan]æ¨¡å / Model[/cyan]",
            default=config.get("model", "claude-3-opus-20240229"),
        )
        config["model"] = model
        
        max_tokens_str = Prompt.ask(
            "[cyan]æå¤§Token / Max tokens[/cyan]",
            default=str(config.get("max_tokens", 4096)),
        )
        try:
            config["max_tokens"] = int(max_tokens_str)
        except ValueError:
            console.print("[yellow]æ ææ°å­ï¼ä½¿ç¨é»è®¤å?/ Invalid number, using default[/yellow]")
        
        temperature_str = Prompt.ask(
            "[cyan]æ¸©åº¦ / Temperature (0.0-1.0)[/cyan]",
            default=str(config.get("temperature", 0.7)),
        )
        try:
            config["temperature"] = float(temperature_str)
        except ValueError:
            console.print("[yellow]æ ææ°å­ï¼ä½¿ç¨é»è®¤å?/ Invalid number, using default[/yellow]")
        
        _save_config(config)
        console.print(f"\n[green]â?éç½®å·²ä¿å­?/ Config saved to {config_file}[/green]")
        return
    
    if subcommand == "list":
        skills = _load_skills()
        
        table = Table(title="Claude API æè?/ Skills", show_header=True)
        table.add_column("åç§° / Name", style="cyan")
        table.add_column("æè¿° / Description")
        table.add_column("ç«¯ç¹ / Endpoint", style="dim")
        
        for skill in skills:
            table.add_row(skill["name"], skill["description"], skill.get("endpoint", "-"))
        
        console.print(table)
        
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("\n[yellow]æç¤º: è¯·åéç½®APIå¯é¥ / Please configure API key first: /claude-api config[/yellow]")
        return
    
    if subcommand == "test":
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("[red]è¯·åéç½®APIå¯é¥ / Please configure API key first: /claude-api config[/red]")
            return
        
        console.print("[yellow]æµè¯APIè¿æ¥ä¸?.. / Testing API connection...[/yellow]")
        
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
                console.print(f"[green]â?APIè¿æ¥æå / API connection successful[/green]")
            elif response.status_code == 401:
                console.print("[red]â?APIå¯é¥æ æ / Invalid API key[/red]")
            else:
                console.print(f"[red]â?è¿æ¥å¤±è´¥ / Connection failed: HTTP {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]â?è¿æ¥å¼å¸¸ / Connection error: {e}[/red]")
        return
    
    if subcommand == "skill" and len(args) >= 2:
        skill_name = args[1]
        skill_args = args[2:]
        skills = _load_skills()
        
        skill = next((s for s in skills if s["name"] == skill_name), None)
        if not skill:
            console.print(f"[red]æè½æªæ¾å° / Skill not found: {skill_name}[/red]")
            console.print("[dim]ä½¿ç¨ /claude-api list æ¥çå¯ç¨æè½[/dim]")
            return
        
        has_key = bool(config.get("api_key"))
        if not has_key:
            console.print("[red]è¯·åéç½®APIå¯é¥ / Please configure API key first: /claude-api config[/red]")
            return
        
        console.print(f"[green]â?æè½å·²éæ© / Skill selected: {skill_name}[/green]")
        console.print(f"[dim]{skill['description']}[/dim]")
        
        if skill_args:
            console.print(f"[dim]åæ° / Args: {' '.join(skill_args)}[/dim]")
        
        console.print("\n[dim]æç¤º: æ­¤æè½å°å¨ä¸æ¬¡å¯¹è¯ä¸­ä½¿ç¨ / This skill will be used in next conversation[/dim]")
        return
    
    console.print(f"[red]æªç¥å­å½ä»?/ Unknown subcommand: {subcommand}[/red]")
    console.print("[dim]å¯ç¨å­å½ä»? config, list, test, skill[/dim]")
