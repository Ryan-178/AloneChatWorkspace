"""
交互增强模块 / Interactive Enhancement Module

提供 / Provides:
- 智能提示 / Smart hints
- 自动补全 / Auto completion
- 命令历史 / Command history
- 快捷键支持 / Hotkey support
- 提示建议（Tab接受/Enter提交） / Prompt suggestions (Tab accept/Enter submit)
"""

from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path
import json
import re

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns

from alonechat.configs import config


@dataclass
class Command:
    """命令数据类 / Command Data Class"""
    name: str
    description: str
    aliases: list[str] = field(default_factory=list)
    usage: str = ""
    examples: list[str] = field(default_factory=list)


class CommandRegistry:
    """命令注册表 / Command Registry"""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}

    def register(self, command: Command) -> None:
        """注册命令 / Register command"""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._aliases[alias] = command.name

    def get(self, name: str) -> Optional[Command]:
        """获取命令 / Get command"""
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands[self._aliases[name]]
        return None

    def list_commands(self) -> list[Command]:
        """列出所有命令 / List all commands"""
        return list(self._commands.values())

    def search(self, query: str) -> list[Command]:
        """搜索命令 / Search commands"""
        query = query.lower()
        return [
            cmd for cmd in self._commands.values()
            if query in cmd.name.lower() or query in cmd.description.lower()
        ]


class CommandHistory:
    """命令历史 / Command History"""

    def __init__(self, max_size: Optional[int] = None, history_file: Optional[Path] = None):
        history_cfg = config.get_history_config()
        self.max_size = max_size or history_cfg.get("default_max_size", 100)

        if history_file is None:
            history_dir = history_cfg.get("history_dir", ".alonechat")
            history_filename = history_cfg.get("history_file", "history.json")
            self.history_file = Path.home() / history_dir / history_filename
        else:
            self.history_file = history_file

        self._history: deque[str] = deque(maxlen=self.max_size)
        self._load()

    def _load(self) -> None:
        """加载历史 / Load history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data[-self.max_size:]:
                        self._history.append(item)
            except Exception:
                pass

    def _save(self) -> None:
        """保存历史 / Save history"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(list(self._history), f, ensure_ascii=False, indent=2)

    def add(self, command: str) -> None:
        """添加命令到历史 / Add command to history"""
        if command.strip():
            self._history.append(command)
            self._save()

    def get_history(self) -> list[str]:
        """获取历史列表 / Get history list"""
        return list(self._history)

    def search(self, query: str) -> list[str]:
        """搜索历史 / Search history"""
        query = query.lower()
        return [cmd for cmd in self._history if query in cmd.lower()]


