from pathlib import Path
from typing import List, Optional


class Document:
    def __init__(self, content: str, source: str, metadata: Optional[dict] = None):
        self.content = content
        self.source = source
        self.metadata = metadata or {}


def load_txt(path: str) -> Document:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return Document(content=content, source=path)


def load_pdf(path: str) -> Document:
    try:
        from pdfminer.high_level import extract_text
        content = extract_text(path)
        return Document(content=content, source=path)
    except ImportError:
        raise ImportError("pdfminer.six is required for PDF loading")


def load_markdown(path: str) -> Document:
    try:
        import markdown
        with open(path, "r", encoding="utf-8") as f:
            md_text = f.read()
        content = markdown.markdown(md_text)
        return Document(content=content, source=path, metadata={"original": md_text})
    except ImportError:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=path)


def load_html(path: str) -> Document:
    try:
        from bs4 import BeautifulSoup
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        content = soup.get_text(separator="\n", strip=True)
        return Document(content=content, source=path)
    except ImportError:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=path)


def load_document(path: str) -> Document:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".txt":
        return load_txt(path)
    elif suffix == ".pdf":
        return load_pdf(path)
    elif suffix in (".md", ".markdown"):
        return load_markdown(path)
    elif suffix in (".html", ".htm"):
        return load_html(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Document(content=content, source=path)
