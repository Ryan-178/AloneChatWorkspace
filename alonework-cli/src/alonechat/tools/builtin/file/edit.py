"""
文件编辑工具 - File Edit Tool

使用SearchReplace模式编辑文件
Edit file using SearchReplace pattern
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

from alonechat.core.base_tool import BaseTool
from alonechat.security.path_validator import PathValidator


class FileEditTool(BaseTool):
    """
    文件编辑工具 - File Edit Tool

    使用SearchReplace模式精确编辑文件
    Edit file precisely using SearchReplace pattern
    """

    name = "file_edit"
    description = "Edit file using SearchReplace pattern. Finds old_str and replaces with new_str."
    category = "file"
    permission_level = "write"
    estimated_cost = 0.001

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to edit",
            },
            "old_str": {
                "type": "string",
                "description": "String to search for (must be unique)",
            },
            "new_str": {
                "type": "string",
                "description": "String to replace with",
            },
            "encoding": {
                "type": "string",
                "description": "File encoding (default: utf-8)",
                "default": "utf-8",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences (default: false)",
                "default": False,
            },
        },
        "required": ["path", "old_str", "new_str"],
    }

    def execute(
        self,
        path: str,
        old_str: str,
        new_str: str,
        encoding: str = "utf-8",
        replace_all: bool = False,
    ) -> Dict[str, Any]:
        """
        编辑文件 / Edit file

        Args:
            path: 文件路径 / File path
            old_str: 要查找的字符串 / String to search
            new_str: 替换字符串 / String to replace
            encoding: 文件编码 / File encoding
            replace_all: 是否替换所有 / Replace all occurrences

        Returns:
            编辑结果 / Edit result
        """
        allowed_base = os.getenv("WORKSPACE_DIR", str(Path.cwd()))
        safe_path = PathValidator.resolve_safe_path(path, allowed_base)
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path traversal blocked: {path}",
            }

        file_path = safe_path
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
            }
        
        if old_str == new_str:
            return {
                "success": False,
                "error": "old_str and new_str are identical",
            }
        
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            
            if old_str not in content:
                return {
                    "success": False,
                    "error": f"String not found in file: {old_str[:50]}...",
                }
            
            if not replace_all:
                count = content.count(old_str)
                if count > 1:
                    return {
                        "success": False,
                        "error": f"Found {count} occurrences. Use replace_all=true or make old_str more specific.",
                    }
            
            new_content = content.replace(old_str, new_str) if replace_all else content.replace(old_str, new_str, 1)
            
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)
            
            return {
                "success": True,
                "path": str(file_path.absolute()),
                "replacements": content.count(old_str) if replace_all else 1,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
