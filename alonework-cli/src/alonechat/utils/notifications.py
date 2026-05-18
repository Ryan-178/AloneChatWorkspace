"""
终端通知模块 / Terminal Notification Module

提供 / Provides:
- iTerm2/Kitty/Ghostty 弹出窗口通知 / Popup window notifications for iTerm2/Kitty/Ghostty
- tmux 内进度条支持 / Progress bar support inside tmux
- 系统通知 / System notifications
"""

import os
import subprocess
from typing import Optional
from rich.console import Console
from alonechat.configs import config


def _is_tmux() -> bool:
    """检查是否在tmux中运行 / Check if running inside tmux"""
    return "TMUX" in os.environ


def _is_iterm2() -> bool:
    """检查是否在iTerm2中运行 / Check if running in iTerm2"""
    return "ITERM_PROFILE" in os.environ or "ITERM_SESSION_ID" in os.environ


def _is_kitty() -> bool:
    """检查是否在Kitty中运行 / Check if running in Kitty"""
    return "KITTY_WINDOW_ID" in os.environ


def _is_ghostty() -> bool:
    """检查是否在Ghostty中运行 / Check if running in Ghostty"""
    return "GHOSTTY_RESOURCES_DIR" in os.environ


def send_notification(
    title: str,
    message: str,
    console: Optional[Console] = None,
) -> None:
    """
    发送终端通知 / Send terminal notification

    支持 iTerm2 (OSC 9), Kitty (OSC 9), Ghostty, tmux 包装

    Args:
        title: 通知标题 / Notification title
        message: 通知消息 / Notification message
        console: Rich控制台实例 / Rich console instance
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
    发送系统通知 / Send system notification

    Args:
        title: 通知标题 / Notification title
        message: 通知消息 / Notification message
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
    发送进度通知（tmux 进度条）/ Send progress notification (tmux progress bar)

    支持 iTerm2 和 tmux 内的进度条显示

    Args:
        progress: 进度值 0.0-1.0 / Progress value 0.0-1.0
        message: 进度消息 / Progress message
        console: Rich控制台实例 / Rich console instance
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
