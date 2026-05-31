"""
框架配置桥接层 / Framework Configuration Bridge

桥接 alonechat 与 alonework-cli 的配置系统
Bridges alonechat and alonework-cli configuration systems

对齐 claude-code-claude 的架构模式：
- 集中式状态管理 / Centralized state management
- 多源设置加载 / Multi-source settings loading
- 命令类型系统 / Command type system
- 工具权限上下文 / Tool permission context

版本 / Version: 2.1.80
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional

# ============================================================
# 路径常量 / Path Constants
# ============================================================

PROJECT_DIR = Path.cwd()
ALONECHAT_DIR = PROJECT_DIR / ".alonechat"
CONFIG_DIR = ALONECHAT_DIR
SESSIONS_DIR = ALONECHAT_DIR / "sessions"
MEMORY_DIR = ALONECHAT_DIR / "memory"
SKILLS_DIR = ALONECHAT_DIR / "skills"
COMMANDS_DIR = ALONECHAT_DIR / "commands"
HOOKS_DIR = ALONECHAT_DIR / "hooks"
SHARED_DIR = ALONECHAT_DIR / "shared"
FEEDBACK_DIR = ALONECHAT_DIR / "feedback"
TAGS_DIR = ALONECHAT_DIR / "tags"

# 框架配置源路径 / Framework config source paths
FRAMEWORK_CONFIGS_DIR = Path(__file__).parent / "configs"
USER_CONFIG_FILE = ALONECHAT_DIR / "config.yaml"
PROJECT_CONFIG_FILE = PROJECT_DIR / ".aloneworkrc"
GLOBAL_CONFIG_FILE = Path.home() / ".alonechat" / "config.yaml"


# ============================================================
# 设置源 / Setting Sources (对齐 claude-code-claude 的 SettingSource)
# ============================================================

@dataclass(frozen=True)
class SettingSource:
    """
    设置来源定义 / Setting source definition

    对齐 claude-code-claude 的 SettingSource 类型
    Aligns with claude-code-claude's SettingSource type
    """
    name: str
    priority: int
    path: Optional[Path] = None
    description: str = ""


SETTING_SOURCES = {
    "framework": SettingSource(
        name="framework",
        priority=0,
        path=FRAMEWORK_CONFIGS_DIR,
        description="框架默认配置 / Framework default configs",
    ),
    "project": SettingSource(
        name="project",
        priority=10,
        path=PROJECT_CONFIG_FILE,
        description="项目级配置 / Project-level config",
    ),
    "user": SettingSource(
        name="user",
        priority=20,
        path=USER_CONFIG_FILE,
        description="用户级配置 / User-level config",
    ),
    "global": SettingSource(
        name="global",
        priority=30,
        path=GLOBAL_CONFIG_FILE,
        description="全局配置 / Global config",
    ),
    "env": SettingSource(
        name="env",
        priority=40,
        description="环境变量 / Environment variables",
    ),
    "cli": SettingSource(
        name="cli",
        priority=50,
        description="CLI参数 / CLI arguments",
    ),
}


# ============================================================
# 命令类型 / Command Types (对齐 claude-code-claude)
# ============================================================

class CommandType:
    """
    命令类型枚举 / Command type enumeration

    对齐 claude-code-claude 的三种命令类型：
    - local: 本地执行命令，返回文本结果
    - prompt: 提示命令，展开为发送给模型的文本
    - interactive: 交互式命令，需要用户输入

    Aligns with claude-code-claude's command types:
    - local: Local execution, returns text result
    - prompt: Prompt command, expands to text sent to model
    - interactive: Interactive command, requires user input
    """
    LOCAL = "local"
    PROMPT = "prompt"
    INTERACTIVE = "interactive"


# ============================================================
# 命令基类 / Command Base (对齐 claude-code-claude 的 CommandBase)
# ============================================================

@dataclass
class CommandBase:
    """
    命令基类 / Command base class

    对齐 claude-code-claude 的 CommandBase 类型定义
    Aligns with claude-code-claude's CommandBase type definition
    """
    name: str
    description: str
    type: str = CommandType.LOCAL
    aliases: list[str] = field(default_factory=list)
    category: str = "general"
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    is_hidden: bool = False
    is_enabled: bool = True
    source: str = "builtin"
    version: str = ""
    when_to_use: str = ""
    argument_hint: str = ""
    disable_model_invocation: bool = False
    user_invocable: bool = True
    immediate: bool = False
    is_sensitive: bool = False


@dataclass
class LocalCommand(CommandBase):
    """
    本地执行命令 / Local execution command

    对齐 claude-code-claude 的 LocalCommand 类型
    """
    type: str = CommandType.LOCAL
    supports_non_interactive: bool = True
    handler: Any = None


@dataclass
class PromptCommand(CommandBase):
    """
    提示命令 / Prompt command

    对齐 claude-code-claude 的 PromptCommand 类型
    展开为发送给模型的内容
    """
    type: str = CommandType.PROMPT
    progress_message: str = ""
    content_length: int = 0
    allowed_tools: list[str] = field(default_factory=list)
    model: str = ""
    context: str = "inline"
    effort: str = ""
    paths: list[str] = field(default_factory=list)
    get_prompt_for_command: Any = None


@dataclass
class InteractiveCommand(CommandBase):
    """
    交互式命令 / Interactive command

    对齐 claude-code-claude 的 LocalJSXCommand 类型
    需要用户交互的命令
    """
    type: str = CommandType.INTERACTIVE
    handler: Any = None


# ============================================================
# 工具权限上下文 / Tool Permission Context (对齐 claude-code-claude)
# ============================================================

@dataclass
class ToolPermissionRule:
    """
    工具权限规则 / Tool permission rule

    对齐 claude-code-claude 的工具权限规则
    """
    tool_name: str
    pattern: str = ""
    action: str = "allow"
    source: str = "user"
    reason: str = ""


@dataclass
class ToolPermissionContext:
    """
    工具权限上下文 / Tool permission context

    对齐 claude-code-claude 的 ToolPermissionContext
    """
    rules: list[ToolPermissionRule] = field(default_factory=list)
    mode: str = "default"
    bypass_permissions: bool = False

    def is_tool_allowed(self, tool_name: str) -> Optional[bool]:
        """
        检查工具是否被允许 / Check if tool is allowed

        Returns:
            True: 允许 / Allowed
            False: 拒绝 / Denied
            None: 需要提示 / Needs prompt
        """
        if self.bypass_permissions:
            return True

        for rule in reversed(self.rules):
            if self._match_rule(rule, tool_name):
                return rule.action == "allow"

        return None

    def _match_rule(self, rule: ToolPermissionRule, tool_name: str) -> bool:
        """匹配规则 / Match rule"""
        if rule.pattern:
            if rule.pattern.endswith("*"):
                return tool_name.startswith(rule.pattern[:-1])
            return tool_name == rule.pattern
        return tool_name == rule.tool_name


# ============================================================
# 设置管理器 / Settings Manager (对齐 claude-code-claude)
# ============================================================

class SettingsManager:
    """
    多源设置管理器 / Multi-source settings manager

    对齐 claude-code-claude 的设置系统：
    - 支持多源设置加载（框架/项目/用户/全局/环境变量/CLI）
    - 按优先级合并设置
    - 设置变更检测

    Aligns with claude-code-claude's settings system:
    - Multi-source settings loading (framework/project/user/global/env/cli)
    - Priority-based settings merging
    - Settings change detection
    """

    def __init__(self):
        self._settings: dict[str, Any] = {}
        self._source_values: dict[str, dict[str, Any]] = {}
        self._change_listeners: list = []
        self._load_all_sources()

    def _load_all_sources(self) -> None:
        """加载所有设置源 / Load all setting sources"""
        for source_name in sorted(SETTING_SOURCES, key=lambda k: SETTING_SOURCES[k].priority):
            source = SETTING_SOURCES[source_name]
            source_settings = self._load_source(source)
            if source_settings:
                self._source_values[source_name] = source_settings
                self._merge_settings(source_settings)

    def _load_source(self, source: SettingSource) -> dict[str, Any]:
        """
        加载单个设置源 / Load single setting source
        """
        if source.name == "env":
            return self._load_env_settings()
        if source.name == "cli":
            return {}

        if source.path and source.path.exists():
            try:
                if source.path.is_file():
                    with open(source.path, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f) or {}
                elif source.path.is_dir():
                    merged = {}
                    for yaml_file in source.path.glob("*.yaml"):
                        with open(yaml_file, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            merged[yaml_file.stem] = data
                    return merged
            except Exception:
                pass
        return {}

    def _load_env_settings(self) -> dict[str, Any]:
        """从环境变量加载设置 / Load settings from env vars"""
        env_settings = {}
        prefix = "ALONEWORK_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                setting_key = key[len(prefix):].lower().replace("_", ".")
                env_settings[setting_key] = value
        return env_settings

    def _merge_settings(self, new_settings: dict[str, Any]) -> None:
        """合并设置 / Merge settings"""
        self._deep_merge(self._settings, new_settings)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并字典 / Deep merge dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取设置值 / Get setting value

        支持点分隔的嵌套键 / Supports dot-separated nested keys
        """
        keys = key.split(".")
        value = self._settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any, source: str = "user") -> None:
        """
        设置值 / Set value

        Args:
            key: 设置键（支持点分隔）/ Setting key (dot-separated)
            value: 设置值 / Setting value
            source: 设置来源 / Setting source
        """
        keys = key.split(".")
        target = self._settings
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        old_value = target.get(keys[-1])
        target[keys[-1]] = value

        if source not in self._source_values:
            self._source_values[source] = {}

        if old_value != value:
            self._notify_change(key, old_value, value)

    def _notify_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知设置变更 / Notify settings change"""
        for listener in self._change_listeners:
            try:
                listener(key, old_value, new_value)
            except Exception:
                pass

    def add_change_listener(self, listener) -> None:
        """添加变更监听器 / Add change listener"""
        self._change_listeners.append(listener)

    def remove_change_listener(self, listener) -> None:
        """移除变更监听器 / Remove change listener"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def reload(self) -> None:
        """重新加载所有设置 / Reload all settings"""
        self._settings.clear()
        self._source_values.clear()
        self._load_all_sources()

    def get_all(self) -> dict[str, Any]:
        """获取所有设置 / Get all settings"""
        return self._settings.copy()

    def get_source_value(self, source: str, key: str, default: Any = None) -> Any:
        """获取指定来源的设置值 / Get setting value from specific source"""
        source_settings = self._source_values.get(source, {})
        keys = key.split(".")
        value = source_settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value


