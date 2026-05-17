"""
代理执行器 / Agent Executor

执行子代理任务 / Executes subagent tasks
"""

from typing import Optional, Any
from rich.console import Console
from rich.panel import Panel

from alonechat.agents.definition import AgentDefinition
from alonechat.agents.manager import AgentManager

console = Console()


class AgentExecutor:
    """代理执行器 / Agent Executor"""
    
    def __init__(self, agent_manager: AgentManager, config_manager=None):
        self.agent_manager = agent_manager
        self.config_manager = config_manager
    
    def execute(
        self,
        agent_name: str,
        task: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        执行代理任务 / Execute agent task
        
        Args:
            agent_name: 代理名称 / Agent name
            task: 任务描述 / Task description
            context: 执行上下文 / Execution context
        
        Returns:
            执行结果 / Execution result
        """
        agent = self.agent_manager.get(agent_name)
        
        if agent is None:
            console.print(f"[red]未知代理 / Unknown agent: {agent_name}[/red]")
            return ""
        
        if not agent.enabled:
            console.print(f"[yellow]代理已禁用 / Agent is disabled: {agent_name}[/yellow]")
            return ""
        
        console.print(Panel(
            f"[bold cyan]代理: {agent.name}[/bold cyan]\n\n"
            f"[dim]{agent.description}[/dim]\n\n"
            f"[bold]任务 / Task:[/bold] {task}",
            border_style="cyan"
        ))
        
        return self._run_agent(agent, task, context)
    
    def _run_agent(
        self,
        agent: AgentDefinition,
        task: str,
        context: Optional[dict] = None,
    ) -> str:
        """运行代理 / Run agent"""
        from alonechat.models import ModelRouter, ChatResponse
        
        if self.config_manager is None:
            console.print("[red]配置管理器不可用 / Config manager not available[/red]")
            return ""
        
        config = self.config_manager.load_config()
        model_router = ModelRouter(config)
        
        system_prompt = agent.prompt
        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
            system_prompt += f"\n\n上下文 / Context:\n{context_str}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]
        
        console.print(f"\n[bold green]{agent.name}[/bold green] 正在执行... / Executing...\n")
        
        try:
            with console.status("[bold green]思考中... / Thinking...[/bold green]"):
                response = model_router.chat_with_reasoning(messages=messages)
            
            if isinstance(response, ChatResponse):
                return response.content
            return str(response)
            
        except Exception as e:
            console.print(f"[red]执行错误 / Execution error: {e}[/red]")
            return ""
    
    def list_available_agents(self) -> None:
        """列出可用代理 / List available agents"""
        from rich.table import Table
        
        agents = self.agent_manager.list_agents()
        
        table = Table(title="可用代理 / Available Agents", show_header=True)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description")
        table.add_column("模型 / Model", style="dim")
        table.add_column("状态 / Status")
        
        for agent in agents:
            status = "[green]启用 / Enabled[/green]" if agent.enabled else "[yellow]禁用 / Disabled[/yellow]"
            table.add_row(
                agent.name,
                agent.description[:50] + "..." if len(agent.description) > 50 else agent.description,
                agent.model.value,
                status,
            )
        
        console.print(table)
