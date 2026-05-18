"""
/vim 命令 - Vim模式 / Vim mode

提供 / Provides:
- Vim模式启用/禁用 / Vim mode enable/disable
- 增强键绑定 / Enhanced key bindings
- 文本对象支持 / Text object support
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


VIM_BINDINGS = {
    "i": {"action": "insert_mode", "description": "插入模式 / Insert mode"},
    "I": {"action": "insert_start", "description": "行首插入 / Insert at line start"},
    "a": {"action": "append", "description": "追加 / Append"},
    "A": {"action": "append_end", "description": "行尾追加 / Append at line end"},
    "o": {"action": "open_below", "description": "下方新行 / Open line below"},
    "O": {"action": "open_above", "description": "上方新行 / Open line above"},
    "Esc": {"action": "normal_mode", "description": "命令模式 / Normal mode"},
    "j": {"action": "cursor_down", "description": "光标下移 / Cursor down"},
    "k": {"action": "cursor_up", "description": "光标上移 / Cursor up"},
    "h": {"action": "cursor_left", "description": "光标左移 / Cursor left"},
    "l": {"action": "cursor_right", "description": "光标右移 / Cursor right"},
    "w": {"action": "word_forward", "description": "下一个词首 / Next word start"},
    "b": {"action": "word_backward", "description": "上一个词首 / Previous word start"},
    "e": {"action": "word_end", "description": "词尾 / Word end"},
    "0": {"action": "line_start", "description": "行首 / Line start"},
    "$": {"action": "line_end", "description": "行尾 / Line end"},
    "x": {"action": "delete_char", "description": "删除字符 / Delete character"},
    "dd": {"action": "delete_line", "description": "删除行 / Delete line"},
    "yy": {"action": "yank_line", "description": "复制行 / Yank line"},
    "y": {"action": "yank", "description": "复制 / Yank (v2.1.0)"},
    "p": {"action": "paste_below", "description": "下方粘贴 / Paste below (v2.1.0)"},
    "P": {"action": "paste_above", "description": "上方粘贴 / Paste above (v2.1.0)"},
    "u": {"action": "undo", "description": "撤销 / Undo"},
    "Ctrl+r": {"action": "redo", "description": "重做 / Redo"},
    ">>": {"action": "indent_right", "description": "右缩进 / Indent right (v2.1.0)"},
    "<<": {"action": "indent_left", "description": "左缩进 / Indent left (v2.1.0)"},
    "J": {"action": "join_lines", "description": "合并行 / Join lines (v2.1.0)"},
    "G": {"action": "goto_end", "description": "跳转到文件尾 / Go to end"},
    "gg": {"action": "goto_start", "description": "跳转到文件头 / Go to start"},
    ";": {"action": "repeat_last_f", "description": "重复上次f/t / Repeat last f/t (v2.1.0)"},
    ",": {"action": "reverse_last_f", "description": "反向重复上次f/t / Reverse last f/t (v2.1.0)"},
    "/": {"action": "search", "description": "搜索 / Search"},
    "n": {"action": "next_search", "description": "下一个匹配 / Next match"},
    "N": {"action": "prev_search", "description": "上一个匹配 / Previous match"},
    ":w": {"action": "save", "description": "保存会话 / Save session"},
    ":q": {"action": "quit", "description": "退出 / Quit"},
    ":wq": {"action": "save_quit", "description": "保存并退出 / Save and quit"},
}


def vim_command(args: list, obj: dict, session_manager, registry, **kwargs) -> str | None:
    """
    Vim模式 / Vim mode

    用法 / Usage:
        /vim              - 启用Vim模式 / Enable Vim mode
        /vim off          - 禁用Vim模式 / Disable Vim mode
        /vim bindings     - 显示所有键绑定 / Show all key bindings
    """
    if args and args[0].lower() == "off":
        obj["_vim_mode"] = False
        console.print(Panel(
            "[bold cyan]Vim模式已禁用 / Vim Mode Disabled[/bold cyan]\n\n"
            "已切换回默认编辑模式 / Switched back to default editing mode",
            border_style="cyan"
        ))
        return "vim_off"

    if args and args[0].lower() == "bindings":
        _show_bindings()
        return "vim_bindings"

    obj["_vim_mode"] = True

    console.print(Panel(
        "[bold cyan]Vim模式已启用 / Vim Mode Enabled[/bold cyan]\n\n"
        "增强键绑定 / Enhanced Key Bindings:\n"
        "• [cyan]i[/cyan] - 插入模式 / Insert mode\n"
        "• [cyan]Esc[/cyan] - 命令模式 / Normal mode\n"
        "• [cyan]j/k/h/l[/cyan] - 光标移动 / Cursor movement\n"
        "• [cyan]y/p[/cyan] - 复制/粘贴 / Yank/Paste [v2.1.0]\n"
        "• [cyan]>>/<<[/cyan] - 缩进 / Indent [v2.1.0]\n"
        "• [cyan]J[/cyan] - 合并行 / Join lines [v2.1.0]\n"
        "• [cyan];/,/[/cyan] - 重复f/t / Repeat f/t [v2.1.0]\n"
        "• [cyan]:w[/cyan] - 保存会话 / Save session\n"
        "• [cyan]:q[/cyan] - 退出 / Quit\n\n"
        "[dim]输入 /vim bindings 查看全部键绑定 / View all key bindings[/dim]",
        border_style="cyan"
    ))
    return "vim_on"


def _show_bindings() -> None:
    """显示所有键绑定 / Show all key bindings"""
    table = Table(title="[bold cyan]Vim键绑定 / Vim Key Bindings[/bold cyan]")
    table.add_column("按键 / Key", style="cyan")
    table.add_column("操作 / Action", style="green")
    table.add_column("说明 / Description")

    for key, binding in VIM_BINDINGS.items():
        table.add_row(key, f"[dim]{binding['action']}[/dim]", binding["description"])

    console.print(table)


class VimBuffer:
    """
    Vim缓冲区管理器 / Vim Buffer Manager

    管理Vim模式下的文本缓冲区操作
    Manages text buffer operations in Vim mode
    """

    def __init__(self):
        self._lines: list[str] = []
        self._yank_register: list[str] = []
        self._last_f_command: str = ""
        self._search_pattern: str = ""
        self._undo_stack: list[list[str]] = []
        self._redo_stack: list[list[str]] = []

    @property
    def lines(self) -> list[str]:
        """获取当前行列表 / Get current lines"""
        return self._lines

    @lines.setter
    def lines(self, value: list[str]) -> None:
        """设置当前行列表 / Set current lines"""
        self._undo_stack.append(self._lines[:])
        self._redo_stack.clear()
        self._lines = value[:]

    def yank_line(self, line_num: int) -> None:
        """
        复制行 / Yank line

        Args:
            line_num: 行号 / Line number
        """
        if 0 <= line_num < len(self._lines):
            self._yank_register = [self._lines[line_num]]

    def yank(self, start: int, end: int) -> None:
        """
        复制文本范围 / Yank text range

        Args:
            start: 起始位置 / Start position
            end: 结束位置 / End position
        """
        if start < end and end <= len(self._lines):
            self._yank_register = self._lines[start:end]

    def paste_below(self, line_num: int) -> None:
        """
        下方粘贴 / Paste below

        Args:
            line_num: 当前行号 / Current line number
        """
        if self._yank_register:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num + 1:line_num + 1] = self._yank_register

    def paste_above(self, line_num: int) -> None:
        """
        上方粘贴 / Paste above

        Args:
            line_num: 当前行号 / Current line number
        """
        if self._yank_register:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num:line_num] = self._yank_register

    def indent_right(self, line_num: int) -> None:
        """
        右缩进 / Indent right

        Args:
            line_num: 行号 / Line number
        """
        if 0 <= line_num < len(self._lines):
            self._undo_stack.append(self._lines[:])
            self._lines[line_num] = "    " + self._lines[line_num]

    def indent_left(self, line_num: int) -> None:
        """
        左缩进 / Indent left

        Args:
            line_num: 行号 / Line number
        """
        if 0 <= line_num < len(self._lines):
            self._undo_stack.append(self._lines[:])
            stripped = self._lines[line_num]
            if stripped.startswith("    "):
                stripped = stripped[4:]
            elif stripped.startswith("\t"):
                stripped = stripped[1:]
            self._lines[line_num] = stripped

    def join_lines(self, line_num: int) -> None:
        """
        合并行 / Join lines

        Args:
            line_num: 行号 / Line number
        """
        if 0 <= line_num < len(self._lines) - 1:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num] = self._lines[line_num].rstrip() + " " + self._lines[line_num + 1].lstrip()
            del self._lines[line_num + 1]

    def delete_line(self, line_num: int) -> Optional[str]:
        """
        删除行 / Delete line

        Args:
            line_num: 行号 / Line number

        Returns:
            被删除的行 / Deleted line
        """
        if 0 <= line_num < len(self._lines):
            self._undo_stack.append(self._lines[:])
            return self._lines.pop(line_num)
        return None

    def undo(self) -> None:
        """撤销 / Undo"""
        if self._undo_stack:
            self._redo_stack.append(self._lines[:])
            self._lines = self._undo_stack.pop()

    def redo(self) -> None:
        """重做 / Redo"""
        if self._redo_stack:
            self._undo_stack.append(self._lines[:])
            self._lines = self._redo_stack.pop()
