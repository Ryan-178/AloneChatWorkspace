"""
技能热重载管理器 / Skills Hot Reload Manager

自动检测技能文件变化并重新加载 / Auto detect skill file changes and reload

功能 / Features:
- 文件监视自动重载 / File watch auto reload
- 无需重启服务 / No service restart needed
- 变更事件回调 / Change event callbacks

版本 / Version: 2.1.0
"""

import asyncio
import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Set, Callable, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class SkillFileInfo:
    """技能文件信息 / Skill file info"""
    path: Path
    last_modified: float = 0.0
    file_hash: str = ""
    last_checked: datetime = field(default_factory=datetime.now)


@dataclass
class ReloadEvent:
    """重载事件 / Reload event"""
    skill_name: str
    event_type: str  # "created", "modified", "deleted"
    timestamp: datetime = field(default_factory=datetime.now)
    old_hash: str = ""
    new_hash: str = ""
    success: bool = False
    error: Optional[str] = None


class SkillsHotReloader:
    """
    技能热重载管理器 / Skills Hot Reload Manager
    
    自动监视技能目录，检测文件变化并触发重载 / Auto watch skills directory, detect changes and trigger reload
    
    使用示例 / Usage Example:
        reloader = SkillsHotReloader(skills_registry, skills_dir)
        reloader.on_reload(callback_function)
        reloader.start()  # 开始监视
        # ... 运行中 ...
        reloader.stop()   # 停止监视
    """
    
    def __init__(
        self,
        registry: Any,
        skills_dir: Optional[Path] = None,
        poll_interval: float = 1.0,
    ):
        """
        初始化热重载器 / Initialize hot reloader
        
        Args:
            registry: 技能注册表 / Skills registry
            skills_dir: 技能目录 / Skills directory
            poll_interval: 轮询间隔（秒）/ Poll interval (seconds)
        """
        self.registry = registry
        self.skills_dir = skills_dir or Path.home() / ".skills"
        self.poll_interval = poll_interval
        
        self._file_cache: Dict[str, SkillFileInfo] = {}
        self._callbacks: List[Callable[[ReloadEvent], None]] = []
        self._running = False
        self._watch_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._reload_history: List[ReloadEvent] = []
        
        self._init_file_cache()
    
    def _init_file_cache(self) -> None:
        """初始化文件缓存 / Initialize file cache"""
        if not self.skills_dir.exists():
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                self._scan_skill_dir(skill_dir)
    
    def _scan_skill_dir(self, skill_dir: Path) -> None:
        """扫描技能目录 / Scan skill directory"""
        for file_path in skill_dir.rglob("*.py"):
            self._cache_file(file_path)
        for file_path in skill_dir.rglob("*.yaml"):
            self._cache_file(file_path)
        for file_path in skill_dir.rglob("*.yml"):
            self._cache_file(file_path)
    
    def _cache_file(self, file_path: Path) -> None:
        """缓存文件信息 / Cache file info"""
        try:
            stat = file_path.stat()
            file_hash = self._compute_hash(file_path)
            
            self._file_cache[str(file_path)] = SkillFileInfo(
                path=file_path,
                last_modified=stat.st_mtime,
                file_hash=file_hash,
            )
        except Exception:
            pass
    
    def _compute_hash(self, file_path: Path) -> str:
        """计算文件哈希 / Compute file hash"""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def on_reload(self, callback: Callable[[ReloadEvent], None]) -> None:
        """
        注册重载回调 / Register reload callback
        
        Args:
            callback: 回调函数，接收ReloadEvent参数 / Callback function receiving ReloadEvent
        """
        self._callbacks.append(callback)
    
    def off_reload(self, callback: Callable[[ReloadEvent], None]) -> None:
        """注销重载回调 / Unregister reload callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, event: ReloadEvent) -> None:
        """通知所有回调 / Notify all callbacks"""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass
    
    def start(self) -> None:
        """开始监视 / Start watching"""
        if self._running:
            return
        
        self._running = True
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
    
    def stop(self) -> None:
        """停止监视 / Stop watching"""
        self._running = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)
            self._watch_thread = None
    
    def _watch_loop(self) -> None:
        """监视循环 / Watch loop"""
        while self._running:
            try:
                self._check_changes()
            except Exception:
                pass
            
            import time
            time.sleep(self.poll_interval)
    
    def _check_changes(self) -> None:
        """检查文件变化 / Check file changes"""
        if not self.skills_dir.exists():
            return
        
        current_files: Set[str] = set()
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                for file_path in skill_dir.rglob("*.py"):
                    current_files.add(str(file_path))
                    self._check_file(file_path)
                for file_path in skill_dir.rglob("*.yaml"):
                    current_files.add(str(file_path))
                    self._check_file(file_path)
                for file_path in skill_dir.rglob("*.yml"):
                    current_files.add(str(file_path))
                    self._check_file(file_path)
        
        deleted_files = set(self._file_cache.keys()) - current_files
        for deleted_path in deleted_files:
            self._handle_deleted(Path(deleted_path))
    
    def _check_file(self, file_path: Path) -> None:
        """检查单个文件 / Check single file"""
        path_str = str(file_path)
        
        try:
            stat = file_path.stat()
            current_hash = self._compute_hash(file_path)
            
            if path_str not in self._file_cache:
                self._handle_created(file_path, current_hash)
            else:
                cached = self._file_cache[path_str]
                if current_hash != cached.file_hash:
                    self._handle_modified(file_path, cached.file_hash, current_hash)
                    
        except FileNotFoundError:
            if path_str in self._file_cache:
                self._handle_deleted(file_path)
        except Exception:
            pass
    
    def _handle_created(self, file_path: Path, file_hash: str) -> None:
        """处理文件创建 / Handle file created"""
        skill_name = self._get_skill_name(file_path)
        
        self._cache_file(file_path)
        
        event = ReloadEvent(
            skill_name=skill_name,
            event_type="created",
            new_hash=file_hash,
            success=True,
        )
        
        self._reload_history.append(event)
        self._notify_callbacks(event)
    
    def _handle_modified(self, file_path: Path, old_hash: str, new_hash: str) -> None:
        """处理文件修改 / Handle file modified"""
        skill_name = self._get_skill_name(file_path)
        
        success, error = self._reload_skill(file_path)
        
        self._cache_file(file_path)
        
        event = ReloadEvent(
            skill_name=skill_name,
            event_type="modified",
            old_hash=old_hash,
            new_hash=new_hash,
            success=success,
            error=error,
        )
        
        self._reload_history.append(event)
        self._notify_callbacks(event)
    
    def _handle_deleted(self, file_path: Path) -> None:
        """处理文件删除 / Handle file deleted"""
        path_str = str(file_path)
        skill_name = self._get_skill_name(file_path)
        
        if path_str in self._file_cache:
            old_hash = self._file_cache[path_str].file_hash
            del self._file_cache[path_str]
            
            event = ReloadEvent(
                skill_name=skill_name,
                event_type="deleted",
                old_hash=old_hash,
                success=True,
            )
            
            self._reload_history.append(event)
            self._notify_callbacks(event)
    
    def _get_skill_name(self, file_path: Path) -> str:
        """获取技能名称 / Get skill name"""
        try:
            relative = file_path.relative_to(self.skills_dir)
            return relative.parts[0] if relative.parts else file_path.parent.name
        except ValueError:
            return file_path.parent.name
    
    def _reload_skill(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        重新加载技能 / Reload skill
        
        Returns:
            (success, error_message)
        """
        if file_path.suffix == ".py":
            return self._reload_python_module(file_path)
        elif file_path.suffix in (".yaml", ".yml"):
            return self._reload_yaml_config(file_path)
        return (True, None)
    
    def _reload_python_module(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """重新加载Python模块 / Reload Python module"""
        try:
            module_name = f"skill_{file_path.stem}"
            
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                if hasattr(self.registry, 'reload_skill'):
                    self.registry.reload_skill(file_path.parent.name)
                
                return (True, None)
            
            return (False, "无法创建模块规范 / Cannot create module spec")
            
        except Exception as e:
            return (False, str(e))
    
    def _reload_yaml_config(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """重新加载YAML配置 / Reload YAML config"""
        try:
            if hasattr(self.registry, 'reload_config'):
                self.registry.reload_config()
            
            return (True, None)
        except Exception as e:
            return (False, str(e))
    
    def get_reload_history(self, limit: int = 20) -> List[ReloadEvent]:
        """获取重载历史 / Get reload history"""
        return self._reload_history[-limit:]
    
    def force_reload(self, skill_name: str) -> ReloadEvent:
        """
        强制重载技能 / Force reload skill
        
        Args:
            skill_name: 技能名称 / Skill name
        
        Returns:
            重载事件 / Reload event
        """
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            return ReloadEvent(
                skill_name=skill_name,
                event_type="error",
                success=False,
                error="技能目录不存在 / Skill directory not found",
            )
        
        success = True
        error = None
        
        for file_path in skill_dir.rglob("*.py"):
            s, e = self._reload_python_module(file_path)
            if not s:
                success = False
                error = e
        
        for file_path in skill_dir.rglob("*.yaml"):
            s, e = self._reload_yaml_config(file_path)
            if not s:
                success = False
                error = e
        
        event = ReloadEvent(
            skill_name=skill_name,
            event_type="force_reload",
            success=success,
            error=error,
        )
        
        self._reload_history.append(event)
        self._notify_callbacks(event)
        
        return event
    
    @property
    def is_running(self) -> bool:
        """是否正在监视 / Is watching"""
        return self._running
    
    @property
    def watched_files_count(self) -> int:
        """监视的文件数量 / Watched files count"""
        return len(self._file_cache)
