"""
Glob 工具 / Glob Tool

使用 glob 模式查找文件
Find files using glob patterns
"""

import glob
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.tool import Tool, ToolResult, ToolUseContext, PermissionResult, ToolProgressCallback

logger = logging.getLogger(__name__)


class GlobTool(Tool[Dict[str, str], List[str]]):
    """
    Glob 工具 / Glob Tool
    
    使用 glob 模式查找文件
    Find files using glob patterns
    
    使用示例 / Usage Example:
        tool = GlobTool()
        result = await tool.execute({"pattern": "**/*.py", "path": "/src"}, context)
    """
    
    @property
    def name(self) -> str:
        return "glob"
    
    @property
    def description(self) -> str:
        return "Find files using glob patterns"
    
    @property
    def aliases(self) -> list:
        return ["find_files", "ls_glob"]
    
    @property
    def search_hint(self) -> str:
        return "find files glob pattern search"
    
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '**/*.py', '*.txt')"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 100)",
                    "default": 100
                }
            },
            "required": ["pattern"]
        }
    
    async def execute(
        self,
        input_data: Dict[str, str],
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        pattern = input_data.get("pattern", "")
        path = input_data.get("path", ".")
        max_results = input_data.get("max_results", 100)
        
        if not pattern:
            return ToolResult(data=[], error="No pattern provided", is_error=True)
        
        try:
            # 构建完整模式 / Build full pattern
            full_pattern = os.path.join(path, pattern)
            
            # 执行 glob 查找 / Execute glob search
            matches = glob.glob(full_pattern, recursive=True)
            
            # 限制结果数量 / Limit result count
            if len(matches) > max_results:
                matches = matches[:max_results]
            
            # 格式化结果 / Format results
            result_lines = []
            for match in matches:
                # 获取相对路径 / Get relative path
                try:
                    rel_path = os.path.relpath(match, path)
                except ValueError:
                    rel_path = match
                
                # 添加类型标记 / Add type marker
                if os.path.isdir(match):
                    result_lines.append(f"[DIR]  {rel_path}")
                else:
                    size = os.path.getsize(match)
                    result_lines.append(f"[FILE] {rel_path} ({size} bytes)")
            
            return ToolResult(data=result_lines)
            
        except Exception as e:
            logger.error(f"Glob search failed: {e}")
            return ToolResult(data=[], error=str(e), is_error=True)
    
    def is_read_only(self, input_data: Dict[str, str]) -> bool:
        return True
    
    def get_activity_description(self, input_data: Optional[Dict[str, str]] = None) -> Optional[str]:
        if input_data:
            pattern = input_data.get("pattern", "")
            return f"Searching: {pattern}"
        return "Searching files"