class PromptSuggestion:
    """
    提示建议 / Prompt Suggestion

    提供类似Claude Code的提示建议功能
    Provides suggestion feature similar to Claude Code
    - Tab: 接受建议并编辑 / Accept suggestion and edit
    - Enter: 直接提交 / Submit directly
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._current_suggestions: list[str] = []
        self._selected_index = 0
        self._show_hint = True

    def set_suggestions(self, suggestions: list[str]) -> None:
        """
        设置当前建议列表 / Set current suggestion list

        Args:
            suggestions: 建议列表 / Suggestion list
        """
        self._current_suggestions = suggestions[:5] if len(suggestions) > 5 else suggestions
        self._selected_index = 0

    def clear_suggestions(self) -> None:
        """清除建议 / Clear suggestions"""
        self._current_suggestions.clear()
        self._selected_index = 0

    def get_current_suggestions(self) -> list[str]:
        """获取当前建议 / Get current suggestions"""
        return self._current_suggestions

    def has_suggestions(self) -> bool:
        """是否有建议 / Has suggestions"""
        return len(self._current_suggestions) > 0

    def display_suggestions(self, partial: str) -> None:
        """
        显示建议 / Display suggestions

        仅在交互模式下显示建议提示
        Only display suggestion hints in interactive mode

        Args:
            partial: 已输入的部分 / Partial input
        """
        if not self._show_hint or not self._current_suggestions:
            return

        hint_text = Text()
        hint_text.append("建议 / Suggestions: ", style="dim")
        for i, suggestion in enumerate(self._current_suggestions):
            if i > 0:
                hint_text.append("  ", style="dim")
            hint_text.append(f"[Tab]", style="cyan bold")
            hint_text.append(f" {suggestion}", style="dim")
            hint_text.append("  ", style="dim")

        self.console.print(hint_text)

    def accept_suggestion(self) -> str:
        """
        接受当前建议（Tab行为）/ Accept current suggestion (Tab behavior)

        Returns:
            选中建议 / Selected suggestion
        """
        if self._current_suggestions:
            suggestion = self._current_suggestions[0]
            self.clear_suggestions()
            return suggestion
        return ""


class InteractiveSession:
    """交互会话 / Interactive Session"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.command_registry = CommandRegistry()
        self.history = CommandHistory()
        self.suggestion = PromptSuggestion(console)
        self._setup_default_commands()

    def _setup_default_commands(self) -> None:
        """设置默认命令 / Setup default commands"""
        default_commands = config.get_default_commands()

        for name, cmd_cfg in default_commands.items():
            command = Command(
                name=name,
                description=cmd_cfg.get("description", ""),
                aliases=cmd_cfg.get("aliases", []),
                usage=cmd_cfg.get("usage", ""),
                examples=cmd_cfg.get("examples", []),
            )
            self.command_registry.register(command)

    def show_help(self, command_name: Optional[str] = None) -> None:
        """显示帮助 / Show help"""
        cmd_messages = config.get_command_messages()
        styles = config.get_ui_styles()

        if command_name:
            cmd = self.command_registry.get(command_name)
            if cmd:
                usage_label = cmd_messages.get("usage_label", "用法")
                example_label = cmd_messages.get("example_label", "示例")
                help_title = cmd_messages.get("command_help_title", "命令帮助")

                self.console.print(Panel(
                    f"[bold]{cmd.name}[/bold]\n\n"
                    f"{cmd.description}\n\n"
                    f"[cyan]{usage_label}:[/cyan] {cmd.usage}\n\n"
                    f"[cyan]{example_label}:[/cyan]\n" + "\n".join(f"  {ex}" for ex in cmd.examples),
                    title=f"{help_title}: {cmd.name}",
                    border_style=styles.get("blue", "blue")
                ))
            else:
                not_found = cmd_messages.get("not_found_message", "未找到命令")
                self.console.print(f"[red]{not_found}: {command_name}[/red]")
        else:
            title = cmd_messages.get("available_commands_title", "可用命令")
            cmd_col = cmd_messages.get("command_column", "命令")
            desc_col = cmd_messages.get("description_column", "描述")
            alias_col = cmd_messages.get("alias_column", "别名")

            table = Table(title=title, show_header=True, header_style="bold cyan")
            table.add_column(cmd_col, style=styles.get("green", "green"))
            table.add_column(desc_col)
            table.add_column(alias_col, style=styles.get("dim", "dim"))

            for cmd in self.command_registry.list_commands():
                aliases = ", ".join(cmd.aliases) if cmd.aliases else "-"
                table.add_row(f"/{cmd.name}", cmd.description, aliases)

            self.console.print(table)

    def parse_input(self, user_input: str) -> tuple[bool, str, list[str]]:
        """解析输入 / Parse input"""
        prefix = config.get("commands.prefix", "/")
        is_command = user_input.startswith(prefix)

        if is_command:
            parts = user_input[1:].split()
            command = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
            return True, command, args

        return False, user_input, []

    def get_input(self, prompt: str = "You") -> tuple[bool, str, list[str]]:
        """获取输入 / Get input"""
        user_input = Prompt.ask(f"[bold blue]{prompt}[/bold blue]")
        self.history.add(user_input)
        return self.parse_input(user_input)

    def get_input_with_suggestions(
        self,
        prompt: str = "You",
        auto_suggest: bool = True,
    ) -> str:
        """
        带建议的输入获取 / Get input with suggestions

        支持 / Supports:
        - Tab: 接受建议并编辑 / Accept suggestion and edit
        - Enter: 直接提交 / Submit directly
        - 自动显示命令补全建议 / Auto show command completion suggestions

        Args:
            prompt: 提示文本 / Prompt text
            auto_suggest: 是否自动建议 / Whether to auto suggest

        Returns:
            用户输入文本 / User input text
        """
        user_input = Prompt.ask(f"[bold blue]{prompt}[/bold blue]")

        if auto_suggest and user_input.startswith("/"):
            suggestions = self.suggest_commands(user_input)
            if suggestions:
                self.suggestion.set_suggestions(suggestions)
                if len(suggestions) <= 3:
                    self.suggestion.display_suggestions(user_input)
            else:
                self.suggestion.clear_suggestions()

        self.history.add(user_input)
        return user_input

    def suggest_commands(self, partial: str) -> list[str]:
        """建议命令 / Suggest commands"""
        prefix = config.get("commands.prefix", "/")

        if not partial.startswith(prefix):
            return []

        partial_name = partial[1:].lower()
        suggestions = []

        for cmd in self.command_registry.list_commands():
            if cmd.name.startswith(partial_name):
                suggestions.append(f"{prefix}{cmd.name}")
            for alias in cmd.aliases:
                if alias.startswith(partial_name):
                    suggestions.append(f"{prefix}{alias}")

        return suggestions


class AutoCompleter:
    """自动补全器 / Auto Completer"""

    def __init__(self, session: InteractiveSession):
        self.session = session
        self._context: list[str] = []
        self._config = config.get_autocompleter_config()

    def add_context(self, text: str) -> None:
        """添加上下文 / Add context"""
        self._context.append(text)
        max_size = self._config.get("max_context_size", 100)
        if len(self._context) > max_size:
            self._context = self._context[-max_size:]

    def get_suggestions(self, partial: str) -> list[str]:
        """获取建议 / Get suggestions"""
        suggestions = []

        if partial.startswith("/"):
            suggestions.extend(self.session.suggest_commands(partial))

        min_len = self._config.get("min_partial_length", 3)
        max_suggestions = self._config.get("max_suggestions", 10)
        max_matches = self._config.get("max_matches_per_context", 3)

        if len(partial) >= min_len:
            pattern = re.compile(re.escape(partial), re.IGNORECASE)
            for text in self._context:
                matches = pattern.findall(text)
                suggestions.extend(matches[:max_matches])

        return list(dict.fromkeys(suggestions))[:max_suggestions]
