"""
可点击超链接模块 / Clickable Hyperlink Module

提供 / Provides:
- OSC 8 超链接支持 / OSC 8 hyperlink support
- 可点击文件路径 / Clickable file paths
- 可点击URL / Clickable URLs
"""

import os
import re
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.text import Text
from alonechat.configs import config


def _supports_osc8() -> bool:
    """检查终端是否支持 OSC 8 超链接 / Check if terminal supports OSC 8 hyperlinks"""
    term = os.environ.get("TERM", "")
    if "kitty" in term:
        return True
    if "tmux" in term:
        return True
    if "xterm" in term:
        return True
    if "alacritty" in term:
        return True
    if "wezterm" in term:
        return True
    if "foot" in term:
        return True
    if os.environ.get("ITERM_PROFILE"):
        return True
    if os.environ.get("TERM_PROGRAM") == "vscode":
        return True
    if os.environ.get("ALACRITTY_LOG"):
        return True
    return False


def osc8_link(uri: str, text: str) -> str:
    """
    创建 OSC 8 超链接 / Create OSC 8 hyperlink

    Args:
        uri: 链接URI / Link URI
        text: 显示文本 / Display text

    Returns:
        OSC 8 超链接字符串 / OSC 8 hyperlink string
    """
    if _supports_osc8():
        return f"\x1b]8;;{uri}\x1b\\{text}\x1b]8;;\x1b\\"
    return text


def make_file_link(filepath: str, display_text: Optional[str] = None) -> str:
    """
    创建可点击文件路径链接 / Create clickable file path link

    Args:
        filepath: 文件路径 / File path
        display_text: 显示文本（默认为文件名）/ Display text (defaults to filename)

    Returns:
        OSC 8 文件链接字符串 / OSC 8 file link string
    """
    abs_path = str(Path(filepath).resolve())
    uri = f"file:///{abs_path.replace(os.sep, '/').lstrip('/')}"
    text = display_text or abs_path
    return osc8_link(uri, text)


def make_line_link(filepath: str, line: int, display_text: Optional[str] = None) -> str:
    """
    创建可点击文件行号链接 / Create clickable file line link

    Args:
        filepath: 文件路径 / File path
        line: 行号 / Line number
        display_text: 显示文本 / Display text

    Returns:
        OSC 8 文件行链接字符串 / OSC 8 file line link string
    """
    abs_path = str(Path(filepath).resolve())
    uri = f"file:///{abs_path.replace(os.sep, '/').lstrip('/')}#L{line}"
    text = display_text or f"{abs_path}:{line}"
    return osc8_link(uri, text)


_FILE_PATH_PATTERN = re.compile(
    r'(?P<path>(?:[A-Za-z]:\\|/)?(?:[\w\-. ]+[\\/])+[\w\-. ]+\.\w+)'
    r'(?::(?P<line>\d+))?'
)


def wrap_file_paths_in_output(text: str, cwd: Optional[str] = None) -> str:
    """
    在输出文本中将文件路径包装为可点击链接
    Wrap file paths in output text as clickable links

    Args:
        text: 输出文本 / Output text
        cwd: 当前工作目录 / Current working directory

    Returns:
        包含可点击链接的文本 / Text with clickable links
    """
    if not _supports_osc8():
        return text

    if cwd is None:
        cwd = os.getcwd()

    def replace_path(match: re.Match) -> str:
        path = match.group("path")
        line = match.group("line")
        try:
            p = Path(path)
            if not p.is_absolute():
                p = Path(cwd) / p
            resolved = str(p.resolve())
            uri = f"file:///{resolved.replace(os.sep, '/').lstrip('/')}"
            if line:
                uri += f"#L{line}"
            return osc8_link(uri, match.group(0))
        except Exception:
            return match.group(0)

    return _FILE_PATH_PATTERN.sub(replace_path, text)


def wrap_file_path_in_rich(text: str) -> Text:
    """
    在 Rich Text 中包装文件路径 / Wrap file paths in Rich Text

    Args:
        text: 原始文本 / Raw text

    Returns:
        Rich Text 对象 / Rich Text object
    """
    result = Text()
    if not _supports_osc8():
        result.append(text)
        return result

    last_end = 0
    for match in _FILE_PATH_PATTERN.finditer(text):
        start, end = match.start(), match.end()
        if start > last_end:
            result.append(text[last_end:start])
        path = match.group(0)
        abs_path = str(Path(path).resolve())
        uri = f"file:///{abs_path.replace(os.sep, '/').lstrip('/')}"
        link_text = Text(path, style=f"link {uri}")
        result.append(link_text)
        last_end = end

    if last_end < len(text):
        result.append(text[last_end:])

    return result
