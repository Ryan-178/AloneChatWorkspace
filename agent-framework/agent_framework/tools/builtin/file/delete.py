"""
文件删除工具 - File Delete Tool

删除文件或目录
Delete file or directory
"""

import os
from typing import Any, Dict
from pathlib import Path
import shutil

from agent_framework.core.base_tool import BaseTool
from agent_framework.security.path_validator import PathValidator


class FileDeleteTool(BaseTool):
    """
    文件删除工具 - File Delete Tool

    删除文件或目录（需确认）
    Delete file or directory (requires confirmation)
    """

    name = "file_delete"
    description = "Delete file or directory. Use with caution."
    category = "file"
    permission_level = "dangerous"
    estimated_cost = 0.001

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to delete",
            },
            "recursive": {
                "type": "boolean",
                "description": "Delete directory recursively",
                "default": False,
            },
        },
        "required": ["path"],
    }

    def execute(
        self,
        path: str,
        recursive: bool = False,
    ) -> Dict[str, Any]:
        """
        删除文件/目录 / Delete file/directory

        Args:
            path: 要删除的路径 / Path to delete
            recursive: 是否递归删除目录 / Recursive delete

        Returns:
            删除结果 / Delete result
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
                "error": f"Path not found: {path}",
            }
        
        try:
            if file_path.is_file():
                file_path.unlink()
                return {
                    "success": True,
                    "path": str(file_path.absolute()),
                    "type": "file",
                }
            elif file_path.is_dir():
                if not recursive and any(file_path.iterdir()):
                    return {
                        "success": False,
                        "error": "Directory not empty. Use recursive=true to delete.",
                    }
                shutil.rmtree(file_path)
                return {
                    "success": True,
                    "path": str(file_path.absolute()),
                    "type": "directory",
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown path type: {path}",
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
