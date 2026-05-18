"""
状态栏组件 / Status Bar Component
参考Claude Code界面设计 / Based on Claude Code interface design

提供实时状态显示 / Provides real-time status display:
- 模型状态 / Model status
- API使用情况 / API usage
- 会话信息 / Session info
- 快捷键提示 / Keyboard shortcuts
"""

from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import time

console = Console()


class StatusState(Enum):
    """状态枚举 / Status enum"""
    IDLE = "idle"
    THINKING = "thinking"
    STREAMING = "streaming"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class UsageInfo:
    """使用量信息 / Usage info"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_rate: float = 0.0


class InteractiveStatusBar:
    """
    交互式状态栏 / Interactive Status Bar
    
    支持实时更新和动态显示
    Supports real-time updates and dynamic display
    """
    
    def __init__(
        self,
        model: str = "deepseek-v4-flash",
        effort: str = "high",
        logged_in: bool = True,
        session_name: Optional[str] = None,
    ):
        self.model = model
        self.effort = effort
        self.logged_in = logged_in
        self.session_name = session_name
        self.state = StatusState.IDLE
        self.usage: Optional[UsageInfo] = None
        self._spinner = Spinner("dots", text="", style="cyan")
        self._start_time: Optional[float] = None
    
    def _get_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80
    
    def _build_left_section(self) -> Text:
        """构建左侧区域 / Build left section"""
        left = Text()
        
        if self.state == StatusState.THINKING:
            left.append("⏳ ", style="yellow")
            left.append("Thinking...", style="bold yellow")
        elif self.state == StatusState.STREAMING:
            left.append("✨ ", style="cyan")
            left.append("Streaming...", style="bold cyan")
        elif self.state == StatusState.ERROR:
            left.append("❌ ", style="red")
            left.append("Error", style="bold red")
        elif self.state == StatusState.SUCCESS:
            left.append("✓ ", style="green")
            left.append("Done", style="bold green")
        else:
            left.append("? ", style="cyan")
            left.append("for shortcuts", style="dim")
        
        return left
    
    def _build_center_section(self) -> Text:
        """构建中间区域 / Build center section"""
        center = Text()
        
        if self.session_name:
            center.append("[", style="dim")
            center.append(self.session_name[:20], style="cyan")
            center.append("]", style="dim")
            center.append(" ", style="default")
        
        if self.usage:
            center.append(f"{self.usage.total_tokens:,}", style="green")
            center.append(" tokens", style="dim")
            if self.usage.cache_hit_rate > 0:
                center.append(" (", style="dim")
                center.append(f"{self.usage.cache_hit_rate*100:.0f}%", style="yellow")
                center.append(" cached)", style="dim")
        
        return center
    
    def _build_right_section(self) -> Text:
        """构建右侧区域 / Build right section"""
        right = Text()
        
        if self._start_time:
            elapsed = time.time() - self._start_time
            right.append(f"{elapsed:.1f}s", style="dim")
            right.append(" ", style="default")
        
        right.append("● ", style="red")
        right.append(self.effort, style="bold")
        right.append(" · ", style="dim")
        right.append("/effort", style="cyan")
        
        return right
    
    def render(self) -> Text:
        """渲染状态栏 / Render status bar"""
        width = self._get_width()
        
        separator = Text()
        separator.append("─" * width, style="dim")
        
        line = Text()
        line.append(self._build_left_section())
        line.append(" " * 10, style="default")
        line.append(self._build_center_section())
        line.append(" " * 10, style="default")
        line.append(self._build_right_section())
        
        result = Text()
        result.append(separator)
        result.append("\n")
        result.append(line)
        
        return result
    
    def print(self) -> None:
        """打印状态栏 / Print status bar"""
        console.print(self.render())
    
    def set_state(self, state: StatusState) -> None:
        """
        设置状态 / Set state
        
        Args:
            state: 新状态 / New state
        """
        self.state = state
        if state in (StatusState.THINKING, StatusState.STREAMING):
            self._start_time = time.time()
        elif state in (StatusState.SUCCESS, StatusState.ERROR):
            pass
    
    def set_usage(self, usage: UsageInfo) -> None:
        """
        设置使用量 / Set usage
        
        Args:
            usage: 使用量信息 / Usage info
        """
        self.usage = usage
    
    def start_timer(self) -> None:
        """开始计时 / Start timer"""
        self._start_time = time.time()
    
    def stop_timer(self) -> float:
        """
        停止计时 / Stop timer
        
        Returns:
            经过时间 / Elapsed time
        """
        if self._start_time:
            elapsed = time.time() - self._start_time
            self._start_time = None
            return elapsed
        return 0.0


class BottomBar:
    """
    底部信息栏 / Bottom Information Bar
    
    显示登录状态、模型信息等
    Shows login status, model info, etc.
    """
    
    def __init__(
        self,
        logged_in: bool = True,
        model: str = "deepseek-v4-flash",
        api_key_masked: Optional[str] = None,
    ):
        self.logged_in = logged_in
        self.model = model
        self.api_key_masked = api_key_masked
    
    def _get_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80
    
    def render(self) -> Text:
        """渲染底部栏 / Render bottom bar"""
        width = self._get_width()
        
        separator = Text()
        separator.append("─" * width, style="dim")
        
        line = Text()
        
        if self.api_key_masked:
            line.append(self.api_key_masked, style="dim")
            line.append(" · ", style="dim")
        
        line.append("API Usage ", style="default")
        line.append("Billing", style="cyan")
        
        return Text().append(separator).append("\n").append(line)
    
    def print(self) -> None:
        """打印底部栏 / Print bottom bar"""
        console.print(self.render())


class InputBar:
    """
    输入栏组件 / Input Bar Component
    
    显示输入提示符和当前上下文
    Shows input prompt and current context
    """
    
    def __init__(
        self,
        session_name: Optional[str] = None,
        context_tokens: int = 0,
        max_tokens: int = 1_000_000,
    ):
        self.session_name = session_name
        self.context_tokens = context_tokens
        self.max_tokens = max_tokens
    
    def _get_width(self) -> int:
        """获取终端宽度 / Get terminal width"""
        try:
            return console.width
        except Exception:
            return 80
    
    def render(self) -> Text:
        """渲染输入栏 / Render input bar"""
        width = self._get_width()
        
        separator = Text()
        separator.append("─" * width, style="dim")
        
        line = Text()
        
        if self.session_name:
            line.append("[", style="dim")
            line.append(self.session_name, style="cyan")
            line.append("] ", style="dim")
        
        line.append("> ", style="bold green")
        
        result = Text()
        result.append(separator)
        result.append("\n")
        result.append(line)
        
        return result
    
    def print(self) -> None:
        """打印输入栏 / Print input bar"""
        console.print(self.render())
    
    def get_context_bar(self) -> Text:
        """
        获取上下文使用条 / Get context usage bar
        
        显示当前上下文使用情况
        Shows current context usage
        """
        if self.max_tokens <= 0:
            return Text()
        
        usage_ratio = self.context_tokens / self.max_tokens
        bar_width = 20
        filled = int(bar_width * usage_ratio)
        empty = bar_width - filled
        
        bar = Text()
        bar.append("Context: ", style="dim")
        bar.append("█" * filled, style="cyan" if usage_ratio < 0.8 else "yellow")
        bar.append("░" * empty, style="dim")
        bar.append(f" {self.context_tokens:,}/{self.max_tokens:,}", style="dim")
        
        return bar


def create_status_bar(
    model: str = "deepseek-v4-flash",
    effort: str = "high",
    logged_in: bool = True,
) -> InteractiveStatusBar:
    """
    创建状态栏 / Create status bar
    
    便捷函数 / Convenience function
    """
    return InteractiveStatusBar(
        model=model,
        effort=effort,
        logged_in=logged_in,
    )


def print_status_line(
    state: StatusState = StatusState.IDLE,
    model: str = "deepseek-v4-flash",
    effort: str = "high",
    usage: Optional[UsageInfo] = None,
) -> None:
    """
    打印状态行 / Print status line
    
    便捷函数 / Convenience function
    """
    bar = InteractiveStatusBar(model=model, effort=effort)
    bar.state = state
    if usage:
        bar.usage = usage
    bar.print()
