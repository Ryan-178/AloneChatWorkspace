"""
Grep 工具 / Grep Tool

在文件中搜索内容
Search for content in files
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.tool import Tool, ToolResult, ToolUseContext, PermissionResult, ToolProgressCallback

logger = logging.getLogger(__name__)


class GrepTool(Tool[Dict[str, Any], List[str]]):
    """
    Grep 工具 / Grep Tool
    
    在文件中搜索内容
    Search for content in files
    
    使用示例 / Usage Example:
        tool = GrepTool()
        result = await tool.execute(
            {"pattern": "def main", "path": "/src", "glob": "*.py"},
            context
        )
    """
    
    @property
    def name(self) -> str:
        return "grep"
    
    @property
    def description(self) -> str:
        return "Search for content in files using regex"
    
    @property
    def aliases(self) -> list:
        return ["search", "find_content"]
    
    @property
    def search_hint(self) -> str:
        return "search grep regex content find"
    
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in (default: current directory)"
                },
                "glob": {
                    "type": "string",
                    "description": "File glob pattern to filter (e.g., '*.py')"
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search (default: false)",
                    "default": False
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 100)",
                    "default": 100
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines before and after match (default: 0)",
                    "default": 0
                }
            },
            "required": ["pattern"]
        }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: ToolUseContext,
        on_progress: Optional[ToolProgressCallback] = None
    ) -> ToolResult:
        pattern = input_data.get("pattern", "")
        path = input_data.get("path", ".")
        glob_pattern = input_data.get("glob")
        case_insensitive = input_data.get("case_insensitive", False)
        max_results = input_data.get("max_results", 100)
        context_lines = input_data.get("context_lines", 0)
        
        if not pattern:
            return ToolResult(data=[], error="No pattern provided", is_error=True)
        
        try:
            # 编译正则表达式 / Compile regex
            flags = re.IGNORECASE if case_insensitive else 0
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult(data=[], error=f"Invalid regex: {e}", is_error=True)
            
            results = []
            path_obj = Path(path)
            
            # 确定要搜索的文件 / Determine files to search
            if path_obj.is_file():
                files = [path_obj]
            elif path_obj.is_dir():
                if glob_pattern:
                    files = list(path_obj.rglob(glob_pattern))
                else:
                    files = list(path_obj.rglob("*"))
                files = [f for f in files if f.is_file()]
            else:
                return ToolResult(data=[], error=f"Path not found: {path}", is_error=True)
            
            # 搜索文件 / Search files
            for file_path in files:
                if len(results) >= max_results:
                    break
                
                try:
                    # 跳过二进制文件 / Skip binary files
                    if self._is_binary(file_path):
                        continue
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # 搜索匹配 / Search matches
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            # 获取上下文 / Get context
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            
                            # 格式化结果 / Format result
                            rel_path = os.path.relpath(file_path, path)
                            match_info = {
                                "file": rel_path,
                                "line_number": i + 1,
                                "line": line.rstrip(),
                                "context": [l.rstrip() for l in lines[start:end]]
                            }
                            results.append(match_info)
                            
                            if len(results) >= max_results:
                                break
                
                except (PermissionError, UnicodeDecodeError):
                    continue
            
            # 格式化输出 / Format output
            output_lines = []
            for r in results:
                output_lines.append(f"{r['file']}:{r['line_number']}: {r['line']}")
                if context_lines > 0:
                    for ctx_line in r['context']:
                        output_lines.append(f"  {ctx_line}")
                    output_lines.append("")
            
            return ToolResult(data=output_lines)
            
        except Exception as e:
            logger.error(f"Grep search failed: {e}")
            return ToolResult(data=[], error=str(e), is_error=True)
    
    def _is_binary(self, file_path: Path) -> bool:
        """检查文件是否为二进制 / Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                return b'\0' in chunk
        except Exception:
            return False
    
    def is_read_only(self, input_data: Dict[str, Any]) -> bool:
        return True
    
    def get_activity_description(self, input_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if input_data:
            pattern = input_data.get("pattern", "")
            return f"Searching: {pattern}"
        return "Searching content"
