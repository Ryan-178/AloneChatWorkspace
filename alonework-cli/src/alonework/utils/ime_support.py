"""
IMEæ¯ææ¨¡å / IME Support Module

æä¾ / Provides:
- ä¸?æ?é©è¾å¥æ³æ¯æ / CJK IME support
- æ°åçªå£æ­£ç¡®å®ä½å¨åæ å¤ / Correct writing window positioning at cursor
- è¾å¥æ³ç¶æç®¡ç?/ IME state management
"""

import os
import sys
import ctypes
from typing import Optional
from rich.console import Console
from alonework.configs import config


def get_cursor_position() -> tuple[int, int]:
    """
    è·åç»ç«¯åæ ä½ç½® / Get terminal cursor position

    ä½¿ç¨ ANSI è½¬ä¹åºå DSR æ¥è¯¢åæ ä½ç½®
    Uses ANSI escape sequence DSR to query cursor position

    Returns:
        (è¡? å? åç» / (row, column) tuple
    """
    try:
        if os.name == "nt":
            return _get_cursor_position_windows()
        else:
            return _get_cursor_position_unix()
    except Exception:
        return (0, 0)


def _get_cursor_position_windows() -> tuple[int, int]:
    """Windowsä¸è·ååæ ä½ç½?/ Get cursor position on Windows"""
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
    """Unixä¸è·ååæ ä½ç½?/ Get cursor position on Unix"""
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
    è®¾ç½®æ°åçªå£ä½ç½® / Set writing window position

    ä½¿ç¨ ANSI è½¬ä¹åºåç¡®ä¿è¾å¥æ³æ°åçªå£æ­£ç¡®å®ä½å¨åæ å¤?    Uses ANSI escape sequences to ensure IME writing window is correctly positioned at cursor

    Args:
        x: ååæ ?/ Column coordinate
        y: è¡åæ ?/ Row coordinate
    """
    try:
        if os.name == "nt":
            _set_writing_window_windows(x, y)
        else:
            _set_writing_window_unix(x, y)
    except Exception:
        pass


def _set_writing_window_windows(x: int, y: int) -> None:
    """Windowsä¸è®¾ç½®çªå£ä½ç½?/ Set window position on Windows"""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        coord = ctypes.wintypes._COORD(int(x), int(y))
        kernel32.SetConsoleCursorPosition(handle, coord)
    except Exception:
        pass


def _set_writing_window_unix(x: int, y: int) -> None:
    """Unixä¸è®¾ç½®çªå£ä½ç½?/ Set window position on Unix"""
    sys.stdout.write(f"\x1b[{y};{x}H")
    sys.stdout.flush()


class IMEManager:
    """
    IMEç®¡çå?/ IME Manager

    ç®¡çè¾å¥æ³ç¶æï¼ç¡®ä¿CJKè¾å¥æ³çæ°åçªå£æ­£ç¡®å®ä½
    Manages IME state, ensuring CJK IME writing window is correctly positioned
    """

    def __init__(self):
        self._enabled = True
        self._last_cursor_pos = (0, 0)
        self._config = config.get("ime", {})

    @property
    def enabled(self) -> bool:
        """æ£æ¥IMEæ¯ææ¯å¦å¯ç¨ / Check if IME support is enabled"""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """
        è®¾ç½®IMEæ¯æ / Set IME support

        Args:
            enabled: æ¯å¦å¯ç¨ / Whether enabled
        """
        self._enabled = enabled

    def before_input(self) -> None:
        """
        è¾å¥åè°ç?/ Call before input

        ç¡®ä¿è¾å¥æ³æ°åçªå£å®ä½å¨æ­£ç¡®ä½ç½®
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
        """è¾å¥åè°ç?/ Call after input"""
        self._last_cursor_pos = get_cursor_position()
