"""
流式输出模块 / Streaming Output Module

提供 / Provides:
- 逐行流式响应输出 / Line-by-line streaming response output
- 行缓冲与实时刷新 / Line buffering and real-time flushing
- 流式JSON输出 / Streaming JSON output
"""

from typing import Optional, Generator, Iterator
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from alonechat.configs import config


class LineStreamer:
    """
    逐行流式输出器 / Line-by-line Streamer

    逐行收集并输出LLM响应内容，支持Markdown实时渲染
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
        输入一个token / Feed a token

        Args:
            token: 文本token / Text token
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
        输入思考过程的token / Feed a reasoning token

        Args:
            token: 思考文本token / Reasoning text token
        """
        self._reasoning_buffer.append(token)

    def _flush_current_line(self) -> None:
        """刷新当前行到输出 / Flush current line to output"""
        line = "".join(self._current_line)
        if line.strip():
            self._line_count += 1
            self._buffer.append(line)
            self.console.print(line)

    def flush(self) -> str:
        """
        刷新所有缓冲区 / Flush all buffers

        Returns:
            完整内容 / Complete content
        """
        if self._current_line:
            self._flush_current_line()
        content = "\n".join(self._buffer)
        return content

    def get_reasoning_content(self) -> str:
        """
        获取思考内容 / Get reasoning content

        Returns:
            思考内容文本 / Reasoning content text
        """
        return "".join(self._reasoning_buffer)


def stream_response_line_by_line(
    stream_iter: Iterator[str],
    console: Optional[Console] = None,
    show_reasoning: bool = False,
) -> str:
    """
    逐行流式输出响应 / Stream response line by line

    Args:
        stream_iter: 流式迭代器 / Stream iterator
        console: Rich控制台实例 / Rich console instance
        show_reasoning: 是否显示思考过程 / Whether to show reasoning process

    Returns:
        完整响应内容 / Complete response content
    """
    streamer = LineStreamer(console)
    reasoning_mode = False

    for chunk in stream_iter:
        if chunk.startswith("[思考]") or chunk.startswith("[reasoning]"):
            reasoning_mode = True
            token = chunk.replace("[思考]", "").replace("[reasoning]", "")
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
