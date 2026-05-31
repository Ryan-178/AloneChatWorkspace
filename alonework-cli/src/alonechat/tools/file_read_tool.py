"""
文件读取工具 / File Read Tool

读取文件内容
Read file contents
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.tool import Tool, ToolResult, ToolUseContext, PermissionResult, ToolProgressCallback

logger = logging.getLogger(__name__)


class FileReadTool(Tool[Dict[str, Any], str]):
    """
    文件读取工具 / File Read Tool
    
    读取文件内容
    Read file contents
    
    使用示例 / Usage Example:
        tool = FileReadTool()
        result = await tool.execute({"file_path": "/path/to/file"}, context)
    """
    
    @property
    def name(self) -> str:
        return "file_read"
    
    @property
    def description(self) -> str:
        return "Read file contents"
    
    @property
    def aliases(self) -> list:
        return ["read", "cat"]
    
    @property
    def search_hint(self) -> str:
        return "read file view content cat"
    
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-based)",
                    "minimum": 1
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                    "minimum": 1
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                }
            },
            "required": ["file_path"]
        }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        file_path = input_data.get("file_path", "")
        offset = input_data.get("offset", 1)
        limit = input_data.get("limit")
        encoding = input_data.get("encoding", "utf-8")
        
        if not file_path:
            return ToolResult(data="", error="No file path provided", is_error=True)
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return ToolResult(data="", error=f"File not found: {file_path}", is_error=True)
            
            if not path.is_file():
                return ToolResult(data="", error=f"Not a file: {file_path}", is_error=True)
            
            # 读取文件 / Read file
            with open(path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # 应用偏移和限制 / Apply offset and limit
            start = max(0, offset - 1)  # 转换为 0-based 索引 / Convert to 0-based index
            if limit:
                lines = lines[start:start + limit]
            else:
                lines = lines[start:]
            
            content = ''.join(lines)
            
            # 添加行号 / Add line numbers
            numbered_lines = []
            for i, line in enumerate(lines, start=start + 1):
                numbered_lines.append(f"{i}: {line}")
            
            result = ''.join(numbered_lines)
            
            return ToolResult(data=result)
            
        except PermissionError:
            return ToolResult(data="", error=f"Permission denied: {file_path}", is_error=True)
        except UnicodeDecodeError as e:
            return ToolResult(data="", error=f"Encoding error: {e}", is_error=True)
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return ToolResult(data="", error=str(e), is_error=True)
    
    def is_read_only(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def get_path(self, input_data: Dict[str, Any]) -> Optional[str]:
        return input_data.get("file_path")
    
    def get_activity_description(self, input_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if input_data:
            file_path = input_data.get("file_path", "")
            return f"Reading: {os.path.basename(file_path)}"
        return "Reading file"
