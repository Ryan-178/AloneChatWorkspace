"""
文件搜索工具 - File Search Tool

使用ripgrep或grep搜索文件内容
Search file content using ripgrep or grep
"""

import os
import subprocess
import shutil
from typing import Any, Dict, List, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool
from agent_framework.security.path_validator import PathValidator


class FileSearchTool(BaseTool):
    """
    文件搜索工具 - File Search Tool
    
    在文件中搜索内容，支持正则表达式
    Search content in files with regex support
    """
    
    name = "file_search"
    description = "Search content in files. Supports regex patterns."
    category = "file"
    permission_level = "read"
    estimated_cost = 0.001
    
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (regex supported)",
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search in",
            },
            "file_pattern": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py')",
            },
            "ignore_case": {
                "type": "boolean",
                "description": "Case insensitive search",
                "default": False,
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 100,
            },
        },
        "required": ["pattern"],
    }
    
    def execute(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: Optional[str] = None,
        ignore_case: bool = False,
        max_results: int = 100,
    ) -> Dict[str, Any]:
        """
        搜索文件内容 / Search file content
        
        Args:
            pattern: 搜索模式 / Search pattern
            path: 搜索路径 / Search path
            file_pattern: 文件过滤模式 / File filter pattern
            ignore_case: 忽略大小写 / Ignore case
            max_results: 最大结果数 / Max results
        
        Returns:
            搜索结果 / Search results
        """
        allowed_base = os.getenv("WORKSPACE_DIR", str(Path.cwd()))
        raw_path = Path(path) if path else Path.cwd()
        safe_path = PathValidator.resolve_safe_path(str(raw_path), allowed_base)
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path traversal blocked: {path}",
                "matches": [],
                "total": 0,
            }
        search_path = safe_path
        
        try:
            has_ripgrep = shutil.which("rg") is not None
        except:
            has_ripgrep = False
        
        if has_ripgrep:
            return self._search_with_ripgrep(
                pattern, search_path, file_pattern, ignore_case, max_results
            )
        else:
            return self._search_with_grep(
                pattern, search_path, file_pattern, ignore_case, max_results
            )
    
    def _search_with_ripgrep(
        self,
        pattern: str,
        path: Path,
        file_pattern: Optional[str],
        ignore_case: bool,
        max_results: int,
    ) -> Dict[str, Any]:
        """使用ripgrep搜索 / Search with ripgrep"""
        import shutil
        
        cmd = ["rg", "--line-number", "--no-heading"]
        
        if ignore_case:
            cmd.append("-i")
        
        if file_pattern:
            cmd.extend(["-g", file_pattern])
        
        cmd.extend(["-c"] if max_results else [])
        cmd.append("--")
        cmd.append(pattern)
        cmd.append(str(path))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            matches = self._parse_output(result.stdout, max_results)
            
            return {
                "success": True,
                "matches": matches,
                "total": len(matches),
                "engine": "ripgrep",
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Search timed out",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _search_with_grep(
        self,
        pattern: str,
        path: Path,
        file_pattern: Optional[str],
        ignore_case: bool,
        max_results: int,
    ) -> Dict[str, Any]:
        """使用grep搜索 / Search with grep"""
        cmd = ["grep", "-rn"]
        
        if ignore_case:
            cmd.append("-i")
        
        if file_pattern:
            cmd.extend(["--include", file_pattern])
        
        cmd.append(pattern)
        cmd.append(str(path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            matches = self._parse_output(result.stdout, max_results)

            return {
                "success": True,
                "matches": matches,
                "total": len(matches),
                "engine": "grep",
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Search timed out",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "grep not found. Please install ripgrep for better search.",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _parse_output(self, output: str, max_results: int) -> List[Dict[str, Any]]:
        """解析搜索输出 / Parse search output"""
        matches = []
        for line in output.strip().split("\n")[:max_results]:
            if not line:
                continue
            
            parts = line.split(":", 2)
            if len(parts) >= 3:
                matches.append({
                    "file": parts[0],
                    "line": int(parts[1]),
                    "content": parts[2].strip(),
                })
            elif len(parts) == 2:
                matches.append({
                    "file": parts[0],
                    "line": 0,
                    "content": parts[1].strip(),
                })
        
        return matches
