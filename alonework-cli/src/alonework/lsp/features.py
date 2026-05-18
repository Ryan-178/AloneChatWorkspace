"""
LSP 功能实现 / LSP Features Implementation

提供便捷的 LSP 功能函数 / Provides convenient LSP feature functions
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from alonework.lsp.client import (
    LSPClient,
    LanguageId,
    Position,
    Range,
    Location,
    DefinitionResult,
    ReferencesResult,
    HoverResult,
)


def detect_language(file_path: str) -> LanguageId:
    """
    根据文件扩展名检测语言 / Detect language from file extension
    
    Args:
        file_path: 文件路径 / File path
        
    Returns:
        语言标识 / Language identifier
    """
    ext = Path(file_path).suffix.lower()
    
    extension_map = {
        ".py": LanguageId.PYTHON,
        ".js": LanguageId.JAVASCRIPT,
        ".jsx": LanguageId.JAVASCRIPT,
        ".ts": LanguageId.TYPESCRIPT,
        ".tsx": LanguageId.TYPESCRIPT,
        ".go": LanguageId.GO,
        ".rs": LanguageId.RUST,
        ".java": LanguageId.JAVA,
        ".cpp": LanguageId.CPP,
        ".cc": LanguageId.CPP,
        ".cxx": LanguageId.CPP,
        ".c": LanguageId.C,
        ".h": LanguageId.C,
        ".hpp": LanguageId.CPP,
    }
    
    return extension_map.get(ext, LanguageId.PYTHON)


def go_to_definition(
    file_path: str,
    line: int,
    character: int,
    workspace_root: Optional[str] = None,
) -> DefinitionResult:
    """
    跳转到定义 / Go to definition
    
    Args:
        file_path: 文件路径 / File path
        line: 行号（1-based）/ Line number (1-based)
        character: 列号（1-based）/ Character number (1-based)
        workspace_root: 工作区根目录 / Workspace root
        
    Returns:
        定义结果 / Definition result
    """
    workspace = workspace_root or str(Path(file_path).parent)
    language = detect_language(file_path)
    
    client = LSPClient(workspace, language)
    
    lsp_line = max(0, line - 1)
    lsp_char = max(0, character - 1)
    
    return client.go_to_definition(file_path, lsp_line, lsp_char)


def find_references(
    file_path: str,
    line: int,
    character: int,
    workspace_root: Optional[str] = None,
    include_declaration: bool = True,
) -> ReferencesResult:
    """
    查找引用 / Find references
    
    Args:
        file_path: 文件路径 / File path
        line: 行号 / Line number
        character: 列号 / Character number
        workspace_root: 工作区根目录 / Workspace root
        include_declaration: 是否包含声明 / Include declaration
        
    Returns:
        引用结果 / References result
    """
    workspace = workspace_root or str(Path(file_path).parent)
    language = detect_language(file_path)
    
    client = LSPClient(workspace, language)
    
    lsp_line = max(0, line - 1)
    lsp_char = max(0, character - 1)
    
    return client.find_references(
        file_path,
        lsp_line,
        lsp_char,
        include_declaration,
    )


def get_hover(
    file_path: str,
    line: int,
    character: int,
    workspace_root: Optional[str] = None,
) -> HoverResult:
    """
    获取悬停文档 / Get hover documentation
    
    Args:
        file_path: 文件路径 / File path
        line: 行号 / Line number
        character: 列号 / Character number
        workspace_root: 工作区根目录 / Workspace root
        
    Returns:
        悬停结果 / Hover result
    """
    workspace = workspace_root or str(Path(file_path).parent)
    language = detect_language(file_path)
    
    client = LSPClient(workspace, language)
    
    lsp_line = max(0, line - 1)
    lsp_char = max(0, character - 1)
    
    return client.get_hover(file_path, lsp_line, lsp_char)


@dataclass
class CompletionItem:
    """补全项 / Completion item"""
    label: str
    kind: int = 1
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None


def get_completions(
    file_path: str,
    line: int,
    character: int,
    workspace_root: Optional[str] = None,
) -> List[CompletionItem]:
    """
    获取补全建议 / Get completion suggestions
    
    Args:
        file_path: 文件路径 / File path
        line: 行号 / Line number
        character: 列号 / Character number
        workspace_root: 工作区根目录 / Workspace root
        
    Returns:
        补全项列表 / List of completion items
    """
    return []


def find_symbol_in_file(
    file_path: str,
    symbol_name: str,
) -> List[Tuple[int, int, str]]:
    """
    在文件中查找符号 / Find symbol in file
    
    简单的文本搜索实现 / Simple text search implementation
    
    Args:
        file_path: 文件路径 / File path
        symbol_name: 符号名称 / Symbol name
        
    Returns:
        (行号, 列号, 行内容) 列表 / List of (line, column, line_content)
    """
    results = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            for match in re.finditer(rf"\b{re.escape(symbol_name)}\b", line):
                results.append((i + 1, match.start() + 1, line.strip()))
    
    except Exception:
        pass
    
    return results


def extract_definition_info(
    file_path: str,
    line: int,
) -> Optional[Dict[str, Any]]:
    """
    提取定义信息 / Extract definition info
    
    从指定行提取函数/类/变量定义信息 / Extract function/class/variable definition info from line
    
    Args:
        file_path: 文件路径 / File path
        line: 行号 / Line number
        
    Returns:
        定义信息或 None / Definition info or None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if line < 1 or line > len(lines):
            return None
        
        line_content = lines[line - 1]
        language = detect_language(file_path)
        
        if language == LanguageId.PYTHON:
            return _extract_python_definition(line_content, line)
        elif language in {LanguageId.JAVASCRIPT, LanguageId.TYPESCRIPT}:
            return _extract_js_definition(line_content, line)
        else:
            return None
    
    except Exception:
        return None


def _extract_python_definition(line: str, line_num: int) -> Optional[Dict[str, Any]]:
    """提取 Python 定义 / Extract Python definition"""
    patterns = [
        (r"def\s+(\w+)\s*\(", "function"),
        (r"async\s+def\s+(\w+)\s*\(", "async_function"),
        (r"class\s+(\w+)\s*[:(]", "class"),
        (r"(\w+)\s*=\s*", "variable"),
    ]
    
    for pattern, kind in patterns:
        match = re.search(pattern, line)
        if match:
            return {
                "name": match.group(1),
                "kind": kind,
                "line": line_num,
                "column": match.start() + 1,
            }
    
    return None


def _extract_js_definition(line: str, line_num: int) -> Optional[Dict[str, Any]]:
    """提取 JavaScript/TypeScript 定义 / Extract JS/TS definition"""
    patterns = [
        (r"function\s+(\w+)\s*\(", "function"),
        (r"const\s+(\w+)\s*=", "const"),
        (r"let\s+(\w+)\s*=", "let"),
        (r"var\s+(\w+)\s*=", "var"),
        (r"class\s+(\w+)\s*\{", "class"),
        (r"(\w+)\s*:\s*function", "method"),
    ]
    
    for pattern, kind in patterns:
        match = re.search(pattern, line)
        if match:
            return {
                "name": match.group(1),
                "kind": kind,
                "line": line_num,
                "column": match.start() + 1,
            }
    
    return None
