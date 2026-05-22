"""
Git差异工具 - Git Diff Tool

查看Git差异
View Git diff
"""

import subprocess
from typing import Any, Dict, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool


class GitDiffTool(BaseTool):
    """
    Git差异工具 - Git Diff Tool
    
    查看文件或提交之间的差异
    View differences between files or commits
    """
    
    name = "git_diff"
    description = "View Git diff between files or commits."
    category = "git"
    permission_level = "read"
    estimated_cost = 0.001
    
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Repository path",
            },
            "target": {
                "type": "string",
                "description": "Target (file, commit, or branch)",
            },
            "staged": {
                "type": "boolean",
                "description": "Show staged changes",
                "default": False,
            },
        },
        "required": [],
    }
    
    def execute(
        self,
        path: Optional[str] = None,
        target: Optional[str] = None,
        staged: bool = False,
    ) -> Dict[str, Any]:
        """
        查看Git差异 / View Git diff
        
        Args:
            path: 仓库路径 / Repository path
            target: 目标 / Target
            staged: 已暂存 / Staged
        
        Returns:
            Git差异 / Git diff
        """
        repo_path = Path(path) if path else Path.cwd()
        
        try:
            cmd = ["git", "diff"]
            
            if staged:
                cmd.append("--staged")
            
            if target:
                cmd.append(target)
            
            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            return {
                "success": True,
                "diff": result.stdout,
                "path": str(repo_path.absolute()),
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
