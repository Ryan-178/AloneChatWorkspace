"""
å¾çé¾æ¥æ¨¡å / Image Link Module

æä¾ / Provides:
- å¯ç¹å»å¾çé¾æ?/ Clickable image links
- [Image #N] å¨é»è®¤æ¥çå¨ä¸­æå¼ / [Image #N] open in default viewer
- å¾çURLå¤ç / Image URL processing
"""

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from rich.text import Text
from alonework.configs import config


_IMAGE_LINK_PATTERN = re.compile(r'\[Image\s*(?:#|No\.)?\s*(\d+)\]')
_IMAGE_PATTERN = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)'
)


def _get_image_path_by_index(index: int, base_dir: Optional[str] = None) -> Optional[Path]:
    """
    éè¿ç´¢å¼è·åå¾çè·¯å¾ / Get image path by index

    Args:
        index: å¾çç´¢å¼ / Image index
        base_dir: åºç¡ç®å½ / Base directory

    Returns:
        å¾çè·¯å¾ / Image path
    """
    if base_dir is None:
        base_dir = os.getcwd()

    base = Path(base_dir)
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"]:
        candidates = list(base.glob(f"*{ext}"))
        candidates.extend(list(base.glob(f"image{index}{ext}")))
        candidates.extend(list(base.glob(f"img{index}{ext}")))
        candidates.extend(list(base.glob(f"*_{index}{ext}")))
        if candidates:
            return candidates[0]

    return None


def open_image(path_or_url: str) -> bool:
    """
    å¨é»è®¤æ¥çå¨ä¸­æå¼å¾ç / Open image in default viewer

    Args:
        path_or_url: å¾çè·¯å¾æURL / Image path or URL

    Returns:
        æ¯å¦æå / Whether successful
    """
    try:
        if path_or_url.startswith(("http://", "https://")):
            webbrowser.open(path_or_url)
            return True

        p = Path(path_or_url)
        if p.exists():
            if os.name == "nt":
                os.startfile(str(p.resolve()))
            elif os.uname().sysname == "Darwin":
                subprocess.Popen(["open", str(p.resolve())])
            else:
                subprocess.Popen(["xdg-open", str(p.resolve())])
            return True
    except Exception:
        pass
    return False


def process_image_links_in_output(text: str, base_dir: Optional[str] = None) -> str:
    """
    å¤çè¾åºä¸­çå¾çé¾æ¥ / Process image links in output

    å°?[Image #N] æ è®°è½¬æ¢ä¸ºå¯ç¹å»ç?OSC 8 è¶é¾æ?
    Args:
        text: è¾åºææ¬ / Output text
        base_dir: åºç¡ç®å½ / Base directory

    Returns:
        å¤çåçææ¬ / Processed text
    """
    def replace_image_ref(match: re.Match) -> str:
        index = int(match.group(1))
        img_path = _get_image_path_by_index(index, base_dir)
        if img_path:
            abs_path = str(img_path.resolve())
            uri = f"file:///{abs_path.replace(os.sep, '/').lstrip('/')}"
            return f"\x1b]8;;{uri}\x1b\\[Image #{index}]\x1b]8;;\x1b\\"
        return match.group(0)

    text = _IMAGE_LINK_PATTERN.sub(replace_image_ref, text)

    def replace_md_image(match: re.Match) -> str:
        url = match.group("url")
        alt = match.group("alt")
        if url.startswith(("http://", "https://")):
            return f"\x1b]8;;{url}\x1b\\![{alt}]({url})\x1b]8;;\x1b\\"
        return match.group(0)

    text = _IMAGE_PATTERN.sub(replace_md_image, text)

    return text
