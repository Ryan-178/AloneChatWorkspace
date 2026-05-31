"""
Git分支工具 - Git Branch Tool

Git分支操作
Git branch operations
"""

import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path

from agent_framework.core.base_tool import BaseTool


class GitBranchTool(BaseTool):
    """
    Git分支工具 - Git Branch Tool
    
    创建、切换、列出分支
    Create, switch, and list branches
    """
    
    name = "git_branch"
    description = "Manage Git branches (list, create, switch, delete)."
    category = "git"
    permission_level = "write"
    estimated_cost = 0.001
    
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Branch action: list, create, switch, delete",
                "enum": ["list", "create", "switch", "delete"],
                "default": "list",
            },
            "branch": {
                "type": "string",
                "description": "Branch name (for create/switch/delete)",
            },
            "path": {
                "type": "string",
                "description": "Repository path",
            },
        },
        "required": [],
    }
    
    def execute(
        self,
        action: str = "list",
        branch: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行分支操作 / Execute branch action
        
        Args:
            action: 操作类型 / Action type
            branch: 分支名 / Branch name
            path: 仓库路径 / Repository path
        
        Returns:
            操作结果 / Operation result
        """
        repo_path = Path(path) if path else Path.cwd()
        
        if action == "list":
            return self._list_branches(repo_path)
        elif action == "create":
            if not branch:
                return {"success": False, "error": "Branch name required"}
            return self._create_branch(repo_path, branch)
        elif action == "switch":
            if not branch:
                return {"success": False, "error": "Branch name required"}
            return self._switch_branch(repo_path, branch)
        elif action == "delete":
            if not branch:
                return {"success": False, "error": "Branch name required"}
            return self._delete_branch(repo_path, branch)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    def _list_branches(self, repo_path: Path) -> Dict[str, Any]:
        """列出分支 / List branches"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            branches: List[Dict[str, Any]] = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                is_current = line.startswith("*")
                name = line.lstrip("* ").strip()
                is_remote = name.startswith("remotes/")
                branches.append({
                    "name": name,
                    "current": is_current,
                    "remote": is_remote,
                })
            
            return {
                "success": True,
                "branches": branches,
                "current": next((b["name"] for b in branches if b["current"]), None),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_branch(self, repo_path: Path, branch: str) -> Dict[str, Any]:
        """创建分支 / Create branch"""
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "branch": branch,
                "message": f"Created and switched to branch '{branch}'",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _switch_branch(self, repo_path: Path, branch: str) -> Dict[str, Any]:
        """切换分支 / Switch branch"""
        try:
            result = subprocess.run(
                ["git", "checkout", branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "branch": branch,
                "message": f"Switched to branch '{branch}'",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _delete_branch(self, repo_path: Path, branch: str) -> Dict[str, Any]:
        """删除分支 / Delete branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {
                "success": True,
                "branch": branch,
                "message": f"Deleted branch '{branch}'",
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
