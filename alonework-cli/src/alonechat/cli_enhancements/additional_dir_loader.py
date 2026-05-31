"""
附加目录加载器 / Additional Directory Loader

支持从 --add-dir 附加目录加载技能/插件/配置 / Supports loading skills/plugins/configs from --add-dir directories

版本 / Versions:
- 从 --add-dir 加载技能/插件 / Load skills/plugins from --add-dir: 2.1.45
- 从 --add-dir 加载 CLAUDE.md / Load CLAUDE.md from --add-dir: 2.1.20
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field

from alonechat.configs import load_yaml_config


@dataclass
class LoadedResource:
    """已加载的资源 / Loaded Resource"""
    name: str
    source_dir: str
    resource_type: str
    content: Any = None
    config: Dict[str, Any] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)


class AdditionalDirLoader:
    """
    附加目录加载器 / Additional Directory Loader
    
    从附加目录加载各类资源 / Load various resources from additional directories
    
    可加载的资源类型 / Loadable resource types:
    - skills: 技能文件 / Skill files
    - plugins: 插件 / Plugins
    - commands: 自定义命令 / Custom commands
    - models: 模型配置 / Model configs
    - config: 通用配置 / General config
    
    用法 / Usage:
        loader = AdditionalDirLoader()
        resources = loader.load_all(["/path/to/dir1", "/path/to/dir2"])
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化附加目录加载器 / Initialize additional directory loader
        
        Args:
            config: 附加目录配置字典 / Additional directory config dict
        """
        if config is None:
            config = load_yaml_config("cli_enhancements.yaml").get("additional_dirs", {})
        self._config = config
        self._loaded_resources: Dict[str, LoadedResource] = {}
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取配置 / Get configuration"""
        return self._config
    
    def load_all(self, directories: List[Path]) -> Dict[str, Any]:
        """
        从所有附加目录加载资源 / Load resources from all additional directories
        
        Args:
            directories: 附加目录列表 / List of additional directories
            
        Returns:
            按类型分类的加载结果字典 / Dict of loaded results by type
        """
        self._loaded_resources.clear()
        
        result: Dict[str, Any] = {
            "skills": [],
            "plugins": [],
            "commands": [],
            "models": [],
            "configs": {},
            "all_resources": [],
        }
        
        for directory in directories:
            if not directory.exists() or not directory.is_dir():
                continue
            
            dir_resources = self._load_directory(directory)
            
            for resource in dir_resources:
                key = f"{resource.resource_type}:{resource.name}"
                if key not in self._loaded_resources:
                    self._loaded_resources[key] = resource
                    
                    resource_list = result.get(resource.resource_type, [])
                    if isinstance(resource_list, list):
                        resource_list.append({
                            "name": resource.name,
                            "source_dir": resource.source_dir,
                            "content": resource.content,
                            "config": resource.config,
                        })
            
            enabled_plugins = self._load_enabled_plugins(directory)
            if enabled_plugins:
                result["plugins"].extend(enabled_plugins)
            
            dir_configs = self._load_directory_configs(directory)
            result["configs"].update(dir_configs)
        
        result["all_resources"] = list(self._loaded_resources.values())
        return result
    
    def _load_directory(self, directory: Path) -> List[LoadedResource]:
        """
        加载单个目录的所有资源 / Load all resources from a single directory
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            已加载资源列表 / List of loaded resources
        """
        resources: List[LoadedResource] = []
        resource_types_map = self._get_resource_type_mapping()
        
        for entry in directory.iterdir():
            if not entry.is_dir() and not entry.is_file():
                continue
            
            name = entry.stem if entry.is_file() else entry.name
            
            resource_type = self._detect_resource_type(entry, resource_types_map)
            if resource_type:
                resource = self._load_resource(entry, name, resource_type)
                if resource:
                    resources.append(resource)
        
        return resources
    
    def _get_resource_type_mapping(self) -> Dict[str, List[str]]:
        """
        获取资源类型到目录/文件名的映射 / Get resource type to directory/filename mapping
        
        Returns:
            类型映射字典 / Type mapping dict
        """
        return {
            "skills": ["skills", "skills.d", "plugins", "extensions"],
            "plugins": ["plugins", "plugins.d", "enabledPlugins.yaml", "enabledPlugins.yml"],
            "commands": ["commands", "commands.d"],
            "models": ["models", "models.d", "model_configs"],
            "config": [".alonechatrc", ".alonechatrc.yaml", "config.yaml", "config.yml"],
        }
    
    def _detect_resource_type(self, entry: Path, type_map: Dict[str, List[str]]) -> Optional[str]:
        """
        检测资源类型 / Detect resource type
        
        Args:
            entry: 文件系统条目 / Filesystem entry
            type_map: 类型映射 / Type mapping
            
        Returns:
            资源类型 / Resource type, or None
        """
        entry_lower = entry.name.lower()
        is_dir = entry.is_dir()
        
        for resource_type, patterns in type_map.items():
            for pattern in patterns:
                if is_dir and entry_lower == pattern:
                    return resource_type
                if not is_dir and fnmatch_match(entry_lower, pattern):
                    return resource_type
        
        return None
    
    def _load_resource(self, entry: Path, name: str, resource_type: str) -> Optional[LoadedResource]:
        """
        加载单个资源 / Load single resource
        
        Args:
            entry: 文件系统条目 / Filesystem entry
            name: 资源名称 / Resource name
            resource_type: 资源类型 / Resource type
            
        Returns:
            已加载资源 / Loaded resource, or None
        """
        resource = LoadedResource(
            name=name,
            source_dir=str(entry.parent),
            resource_type=resource_type,
        )
        
        if entry.is_dir():
            resource.files = self._scan_directory(entry)
            resource.config = self._load_dir_config(entry)
        elif entry.is_file():
            resource.files = [entry.name]
            resource.content = self._load_file_content(entry)
        
        return resource
    
    def _scan_directory(self, directory: Path) -> List[str]:
        """
        扫描目录内容 / Scan directory contents
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            文件列表 / List of filenames
        """
        files = []
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    files.append(entry.name)
                elif entry.is_dir():
                    files.append(f"{entry.name}/")
        except OSError:
            pass
        return files
    
    def _load_dir_config(self, directory: Path) -> Dict[str, Any]:
        """
        加载目录内的配置文件 / Load config files within directory
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            配置字典 / Config dict
        """
        config: Dict[str, Any] = {}
        
        for config_name in [".alonechatrc", ".alonechatrc.yaml", "config.yaml", "config.yml"]:
            config_path = directory / config_name
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        loaded = yaml.safe_load(f) or {}
                        config.update(loaded)
                except (yaml.YAMLError, OSError):
                    pass
        
        return config
    
    def _load_file_content(self, file_path: Path) -> Any:
        """
        加载文件内容 / Load file content
        
        Args:
            file_path: 文件路径 / File path
            
        Returns:
            文件内容 / File content
        """
        ext = file_path.suffix.lower()
        
        try:
            if ext in (".yaml", ".yml"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            elif ext in (".json",):
                import json
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            elif ext in (".md", ".txt", ".toml"):
                return file_path.read_text(encoding="utf-8")
            else:
                return file_path.read_text(encoding="utf-8")
        except Exception:
            return None
    
    def _load_enabled_plugins(self, directory: Path) -> List[Dict[str, Any]]:
        """
        加载 enabledPlugins 配置 / Load enabledPlugins config
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            启用的插件列表 / List of enabled plugins
        """
        config_patterns = self._config.get("config_patterns", [
            "enabledPlugins.yaml",
            "enabledPlugins.yml",
        ])
        
        for pattern in config_patterns:
            config_path = directory / pattern
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    
                    plugins = data.get("plugins", data.get("enabled_plugins", []))
                    if isinstance(plugins, list):
                        return [{"name": p} if isinstance(p, str) else p for p in plugins]
                except (yaml.YAMLError, OSError):
                    continue
        
        return []
    
    def _load_directory_configs(self, directory: Path) -> Dict[str, Any]:
        """
        加载目录级别的配置文件 / Load directory-level config files
        
        Args:
            directory: 目录路径 / Directory path
            
        Returns:
            配置字典 / Config dict
        """
        configs: Dict[str, Any] = {}
        
        config_patterns = self._config.get("config_patterns", [
            "enabledPlugins.yaml", "enabledPlugins.yml",
            ".alonechatrc", ".alonechatrc.yaml",
        ])
        
        for pattern in config_patterns:
            config_path = directory / pattern
            if config_path.exists() and config_path.suffix in (".yaml", ".yml"):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        configs[config_path.stem] = yaml.safe_load(f) or {}
                except (yaml.YAMLError, OSError):
                    pass
        
        return configs
    
    def get_enabled_plugins(self) -> List[str]:
        """
        获取所有已启用插件名列表 / Get all enabled plugin names
        
        Returns:
            插件名列表 / List of plugin names
        """
        plugins = set()
        
        for key, resource in self._loaded_resources.items():
            if resource.resource_type == "plugins":
                if isinstance(resource.content, dict):
                    plugin_list = resource.content.get("plugins", resource.content.get("enabled_plugins", []))
                    if isinstance(plugin_list, list):
                        for p in plugin_list:
                            if isinstance(p, str):
                                plugins.add(p)
                            elif isinstance(p, dict):
                                plugins.add(p.get("name", ""))
        
        return list(plugins)
    
    @staticmethod
    def get_additional_dirs_from_env() -> List[str]:
        """
        从环境变量获取附加目录列表 / Get additional directories from env var
        
        Returns:
            目录路径列表 / List of directory paths
        """
        env_var = "ALONECHAT_ADDITIONAL_DIRECTORIES"
        env_value = os.environ.get(env_var, "")
        
        if not env_value:
            return []
        
        dirs = [d.strip() for d in env_value.split(os.pathsep) if d.strip()]
        return [d for d in dirs if Path(d).exists()]


def fnmatch_match(name: str, pattern: str) -> bool:
    """
    fnmatch 模式匹配 / fnmatch pattern matching
    
    Args:
        name: 文件名 / Filename
        pattern: 匹配模式 / Match pattern
        
    Returns:
        是否匹配 / Whether matches
    """
    import fnmatch
    return fnmatch.fnmatch(name, pattern)
