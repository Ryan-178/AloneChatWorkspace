"""
文件写入工具 / File Write Tool

写入或创建文件
Write or create files
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.tool import Tool, ToolResult, ToolUseContext, PermissionResult, ToolProgressCallback

logger = logging.getLogger(__name__)


class FileWriteTool(Tool[Dict[str, str], str]):
    """
    文件写入工具 / File Write Tool
    
    写入或创建文件
    Write or create files
    
    使用示例 / Usage Example:
        tool = FileWriteTool()
        result = await tool.execute(
            {"file_path": "/path/to/file", "content": "Hello!"},
            context
        )
    """
    
    @property
    def name(self) -> str:
        return "file_write"
    
    @property
    def description(self) -> str:
        return "Write content to a file"
    
    @property
    def aliases(self) -> list:
        return ["write"]
    
    @property
    def search_hint(self) -> str:
        return "write file create save"
    
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to file instead of overwriting (default: false)",
                    "default": False
                }
            },
            "required": ["file_path", "content"]
        }
    
    async def execute(
        self,
        input_data: Dict[str, str],
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        file_path = input_data.get("file_path", "")
        content = input_data.get("content", "")
        encoding = input_data.get("encoding", "utf-8")
        append = input_data.get("append", False)
        
        if not file_path:
            return ToolResult(data="", error="No file path provided", is_error=True)
        
        try:
            path = Path(file_path)
            
            # 创建目录（如果不存在）/ Create directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入模式 / Write mode
            mode = 'a' if append else 'w'
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            action = "Appended to" if append else "Wrote"
            return ToolResult(data=f"{action} file: {file_path}")
            
        except PermissionError:
            return ToolResult(data="", error=f"Permission denied: {file_path}", is_error=True)
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return ToolResult(data="", error=str(e), is_error=True)
    
    def is_read_only(self, input_data: Dict[str, str]) -> bool:
        return False
    
    def is_destructive(self, input_data: Dict[str, str]) -> bool:
        # 覆盖写入是破坏性的 / Overwriting is destructive
        append = input_data.get("append", False)
        return not append
    
    def get_path(self, input_data: Dict[str, str]) -> Optional[str]:
        return input_data.get("file_path")
    
    async def check_permissions(
        self,
        input_data: Dict[str, str],
        context: ToolUseContext
    ) -> PermissionResult:
        # 覆盖写入需要确认 / Overwriting needs confirmation
        if self.is_destructive(input_data):
            return PermissionResult.ASK
        return PermissionResult.ALLOW
    
    def get_activity_description(self, input_data: Optional[Dict[str, str]] = None) -> Optional[str]:
        if input_data:
            file_path = input_data.get("file_path", "")
            return f"Writing: {os.path.basename(file_path)}"
        return "Writing file"
