"""
AloneChat CLI 增强模块 / AloneChat CLI Enhancements Module

提供类似 Claude Code 的高级 CLI 功能 / Provides advanced CLI features similar to Claude Code:

- --worktree: 在隔离的 Git 工作树中启动 / Start in isolated Git worktree
- --add-dir: 从附加目录加载技能/插件/CLAUDE.md / Load skills/plugins/CLAUDE.md from additional directories
- 稀疏检出 / Sparse checkout support
- 嵌套技能自动发现 / Nested skill auto-discovery
- .claude/rules/ 条件性规则加载 / Conditional rule loading from .claude/rules/
- CLAUDE.md @import 支持 / CLAUDE.md @import support

使用前需初始化 / Initialize before use:
    from alonechat.cli_enhancements import CliEnhancementsManager
    manager = CliEnhancementsManager()
    manager.init_worktree(worktree_dir)
    manager.load_additional_dirs(["/path/to/dir"])
"""

from alonechat.cli_enhancements.manager import CliEnhancementsManager
from alonechat.cli_enhancements.worktree_manager import WorktreeManager, WorktreeInfo
from alonechat.cli_enhancements.claude_md_loader import ClaudeMdLoader, ClaudeMdConfig
from alonechat.cli_enhancements.rules_loader import RulesLoader, RuleFile
from alonechat.cli_enhancements.skills_discovery import SkillsDiscovery
from alonechat.cli_enhancements.additional_dir_loader import AdditionalDirLoader

__all__ = [
    "CliEnhancementsManager",
    "WorktreeManager",
    "WorktreeInfo",
    "ClaudeMdLoader",
    "ClaudeMdConfig",
    "RulesLoader",
    "RuleFile",
    "SkillsDiscovery",
    "AdditionalDirLoader",
]
