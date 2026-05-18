"""
ç»ç«¯éç¥æ¨¡å / Terminal Notification Module

æä¾ / Provides:
- iTerm2/Kitty/Ghostty å¼¹åºçªå£éç¥ / Popup window notifications for iTerm2/Kitty/Ghostty
- tmux åè¿åº¦æ¡æ¯æ / Progress bar support inside tmux
- ç³»ç»éç¥ / System notifications
"""

import os
import subprocess
from typing import Optional
from rich.console import Console
from alonework.configs import config


def _is_tmux() -> bool:
    """æ£æ¥æ¯å¦å¨tmuxä¸­è¿è¡?/ Check if running inside tmux"""
    return "TMUX" in os.environ


def _is_iterm2() -> bool:
    """æ£æ¥æ¯å¦å¨iTerm2ä¸­è¿è¡?/ Check if running in iTerm2"""
    return "ITERM_PROFILE" in os.environ or "ITERM_SESSION_ID" in os.environ


def _is_kitty() -> bool:
    """æ£æ¥æ¯å¦å¨Kittyä¸­è¿è¡?/ Check if running in Kitty"""
    return "KITTY_WINDOW_ID" in os.environ


def _is_ghostty() -> bool:
    """æ£æ¥æ¯å¦å¨Ghosttyä¸­è¿è¡?/ Check if running in Ghostty"""
    return "GHOSTTY_RESOURCES_DIR" in os.environ


def send_notification(
    title: str,
    message: str,
    console: Optional[Console] = None,
) -> None:
    """
    åéç»ç«¯éç¥ / Send terminal notification

    æ¯æ iTerm2 (OSC 9), Kitty (OSC 9), Ghostty, tmux åè£

    Args:
        title: éç¥æ é¢ / Notification title
        message: éç¥æ¶æ¯ / Notification message
        console: Richæ§å¶å°å®ä¾?/ Rich console instance
    """
    stripped_message = message[:200] if len(message) > 200 else message
    is_tmux_session = _is_tmux()

    if _is_iterm2() or is_tmux_session:
        osc9 = f"\x1b]9;{stripped_message}\x07"
        if is_tmux_session:
            osc9 = f"\x1bPtmux;\x1b{osc9}\x1b\\"
        if console:
            console.print(osc9, end="")
        else:
            os.write(1, osc9.encode())

    if _is_kitty():
        kitty_cmd = f"\x1b]99;i=0:d=0;{stripped_message}\x1b\\"
        if console:
            console.print(kitty_cmd, end="")
        else:
            os.write(1, kitty_cmd.encode())

    if _is_ghostty():
        ghostty_msg = f"{title}: {stripped_message}" if title else stripped_message
        ghostty_cmd = f"\x1b]9;{ghostty_msg}\x07"
        if console:
            console.print(ghostty_cmd, end="")
        else:
            os.write(1, ghostty_cmd.encode())

    send_system_notification(title, stripped_message)


def send_system_notification(title: str, message: str) -> None:
    """
    åéç³»ç»éç¥ / Send system notification

    Args:
        title: éç¥æ é¢ / Notification title
        message: éç¥æ¶æ¯ / Notification message
    """
    try:
        if os.name == "nt":
            from plyer import notification as plyer_notification
            plyer_notification.notify(title=title, message=message, timeout=5)
        else:
            subprocess.Popen(
                ["notify-send", title, message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def send_progress_notification(
    progress: float,
    message: str,
    console: Optional[Console] = None,
) -> None:
    """
    åéè¿åº¦éç¥ï¼tmux è¿åº¦æ¡ï¼/ Send progress notification (tmux progress bar)

    æ¯æ iTerm2 å?tmux åçè¿åº¦æ¡æ¾ç¤?
    Args:
        progress: è¿åº¦å?0.0-1.0 / Progress value 0.0-1.0
        message: è¿åº¦æ¶æ¯ / Progress message
        console: Richæ§å¶å°å®ä¾?/ Rich console instance
    """
    is_tmux_session = _is_tmux()
    percentage = max(0, min(100, int(progress * 100)))

    osc9 = f"\x1b]9;{percentage};{message}\x07"
    if is_tmux_session:
        osc9 = f"\x1bPtmux;\x1b{osc9}\x1b\\"
    if console:
        console.print(osc9, end="")
    else:
        os.write(1, osc9.encode())
