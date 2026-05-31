"""
文件读取工具 - File Read Tool

读取文件内容，支持多种编码
Read file content with multiple encoding support
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool
from agent_framework.security.path_validator import PathValidator


class FileReadTool(BaseTool):
    """
    文件读取工具 - File Read Tool

    读取文件内容，支持指定编码和行范围
    Read file content with encoding and line range support
    """

    name = "file_read"
    description = "Read file content. Supports encoding specification and line range."
    category = "file"
    permission_level = "read"
    estimated_cost = 0.001

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to read",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
            "start_line": {
                "type": "integer",
                "description": "Start line number (1-indexed)",
            },
            "end_line": {
                "type": "integer",
                "description": "End line number (1-indexed)",
            },
            "max_size": {
                "type": "integer",
                "description": "Maximum file size in bytes (default: 10MB)",
                "default": 10485760,
            },
        },
        "required": ["path"],
    }

    def _validate_safe_path(self, path: str) -> Optional[Path]:
        allowed_base = os.getenv("WORKSPACE_DIR", str(Path.cwd()))
        return PathValidator.resolve_safe_path(path, allowed_base)

    def execute(
        self,
        path: str,
        encoding: str = "utf-8",
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_size: int = 10485760,
    ) -> Dict[str, Any]:
        """
        读取文件 / Read file

        Args:
            path: 文件路径 / File path
            encoding: 文件编码 / File encoding
            start_line: 起始行号 / Start line number
            end_line: 结束行号 / End line number
            max_size: 最大文件大小 / Maximum file size

        Returns:
            读取结果 / Read result
        """
        safe_path = self._validate_safe_path(path)
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path traversal blocked: {path}",
                "content": "",
            }

        file_path = safe_path
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
                "content": "",
            }
        
        if not file_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path}",
                "content": "",
            }
        
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return {
                "success": False,
                "error": f"File too large: {file_size} bytes (max: {max_size})",
                "content": "",
                "size": file_size,
            }
        
        try:
            with open(file_path, "r", encoding=encoding) as f:
                if start_line is None and end_line is None:
                    content = f.read()
                else:
                    lines = f.readlines()
                    start = (start_line or 1) - 1
                    end = end_line or len(lines)
                    content = "".join(lines[start:end])
            
            return {
                "success": True,
                "content": content,
                "path": str(file_path.absolute()),
                "size": file_size,
                "encoding": encoding,
            }
            
        except UnicodeDecodeError as e:
            return {
                "success": False,
                "error": f"Encoding error: {e}. Try different encoding.",
                "content": "",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "",
            }
