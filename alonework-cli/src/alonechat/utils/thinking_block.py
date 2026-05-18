"""
思维块实时显示模块 / Thinking Block Live Display Module

提供 / Provides:
- Ctrl+O 切换实时显示思维块 / Ctrl+O toggle live display of thinking blocks
- 转录模式下实时显示思考过程 / Real-time display of reasoning process in transcription mode
- 思维块管理 / Thinking block management
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text


class ThinkingBlockDisplay:
    """
    思维块实时显示器 / Thinking Block Live Display

    支持 Ctrl+O 切换实时显示AI的思考过程
    Supports Ctrl+O to toggle real-time display of AI reasoning process
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._visible = False
        self._reasoning_content: list[str] = []
        self._live: Optional[Live] = None
        self._content_cache: list[str] = []

    @property
    def is_visible(self) -> bool:
        """检查思维块是否可见 / Check if thinking block is visible"""
        return self._visible

    def toggle(self) -> bool:
        """
        切换思维块显示 / Toggle thinking block display

        Returns:
            切换后的状态 / New state after toggle
        """
        self._visible = not self._visible
        if self._visible:
            self._start_live_display()
        else:
            self._stop_live_display()
        return self._visible

    def set_visible(self, visible: bool) -> None:
        """
        设置思维块可见性 / Set thinking block visibility

        Args:
            visible: 是否可见 / Whether visible
        """
        if visible != self._visible:
            self.toggle()

    def _start_live_display(self) -> None:
        """开始实时显示 / Start live display"""
        if self._live is None:
            self._live = Live(
                self._render_panel(),
                console=self.console,
                refresh_per_second=10,
                transient=False,
            )
            self._live.__enter__()

    def _stop_live_display(self) -> None:
        """停止实时显示 / Stop live display"""
        if self._live is not None:
            try:
                self._live.__exit__(None, None, None)
            except Exception:
                pass
            self._live = None
        self.console.print()

    def _render_panel(self) -> Panel:
        """渲染思维面板 / Render thinking panel"""
        lines = self._reasoning_content[-50:] if self._reasoning_content else ["等待思考内容..."]

        text = Text()
        for i, line in enumerate(lines):
            text.append(line + "\n", style="dim cyan" if i < len(lines) - 1 else "cyan")

        return Panel(
            text,
            title="[bold yellow]思考过程 / Reasoning Process[/bold yellow]",
            border_style="yellow",
            subtitle=f"[dim]{len(self._reasoning_content)} tokens[/dim]",
        )

    def feed_reasoning(self, token: str) -> None:
        """
        输入思考token / Feed reasoning token

        Args:
            token: 思考文本token / Reasoning text token
        """
        self._reasoning_content.append(token)
        self._content_cache.append(token)
        if self._visible and self._live is not None:
            try:
                self._live.update(self._render_panel())
            except Exception:
                pass

    def get_reasoning_text(self) -> str:
        """
        获取完整思考文本 / Get full reasoning text

        Returns:
            思考文本 / Reasoning text
        """
        return "".join(self._reasoning_content)

    def clear(self) -> None:
        """清除思维内容 / Clear thinking content"""
        self._reasoning_content.clear()
        self._content_cache.clear()
        if self._visible and self._live is not None:
            try:
                self._live.update(self._render_panel())
            except Exception:
                pass

    def close(self) -> None:
        """关闭显示器 / Close display"""
        self._stop_live_display()
        self._reasoning_content.clear()
        self._content_cache.clear()
        self._visible = False
