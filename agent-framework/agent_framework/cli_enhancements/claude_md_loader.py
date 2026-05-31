"""
CLAUDE.md 加载器 / CLAUDE.md Loader

支持加载 CLAUDE.md 文件及其 @import 语法 / Supports loading CLAUDE.md files with @import syntax

版本 / Versions:
- 从 --add-dir 加载 CLAUDE.md / Load CLAUDE.md from --add-dir: 2.1.20
- CLAUDE.md @import 支持 / CLAUDE.md @import support: 0.2.107
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field

from agent_framework.configs import load_yaml_config


@dataclass
class ClaudeMdImport:
    """CLAUDE.md 导入引用 / CLAUDE.md Import Reference"""
    path: str
    resolved_path: Optional[str] = None
    content: str = ""
    resolved: bool = False
    error: Optional[str] = None


@dataclass
class ClaudeMdConfig:
    """CLAUDE.md 配置 / CLAUDE.md Configuration"""
    filename: str = "CLAUDE.md"
    additional_dirs_enabled: bool = True
    import_extensions: List[str] = field(default_factory=lambda: [".md", ".txt", ".yaml", ".yml", ".json", ".toml"])


class ClaudeMdLoader:
    """
    CLAUDE.md 加载器 / CLAUDE.md Loader
    
    支持:
    - 从项目目录和附加目录加载 CLAUDE.md / Load from project dir and additional dirs
    - @import 语法引用其他文件 / @import syntax for referencing other files
    - 递归解析导入链 / Recursive import chain resolution
    
    用法 / Usage:
        loader = ClaudeMdLoader()
        content = loader.load_and_resolve("/path/to/project")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化加载器 / Initialize loader
        
        Args:
            config: CLAUDE.md 配置字典 / CLAUDE.md config dict
        """
        if config is None:
            config = load_yaml_config("cli_enhancements.yaml").get("claude_md", {})
        self._config = config
        self._resolved_imports: Set[str] = set()
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    def load_and_resolve(
        self,
        project_dir: str,
        additional_dirs: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        加载并解析 CLAUDE.md（包括 @import）/ Load and resolve CLAUDE.md (including @import)
        
        Args:
            project_dir: 项目目录 / Project directory
            additional_dirs: 附加目录列表 / Additional directories list
            
        Returns:
            解析后的内容 / Resolved content, or None if not found
        """
        self._resolved_imports.clear()
        
        content = self._load_raw(project_dir)
        
        dirs_to_search = [project_dir]
        if additional_dirs:
            dirs_to_search.extend(additional_dirs)
        
        if not content and len(dirs_to_search) > 1:
            for extra_dir in additional_dirs or []:
                content = self._load_raw(extra_dir)
                if content:
                    break
        
        if content is None:
            return None
        
        resolved = self._resolve_imports(content, project_dir, dirs_to_search)
        return resolved
    
    def _load_raw(self, directory: str) -> Optional[str]:
        """
        从目录加载原始 CLAUDE.md / Load raw CLAUDE.md from directory
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            文件内容 / File content, or None if not found
        """
        filename = self._config.get("filename", "CLAUDE.md")
        md_path = Path(directory) / filename
        
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as f:
                return f.read()
        
        return None
    
    def _resolve_imports(
        self,
        content: str,
        base_dir: str,
        search_dirs: List[str],
        depth: int = 0,
    ) -> str:
        """
        解析 @import 语法 / Resolve @import syntax
        
        @path/to/file.md 语法用于导入其他文件 / @path/to/file.md syntax for importing other files
        
        Args:
            content: 原始内容 / Raw content
            base_dir: 基础目录 / Base directory
            search_dirs: 搜索目录列表 / Search directories
            depth: 递归深度 / Recursion depth
            
        Returns:
            解析后的内容 / Resolved content
        """
        if depth > 10:
            return content
        
        import_pattern = re.compile(r'@([^\s@]+\.(?:md|txt|yaml|yml|json|toml))')
        
        def replace_import(match: re.Match) -> str:
            import_path = match.group(1)
            
            import_obj = self._resolve_single_import(import_path, base_dir, search_dirs)
            
            if import_obj.resolved and import_obj.content:
                resolved_content = self._resolve_imports(
                    import_obj.content,
                    os.path.dirname(import_obj.resolved_path) if import_obj.resolved_path else base_dir,
                    search_dirs,
                    depth + 1,
                )
                
                header = f"\n<!-- Imported from: {import_path} -->\n"
                footer = f"\n<!-- End of: {import_path} -->\n"
                return f"{header}{resolved_content}{footer}"
            
            if import_obj.error:
                return f"\n<!-- Import failed: {import_path} - {import_obj.error} -->\n"
            
            return match.group(0)
        
        return import_pattern.sub(replace_import, content)
    
    def _resolve_single_import(
        self,
        import_path: str,
        base_dir: str,
        search_dirs: List[str],
    ) -> ClaudeMdImport:
        """
        解析单个导入引用 / Resolve single import reference
        
        Args:
            import_path: 导入路径 / Import path
            base_dir: 基础目录 / Base directory
            search_dirs: 搜索目录 / Search directories
            
        Returns:
            导入结果 / Import result
        """
        import_obj = ClaudeMdImport(path=import_path)
        
        import_key = f"{base_dir}:{import_path}"
        if import_key in self._resolved_imports:
            import_obj.error = "Circular reference detected"
            return import_obj
        self._resolved_imports.add(import_key)
        
        abs_path = Path(import_path)
        if abs_path.is_absolute():
            import_obj.error = "Absolute paths are not allowed for security reasons"
            return import_obj
        
        import_extensions = self._config.get("import_extensions", [".md", ".txt", ".yaml", ".yml", ".json", ".toml"])
        has_extension = any(import_path.endswith(ext) for ext in import_extensions)
        
        for search_dir in search_dirs:
            candidates = []
            
            candidates.append(Path(search_dir) / import_path)
            
            if not has_extension:
                for ext in import_extensions:
                    candidates.append(Path(search_dir) / f"{import_path}{ext}")
            
            for candidate in candidates:
                if candidate.exists():
                    import_obj.resolved_path = str(candidate)
                    import_obj.resolved = True
                    with open(candidate, "r", encoding="utf-8") as f:
                        import_obj.content = f.read()
                    return import_obj
        
        import_obj.error = f"File not found in search paths: {import_path}"
        return import_obj
    
    def load_with_metadata(
        self,
        project_dir: str,
        additional_dirs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        加载 CLAUDE.md 并返回元数据 / Load CLAUDE.md with metadata
        
        Args:
            project_dir: 项目目录 / Project directory
            additional_dirs: 附加目录 / Additional directories
            
        Returns:
            包含内容和元数据的字典 / Dict with content and metadata
        """
        content = self.load_and_resolve(project_dir, additional_dirs)
        
        return {
            "content": content,
            "loaded": content is not None,
            "resolved_imports": list(self._resolved_imports),
            "source_dir": project_dir,
            "additional_dirs": additional_dirs or [],
        }
    
    @staticmethod
    def check_additional_dirs_env() -> bool:
        """
        检查环境变量是否启用附加目录 CLAUDE.md 加载 / Check env var for add-dir CLAUDE.md loading
        
        版本 / Version: 2.1.20
        需要 CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 / Requires CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1
        
        Returns:
            是否启用 / Whether enabled
        """
        env_var = "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD"
        return os.environ.get(env_var, "0") == "1"
    
    @staticmethod
    def parse_frontmatter(content: str) -> Dict[str, Any]:
        """
        解析 CLAUDE.md 的 YAML frontmatter / Parse CLAUDE.md YAML frontmatter
        
        Args:
            content: 文件内容 / File content
            
        Returns:
            frontmatter 字典 / Frontmatter dict
        """
        import yaml
        
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)
        
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        
        return {}
    
    @staticmethod
    def extract_imports(content: str) -> List[str]:
        """
        提取内容中的所有 @import 路径 / Extract all @import paths from content
        
        Args:
            content: 文件内容 / File content
            
        Returns:
            导入路径列表 / List of import paths
        """
        import_pattern = re.compile(r'@([^\s@]+\.(?:md|txt|yaml|yml|json|toml))')
        return import_pattern.findall(content)
