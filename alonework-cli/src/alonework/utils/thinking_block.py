"""
æç»´åå®æ¶æ¾ç¤ºæ¨¡å?/ Thinking Block Live Display Module

æä¾ / Provides:
- Ctrl+O åæ¢å®æ¶æ¾ç¤ºæç»´å?/ Ctrl+O toggle live display of thinking blocks
- è½¬å½æ¨¡å¼ä¸å®æ¶æ¾ç¤ºæèè¿ç¨?/ Real-time display of reasoning process in transcription mode
- æç»´åç®¡ç?/ Thinking block management
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text


class ThinkingBlockDisplay:
    """
    æç»´åå®æ¶æ¾ç¤ºå¨ / Thinking Block Live Display

    æ¯æ Ctrl+O åæ¢å®æ¶æ¾ç¤ºAIçæèè¿ç¨?    Supports Ctrl+O to toggle real-time display of AI reasoning process
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._visible = False
        self._reasoning_content: list[str] = []
        self._live: Optional[Live] = None
        self._content_cache: list[str] = []

    @property
    def is_visible(self) -> bool:
        """æ£æ¥æç»´åæ¯å¦å¯è§?/ Check if thinking block is visible"""
        return self._visible

    def toggle(self) -> bool:
        """
        åæ¢æç»´åæ¾ç¤?/ Toggle thinking block display

        Returns:
            åæ¢åçç¶æ?/ New state after toggle
        """
        self._visible = not self._visible
        if self._visible:
            self._start_live_display()
        else:
            self._stop_live_display()
        return self._visible

    def set_visible(self, visible: bool) -> None:
        """
        è®¾ç½®æç»´åå¯è§æ?/ Set thinking block visibility

        Args:
            visible: æ¯å¦å¯è§ / Whether visible
        """
        if visible != self._visible:
            self.toggle()

    def _start_live_display(self) -> None:
        """å¼å§å®æ¶æ¾ç¤?/ Start live display"""
        if self._live is None:
            self._live = Live(
                self._render_panel(),
                console=self.console,
                refresh_per_second=10,
                transient=False,
            )
            self._live.__enter__()

    def _stop_live_display(self) -> None:
        """åæ­¢å®æ¶æ¾ç¤º / Stop live display"""
        if self._live is not None:
            try:
                self._live.__exit__(None, None, None)
            except Exception:
                pass
            self._live = None
        self.console.print()

    def _render_panel(self) -> Panel:
        """æ¸²ææç»´é¢æ¿ / Render thinking panel"""
        lines = self._reasoning_content[-50:] if self._reasoning_content else ["ç­å¾æèåå®?.."]

        text = Text()
        for i, line in enumerate(lines):
            text.append(line + "\n", style="dim cyan" if i < len(lines) - 1 else "cyan")

        return Panel(
            text,
            title="[bold yellow]æèè¿ç¨?/ Reasoning Process[/bold yellow]",
            border_style="yellow",
            subtitle=f"[dim]{len(self._reasoning_content)} tokens[/dim]",
        )

    def feed_reasoning(self, token: str) -> None:
        """
        è¾å¥æètoken / Feed reasoning token

        Args:
            token: æèææ¬token / Reasoning text token
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
        è·åå®æ´æèææ?/ Get full reasoning text

        Returns:
            æèææ?/ Reasoning text
        """
        return "".join(self._reasoning_content)

    def clear(self) -> None:
        """æ¸é¤æç»´åå®¹ / Clear thinking content"""
        self._reasoning_content.clear()
        self._content_cache.clear()
        if self._visible and self._live is not None:
            try:
                self._live.update(self._render_panel())
            except Exception:
                pass

    def close(self) -> None:
        """å³é­æ¾ç¤ºå?/ Close display"""
        self._stop_live_display()
        self._reasoning_content.clear()
        self._content_cache.clear()
        self._visible = False
