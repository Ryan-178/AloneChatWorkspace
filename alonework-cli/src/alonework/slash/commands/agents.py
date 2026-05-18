"""
/agents å½ä»¤ - ç®¡çå­ä»£ç?/ Manage subagents
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def agents_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    ç®¡çå­ä»£ç?/ Manage subagents
    
    ç¨æ³ / Usage:
        /agents              - ååºææä»£ç?/ List all agents
        /agents <name>       - æ¾ç¤ºä»£çè¯¦æ / Show agent details
        /agents run <name>   - è¿è¡ä»£ç / Run agent
    """
    from alonework.agents import AgentManager, AgentExecutor
    
    agent_manager = AgentManager()
    config_manager = obj.get("config_manager")
    executor = AgentExecutor(agent_manager, config_manager)
    
    if not args:
        executor.list_available_agents()
        return
    
    subcommand = args[0]
    
    if subcommand == "run" and len(args) >= 2:
        agent_name = args[1]
        task = " ".join(args[2:]) if len(args) > 2 else "æ§è¡é»è®¤ä»»å¡ / Execute default task"
        executor.execute(agent_name, task)
        return
    
    if subcommand == "enable" and len(args) >= 2:
        agent_name = args[1]
        if agent_manager.enable(agent_name):
            console.print(f"[green]â?å·²å¯ç¨ä»£ç?/ Agent enabled: {agent_name}[/green]")
        else:
            console.print(f"[red]æªç¥ä»£ç / Unknown agent: {agent_name}[/red]")
        return
    
    if subcommand == "disable" and len(args) >= 2:
        agent_name = args[1]
        if agent_manager.disable(agent_name):
            console.print(f"[green]â?å·²ç¦ç¨ä»£ç?/ Agent disabled: {agent_name}[/green]")
        else:
            console.print(f"[red]æªç¥ä»£ç / Unknown agent: {agent_name}[/red]")
        return
    
    agent = agent_manager.get(subcommand)
    if agent:
        info = agent_manager.get_agent_info(subcommand)
        console.print(Panel(
            f"[bold cyan]{agent.name}[/bold cyan]\n\n"
            f"{agent.description}\n\n"
            f"[dim]æ¨¡å / Model: {agent.model.value}[/dim]\n"
            f"[dim]å·¥å· / Tools: {', '.join(agent.tools) if agent.tools else 'å¨é¨ / All'}[/dim]\n"
            f"[dim]ç¶æ?/ Status: {'å¯ç¨ / Enabled' if agent.enabled else 'ç¦ç¨ / Disabled'}[/dim]",
            title="ä»£çè¯¦æ / Agent Details",
            border_style="cyan"
        ))
        return
    
    console.print(f"[red]æªç¥å½ä»¤æä»£ç?/ Unknown command or agent: {subcommand}[/red]")
    console.print("[dim]ä½¿ç¨ /agents æ¥çææä»£ç?/ Use /agents to list all agents[/dim]")
