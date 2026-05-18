"""
ä»£çæ§è¡å?/ Agent Executor

æ§è¡å­ä»£çä»»å?/ Executes subagent tasks
"""

from typing import Optional, Any
from rich.console import Console
from rich.panel import Panel

from alonework.agents.definition import AgentDefinition
from alonework.agents.manager import AgentManager

console = Console()


class AgentExecutor:
    """ä»£çæ§è¡å?/ Agent Executor"""
    
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
        æ§è¡ä»£çä»»å¡ / Execute agent task
        
        Args:
            agent_name: ä»£çåç§° / Agent name
            task: ä»»å¡æè¿° / Task description
            context: æ§è¡ä¸ä¸æ?/ Execution context
        
        Returns:
            æ§è¡ç»æ / Execution result
        """
        agent = self.agent_manager.get(agent_name)
        
        if agent is None:
            console.print(f"[red]æªç¥ä»£ç / Unknown agent: {agent_name}[/red]")
            return ""
        
        if not agent.enabled:
            console.print(f"[yellow]ä»£çå·²ç¦ç?/ Agent is disabled: {agent_name}[/yellow]")
            return ""
        
        console.print(Panel(
            f"[bold cyan]ä»£ç: {agent.name}[/bold cyan]\n\n"
            f"[dim]{agent.description}[/dim]\n\n"
            f"[bold]ä»»å¡ / Task:[/bold] {task}",
            border_style="cyan"
        ))
        
        return self._run_agent(agent, task, context)
    
    def _run_agent(
        self,
        agent: AgentDefinition,
        task: str,
        context: Optional[dict] = None,
    ) -> str:
        """è¿è¡ä»£ç / Run agent"""
        from alonework.models import ModelRouter, ChatResponse
        
        if self.config_manager is None:
            console.print("[red]éç½®ç®¡çå¨ä¸å¯ç¨ / Config manager not available[/red]")
            return ""
        
        config = self.config_manager.load_config()
        model_router = ModelRouter(config)
        
        system_prompt = agent.prompt
        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
            system_prompt += f"\n\nä¸ä¸æ?/ Context:\n{context_str}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]
        
        console.print(f"\n[bold green]{agent.name}[/bold green] æ­£å¨æ§è¡... / Executing...\n")
        
        try:
            with console.status("[bold green]æèä¸­... / Thinking...[/bold green]"):
                response = model_router.chat_with_reasoning(messages=messages)
            
            if isinstance(response, ChatResponse):
                return response.content
            return str(response)
            
        except Exception as e:
            console.print(f"[red]æ§è¡éè¯¯ / Execution error: {e}[/red]")
            return ""
    
    def list_available_agents(self) -> None:
        """ååºå¯ç¨ä»£ç / List available agents"""
        from rich.table import Table
        
        agents = self.agent_manager.list_agents()
        
        table = Table(title="å¯ç¨ä»£ç / Available Agents", show_header=True)
        table.add_column("åç§° / Name", style="cyan")
        table.add_column("æè¿° / Description")
        table.add_column("æ¨¡å / Model", style="dim")
        table.add_column("ç¶æ?/ Status")
        
        for agent in agents:
            status = "[green]å¯ç¨ / Enabled[/green]" if agent.enabled else "[yellow]ç¦ç¨ / Disabled[/yellow]"
            table.add_row(
                agent.name,
                agent.description[:50] + "..." if len(agent.description) > 50 else agent.description,
                agent.model.value,
                status,
            )
        
        console.print(table)
