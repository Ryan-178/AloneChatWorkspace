"""
嵌套技能自动发现 / Nested Skill Auto-Discovery

从嵌套的 .claude/skills 目录中自动发现技能 / Auto-discover skills from nested .claude/skills directories

版本 / Version: 2.1.6
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field

from agent_framework.configs import load_yaml_config


@dataclass
class DiscoveredSkill:
    """发现的技能 / Discovered Skill"""
    name: str
    path: str
    source_dir: str
    definition_file: str
    description: str = ""
    version: str = ""
    nested_depth: int = 0
    skill_type: str = "local"
    config: Dict[str, Any] = field(default_factory=dict)


class SkillsDiscovery:
    """
    嵌套技能自动发现器 / Nested Skill Auto-Discovery
    
    从多个目录自动发现技能文件 / Auto-discover skill files from multiple directories
    
    扫描路径 / Scan paths:
    - .claude/skills/
    - .skills/
    - $HOME/.claude/skills/
    - $HOME/.skills/
    
    用法 / Usage:
        discovery = SkillsDiscovery()
        skills = discovery.discover_all("/path/to/project")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化技能发现器 / Initialize skills discovery
        
        Args:
            config: 技能发现配置字典 / Skills discovery config dict
        """
        if config is None:
            config = load_yaml_config("cli_enhancements.yaml").get("skills", {})
        self._config = config
        self._discovered: Dict[str, DiscoveredSkill] = {}
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    def discover_all(self, project_dir: str) -> List[Dict[str, Any]]:
        """
        从所有目录发现技能 / Discover skills from all directories
        
        Args:
            project_dir: 项目目录 / Project directory
            
        Returns:
            技能字典列表 / List of skill dicts
        """
        self._discovered.clear()
        
        discovery_dirs = self._config.get("discovery_dirs", [
            ".claude/skills",
            ".skills",
        ])
        
        search_paths = self._build_search_paths(project_dir, discovery_dirs)
        
        for search_path in search_paths:
            self._discover_in_directory(search_path)
        
        additional_search_dirs = self._config.get("additional_search_dirs", [])
        for additional_dir in additional_search_dirs:
            self._discover_in_directory(Path(additional_dir))
        
        return list(self._discovered.values())
    
    def _build_search_paths(self, project_dir: str, discovery_dirs: List[str]) -> List[Path]:
        """
        构建搜索路径列表 / Build search path list
        
        Args:
            project_dir: 项目目录 / Project directory
            discovery_dirs: 发现目录列表 / Discovery directory list
            
        Returns:
            搜索路径列表 / List of search paths
        """
        paths: List[Path] = []
        project_path = Path(project_dir)
        
        for rel_dir in discovery_dirs:
            paths.append(project_path / rel_dir)
        
        home_dir = Path.home()
        for rel_dir in discovery_dirs:
            paths.append(home_dir / rel_dir)
        
        return paths
    
    def _discover_in_directory(self, directory: Path, depth: int = 0) -> None:
        """
        在目录中发现技能 / Discover skills in directory
        
        Args:
            directory: 要搜索的目录 / Directory to search
            depth: 当前嵌套深度 / Current nesting depth
        """
        if not directory.exists() or not directory.is_dir():
            return
        
        max_depth = self._config.get("max_depth", 3)
        if depth > max_depth:
            return
        
        skill_def_file = self._config.get("skill_def_file", "SKILL.md")
        
        for entry in directory.iterdir():
            if not entry.is_dir():
                continue
            
            skill_name = entry.name
            skill_def_path = entry / skill_def_file
            
            if skill_def_path.exists():
                skill_info = self._parse_skill_definition(skill_def_path, entry, skill_name, depth)
                if skill_info and skill_name not in self._discovered:
                    self._discovered[skill_name] = skill_info
            
            self._discover_in_directory(entry, depth + 1)
    
    def _parse_skill_definition(
        self,
        def_path: Path,
        skill_dir: Path,
        skill_name: str,
        depth: int,
    ) -> Optional[DiscoveredSkill]:
        """
        解析技能定义文件 / Parse skill definition file
        
        Args:
            def_path: 定义文件路径 / Definition file path
            skill_dir: 技能目录 / Skill directory
            skill_name: 技能名称 / Skill name
            depth: 嵌套深度 / Depth
            
        Returns:
            发现的技能对象 / Discovered skill object, or None
        """
        try:
            content = def_path.read_text(encoding="utf-8")
        except OSError:
            return None
        
        description = self._extract_description(content)
        version = self._extract_version(content)
        
        config = self._scan_skill_config(skill_dir)
        
        return DiscoveredSkill(
            name=skill_name,
            path=str(skill_dir),
            source_dir=str(skill_dir.parent),
            definition_file=str(def_path),
            description=description,
            version=version,
            nested_depth=depth,
            config=config,
        )
    
    def _extract_description(self, content: str) -> str:
        """
        从 SKILL.md 提取描述 / Extract description from SKILL.md
        
        Args:
            content: 文件内容 / File content
            
        Returns:
            描述文本 / Description text
        """
        lines = content.strip().split("\n")
        for line in lines[:10]:
            line = line.strip()
            if line.startswith("# ") or line.startswith("#"):
                return line.lstrip("#").strip()
            if line and not line.startswith("---"):
                return line[:120]
        return ""
    
    def _extract_version(self, content: str) -> str:
        """
        从 SKILL.md 提取版本 / Extract version from SKILL.md
        
        Args:
            content: 文件内容 / File content
            
        Returns:
            版本号 / Version string
        """
        import re
        version_match = re.search(r'version[:\s]+([\d.]+)', content, re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        return ""
    
    def _scan_skill_config(self, skill_dir: Path) -> Dict[str, Any]:
        """
        扫描技能目录中的配置文件 / Scan skill directory for config files
        
        Args:
            skill_dir: 技能目录 / Skill directory
            
        Returns:
            配置字典 / Config dict
        """
        config: Dict[str, Any] = {
            "files": [],
            "has_python": False,
            "has_javascript": False,
            "has_yaml": False,
        }
        
        try:
            for entry in skill_dir.iterdir():
                name = entry.name.lower()
                config["files"].append(entry.name)
                
                if entry.suffix == ".py":
                    config["has_python"] = True
                elif entry.suffix in (".js", ".ts"):
                    config["has_javascript"] = True
                elif entry.suffix in (".yaml", ".yml"):
                    config["has_yaml"] = True
        except OSError:
            pass
        
        return config
    
    def get_discovered_skills(self) -> List[Dict[str, Any]]:
        """
        获取已发现的技能列表 / Get discovered skills list
        
        Returns:
            技能字典列表 / List of skill dicts
        """
        return [
            {
                "name": s.name,
                "path": s.path,
                "source_dir": s.source_dir,
                "description": s.description,
                "version": s.version,
                "nested_depth": s.nested_depth,
                "skill_type": s.skill_type,
            }
            for s in self._discovered.values()
        ]
    
    def register_discovered_skills(self, registry) -> int:
        """
        将发现的技能注册到注册中心 / Register discovered skills to registry
        
        Args:
            registry: 技能注册中心 / Skills registry instance
            
        Returns:
            注册的技能数量 / Number of registered skills
        """
        registered = 0
        
        for skill in self._discovered.values():
            try:
                if hasattr(registry, 'register_skill'):
                    registry.register_skill(
                        name=skill.name,
                        path=skill.path,
                        description=skill.description,
                    )
                elif hasattr(registry, 'load_skill'):
                    registry.load_skill(skill.path)
                
                registered += 1
            except Exception:
                continue
        
        return registered
    
    def get_skill_count(self) -> int:
        """获取发现的技能数量 / Get discovered skill count"""
        return len(self._discovered)