# ============================================================
# 应用状态 / Application State (对齐 claude-code-claude 的 AppState)
# ============================================================

class AppState:
    """
    应用状态管理 / Application state management

    对齐 claude-code-claude 的 AppState：
    - 集中式状态存储
    - 状态变更通知
    - 选择器支持

    Aligns with claude-code-claude's AppState:
    - Centralized state storage
    - State change notification
    - Selector support
    """

    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        self._state: dict[str, Any] = {
            "verbose": False,
            "model_name": "deepseek-v4-flash",
            "output_format": "text",
            "theme": "dark",
            "agent_color": "cyan",
            "effort_level": "auto",
            "fast_mode": {"enabled": False},
            "output_style": "default",
            "interaction_mode": "agent",
            "no_stream": False,
            "show_thinking": False,
            "no_ime": False,
            "auto_compact": False,
            "compact_threshold": 100,
            "context_files": [],
            "tool_permission_context": ToolPermissionContext(),
        }
        self._settings_manager = settings_manager or SettingsManager()
        self._listeners: list = []
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        """从设置加载状态 / Load state from settings"""
        theme = self._settings_manager.get("theme.default", "dark")
        if theme:
            self._state["theme"] = theme

        effort = self._settings_manager.get("effort.default", "auto")
        if effort:
            self._state["effort_level"] = effort

    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值 / Get state value"""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置状态值 / Set state value"""
        old_value = self._state.get(key)
        self._state[key] = value
        if old_value != value:
            self._notify(key, old_value, value)

    def _notify(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知状态变更 / Notify state change"""
        for listener in self._listeners:
            try:
                listener(key, old_value, new_value)
            except Exception:
                pass

    def add_listener(self, listener) -> None:
        """添加监听器 / Add listener"""
        self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        """移除监听器 / Remove listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def get_all(self) -> dict[str, Any]:
        """获取所有状态 / Get all state"""
        return self._state.copy()

    def update(self, updates: dict[str, Any]) -> None:
        """批量更新状态 / Batch update state"""
        for key, value in updates.items():
            self.set(key, value)

    @property
    def settings(self) -> SettingsManager:
        """获取设置管理器 / Get settings manager"""
        return self._settings_manager

    @property
    def tool_permission_context(self) -> ToolPermissionContext:
        """获取工具权限上下文 / Get tool permission context"""
        return self._state.get("tool_permission_context", ToolPermissionContext())


# ============================================================
# 全局实例 / Global Instances
# ============================================================

_settings_manager: Optional[SettingsManager] = None
_app_state: Optional[AppState] = None


def get_settings_manager() -> SettingsManager:
    """获取全局设置管理器 / Get global settings manager"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_app_state() -> AppState:
    """获取全局应用状态 / Get global application state"""
    global _app_state
    if _app_state is None:
        _app_state = AppState(get_settings_manager())
    return _app_state


def reset_state() -> None:
    """重置全局状态 / Reset global state"""
    global _settings_manager, _app_state
    _settings_manager = None
    _app_state = None


def ensure_directories() -> None:
    """确保所有必要目录存在 / Ensure all necessary directories exist"""
    for dir_path in [
        ALONECHAT_DIR,
        SESSIONS_DIR,
        MEMORY_DIR,
        SKILLS_DIR,
        COMMANDS_DIR,
        HOOKS_DIR,
        SHARED_DIR,
        FEEDBACK_DIR,
        TAGS_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
