"""
å¯ç¹å»è¶é¾æ¥æ¨¡å / Clickable Hyperlink Module

æä¾ / Provides:
- OSC 8 è¶é¾æ¥æ¯æ?/ OSC 8 hyperlink support
- å¯ç¹å»æä»¶è·¯å¾?/ Clickable file paths
- å¯ç¹å»URL / Clickable URLs
"""

import os
import re
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.text import Text
from alonework.configs import config


def _supports_osc8() -> bool:
    """æ£æ¥ç»ç«¯æ¯å¦æ¯æ?OSC 8 è¶é¾æ?/ Check if terminal supports OSC 8 hyperlinks"""
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
    åå»º OSC 8 è¶é¾æ?/ Create OSC 8 hyperlink

    Args:
        uri: é¾æ¥URI / Link URI
        text: æ¾ç¤ºææ¬ / Display text

    Returns:
        OSC 8 è¶é¾æ¥å­ç¬¦ä¸² / OSC 8 hyperlink string
    """
    if _supports_osc8():
        return f"\x1b]8;;{uri}\x1b\\{text}\x1b]8;;\x1b\\"
    return text


def make_file_link(filepath: str, display_text: Optional[str] = None) -> str:
    """
    åå»ºå¯ç¹å»æä»¶è·¯å¾é¾æ?/ Create clickable file path link

    Args:
        filepath: æä»¶è·¯å¾ / File path
        display_text: æ¾ç¤ºææ¬ï¼é»è®¤ä¸ºæä»¶åï¼/ Display text (defaults to filename)

    Returns:
        OSC 8 æä»¶é¾æ¥å­ç¬¦ä¸?/ OSC 8 file link string
    """
    abs_path = str(Path(filepath).resolve())
    uri = f"file:///{abs_path.replace(os.sep, '/').lstrip('/')}"
    text = display_text or abs_path
    return osc8_link(uri, text)


def make_line_link(filepath: str, line: int, display_text: Optional[str] = None) -> str:
    """
    åå»ºå¯ç¹å»æä»¶è¡å·é¾æ?/ Create clickable file line link

    Args:
        filepath: æä»¶è·¯å¾ / File path
        line: è¡å· / Line number
        display_text: æ¾ç¤ºææ¬ / Display text

    Returns:
        OSC 8 æä»¶è¡é¾æ¥å­ç¬¦ä¸² / OSC 8 file line link string
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
    å¨è¾åºææ¬ä¸­å°æä»¶è·¯å¾åè£ä¸ºå¯ç¹å»é¾æ?    Wrap file paths in output text as clickable links

    Args:
        text: è¾åºææ¬ / Output text
        cwd: å½åå·¥ä½ç®å½ / Current working directory

    Returns:
        åå«å¯ç¹å»é¾æ¥çææ¬ / Text with clickable links
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
    å?Rich Text ä¸­åè£æä»¶è·¯å¾?/ Wrap file paths in Rich Text

    Args:
        text: åå§ææ¬ / Raw text

    Returns:
        Rich Text å¯¹è±¡ / Rich Text object
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
