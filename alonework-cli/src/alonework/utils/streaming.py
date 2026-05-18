"""
æµå¼è¾åºæ¨¡å / Streaming Output Module

æä¾ / Provides:
- éè¡æµå¼ååºè¾åº / Line-by-line streaming response output
- è¡ç¼å²ä¸å®æ¶å·æ° / Line buffering and real-time flushing
- æµå¼JSONè¾åº / Streaming JSON output
"""

from typing import Optional, Generator, Iterator
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from alonework.configs import config


class LineStreamer:
    """
    éè¡æµå¼è¾åºå?/ Line-by-line Streamer

    éè¡æ¶éå¹¶è¾åºLLMååºåå®¹ï¼æ¯æMarkdownå®æ¶æ¸²æ
    Collects and outputs LLM response content line by line, supporting real-time Markdown rendering
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._buffer: list[str] = []
        self._current_line: list[str] = []
        self._line_count = 0
        self._is_reasoning = False
        self._reasoning_buffer: list[str] = []

    def feed_token(self, token: str) -> None:
        """
        è¾å¥ä¸ä¸ªtoken / Feed a token

        Args:
            token: ææ¬token / Text token
        """
        self._current_line.append(token)
        content = "".join(self._current_line)

        if "\n" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines[:-1]):
                if i == 0:
                    self._current_line = list(line)
                else:
                    self._current_line = [line]
                self._flush_current_line()

            if lines[-1]:
                self._current_line = [lines[-1]]
            else:
                self._current_line = []
        else:
            self._current_line = [content]

    def feed_reasoning_token(self, token: str) -> None:
        """
        è¾å¥æèè¿ç¨çtoken / Feed a reasoning token

        Args:
            token: æèææ¬token / Reasoning text token
        """
        self._reasoning_buffer.append(token)

    def _flush_current_line(self) -> None:
        """å·æ°å½åè¡å°è¾åº / Flush current line to output"""
        line = "".join(self._current_line)
        if line.strip():
            self._line_count += 1
            self._buffer.append(line)
            self.console.print(line)

    def flush(self) -> str:
        """
        å·æ°ææç¼å²åº / Flush all buffers

        Returns:
            å®æ´åå®¹ / Complete content
        """
        if self._current_line:
            self._flush_current_line()
        content = "\n".join(self._buffer)
        return content

    def get_reasoning_content(self) -> str:
        """
        è·åæèåå®?/ Get reasoning content

        Returns:
            æèåå®¹ææ?/ Reasoning content text
        """
        return "".join(self._reasoning_buffer)


def stream_response_line_by_line(
    stream_iter: Iterator[str],
    console: Optional[Console] = None,
    show_reasoning: bool = False,
) -> str:
    """
    éè¡æµå¼è¾åºååº / Stream response line by line

    Args:
        stream_iter: æµå¼è¿­ä»£å?/ Stream iterator
        console: Richæ§å¶å°å®ä¾?/ Rich console instance
        show_reasoning: æ¯å¦æ¾ç¤ºæèè¿ç¨?/ Whether to show reasoning process

    Returns:
        å®æ´ååºåå®¹ / Complete response content
    """
    streamer = LineStreamer(console)
    reasoning_mode = False

    for chunk in stream_iter:
        if chunk.startswith("[æè]") or chunk.startswith("[reasoning]"):
            reasoning_mode = True
            token = chunk.replace("[æè]", "").replace("[reasoning]", "")
            streamer.feed_reasoning_token(token)
            if show_reasoning:
                streamer.console.print(f"[dim]{token}[/dim]", end="")
        else:
            if reasoning_mode:
                if show_reasoning and streamer._reasoning_buffer:
                    streamer.console.print()
                reasoning_mode = False
            streamer.feed_token(chunk)

    return streamer.flush()
