"""
/agents 命令 - 管理子代理 / Manage subagents
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def agents_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理子代理 / Manage subagents
    
    用法 / Usage:
        /agents              - 列出所有代理 / List all agents
        /agents <name>       - 显示代理详情 / Show agent details
        /agents run <name>   - 运行代理 / Run agent
    """
    from alonechat.agents import AgentManager, AgentExecutor
    
    agent_manager = AgentManager()
    config_manager = obj.get("config_manager")
    executor = AgentExecutor(agent_manager, config_manager)
    
    if not args:
        executor.list_available_agents()
        return
    
    subcommand = args[0]
    
    if subcommand == "run" and len(args) >= 2:
        agent_name = args[1]
        task = " ".join(args[2:]) if len(args) > 2 else "执行默认任务 / Execute default task"
        executor.execute(agent_name, task)
        return
    
    if subcommand == "enable" and len(args) >= 2:
        agent_name = args[1]
        if agent_manager.enable(agent_name):
            console.print(f"[green]✓ 已启用代理 / Agent enabled: {agent_name}[/green]")
        else:
            console.print(f"[red]未知代理 / Unknown agent: {agent_name}[/red]")
        return
    
    if subcommand == "disable" and len(args) >= 2:
        agent_name = args[1]
        if agent_manager.disable(agent_name):
            console.print(f"[green]✓ 已禁用代理 / Agent disabled: {agent_name}[/green]")
        else:
            console.print(f"[red]未知代理 / Unknown agent: {agent_name}[/red]")
        return
    
    agent = agent_manager.get(subcommand)
    if agent:
        info = agent_manager.get_agent_info(subcommand)
        console.print(Panel(
            f"[bold cyan]{agent.name}[/bold cyan]\n\n"
            f"{agent.description}\n\n"
            f"[dim]模型 / Model: {agent.model.value}[/dim]\n"
            f"[dim]工具 / Tools: {', '.join(agent.tools) if agent.tools else '全部 / All'}[/dim]\n"
            f"[dim]状态 / Status: {'启用 / Enabled' if agent.enabled else '禁用 / Disabled'}[/dim]",
            title="代理详情 / Agent Details",
            border_style="cyan"
        ))
        return
    
    console.print(f"[red]未知命令或代理 / Unknown command or agent: {subcommand}[/red]")
    console.print("[dim]使用 /agents 查看所有代理 / Use /agents to list all agents[/dim]")
