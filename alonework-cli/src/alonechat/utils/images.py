"""
图片链接模块 / Image Link Module

提供 / Provides:
- 可点击图片链接 / Clickable image links
- [Image #N] 在默认查看器中打开 / [Image #N] open in default viewer
- 图片URL处理 / Image URL processing
"""

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
from rich.text import Text
from alonechat.configs import config


_IMAGE_LINK_PATTERN = re.compile(r'\[Image\s*(?:#|No\.)?\s*(\d+)\]')
_IMAGE_PATTERN = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)'
)


def _get_image_path_by_index(index: int, base_dir: Optional[str] = None) -> Optional[Path]:
    """
    通过索引获取图片路径 / Get image path by index

    Args:
        index: 图片索引 / Image index
        base_dir: 基础目录 / Base directory

    Returns:
        图片路径 / Image path
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
    在默认查看器中打开图片 / Open image in default viewer

    Args:
        path_or_url: 图片路径或URL / Image path or URL

    Returns:
        是否成功 / Whether successful
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
    处理输出中的图片链接 / Process image links in output

    将 [Image #N] 标记转换为可点击的 OSC 8 超链接

    Args:
        text: 输出文本 / Output text
        base_dir: 基础目录 / Base directory

    Returns:
        处理后的文本 / Processed text
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
