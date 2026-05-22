"""
Git状态工具 - Git Status Tool

查看Git仓库状态
View Git repository status
"""

import subprocess
from typing import Any, Dict, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool


class GitStatusTool(BaseTool):
    """
    Git状态工具 - Git Status Tool
    
    查看Git仓库的当前状态
    View current status of Git repository
    """
    
    name = "git_status"
    description = "View Git repository status."
    category = "git"
    permission_level = "read"
    estimated_cost = 0.001
    
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Repository path (default: current directory)",
            },
            "short": {
                "type": "boolean",
                "description": "Short format output",
                "default": False,
            },
        },
        "required": [],
    }
    
    def execute(
        self,
        path: Optional[str] = None,
        short: bool = False,
    ) -> Dict[str, Any]:
        """
        查看Git状态 / View Git status
        
        Args:
            path: 仓库路径 / Repository path
            short: 简短格式 / Short format
        
        Returns:
            Git状态 / Git status
        """
        repo_path = Path(path) if path else Path.cwd()
        
        try:
            cmd = ["git", "status"]
            if short:
                cmd.append("-s")
            
            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or "Not a git repository",
                }
            
            return {
                "success": True,
                "output": result.stdout,
                "path": str(repo_path.absolute()),
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
