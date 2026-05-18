"""
IME支持模块 / IME Support Module

提供 / Provides:
- 中/日/韩输入法支持 / CJK IME support
- 撰写窗口正确定位在光标处 / Correct writing window positioning at cursor
- 输入法状态管理 / IME state management
"""

import os
import sys
import ctypes
from typing import Optional
from rich.console import Console
from alonechat.configs import config


def get_cursor_position() -> tuple[int, int]:
    """
    获取终端光标位置 / Get terminal cursor position

    使用 ANSI 转义序列 DSR 查询光标位置
    Uses ANSI escape sequence DSR to query cursor position

    Returns:
        (行, 列) 元组 / (row, column) tuple
    """
    try:
        if os.name == "nt":
            return _get_cursor_position_windows()
        else:
            return _get_cursor_position_unix()
    except Exception:
        return (0, 0)


def _get_cursor_position_windows() -> tuple[int, int]:
    """Windows下获取光标位置 / Get cursor position on Windows"""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        csbi = ctypes.create_string_buffer(22)
        if kernel32.GetConsoleScreenBufferInfo(handle, csbi):
            import struct
            _, _, _, _, _, left, top, _, _ = struct.unpack("hhhhHhhhhh", csbi.raw[:22])
            return (top + 1, left + 1)
    except Exception:
        pass
    return (0, 0)


def _get_cursor_position_unix() -> tuple[int, int]:
    """Unix下获取光标位置 / Get cursor position on Unix"""
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdout.write("\x1b[6n")
            sys.stdout.flush()
            response = ""
            while True:
                ch = sys.stdin.read(1)
                response += ch
                if ch == "R":
                    break
            match = __import__("re").match(r"\x1b\[(\d+);(\d+)R", response)
            if match:
                return (int(match.group(1)), int(match.group(2)))
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, old)
    except Exception:
        pass
    return (0, 0)


def set_writing_window_position(x: int, y: int) -> None:
    """
    设置撰写窗口位置 / Set writing window position

    使用 ANSI 转义序列确保输入法撰写窗口正确定位在光标处
    Uses ANSI escape sequences to ensure IME writing window is correctly positioned at cursor

    Args:
        x: 列坐标 / Column coordinate
        y: 行坐标 / Row coordinate
    """
    try:
        if os.name == "nt":
            _set_writing_window_windows(x, y)
        else:
            _set_writing_window_unix(x, y)
    except Exception:
        pass


def _set_writing_window_windows(x: int, y: int) -> None:
    """Windows下设置窗口位置 / Set window position on Windows"""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        coord = ctypes.wintypes._COORD(int(x), int(y))
        kernel32.SetConsoleCursorPosition(handle, coord)
    except Exception:
        pass


def _set_writing_window_unix(x: int, y: int) -> None:
    """Unix下设置窗口位置 / Set window position on Unix"""
    sys.stdout.write(f"\x1b[{y};{x}H")
    sys.stdout.flush()


class IMEManager:
    """
    IME管理器 / IME Manager

    管理输入法状态，确保CJK输入法的撰写窗口正确定位
    Manages IME state, ensuring CJK IME writing window is correctly positioned
    """

    def __init__(self):
        self._enabled = True
        self._last_cursor_pos = (0, 0)
        self._config = config.get("ime", {})

    @property
    def enabled(self) -> bool:
        """检查IME支持是否启用 / Check if IME support is enabled"""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """
        设置IME支持 / Set IME support

        Args:
            enabled: 是否启用 / Whether enabled
        """
        self._enabled = enabled

    def before_input(self) -> None:
        """
        输入前调用 / Call before input

        确保输入法撰写窗口定位在正确位置
        Ensures IME writing window is positioned correctly
        """
        if not self._enabled:
            return
        try:
            self._last_cursor_pos = get_cursor_position()
            x, y = self._last_cursor_pos
            if x > 0 and y > 0:
                set_writing_window_position(x, y)
        except Exception:
            pass

    def after_input(self) -> None:
        """输入后调用 / Call after input"""
        self._last_cursor_pos = get_cursor_position()
