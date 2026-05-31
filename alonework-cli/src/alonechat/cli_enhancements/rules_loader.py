"""
条件性规则加载器 / Conditional Rules Loader

从 .claude/rules/ 目录加载条件性规则文件 / Load conditional rule files from .claude/rules/ directory

版本 / Version: 2.0.64
"""

import os
import fnmatch
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field

from alonechat.configs import load_yaml_config


@dataclass
class RuleFile:
    """规则文件 / Rule File"""
    name: str
    path: str
    content: str
    condition: str = ""
    loaded: bool = False
    priority: int = 0
    description: str = ""


class RulesLoader:
    """
    条件性规则加载器 / Conditional Rules Loader
    
    从 .claude/rules/ 目录加载规则文件，支持条件性加载 / Load rules from .claude/rules/ with conditional support
    
    文件命名规则 / File naming convention:
    - always.md: 始终加载 / Always loaded
    - python.md: 仅在检测到 Python 项目时加载 / Loaded when Python project detected
    - react.md: 仅在检测到 React 项目时加载 / Loaded when React project detected
    
    用法 / Usage:
        loader = RulesLoader()
        rules = loader.load_all("/path/to/project")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化规则加载器 / Initialize rules loader
        
        Args:
            config: 规则配置字典 / Rules config dict
        """
        if config is None:
            config = load_yaml_config("cli_enhancements.yaml").get("rules", {})
        self._config = config
        self._loaded_rules: Set[str] = set()
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    def load_all(self, project_dir: str) -> List[Dict[str, Any]]:
        """
        加载所有符合条件的规则 / Load all matching rules
        
        Args:
            project_dir: 项目目录 / Project directory
            
        Returns:
            规则字典列表 / List of rule dicts
        """
        rules_dir = self._find_rules_dir(project_dir)
        if not rules_dir:
            return []
        
        rules = self._scan_rules_dir(rules_dir)
        project_files = self._scan_project_files(project_dir)
        
        loaded_rules = []
        for rule in rules:
            if self._check_condition(rule, project_dir, project_files):
                rule.loaded = True
                loaded_rules.append({
                    "name": rule.name,
                    "path": rule.path,
                    "content": rule.content,
                    "condition": rule.condition,
                    "priority": rule.priority,
                    "description": rule.description,
                })
                self._loaded_rules.add(rule.name)
        
        loaded_rules.sort(key=lambda r: r.get("priority", 0), reverse=True)
        return loaded_rules
    
    def _find_rules_dir(self, project_dir: str) -> Optional[Path]:
        """
        查找 .claude/rules/ 目录 / Find .claude/rules/ directory
        
        Args:
            project_dir: 项目目录 / Project directory
            
        Returns:
            规则目录路径 / Rules directory path, or None
        """
        rules_dir_name = self._config.get("rules_dir", ".claude/rules")
        candidates = [
            Path(project_dir) / rules_dir_name,
            Path(project_dir) / ".claude" / "rules",
            Path(project_dir) / ".alonechat" / "rules",
        ]
        
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        
        return None
    
    def _scan_rules_dir(self, rules_dir: Path) -> List[RuleFile]:
        """
        扫描规则目录 / Scan rules directory
        
        Args:
            rules_dir: 规则目录路径 / Rules directory path
            
        Returns:
            规则文件列表 / List of rule files
        """
        rules = []
        
        if not rules_dir.exists():
            return rules
        
        for file_path in sorted(rules_dir.iterdir()):
            if file_path.is_file() and file_path.suffix in (".md", ".txt", ".yaml", ".yml"):
                name = file_path.stem
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                
                description = self._extract_description(content)
                
                rule = RuleFile(
                    name=name,
                    path=str(file_path),
                    content=content,
                    condition=name,
                    description=description,
                )
                
                if name == "always":
                    rule.priority = 100
                else:
                    rule.priority = 50
                
                rules.append(rule)
        
        return rules
    
    def _extract_description(self, content: str) -> str:
        """
        从规则内容提取描述 / Extract description from rule content
        
        Args:
            content: 规则内容 / Rule content
            
        Returns:
            描述文本 / Description text
        """
        lines = content.strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            if line.startswith("#") and not line.startswith("##"):
                return line.lstrip("#").strip()
        return ""
    
    def _check_condition(
        self,
        rule: RuleFile,
        project_dir: str,
        project_files: Set[str],
    ) -> bool:
        """
        检查规则条件是否满足 / Check if rule condition is met
        
        Args:
            rule: 规则文件 / Rule file
            project_dir: 项目目录 / Project directory
            project_files: 项目文件集合 / Project files set
            
        Returns:
            条件是否满足 / Whether condition is met
        """
        condition = rule.condition.lower()
        
        if condition == "always":
            return True
        
        if condition in ("python", "py"):
            return self._has_files(project_files, ["*.py", "setup.py", "pyproject.toml", "requirements.txt"])
        
        if condition in ("javascript", "js"):
            return self._has_files(project_files, ["*.js", "package.json", "webpack.config.js"])
        
        if condition in ("typescript", "ts"):
            return self._has_files(project_files, ["*.ts", "*.tsx", "tsconfig.json"])
        
        if condition in ("react", "reactjs", "react.js"):
            return self._has_files(project_files, ["*.jsx", "*.tsx", "react", "next.config.js"])
        
        if condition == "rust":
            return self._has_files(project_files, ["*.rs", "Cargo.toml"])
        
        if condition == "go":
            return self._has_files(project_files, ["*.go", "go.mod"])
        
        if condition in ("java", "kotlin"):
            return self._has_files(project_files, ["*.java", "*.kt", "pom.xml", "build.gradle"])
        
        if condition in ("docker", "container"):
            return self._has_files(project_files, ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Containerfile"])
        
        if condition in ("test", "testing"):
            return self._has_files(project_files, ["*test*", "*spec*", "test_*", "*_test"])
        
        if condition in ("api", "rest", "graphql"):
            return self._has_files(project_files, ["*api*", "*graphql*", "openapi.yaml", "swagger"])
        
        if condition == "frontend":
            has_html_css = self._has_files(project_files, ["*.html", "*.css", "*.scss", "*.less"])
            has_framework = self._has_files(project_files, ["package.json", "vue.config.js", "next.config.js", "nuxt.config.js", "svelte.config.js"])
            return has_html_css or has_framework
        
        if condition == "backend":
            return self._has_files(project_files, ["server.py", "app.py", "main.py", "index.js", "server.js", "api/", "routes/"])
        
        is_present = self._has_files(project_files, [f"*{condition}*", f"*.{condition}*", condition])
        return is_present
    
    def _has_files(self, project_files: Set[str], patterns: List[str]) -> bool:
        """
        检查项目是否包含匹配模式的文件 / Check if project has files matching patterns
        
        Args:
            project_files: 项目文件集合 / Project files set
            patterns: 匹配模式列表 / List of match patterns
            
        Returns:
            是否有匹配文件 / Whether any file matches
        """
        for f in project_files:
            lower_f = f.lower()
            for pattern in patterns:
                if fnmatch.fnmatch(lower_f, pattern.lower()):
                    return True
                if lower_f == pattern.lower():
                    return True
        return False
    
    def _scan_project_files(self, project_dir: str, max_depth: int = 3) -> Set[str]:
        """
        扫描项目文件列表 / Scan project file list
        
        Args:
            project_dir: 项目目录 / Project directory
            max_depth: 最大扫描深度 / Max scan depth
            
        Returns:
            相对路径集合 / Set of relative paths
        """
        files: Set[str] = set()
        root = Path(project_dir)
        
        if not root.exists():
            return files
        
        for i, entry in enumerate(root.rglob("*")):
            if i > 10000:
                break
            
            try:
                rel_path = entry.relative_to(root)
                
                parts = len(rel_path.parts)
                if parts > max_depth and not entry.is_dir():
                    continue
                
                if entry.is_dir():
                    files.add(str(rel_path) + "/")
                else:
                    files.add(str(rel_path))
                    files.add(entry.name)
            except (ValueError, OSError):
                continue
        
        return files
    
    def get_combined_content(self, rules: List[Dict[str, Any]]) -> str:
        """
        合并所有规则内容 / Combine all rule contents
        
        Args:
            rules: 规则列表 / Rules list
            
        Returns:
            合并后的内容 / Combined content
        """
        parts = ["<!-- Loaded Rules -->"]
        
        for rule in rules:
            header = f"\n## Rule: {rule.get('name', 'unknown')}"
            desc = rule.get('description', '')
            if desc:
                header += f" - {desc}"
            
            parts.append(header)
            parts.append(rule.get('content', ''))
        
        return "\n\n".join(parts)
    
    def list_conditions(self) -> List[str]:
        """
        列出所有支持的条件 / List all supported conditions
        
        Returns:
            条件名称列表 / List of condition names
        """
        return [
            "always",
            "python", "javascript", "typescript",
            "react", "vue", "angular", "svelte",
            "rust", "go", "java", "kotlin",
            "docker", "kubernetes",
            "frontend", "backend", "api", "graphql",
            "test", "documentation",
        ]
