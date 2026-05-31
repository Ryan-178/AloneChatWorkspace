"""
Git提交工具 - Git Commit Tool

提交Git更改
Commit Git changes
"""

import subprocess
from typing import Any, Dict, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool


class GitCommitTool(BaseTool):
    """
    Git提交工具 - Git Commit Tool
    
    提交暂存的更改
    Commit staged changes
    """
    
    name = "git_commit"
    description = "Commit staged changes to Git."
    category = "git"
    permission_level = "write"
    estimated_cost = 0.001
    
    parameters = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Commit message",
            },
            "path": {
                "type": "string",
                "description": "Repository path",
            },
            "add_all": {
                "type": "boolean",
                "description": "Stage all changes before commit",
                "default": False,
            },
        },
        "required": ["message"],
    }
    
    def execute(
        self,
        message: str,
        path: Optional[str] = None,
        add_all: bool = False,
    ) -> Dict[str, Any]:
        """
        提交更改 / Commit changes
        
        Args:
            message: 提交消息 / Commit message
            path: 仓库路径 / Repository path
            add_all: 暂存所有更改 / Stage all changes
        
        Returns:
            提交结果 / Commit result
        """
        repo_path = Path(path) if path else Path.cwd()
        
        try:
            if add_all:
                add_result = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                )
                if add_result.returncode != 0:
                    return {"success": False, "error": add_result.stderr}
            
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                if "nothing to commit" in result.stdout:
                    return {
                        "success": True,
                        "message": "Nothing to commit",
                    }
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "output": result.stdout,
                "message": message,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
