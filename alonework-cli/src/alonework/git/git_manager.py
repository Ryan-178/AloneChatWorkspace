"""
Gitéææ¨¡å / Git Integration Module

æä¾ / Provides:
- æºè½æäº¤ / Smart commit
- PRçæ / PR generation
- åæ´åæ / Change analysis
- åæ»æºå¶ / Rollback mechanism
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import yaml

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from alonework.configs import config


class ChangeType(Enum):
    """åæ´ç±»åæä¸¾ / Change Type Enum"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """æä»¶åæ´æ°æ®ç±?/ File Change Data Class"""
    path: str
    change_type: ChangeType
    old_path: Optional[str] = None
    insertions: int = 0
    deletions: int = 0
    
    @property
    def is_binary(self) -> bool:
        return self.insertions == 0 and self.deletions == 0


@dataclass
class CommitInfo:
    """æäº¤ä¿¡æ¯æ°æ®ç±?/ Commit Info Data Class"""
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    subject: str
    body: str = ""


@dataclass
class BranchInfo:
    """åæ¯ä¿¡æ¯æ°æ®ç±?/ Branch Info Data Class"""
    name: str
    is_current: bool
    is_remote: bool
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0


class GitConfigLoader:
    """Gitéç½®å è½½å?/ Git Config Loader"""
    
    _instance: Optional["GitConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """å è½½Gitéç½® / Load Git configuration"""
        config_path = Path(__file__).parent / "git_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """è·åé»è®¤éç½® / Get default configuration"""
        return {
            "git": {
                "commit": {
                    "types": [
                        {"key": "feat", "description": "æ°åè?, "emoji": "â?},
                        {"key": "fix", "description": "ä¿®å¤bug", "emoji": "ð"},
                        {"key": "docs", "description": "ææ¡£æ´æ°", "emoji": "ð"},
                        {"key": "style", "description": "ä»£ç æ ¼å¼", "emoji": "ð"},
                        {"key": "refactor", "description": "éæ", "emoji": "â»ï¸"},
                        {"key": "perf", "description": "æ§è½ä¼å", "emoji": "â?},
                        {"key": "test", "description": "æµè¯", "emoji": "â?},
                        {"key": "chore", "description": "æå»º/å·¥å·", "emoji": "ð§"},
                    ],
                    "max_subject_length": 72,
                },
                "diff": {
                    "context_lines": 3,
                    "max_diff_size": 10000,
                },
            },
            "messages": {
                "git": {
                    "no_changes": "æ²¡ææ£æµå°åæ´",
                    "commit_success": "æäº¤æå",
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """è·åéç½®å?/ Get configuration value"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def get_instance(cls) -> "GitConfigLoader":
        """è·ååä¾å®ä¾ / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


git_config = GitConfigLoader.get_instance()


class GitManager:
    """Gitç®¡çå?/ Git Manager"""
    
    def __init__(self, repo_path: Optional[Path] = None, console: Optional[Console] = None):
        self.repo_path = repo_path or Path.cwd()
        self.console = console or Console()
        self._git_config = git_config
    
    def _run_git(
        self,
        *args: str,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """æ§è¡Gitå½ä»¤ / Execute Git command"""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=capture_output,
            text=True,
        )
    
    def is_git_repo(self) -> bool:
        """æ£æ¥æ¯å¦ä¸ºGitä»åº / Check if is Git repository"""
        try:
            self._run_git("rev-parse", "--git-dir")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """è·åå½ååæ¯ / Get current branch"""
        try:
            result = self._run_git("branch", "--show-current")
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None
    
    def get_branches(self) -> List[BranchInfo]:
        """è·åææåæ?/ Get all branches"""
        branches = []
        
        try:
            result = self._run_git("branch", "-a", "--format=%(refname:short)|%(HEAD)|%(upstream:short)|%(ahead)|%(behind)")
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split("|")
                name = parts[0]
                is_current = parts[1] == "*" if len(parts) > 1 else False
                upstream = parts[2] if len(parts) > 2 and parts[2] else None
                ahead = int(parts[3]) if len(parts) > 3 and parts[3] else 0
                behind = int(parts[4]) if len(parts) > 4 and parts[4] else 0
                is_remote = name.startswith("remotes/")
                
                branches.append(BranchInfo(
                    name=name,
                    is_current=is_current,
                    is_remote=is_remote,
                    upstream=upstream,
                    ahead=ahead,
                    behind=behind,
                ))
        except subprocess.CalledProcessError:
            pass
        
        return branches
    
    def get_status(self) -> List[FileChange]:
        """è·åæä»¶ç¶æ?/ Get file status"""
        changes = []
        
        try:
            result = self._run_git("status", "--porcelain")
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                status = line[:2]
                path = line[3:].strip()
                
                if status.startswith("R"):
                    old_path, new_path = path.split(" -> ")
                    changes.append(FileChange(
                        path=new_path,
                        change_type=ChangeType.RENAMED,
                        old_path=old_path,
                    ))
                elif status.strip() in ("A", "??"):
                    changes.append(FileChange(path=path, change_type=ChangeType.ADDED))
                elif status.strip() == "D":
                    changes.append(FileChange(path=path, change_type=ChangeType.DELETED))
                else:
                    changes.append(FileChange(path=path, change_type=ChangeType.MODIFIED))
        except subprocess.CalledProcessError:
            pass
        
        return changes
    
    def get_diff(
        self,
        staged: bool = False,
        file_path: Optional[str] = None,
    ) -> str:
        """è·åå·®å¼ / Get diff"""
        args = ["diff"]
        
        if staged:
            args.append("--staged")
        
        context_lines = self._git_config.get("git.diff.context_lines", 3)
        args.extend(["-U", str(context_lines)])
        
        if file_path:
            args.append("--")
            args.append(file_path)
        
        try:
            result = self._run_git(*args)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
    
    def get_log(
        self,
        count: int = 10,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """è·åæäº¤æ¥å¿ / Get commit log"""
        commits = []
        
        args = [
            "log",
            f"-{count}",
            "--format=%H|%h|%an|%ae|%at|%s|%b",
            "--no-merges",
        ]
        
        if branch:
            args.append(branch)
        
        try:
            result = self._run_git(*args)
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                parts = line.split("|")
                if len(parts) >= 6:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        email=parts[3],
                        date=datetime.fromtimestamp(int(parts[4])),
                        subject=parts[5],
                        body=parts[6] if len(parts) > 6 else "",
                    ))
        except subprocess.CalledProcessError:
            pass
        
        return commits
    
    def analyze_changes(self) -> Dict[str, Any]:
        """åæåæ´ / Analyze changes"""
        changes = self.get_status()
        
        if not changes:
            return {
                "has_changes": False,
                "summary": self._git_config.get("messages.git.no_changes", "æ²¡ææ£æµå°åæ´"),
            }
        
        by_type: Dict[ChangeType, List[FileChange]] = {}
        for change in changes:
            if change.change_type not in by_type:
                by_type[change.change_type] = []
            by_type[change.change_type].append(change)
        
        extensions: Dict[str, int] = {}
        for change in changes:
            ext = Path(change.path).suffix or "no_ext"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            "has_changes": True,
            "total_files": len(changes),
            "by_type": {t.value: len(v) for t, v in by_type.items()},
            "by_extension": extensions,
            "files": changes,
        }
    
    def suggest_commit_type(self, changes: List[FileChange]) -> str:
        """å»ºè®®æäº¤ç±»å / Suggest commit type"""
        for change in changes:
            path = change.path.lower()
            
            if path.endswith((".md", ".rst", ".txt", "readme")):
                return "docs"
            if path.endswith(("_test.py", "test_", ".test.js", ".spec.js")):
                return "test"
            if path.startswith(("dockerfile", "docker-compose", ".github/workflows")):
                return "ci"
            if path.endswith((".json", ".yaml", ".yml", ".toml", ".cfg")):
                return "chore"
        
        return "feat"
    
    def generate_commit_message(
        self,
        changes: List[FileChange],
        commit_type: Optional[str] = None,
        scope: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """çææäº¤æ¶æ¯ / Generate commit message"""
        if commit_type is None:
            commit_type = self.suggest_commit_type(changes)
        
        commit_types = self._git_config.get("git.commit.types", [])
        emoji = ""
        for ct in commit_types:
            if ct.get("key") == commit_type:
                emoji = ct.get("emoji", "")
                break
        
        max_length = self._git_config.get("git.commit.max_subject_length", 72)
        
        if description is None:
            file_count = len(changes)
            description = f"æ´æ° {file_count} ä¸ªæä»?
        
        subject = f"{commit_type}"
        if scope:
            subject += f"({scope})"
        subject += f": {description}"
        
        if len(subject) > max_length:
            subject = subject[:max_length - 3] + "..."
        
        if emoji:
            subject = f"{emoji} {subject}"
        
        return subject
    
    def commit(
        self,
        message: str,
        add_all: bool = False,
        files: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """æäº¤åæ´ / Commit changes"""
        try:
            if add_all:
                self._run_git("add", "-A")
            elif files:
                self._run_git("add", *files)
            
            self._run_git("commit", "-m", message)
            
            return True, self._git_config.get("messages.git.commit_success", "æäº¤æå")
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.commit_failed', 'æäº¤å¤±è´¥')}: {e.stderr}"
    
    def create_branch(self, branch_name: str, base: Optional[str] = None) -> Tuple[bool, str]:
        """åå»ºåæ¯ / Create branch"""
        try:
            args = ["checkout", "-b", branch_name]
            if base:
                args.append(base)
            
            self._run_git(*args)
            return True, f"åæ¯åå»ºæå: {branch_name}"
        except subprocess.CalledProcessError as e:
            return False, f"åæ¯åå»ºå¤±è´¥: {e.stderr}"
    
    def push(
        self,
        branch: Optional[str] = None,
        remote: str = "origin",
        set_upstream: bool = False,
    ) -> Tuple[bool, str]:
        """æ¨éå°è¿ç¨ / Push to remote"""
        try:
            args = ["push", remote]
            
            if branch:
                args.append(branch)
            
            if set_upstream:
                args.append("-u")
            
            self._run_git(*args)
            return True, self._git_config.get("messages.git.push_success", "æ¨éæå?)
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.push_failed', 'æ¨éå¤±è´?)}: {e.stderr}"
    
    def rollback(
        self,
        target: Optional[str] = None,
        hard: bool = False,
        create_backup: bool = True,
    ) -> Tuple[bool, str]:
        """åæ»åæ´ / Rollback changes"""
        try:
            if create_backup:
                backup_prefix = self._git_config.get("git.rollback.backup_branch_prefix", "backup/")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{backup_prefix}rollback_{timestamp}"
                
                try:
                    self._run_git("branch", backup_name)
                except subprocess.CalledProcessError:
                    pass
            
            args = ["reset"]
            
            if hard:
                args.append("--hard")
            else:
                args.append("--soft")
            
            if target:
                args.append(target)
            else:
                args.append("HEAD~1")
            
            self._run_git(*args)
            return True, self._git_config.get("messages.git.rollback_success", "åæ»æå")
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.rollback_failed', 'åæ»å¤±è´¥')}: {e.stderr}"
    
    def render_status(self) -> Panel:
        """æ¸²æç¶æé¢æ?/ Render status panel"""
        analysis = self.analyze_changes()
        
        if not analysis.get("has_changes"):
            return Panel(
                analysis.get("summary", "æ²¡æåæ´"),
                title="Git ç¶æ?/ Git Status",
                border_style="green",
            )
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ç¶æ?/ Status", style="yellow")
        table.add_column("æä»¶ / File")
        
        status_map = {
            ChangeType.ADDED: "æ°å¢ / Added",
            ChangeType.MODIFIED: "ä¿®æ¹ / Modified",
            ChangeType.DELETED: "å é¤ / Deleted",
            ChangeType.RENAMED: "éå½å?/ Renamed",
        }
        
        for change in analysis.get("files", []):
            status = status_map.get(change.change_type, "æªç¥ / Unknown")
            table.add_row(status, change.path)
        
        return Panel(
            table,
            title=f"Git ç¶æ?/ Git Status ({analysis.get('total_files', 0)} æä»¶ / files)",
            border_style="blue",
        )
    
    def render_log(self, count: int = 10) -> Panel:
        """æ¸²ææ¥å¿é¢æ¿ / Render log panel"""
        commits = self.get_log(count)
        
        if not commits:
            return Panel(
                "æ²¡ææäº¤åå² / No commit history",
                title="Git æ¥å¿ / Git Log",
                border_style="yellow",
            )
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Hash", style="green", width=8)
        table.add_column("ä½è?/ Author", width=15)
        table.add_column("æ¥æ / Date", width=12)
        table.add_column("æ¶æ¯ / Message")
        
        for commit in commits:
            date_str = commit.date.strftime("%Y-%m-%d")
            table.add_row(
                commit.short_hash,
                commit.author[:15],
                date_str,
                commit.subject[:50],
            )
        
        return Panel(table, title="Git æ¥å¿ / Git Log", border_style="blue")
