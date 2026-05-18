"""
Git集成模块 / Git Integration Module

提供 / Provides:
- 智能提交 / Smart commit
- PR生成 / PR generation
- 变更分析 / Change analysis
- 回滚机制 / Rollback mechanism
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

from alonechat.configs import config


class ChangeType(Enum):
    """变更类型枚举 / Change Type Enum"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """文件变更数据类 / File Change Data Class"""
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
    """提交信息数据类 / Commit Info Data Class"""
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    subject: str
    body: str = ""


@dataclass
class BranchInfo:
    """分支信息数据类 / Branch Info Data Class"""
    name: str
    is_current: bool
    is_remote: bool
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0


class GitConfigLoader:
    """Git配置加载器 / Git Config Loader"""
    
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
        """加载Git配置 / Load Git configuration"""
        config_path = Path(__file__).parent / "git_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置 / Get default configuration"""
        return {
            "git": {
                "commit": {
                    "types": [
                        {"key": "feat", "description": "新功能", "emoji": "✨"},
                        {"key": "fix", "description": "修复bug", "emoji": "🐛"},
                        {"key": "docs", "description": "文档更新", "emoji": "📝"},
                        {"key": "style", "description": "代码格式", "emoji": "💄"},
                        {"key": "refactor", "description": "重构", "emoji": "♻️"},
                        {"key": "perf", "description": "性能优化", "emoji": "⚡"},
                        {"key": "test", "description": "测试", "emoji": "✅"},
                        {"key": "chore", "description": "构建/工具", "emoji": "🔧"},
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
                    "no_changes": "没有检测到变更",
                    "commit_success": "提交成功",
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值 / Get configuration value"""
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
        """获取单例实例 / Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


git_config = GitConfigLoader.get_instance()


class GitManager:
    """Git管理器 / Git Manager"""
    
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
        """执行Git命令 / Execute Git command"""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=capture_output,
            text=True,
        )
    
    def is_git_repo(self) -> bool:
        """检查是否为Git仓库 / Check if is Git repository"""
        try:
            self._run_git("rev-parse", "--git-dir")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """获取当前分支 / Get current branch"""
        try:
            result = self._run_git("branch", "--show-current")
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None
    
    def get_branches(self) -> List[BranchInfo]:
        """获取所有分支 / Get all branches"""
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
        """获取文件状态 / Get file status"""
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
        """获取差异 / Get diff"""
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
        """获取提交日志 / Get commit log"""
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
        """分析变更 / Analyze changes"""
        changes = self.get_status()
        
        if not changes:
            return {
                "has_changes": False,
                "summary": self._git_config.get("messages.git.no_changes", "没有检测到变更"),
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
        """建议提交类型 / Suggest commit type"""
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
        """生成提交消息 / Generate commit message"""
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
            description = f"更新 {file_count} 个文件"
        
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
        """提交变更 / Commit changes"""
        try:
            if add_all:
                self._run_git("add", "-A")
            elif files:
                self._run_git("add", *files)
            
            self._run_git("commit", "-m", message)
            
            return True, self._git_config.get("messages.git.commit_success", "提交成功")
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.commit_failed', '提交失败')}: {e.stderr}"
    
    def create_branch(self, branch_name: str, base: Optional[str] = None) -> Tuple[bool, str]:
        """创建分支 / Create branch"""
        try:
            args = ["checkout", "-b", branch_name]
            if base:
                args.append(base)
            
            self._run_git(*args)
            return True, f"分支创建成功: {branch_name}"
        except subprocess.CalledProcessError as e:
            return False, f"分支创建失败: {e.stderr}"
    
    def push(
        self,
        branch: Optional[str] = None,
        remote: str = "origin",
        set_upstream: bool = False,
    ) -> Tuple[bool, str]:
        """推送到远程 / Push to remote"""
        try:
            args = ["push", remote]
            
            if branch:
                args.append(branch)
            
            if set_upstream:
                args.append("-u")
            
            self._run_git(*args)
            return True, self._git_config.get("messages.git.push_success", "推送成功")
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.push_failed', '推送失败')}: {e.stderr}"
    
    def rollback(
        self,
        target: Optional[str] = None,
        hard: bool = False,
        create_backup: bool = True,
    ) -> Tuple[bool, str]:
        """回滚变更 / Rollback changes"""
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
            return True, self._git_config.get("messages.git.rollback_success", "回滚成功")
        except subprocess.CalledProcessError as e:
            return False, f"{self._git_config.get('messages.git.rollback_failed', '回滚失败')}: {e.stderr}"
    
    def render_status(self) -> Panel:
        """渲染状态面板 / Render status panel"""
        analysis = self.analyze_changes()
        
        if not analysis.get("has_changes"):
            return Panel(
                analysis.get("summary", "没有变更"),
                title="Git 状态 / Git Status",
                border_style="green",
            )
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("状态 / Status", style="yellow")
        table.add_column("文件 / File")
        
        status_map = {
            ChangeType.ADDED: "新增 / Added",
            ChangeType.MODIFIED: "修改 / Modified",
            ChangeType.DELETED: "删除 / Deleted",
            ChangeType.RENAMED: "重命名 / Renamed",
        }
        
        for change in analysis.get("files", []):
            status = status_map.get(change.change_type, "未知 / Unknown")
            table.add_row(status, change.path)
        
        return Panel(
            table,
            title=f"Git 状态 / Git Status ({analysis.get('total_files', 0)} 文件 / files)",
            border_style="blue",
        )
    
    def render_log(self, count: int = 10) -> Panel:
        """渲染日志面板 / Render log panel"""
        commits = self.get_log(count)
        
        if not commits:
            return Panel(
                "没有提交历史 / No commit history",
                title="Git 日志 / Git Log",
                border_style="yellow",
            )
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Hash", style="green", width=8)
        table.add_column("作者 / Author", width=15)
        table.add_column("日期 / Date", width=12)
        table.add_column("消息 / Message")
        
        for commit in commits:
            date_str = commit.date.strftime("%Y-%m-%d")
            table.add_row(
                commit.short_hash,
                commit.author[:15],
                date_str,
                commit.subject[:50],
            )
        
        return Panel(table, title="Git 日志 / Git Log", border_style="blue")
