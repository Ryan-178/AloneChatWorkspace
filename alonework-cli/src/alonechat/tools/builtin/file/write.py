"""
文件写入工具 - File Write Tool

写入文件内容，支持创建目录
Write file content with directory creation support
"""

import os
from typing import Any, Dict
from pathlib import Path

from alonechat.core.base_tool import BaseTool
from alonechat.security.path_validator import PathValidator


class FileWriteTool(BaseTool):
    """
    文件写入工具 - File Write Tool

    写入文件内容，自动创建父目录
    Write file content, auto-create parent directories
    """

    name = "file_write"
    description = "Write content to file. Creates directories if needed."
    category = "file"
    permission_level = "write"
    estimated_cost = 0.001

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
            "mode": {
                "type": "string",
                "description": "Write mode: 'write' or 'append'",
                "enum": ["write", "append"],
                "default": "write",
            },
        },
        "required": ["path", "content"],
    }

    def execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        mode: str = "write",
    ) -> Dict[str, Any]:
        """
        写入文件 / Write file

        Args:
            path: 文件路径 / File path
            content: 写入内容 / Content to write
            encoding: 文件编码 / File encoding
            mode: 写入模式 / Write mode

        Returns:
            写入结果 / Write result
        """
        allowed_base = os.getenv("WORKSPACE_DIR", str(Path.cwd()))
        safe_path = PathValidator.resolve_safe_path(path, allowed_base)
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path traversal blocked: {path}",
            }

        file_path = safe_path
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            write_mode = "a" if mode == "append" else "w"
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": str(file_path.absolute()),
                "size": len(content.encode(encoding)),
                "mode": mode,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
