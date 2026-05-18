"""
Git 工作树管理器 / Git Worktree Manager

提供隔离的 Git 工作树和稀疏检出功能 / Provides isolated Git worktree and sparse checkout features

版本 / Versions:
- --worktree 标志 / --worktree flag: 2.1.49
- 工作树稀疏检出 / Worktree sparse checkout: 2.1.76
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agent_framework.configs import load_yaml_config


@dataclass
class WorktreeInfo:
    """工作树信息 / Worktree Information"""
    path: str
    branch: str
    commit_hash: str
    is_sparse: bool = False
    sparse_paths: List[str] = field(default_factory=list)
    created_at: str = ""
    session_id: str = ""


class WorktreeManager:
    """
    Git 工作树管理器 / Git Worktree Manager
    
    在隔离的 Git 工作树中启动会话，避免影响主仓库 / Start session in isolated Git worktree
    支持稀疏检出，仅检出需要的目录 / Support sparse checkout for needed directories only
    
    用法 / Usage:
        wm = WorktreeManager()
        wm.create_worktree("/path/to/worktree")
        wm.setup_sparse_checkout(["/src", "/configs"])
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工作树管理器 / Initialize worktree manager
        
        Args:
            config: 工作树配置字典 / Worktree config dict
        """
        if config is None:
            config = load_yaml_config("cli_enhancements.yaml").get("worktree", {})
        self._config = config
        self._git_dir: Optional[str] = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    def is_git_repo(self, repo_path: Optional[str] = None) -> bool:
        """
        检查是否为 Git 仓库 / Check if is Git repository
        
        Args:
            repo_path: 仓库路径 / Repository path
            
        Returns:
            是否为 Git 仓库 / Whether is Git repository
        """
        target = repo_path or os.getcwd()
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=target,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._git_dir = result.stdout.strip()
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def create_worktree(
        self,
        worktree_path: str,
        branch: Optional[str] = None,
        session_id: Optional[str] = None,
        from_branch: Optional[str] = None,
    ) -> bool:
        """
        创建隔离的 Git 工作树 / Create isolated Git worktree
        
        Args:
            worktree_path: 工作树路径 / Worktree path
            branch: 分支名称（可选，默认自动生成）/ Branch name (optional)
            session_id: 会话ID（用于分支命名）/ Session ID (for branch naming)
            from_branch: 来源分支（默认为当前分支）/ Source branch (default: current)
            
        Returns:
            是否创建成功 / Whether creation succeeded
        """
        if not self.is_git_repo():
            return False
        
        if branch is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_part = f"_{session_id[:8]}" if session_id else ""
            branch = f"alonechat_worktree_{timestamp}{session_part}"
        
        try:
            if not Path(worktree_path).parent.exists():
                Path(worktree_path).parent.mkdir(parents=True, exist_ok=True)
            
            cmd = ["git", "worktree", "add", worktree_path, branch]
            if from_branch:
                cmd.extend(["-b", from_branch])
            
            result = subprocess.run(
                cmd,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                return False
            
            self._setup_sparse_checkout(worktree_path)
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return False
    
    def _setup_sparse_checkout(self, worktree_path: str) -> bool:
        """
        设置工作树稀疏检出 / Setup sparse checkout for worktree
        
        仅检出需要的目录以减少开销 / Only checkout needed directories to reduce overhead
        
        Args:
            worktree_path: 工作树路径 / Worktree path
            
        Returns:
            是否设置成功 / Whether setup succeeded
        """
        sparse_paths = self._config.get("sparse_paths", [])
        if not sparse_paths:
            return True
        
        try:
            git_dir = os.path.join(worktree_path, ".git")
            if not os.path.exists(git_dir):
                return False
            
            cmds = [
                (["git", "sparse-checkout", "init", "--cone"], worktree_path),
            ]
            
            for path in sparse_paths:
                cmds.append((["git", "sparse-checkout", "add", path], worktree_path))
            
            for cmd, cwd in cmds:
                subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def setup_sparse_checkout_for_current_dir(self, paths: Optional[List[str]] = None) -> bool:
        """
        为当前目录设置稀疏检出 / Setup sparse checkout for current directory
        
        版本 / Version: 2.1.76
        
        Args:
            paths: 要检出的路径列表 / List of paths to checkout
            
        Returns:
            是否设置成功 / Whether setup succeeded
        """
        sparse_paths = paths or self._config.get("sparse_paths", [])
        if not sparse_paths:
            return True
        
        try:
            subprocess.run(
                ["git", "sparse-checkout", "init", "--cone"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            
            for path in sparse_paths:
                subprocess.run(
                    ["git", "sparse-checkout", "add", path],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def list_worktrees(self) -> List[WorktreeInfo]:
        """
        列出所有工作树 / List all worktrees
        
        Returns:
            工作树信息列表 / List of worktree information
        """
        worktrees = []
        
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                return worktrees
            
            current = {}
            for line in result.stdout.strip().split("\n"):
                if line.startswith("worktree "):
                    if current:
                        worktrees.append(self._parse_worktree_entry(current))
                    current = {"path": line[9:]}
                elif line.startswith("HEAD "):
                    current["commit"] = line[5:]
                elif line.startswith("branch "):
                    ref = line[7:]
                    if ref.startswith("refs/heads/"):
                        current["branch"] = ref[11:]
                elif line == "" and current:
                    worktrees.append(self._parse_worktree_entry(current))
                    current = {}
            
            if current:
                worktrees.append(self._parse_worktree_entry(current))
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return worktrees
    
    def _parse_worktree_entry(self, entry: Dict[str, str]) -> WorktreeInfo:
        """解析工作树条目 / Parse worktree entry"""
        return WorktreeInfo(
            path=entry.get("path", ""),
            branch=entry.get("branch", ""),
            commit_hash=entry.get("commit", ""),
        )
    
    def remove_worktree(self, worktree_path: str, force: bool = False) -> bool:
        """
        移除工作树 / Remove worktree
        
        Args:
            worktree_path: 工作树路径 / Worktree path
            force: 是否强制移除 / Whether to force remove
            
        Returns:
            是否移除成功 / Whether removal succeeded
        """
        try:
            cmd = ["git", "worktree", "remove"]
            if force:
                cmd.append("--force")
            cmd.append(worktree_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                return False
            
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def prune_worktrees(self) -> bool:
        """
        清理过期的工作树 / Prune expired worktrees
        
        Returns:
            是否清理成功 / Whether pruning succeeded
        """
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def cleanup_old_worktrees(self, max_age_days: Optional[int] = None) -> int:
        """
        清理旧工作树 / Cleanup old worktrees
        
        Args:
            max_age_days: 最大保留天数 / Max retention days
            
        Returns:
            清理的工作树数量 / Number of cleaned worktrees
        """
        if max_age_days is None:
            max_age_days = self._config.get("max_age_days", 7)
        
        cleaned = 0
        worktrees = self.list_worktrees()
        now = datetime.now()
        threshold = timedelta(days=max_age_days)
        
        for wt in worktrees:
            try:
                wt_path = Path(wt.path)
                if not wt_path.exists():
                    self.prune_worktrees()
                    cleaned += 1
                    continue
                
                created = datetime.fromtimestamp(wt_path.stat().st_ctime)
                if now - created > threshold:
                    if self.remove_worktree(wt.path, force=True):
                        cleaned += 1
                        
            except (OSError, ValueError):
                continue
        
        return cleaned
    
    def get_worktree_git_dir(self, worktree_path: str) -> Optional[str]:
        """
        获取工作树的 Git 目录 / Get worktree's Git directory
        
        Args:
            worktree_path: 工作树路径 / Worktree path
            
        Returns:
            Git 目录路径 / Git directory path, or None if not found
        """
        git_dir = os.path.join(worktree_path, ".git")
        
        if os.path.isdir(git_dir):
            return git_dir
        
        if os.path.isfile(git_dir):
            try:
                with open(git_dir, "r") as f:
                    content = f.read().strip()
                if content.startswith("gitdir: "):
                    git_dir_path = content[8:]
                    if os.path.isabs(git_dir_path):
                        return git_dir_path
                    return os.path.normpath(os.path.join(worktree_path, git_dir_path))
            except OSError:
                return None
        
        return None
    
    def create_temp_worktree(self, session_id: str) -> Optional[str]:
        """
        创建临时工作树 / Create temporary worktree
        
        Args:
            session_id: 会话ID / Session ID
            
        Returns:
            工作树路径 / Worktree path, or None if failed
        """
        base_dir = self._config.get("base_dir", ".alonechat/worktrees")
        prefix = self._config.get("prefix", "session_")
        
        worktree_base = Path(os.getcwd()) / base_dir
        worktree_base.mkdir(parents=True, exist_ok=True)
        
        worktree_path = str(worktree_base / f"{prefix}{session_id[:16]}")
        
        if self.create_worktree(worktree_path, session_id=session_id):
            return worktree_path
        
        temp_dir = tempfile.mkdtemp(prefix=f"alonechat_{session_id[:8]}_")
        return temp_dir
    
    def is_in_worktree(self, path: Optional[str] = None) -> bool:
        """
        检查是否在工作树中 / Check if inside a worktree
        
        Args:
            path: 要检查的路径 / Path to check
            
        Returns:
            是否在工作树中 / Whether inside a worktree
        """
        target = path or os.getcwd()
        worktrees = self.list_worktrees()
        abs_target = os.path.abspath(target)
        
        for wt in worktrees:
            if os.path.abspath(wt.path) == abs_target:
                return True
        
        return False
