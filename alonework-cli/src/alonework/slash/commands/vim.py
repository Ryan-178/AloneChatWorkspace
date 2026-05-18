"""
/vim å½ä»¤ - Vimæ¨¡å¼ / Vim mode

æä¾ / Provides:
- Vimæ¨¡å¼å¯ç¨/ç¦ç¨ / Vim mode enable/disable
- å¢å¼ºé®ç»å®?/ Enhanced key bindings
- ææ¬å¯¹è±¡æ¯æ / Text object support
"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


VIM_BINDINGS = {
    "i": {"action": "insert_mode", "description": "æå¥æ¨¡å¼ / Insert mode"},
    "I": {"action": "insert_start", "description": "è¡é¦æå¥ / Insert at line start"},
    "a": {"action": "append", "description": "è¿½å  / Append"},
    "A": {"action": "append_end", "description": "è¡å°¾è¿½å  / Append at line end"},
    "o": {"action": "open_below", "description": "ä¸æ¹æ°è¡ / Open line below"},
    "O": {"action": "open_above", "description": "ä¸æ¹æ°è¡ / Open line above"},
    "Esc": {"action": "normal_mode", "description": "å½ä»¤æ¨¡å¼ / Normal mode"},
    "j": {"action": "cursor_down", "description": "åæ ä¸ç§» / Cursor down"},
    "k": {"action": "cursor_up", "description": "åæ ä¸ç§» / Cursor up"},
    "h": {"action": "cursor_left", "description": "åæ å·¦ç§» / Cursor left"},
    "l": {"action": "cursor_right", "description": "åæ å³ç§» / Cursor right"},
    "w": {"action": "word_forward", "description": "ä¸ä¸ä¸ªè¯é¦?/ Next word start"},
    "b": {"action": "word_backward", "description": "ä¸ä¸ä¸ªè¯é¦?/ Previous word start"},
    "e": {"action": "word_end", "description": "è¯å°¾ / Word end"},
    "0": {"action": "line_start", "description": "è¡é¦ / Line start"},
    "$": {"action": "line_end", "description": "è¡å°¾ / Line end"},
    "x": {"action": "delete_char", "description": "å é¤å­ç¬¦ / Delete character"},
    "dd": {"action": "delete_line", "description": "å é¤è¡?/ Delete line"},
    "yy": {"action": "yank_line", "description": "å¤å¶è¡?/ Yank line"},
    "y": {"action": "yank", "description": "å¤å¶ / Yank (v2.1.0)"},
    "p": {"action": "paste_below", "description": "ä¸æ¹ç²è´´ / Paste below (v2.1.0)"},
    "P": {"action": "paste_above", "description": "ä¸æ¹ç²è´´ / Paste above (v2.1.0)"},
    "u": {"action": "undo", "description": "æ¤é / Undo"},
    "Ctrl+r": {"action": "redo", "description": "éå / Redo"},
    ">>": {"action": "indent_right", "description": "å³ç¼©è¿?/ Indent right (v2.1.0)"},
    "<<": {"action": "indent_left", "description": "å·¦ç¼©è¿?/ Indent left (v2.1.0)"},
    "J": {"action": "join_lines", "description": "åå¹¶è¡?/ Join lines (v2.1.0)"},
    "G": {"action": "goto_end", "description": "è·³è½¬å°æä»¶å°¾ / Go to end"},
    "gg": {"action": "goto_start", "description": "è·³è½¬å°æä»¶å¤´ / Go to start"},
    ";": {"action": "repeat_last_f", "description": "éå¤ä¸æ¬¡f/t / Repeat last f/t (v2.1.0)"},
    ",": {"action": "reverse_last_f", "description": "ååéå¤ä¸æ¬¡f/t / Reverse last f/t (v2.1.0)"},
    "/": {"action": "search", "description": "æç´¢ / Search"},
    "n": {"action": "next_search", "description": "ä¸ä¸ä¸ªå¹é?/ Next match"},
    "N": {"action": "prev_search", "description": "ä¸ä¸ä¸ªå¹é?/ Previous match"},
    ":w": {"action": "save", "description": "ä¿å­ä¼è¯ / Save session"},
    ":q": {"action": "quit", "description": "éå?/ Quit"},
    ":wq": {"action": "save_quit", "description": "ä¿å­å¹¶éå?/ Save and quit"},
}


def vim_command(args: list, obj: dict, session_manager, registry, **kwargs) -> str | None:
    """
    Vimæ¨¡å¼ / Vim mode

    ç¨æ³ / Usage:
        /vim              - å¯ç¨Vimæ¨¡å¼ / Enable Vim mode
        /vim off          - ç¦ç¨Vimæ¨¡å¼ / Disable Vim mode
        /vim bindings     - æ¾ç¤ºææé®ç»å® / Show all key bindings
    """
    if args and args[0].lower() == "off":
        obj["_vim_mode"] = False
        console.print(Panel(
            "[bold cyan]Vimæ¨¡å¼å·²ç¦ç?/ Vim Mode Disabled[/bold cyan]\n\n"
            "å·²åæ¢åé»è®¤ç¼è¾æ¨¡å¼ / Switched back to default editing mode",
            border_style="cyan"
        ))
        return "vim_off"

    if args and args[0].lower() == "bindings":
        _show_bindings()
        return "vim_bindings"

    obj["_vim_mode"] = True

    console.print(Panel(
        "[bold cyan]Vimæ¨¡å¼å·²å¯ç?/ Vim Mode Enabled[/bold cyan]\n\n"
        "å¢å¼ºé®ç»å®?/ Enhanced Key Bindings:\n"
        "â?[cyan]i[/cyan] - æå¥æ¨¡å¼ / Insert mode\n"
        "â?[cyan]Esc[/cyan] - å½ä»¤æ¨¡å¼ / Normal mode\n"
        "â?[cyan]j/k/h/l[/cyan] - åæ ç§»å¨ / Cursor movement\n"
        "â?[cyan]y/p[/cyan] - å¤å¶/ç²è´´ / Yank/Paste [v2.1.0]\n"
        "â?[cyan]>>/<<[/cyan] - ç¼©è¿ / Indent [v2.1.0]\n"
        "â?[cyan]J[/cyan] - åå¹¶è¡?/ Join lines [v2.1.0]\n"
        "â?[cyan];/,/[/cyan] - éå¤f/t / Repeat f/t [v2.1.0]\n"
        "â?[cyan]:w[/cyan] - ä¿å­ä¼è¯ / Save session\n"
        "â?[cyan]:q[/cyan] - éå?/ Quit\n\n"
        "[dim]è¾å¥ /vim bindings æ¥çå¨é¨é®ç»å®?/ View all key bindings[/dim]",
        border_style="cyan"
    ))
    return "vim_on"


def _show_bindings() -> None:
    """æ¾ç¤ºææé®ç»å® / Show all key bindings"""
    table = Table(title="[bold cyan]Vimé®ç»å®?/ Vim Key Bindings[/bold cyan]")
    table.add_column("æé® / Key", style="cyan")
    table.add_column("æä½ / Action", style="green")
    table.add_column("è¯´æ / Description")

    for key, binding in VIM_BINDINGS.items():
        table.add_row(key, f"[dim]{binding['action']}[/dim]", binding["description"])

    console.print(table)


class VimBuffer:
    """
    Vimç¼å²åºç®¡çå¨ / Vim Buffer Manager

    ç®¡çVimæ¨¡å¼ä¸çææ¬ç¼å²åºæä½?    Manages text buffer operations in Vim mode
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
        """è·åå½åè¡åè¡?/ Get current lines"""
        return self._lines

    @lines.setter
    def lines(self, value: list[str]) -> None:
        """è®¾ç½®å½åè¡åè¡?/ Set current lines"""
        self._undo_stack.append(self._lines[:])
        self._redo_stack.clear()
        self._lines = value[:]

    def yank_line(self, line_num: int) -> None:
        """
        å¤å¶è¡?/ Yank line

        Args:
            line_num: è¡å· / Line number
        """
        if 0 <= line_num < len(self._lines):
            self._yank_register = [self._lines[line_num]]

    def yank(self, start: int, end: int) -> None:
        """
        å¤å¶ææ¬èå´ / Yank text range

        Args:
            start: èµ·å§ä½ç½® / Start position
            end: ç»æä½ç½® / End position
        """
        if start < end and end <= len(self._lines):
            self._yank_register = self._lines[start:end]

    def paste_below(self, line_num: int) -> None:
        """
        ä¸æ¹ç²è´´ / Paste below

        Args:
            line_num: å½åè¡å· / Current line number
        """
        if self._yank_register:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num + 1:line_num + 1] = self._yank_register

    def paste_above(self, line_num: int) -> None:
        """
        ä¸æ¹ç²è´´ / Paste above

        Args:
            line_num: å½åè¡å· / Current line number
        """
        if self._yank_register:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num:line_num] = self._yank_register

    def indent_right(self, line_num: int) -> None:
        """
        å³ç¼©è¿?/ Indent right

        Args:
            line_num: è¡å· / Line number
        """
        if 0 <= line_num < len(self._lines):
            self._undo_stack.append(self._lines[:])
            self._lines[line_num] = "    " + self._lines[line_num]

    def indent_left(self, line_num: int) -> None:
        """
        å·¦ç¼©è¿?/ Indent left

        Args:
            line_num: è¡å· / Line number
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
        åå¹¶è¡?/ Join lines

        Args:
            line_num: è¡å· / Line number
        """
        if 0 <= line_num < len(self._lines) - 1:
            self._undo_stack.append(self._lines[:])
            self._lines[line_num] = self._lines[line_num].rstrip() + " " + self._lines[line_num + 1].lstrip()
            del self._lines[line_num + 1]

    def delete_line(self, line_num: int) -> Optional[str]:
        """
        å é¤è¡?/ Delete line

        Args:
            line_num: è¡å· / Line number

        Returns:
            è¢«å é¤çè¡?/ Deleted line
        """
        if 0 <= line_num < len(self._lines):
            self._undo_stack.append(self._lines[:])
            return self._lines.pop(line_num)
        return None

    def undo(self) -> None:
        """æ¤é / Undo"""
        if self._undo_stack:
            self._redo_stack.append(self._lines[:])
            self._lines = self._undo_stack.pop()

    def redo(self) -> None:
        """éå / Redo"""
        if self._redo_stack:
            self._undo_stack.append(self._lines[:])
            self._lines = self._redo_stack.pop()
