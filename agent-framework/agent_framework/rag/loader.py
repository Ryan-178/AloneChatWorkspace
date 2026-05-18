from pathlib import Path
from typing import List, Optional
import os


class Document:
    def __init__(self, content: str, source: str, metadata: Optional[dict] = None):
        self.content = content
        self.source = source
        self.metadata = metadata or {}


def _resolve_safe_path(path: str, base_dir: Optional[str] = None) -> Path:
    """
    安全地解析路径，防止路径遍历攻击。
    如果提供了 base_dir，则确保解析后的路径在 base_dir 内。
    """
    # 先获取绝对路径并规范化
    target_path = Path(path).resolve()

    if base_dir:
        base_path = Path(base_dir).resolve()
        # 确保目标路径在 base_dir 内
        try:
            target_path.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Path traversal detected: {path} is outside of allowed directory {base_dir}")
    else:
        # 如果没有提供 base_dir，至少确保路径不是绝对路径指向敏感系统目录
        if target_path.is_absolute():
            # 检查是否指向常见的敏感系统目录
            sensitive_prefixes = [
                Path("/etc"),
                Path("/usr"),
                Path("/bin"),
                Path("/sbin"),
                Path("/lib"),
                Path("/lib64"),
                Path("/boot"),
                Path("/proc"),
                Path("/sys"),
                Path("/dev"),
                Path("/root"),
                Path("/home"),
                Path("C:/Windows"),
                Path("C:/Program Files"),
                Path("C:/ProgramData"),
            ]
            for prefix in sensitive_prefixes:
                try:
                    target_path.relative_to(prefix.resolve())
                    raise ValueError(f"Access to system path is not allowed: {path}")
                except ValueError:
                    continue

    return target_path


def load_txt(path: str) -> Document:
    safe_path = _resolve_safe_path(path)
    with open(safe_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Document(content=content, source=str(safe_path))


def load_pdf(path: str) -> Document:
    safe_path = _resolve_safe_path(path)
    try:
        from pdfminer.high_level import extract_text
        content = extract_text(str(safe_path))
        return Document(content=content, source=str(safe_path))
    except ImportError:
        raise ImportError("pdfminer.six is required for PDF loading")


def load_markdown(path: str) -> Document:
    safe_path = _resolve_safe_path(path)
    try:
        import markdown
        with open(safe_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        content = markdown.markdown(md_text)
        return Document(content=content, source=str(safe_path), metadata={"original": md_text})
    except ImportError:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=str(safe_path))


def load_html(path: str) -> Document:
    safe_path = _resolve_safe_path(path)
    try:
        from bs4 import BeautifulSoup
        with open(safe_path, "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        content = soup.get_text(separator="\n", strip=True)
        return Document(content=content, source=str(safe_path))
    except ImportError:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=str(safe_path))


def load_document(path: str, base_dir: Optional[str] = None) -> Document:
    """
    加载文档，支持路径安全校验。

    Args:
        path: 文件路径（相对或绝对）
        base_dir: 可选，限制文件必须在此目录下
    """
    safe_path = _resolve_safe_path(path, base_dir)
    suffix = safe_path.suffix.lower()
    if suffix == ".txt":
        return load_txt(str(safe_path))
    elif suffix == ".pdf":
        return load_pdf(str(safe_path))
    elif suffix in (".md", ".markdown"):
        return load_markdown(str(safe_path))
    elif suffix in (".html", ".htm"):
        return load_html(str(safe_path))
    else:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=str(safe_path))
