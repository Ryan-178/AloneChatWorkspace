"""
Git模块 / Git Module

提供 / Provides:
- Git管理器 / Git manager
- 智能提交 / Smart commit
- PR生成 / PR generation
"""

from alonechat.git.git_manager import (
    GitManager,
    GitConfigLoader,
    git_config,
    FileChange,
    CommitInfo,
    BranchInfo,
    ChangeType,
)
from alonechat.git.smart_commit import SmartCommit

__all__ = [
    "GitManager",
    "GitConfigLoader",
    "git_config",
    "FileChange",
    "CommitInfo",
    "BranchInfo",
    "ChangeType",
    "SmartCommit",
]
