"""
CLI模式管理器 - CLI Mode Manager

实现CLI层的交互模式管理，提供Rich终端审批界面
Implements interaction mode management for CLI layer with Rich terminal approval interface

功能 / Features:
- 继承agent-framework的ModeManager基类
- 使用Rich终端界面进行用户确认
- 支持批量批准
- 显示模式切换通知
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.text import Text

from agent_framework.core.mode_manager import ModeManager
from agent_framework.core.types import InteractionMode, ModeConfig


console = Console()


class CliModeManager(ModeManager):
    """
    CLI模式管理器 - CLI Mode Manager
    
    继承ModeManager基类，实现Rich终端的用户交互
    Extends ModeManager base class with Rich terminal user interaction
    
    特性 / Features:
    - 使用Rich Confirm进行用户确认
    - 显示工具执行详情
    - 支持记住选择
    - 彩色模式指示
    """
    
    def __init__(
        self, 
        config: Optional[ModeConfig] = None,
        verbose: bool = False,
    ):
        """
        初始化CLI模式管理器 / Initialize CLI mode manager
        
        Args:
            config: 模式配置 / Mode config
            verbose: 是否显示详细信息 / Whether to show verbose info
        """
        super().__init__(config)
        self.verbose = verbose
        self._remembered_approvals: Dict[str, bool] = {}
    
    async def request_approval(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """
        请求用户批准工具执行 / Request user approval for tool execution
        
        使用Rich终端界面显示工具信息并请求用户确认
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        
        Returns:
            用户是否批准 / Whether user approved
        """
        if self._mode == InteractionMode.YOLO:
            if self.verbose:
                console.print(f"[dim]YOLO模式：自动批准 {tool_name} / YOLO mode: Auto-approving {tool_name}[/dim]")
            return True
        
        if not self.needs_confirmation(tool_name):
            return True
        
        cache_key = f"{tool_name}:{self._get_params_signature(params)}"
        if cache_key in self._remembered_approvals:
            return self._remembered_approvals[cache_key]
        
        self._display_tool_request(tool_name, params)
        
        try:
            approved = Confirm.ask(
                f"[bold yellow]允许执行 {tool_name}? / Allow {tool_name}?[/bold yellow]",
                default=False,
            )
            
            if approved:
                remember = Confirm.ask(
                    "[dim]记住此选择? / Remember this choice?[/dim]",
                    default=False,
                )
                if remember:
                    self._remembered_approvals[cache_key] = approved
            
            return approved
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]已取消 / Cancelled[/red]")
            return False
    
    def _get_params_signature(self, params: Dict[str, Any]) -> str:
        """
        获取参数签名用于缓存 / Get params signature for caching
        
        Args:
            params: 工具参数 / Tool parameters
        
        Returns:
            参数签名字符串 / Params signature string
        """
        safe_params = {}
        for k, v in params.items():
            if isinstance(v, str) and len(v) > 50:
                safe_params[k] = v[:50] + "..."
            else:
                safe_params[k] = v
        return str(sorted(safe_params.items()))
    
    def _display_tool_request(self, tool_name: str, params: Dict[str, Any]) -> None:
        """
        显示工具执行请求 / Display tool execution request
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        """
        console.print()
        
        params_text = Text()
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 100:
                display_value = value[:100] + "..."
            else:
                display_value = str(value)
            params_text.append(f"\n  {key}: ", style="cyan")
            params_text.append(display_value, style="white")
        
        panel_content = Text()
        panel_content.append(f"工具: {tool_name}", style="bold yellow")
        panel_content.append("\n参数:", style="cyan")
        panel_content.append(params_text)
        
        console.print(Panel(
            panel_content,
            title="[bold red]⚠ 工具执行请求 / Tool Execution Request[/bold red]",
            border_style="yellow",
        ))
    
    def notify_mode_change(self, old_mode: InteractionMode, new_mode: InteractionMode) -> None:
        """
        通知模式变化 / Notify mode change
        
        使用Rich终端显示模式切换通知
        
        Args:
            old_mode: 旧模式 / Old mode
            new_mode: 新模式 / New mode
        """
        old_icon = self._get_mode_icon(old_mode)
        new_icon = self._get_mode_icon(new_mode)
        new_color = self._get_mode_color(new_mode)
        
        console.print()
        console.print(Panel(
            f"{old_icon} {old_mode.value.upper()} → {new_icon} {new_mode.value.upper()}\n\n"
            f"{self.get_mode_description()}",
            title="[bold cyan]模式切换 / Mode Changed[/bold cyan]",
            border_style=new_color,
        ))
    
    def _get_mode_icon(self, mode: InteractionMode) -> str:
        """获取模式图标 / Get mode icon"""
        icons = {
            InteractionMode.PLAN: "🔍",
            InteractionMode.AGENT: "🤖",
            InteractionMode.YOLO: "🚀",
        }
        return icons.get(mode, "❓")
    
    def _get_mode_color(self, mode: InteractionMode) -> str:
        """获取模式颜色 / Get mode color"""
        colors = {
            InteractionMode.PLAN: "blue",
            InteractionMode.AGENT: "green",
            InteractionMode.YOLO: "yellow",
        }
        return colors.get(mode, "white")
    
    def display_mode_status(self) -> None:
        """
        显示当前模式状态 / Display current mode status
        
        在状态栏显示当前模式的简洁信息
        """
        icon = self.get_mode_icon()
        color = self.get_mode_color()
        mode_name = self._mode.value.upper()
        
        console.print(f"[{color}]{icon} 模式: {mode_name}[/{color}]")
    
    def get_status_bar_text(self) -> str:
        """
        获取状态栏文本 / Get status bar text
        
        Returns:
            用于状态栏显示的文本 / Text for status bar display
        """
        icon = self.get_mode_icon()
        mode_name = self._mode.value.upper()
        return f"{icon} {mode_name}"
    
    def clear_remembered_approvals(self) -> None:
        """
        清除记住的批准 / Clear remembered approvals
        
        清除所有缓存的批准决定
        """
        self._remembered_approvals.clear()
        if self.verbose:
            console.print("[dim]已清除记住的批准 / Cleared remembered approvals[/dim]")
    
    def cycle_mode(self) -> InteractionMode:
        """
        循环切换模式 / Cycle through modes
        
        按顺序切换模式: PLAN → AGENT → YOLO → PLAN
        
        Returns:
            新模式 / New mode
        """
        mode_order = [InteractionMode.PLAN, InteractionMode.AGENT, InteractionMode.YOLO]
        current_index = mode_order.index(self._mode)
        next_index = (current_index + 1) % len(mode_order)
        next_mode = mode_order[next_index]
        
        self.set_mode(next_mode)
        return next_mode
