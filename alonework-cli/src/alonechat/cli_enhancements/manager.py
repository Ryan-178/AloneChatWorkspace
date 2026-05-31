"""
CLI 增强管理器 / CLI Enhancements Manager

统一管理所有 CLI 增强功能 / Unified manager for all CLI enhancement features
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from alonechat.configs import load_yaml_config


@dataclass
class CliEnhancementsState:
    """CLI 增强状态 / CLI Enhancements State"""
    worktree_dir: Optional[Path] = None
    worktree_active: bool = False
    additional_dirs: List[Path] = field(default_factory=list)
    claude_md_content: Optional[str] = None
    rules: List[Dict[str, Any]] = field(default_factory=list)
    discovered_skills: List[Dict[str, Any]] = field(default_factory=list)
    loaded_configs: Dict[str, Any] = field(default_factory=dict)
    original_cwd: Optional[Path] = None


class CliEnhancementsManager:
    """
    CLI 增强管理器 / CLI Enhancements Manager
    
    作为所有 CLI 增强功能的统一入口 / Acts as unified entry for all CLI enhancements
    
    用法 / Usage:
        manager = CliEnhancementsManager()
        manager.setup(worktree_dir="/path/to/worktree", additional_dirs=["/path/to/dir"])
        state = manager.get_state()
    """
    
    def __init__(self):
        self._config = load_yaml_config("cli_enhancements.yaml")
        self._state = CliEnhancementsState()
        self._initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    @property
    def state(self) -> CliEnhancementsState:
        """获取当前状态 / Get current state"""
        return self._state
    
    def setup(
        self,
        worktree_dir: Optional[str] = None,
        additional_dirs: Optional[List[str]] = None,
        cwd: Optional[str] = None,
    ) -> "CliEnhancementsState":
        """
        设置所有 CLI 增强 / Setup all CLI enhancements
        
        Args:
            worktree_dir: 工作树目录 / Worktree directory
            additional_dirs: 附加目录 / Additional directories
            cwd: 当前工作目录 / Current working directory
            
        Returns:
            设置后的状态 / State after setup
        """
        from alonechat.cli_enhancements.worktree_manager import WorktreeManager
        from alonechat.cli_enhancements.additional_dir_loader import AdditionalDirLoader
        from alonechat.cli_enhancements.skills_discovery import SkillsDiscovery
        from alonechat.cli_enhancements.rules_loader import RulesLoader
        from alonechat.cli_enhancements.claude_md_loader import ClaudeMdLoader
        
        current_cwd = Path(cwd).resolve() if cwd else Path.cwd().resolve()
        self._state.original_cwd = current_cwd
        
        # 1. 初始化工作树 / Initialize worktree
        if worktree_dir:
            wm = WorktreeManager(self._config.get("worktree", {}))
            worktree_path = Path(worktree_dir).resolve()
            success = wm.create_worktree(str(worktree_path))
            if success:
                self._state.worktree_dir = worktree_path
                self._state.worktree_active = True
        
        # 2. 加载附加目录 / Load additional directories
        if additional_dirs:
            dirs = [Path(d).resolve() for d in additional_dirs if Path(d).exists()]
            self._state.additional_dirs = dirs
            loader = AdditionalDirLoader(self._config.get("additional_dirs", {}))
            self._state.loaded_configs = loader.load_all(dirs)
        
        # 3. 发现嵌套技能 / Discover nested skills
        work_dir = self._state.worktree_dir if self._state.worktree_dir else current_cwd
        discovery = SkillsDiscovery(self._config.get("skills", {}))
        self._state.discovered_skills = discovery.discover_all(str(work_dir))
        
        # 4. 加载规则 / Load rules
        rules_loader = RulesLoader(self._config.get("rules", {}))
        self._state.rules = rules_loader.load_all(str(work_dir))
        
        # 5. 加载 CLAUDE.md / Load CLAUDE.md
        claude_loader = ClaudeMdLoader(self._config.get("claude_md", {}))
        self._state.claude_md_content = claude_loader.load_and_resolve(str(work_dir))
        
        self._initialized = True
        return self._state
    
    def get_combined_context(self) -> str:
        """
        获取合并后的上下文信息 / Get combined context information
        
        将所有增强功能的信息合并为一个字符串 / Combine all enhancement info into one string
        
        Returns:
            合并后的上下文字符串 / Combined context string
        """
        parts = []
        
        if self._state.worktree_active:
            parts.append(f"[Worktree Active: {self._state.worktree_dir}]")
        
        if self._state.additional_dirs:
            dirs_str = ", ".join(str(d) for d in self._state.additional_dirs)
            parts.append(f"[Additional Dirs: {dirs_str}]")
        
        if self._state.rules:
            rule_names = [r.get("name", "unknown") for r in self._state.rules]
            parts.append(f"[Rules Loaded: {', '.join(rule_names)}]")
        
        if self._state.discovered_skills:
            skill_names = [s.get("name", "unknown") for s in self._state.discovered_skills]
            parts.append(f"[Skills Discovered: {', '.join(skill_names)}]")
        
        if self._state.claude_md_content:
            parts.append("[CLAUDE.md Loaded]")
        
        return "\n".join(parts)
    
    def cleanup(self) -> None:
        """清理所有资源 / Cleanup all resources"""
        if self._state.worktree_active and self._state.worktree_dir:
            from alonechat.cli_enhancements.worktree_manager import WorktreeManager
            wm = WorktreeManager(self._config.get("worktree", {}))
            wm.remove_worktree(str(self._state.worktree_dir))
            self._state.worktree_active = False
            self._state.worktree_dir = None
    
    def is_initialized(self) -> bool:
        """是否已初始化 / Whether initialized"""
        return self._initialized
