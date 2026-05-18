"""
终端欢迎界面组件 / Terminal Welcome Screen Component
参考Claude Code界面设计 / Based on Claude Code interface design

提供美观的终端欢迎界面 / Provides beautiful terminal welcome screen:
- ASCII艺术Logo / ASCII art logo
- 功能提示卡片 / Feature tips card
- 状态信息显示 / Status info display
- 底部状态栏 / Bottom status bar
"""

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.padding import Padding
from typing import Optional
from pathlib import Path

console = Console()

ALONEWORK_ASCII_ART = """
              ▐▛███▜▌
             ▝▜█████▛▘
               ▘▘ ▝▝
"""

ALONEWORK_LOGO_SMALL = """
    ╭────────────────╮
    │  ▐▛███▜▌       │
    │ ▝▜█████▛▘      │
    │   ▘▘ ▝▝        │
    ╰────────────────╯
"""


class WelcomeScreen:
    """
    欢迎界面组件 / Welcome Screen Component
    
    参考Claude Code的界面设计风格
    Based on Claude Code interface design style
    """
    
    def __init__(
        self,
        version: str = "0.2.1",
        model: str = "deepseek-v4-flash",
        working_dir: Optional[str] = None,
        api_key_masked: Optional[str] = None,
    ):
        self.version = version
        self.model = model
        self.working_dir = working_dir or str(Path.cwd())
        self.api_key_masked = api_key_masked
    
    def _get_terminal_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80
    
    def _build_header(self) -> Text:
        """构建标题栏 / Build header bar"""
        header = Text()
        header.append("AloneWork ", style="bold cyan")
        header.append(f"v{self.version}", style="dim")
        return header
    
    def _build_tips_card(self) -> Panel:
        """构建提示卡片 / Build tips card"""
        tips_content = Text()
        tips_content.append("Tips for getting started\n", style="bold yellow")
        tips_content.append("Run ", style="default")
        tips_content.append("/init", style="cyan")
        tips_content.append(" to create a CLAUDE.md file with instructions for AloneWork\n", style="default")
        tips_content.append("Note: You have launched alonework in your working directory. For the\n", style="dim")
        tips_content.append("best experience, navigate to a project directory first.\n", style="dim")
        tips_content.append("─" * 40 + "\n", style="dim")
        tips_content.append("What's new\n", style="bold green")
        tips_content.append("• Added ", style="default")
        tips_content.append("--show-thinking", style="cyan")
        tips_content.append(" for live thinking display\n", style="default")
        tips_content.append("• Improved Chinese NLP support\n", style="default")
        tips_content.append("• Enhanced terminal UI with Claude-style interface\n", style="default")
        tips_content.append("• ", style="default")
        tips_content.append("/release-notes", style="cyan")
        tips_content.append(" for more\n", style="default")
        
        return Panel(
            tips_content,
            title="",
            border_style="dim",
            padding=(0, 1),
        )
    
    def _build_ascii_art(self) -> Text:
        """构建ASCII艺术 / Build ASCII art"""
        art = Text()
        lines = ALONEWORK_ASCII_ART.strip().split("\n")
        for line in lines:
            art.append(line + "\n", style="bold cyan")
        return art
    
    def _build_status_line(self) -> Text:
        """构建状态行 / Build status line"""
        status = Text()
        
        if self.api_key_masked:
            status.append(f"{self.api_key_masked}", style="dim")
            status.append(" · ", style="dim")
        
        status.append("API Usage ", style="default")
        status.append("Billing", style="cyan")
        status.append("  ", style="default")
        status.append(self.working_dir[:50] + "..." if len(self.working_dir) > 50 else self.working_dir, style="dim")
        
        return status
    
    def _build_whats_new(self) -> Text:
        """构建新功能说明 / Build what's new section"""
        content = Text()
        content.append("What's new\n", style="bold green")
        content.append("─" * 30 + "\n", style="dim")
        content.append("• ", style="default")
        content.append("--show-thinking", style="cyan")
        content.append(" now shows live thinking blocks\n", style="default")
        content.append("• Added ", style="default")
        content.append("--no-stream", style="cyan")
        content.append(" for non-streaming mode\n", style="default")
        content.append("• Improved Chinese text processing\n", style="default")
        content.append("• ", style="default")
        content.append("/release-notes", style="cyan")
        content.append(" for more\n", style="default")
        return content
    
    def render(self) -> None:
        """
        渲染完整的欢迎界面 / Render complete welcome screen
        
        参考Claude Code的布局风格
        """
        width = self._get_terminal_width()
        
        header_text = f"AloneWork v{self.version}"
        full_width = width - 4
        
        left_content = Text()
        left_content.append("\n")
        left_content.append("                    ", style="default")
        left_content.append("Welcome back!\n", style="bold white")
        left_content.append("\n")
        left_content.append(self._build_ascii_art())
        
        tips_panel = self._build_tips_card()
        
        right_renderable = tips_panel
        
        columns = Columns(
            [left_content, right_renderable],
            padding=2,
            expand=True,
        )
        
        main_panel = Panel(
            columns,
            title=f"[bold cyan]AloneWork v{self.version}[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
            expand=True,
        )
        
        console.print(main_panel)
        
        console.print()
        
        status_line = self._build_status_line()
        console.print(status_line, justify="left")
    
    def render_compact(self) -> None:
        """
        渲染紧凑版欢迎界面 / Render compact welcome screen
        """
        width = self._get_terminal_width()
        
        content = Text()
        content.append("\n")
        content.append("                    ", style="default")
        content.append("Welcome to AloneWork!\n\n", style="bold white")
        content.append("              ", style="default")
        content.append("▐▛███▜▌\n", style="bold cyan")
        content.append("             ", style="default")
        content.append("▝▜█████▛▘\n", style="bold cyan")
        content.append("               ", style="default")
        content.append("▘▘ ▝▝\n\n", style="bold cyan")
        content.append("  ", style="default")
        content.append("Tips: ", style="bold yellow")
        content.append("/init", style="cyan")
        content.append(" to initialize | ", style="default")
        content.append("/help", style="cyan")
        content.append(" for commands | ", style="default")
        content.append("?", style="cyan")
        content.append(" for shortcuts\n", style="default")
        
        panel = Panel(
            content,
            title=f"[bold cyan]AloneWork v{self.version}[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
        
        console.print(panel)
        
        status = self._build_status_line()
        console.print(status)


class StatusBar:
    """
    底部状态栏组件 / Bottom Status Bar Component
    
    显示当前状态、模型信息等
    Shows current status, model info, etc.
    """
    
    def __init__(
        self,
        model: str = "deepseek-v4-flash",
        effort: str = "high",
        logged_in: bool = True,
    ):
        self.model = model
        self.effort = effort
        self.logged_in = logged_in
    
    def render(self) -> str:
        """
        渲染状态栏 / Render status bar
        
        Returns:
            状态栏字符串 / Status bar string
        """
        parts = []
        
        parts.append("? for shortcuts")
        
        if self.logged_in:
            parts.append("Logged in")
        else:
            parts.append("Not logged in · Run /login")
        
        parts.append(f"● {self.effort} · /effort")
        
        return " " * 5 + "           ".join(parts)
    
    def print(self) -> None:
        """打印状态栏 / Print status bar"""
        width = self._get_width()
        separator = "─" * width
        
        console.print(f"\n{separator}")
        
        status_text = Text()
        status_text.append("? ", style="cyan")
        status_text.append("for shortcuts", style="dim")
        status_text.append(" " * 20, style="default")
        
        if self.logged_in:
            status_text.append("Logged in", style="green")
        else:
            status_text.append("Not logged in", style="yellow")
            status_text.append(" · Run ", style="dim")
            status_text.append("/login", style="cyan")
        
        status_text.append(" " * 20, style="default")
        status_text.append("● ", style="red")
        status_text.append(self.effort, style="bold")
        status_text.append(" · ", style="dim")
        status_text.append("/effort", style="cyan")
        
        console.print(status_text)
    
    def _get_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80


class InputPrompt:
    """
    输入提示符组件 / Input Prompt Component
    
    显示美化的输入提示符
    Shows beautified input prompt
    """
    
    def __init__(self, session_name: Optional[str] = None):
        self.session_name = session_name
    
    def render(self) -> None:
        """渲染输入提示符 / Render input prompt"""
        width = self._get_width()
        separator = "─" * width
        
        console.print(f"\n{separator}")
        
        prompt = Text()
        prompt.append("> ", style="bold green")
        
        console.print(prompt, end="")
    
    def _get_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80


def show_welcome(
    version: str = "0.2.1",
    model: str = "deepseek-v4-flash",
    working_dir: Optional[str] = None,
    api_key_masked: Optional[str] = None,
    compact: bool = False,
) -> None:
    """
    显示欢迎界面 / Show welcome screen
    
    便捷函数 / Convenience function
    
    Args:
        version: 版本号 / Version number
        model: 模型名称 / Model name
        working_dir: 工作目录 / Working directory
        api_key_masked: 遮蔽后的API密钥 / Masked API key
        compact: 是否使用紧凑模式 / Use compact mode
    """
    screen = WelcomeScreen(
        version=version,
        model=model,
        working_dir=working_dir,
        api_key_masked=api_key_masked,
    )
    
    if compact:
        screen.render_compact()
    else:
        screen.render()
    
    status = StatusBar(model=model, effort="high")
    status.print()


def show_input_prompt(session_name: Optional[str] = None) -> None:
    """
    显示输入提示符 / Show input prompt
    
    便捷函数 / Convenience function
    """
    prompt = InputPrompt(session_name=session_name)
    prompt.render()
