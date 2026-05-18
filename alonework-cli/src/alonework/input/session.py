"""
å¢å¼ºè¾å¥ä¼è¯ / Enhanced Input Session

åºäº prompt_toolkit çç»ä¸è¾å¥ä¼è¯ / Unified input session based on prompt_toolkit
æ¯æå¿«æ·é®ãåå²è¡¥å¨ãå¤é¨ç¼è¾å¨ / Supports shortcuts, history completion, external editor
"""

from typing import Optional, List, Callable, Any, Dict
from enum import Enum
from dataclasses import dataclass

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText

from alonework.input.history import CommandHistory
from alonework.input.external_editor import ExternalEditor
from alonework.input.key_bindings import create_key_bindings


class InputMode(Enum):
    """è¾å¥æ¨¡å¼ / Input mode"""
    NORMAL = "normal"
    BANG_HISTORY = "bang_history"
    SLASH_COMMAND = "slash_command"


@dataclass
class InputResult:
    """è¾å¥ç»æ / Input result"""
    text: str
    mode: InputMode
    from_editor: bool = False
    background_requested: bool = False


class EnhancedInputSession:
    """
    å¢å¼ºè¾å¥ä¼è¯ / Enhanced Input Session
    
    æä¾ç»ä¸çäº¤äºå¼è¾å¥æ¥å£ / Provides unified interactive input interface
    """
    
    STYLE = Style.from_dict({
        "prompt": "bold blue",
        "history": "ansiyellow",
        "completion": "ansigreen",
    })
    
    def __init__(
        self,
        history: Optional[CommandHistory] = None,
        editor: Optional[ExternalEditor] = None,
        slash_completer: Optional[Completer] = None,
        on_background_request: Optional[Callable[[str], Any]] = None,
    ):
        """
        åå§åå¢å¼ºè¾å¥ä¼è¯?/ Initialize enhanced input session
        
        Args:
            history: å½ä»¤åå²ç®¡çå?/ Command history manager
            editor: å¤é¨ç¼è¾å?/ External editor
            slash_completer: Slashå½ä»¤è¡¥å¨å?/ Slash command completer
            on_background_request: åå°è¯·æ±åè° / Background request callback
        """
        self.history = history or CommandHistory()
        self.editor = editor or ExternalEditor()
        self.slash_completer = slash_completer
        self.on_background_request = on_background_request
        
        self._mode = InputMode.NORMAL
        self._current_input = ""
        self._background_requested = False
        
        self._key_bindings = self._create_key_bindings()
        
        self._session = PromptSession(
            history=self._create_pt_history(),
            key_bindings=self._key_bindings,
            style=self.STYLE,
            mouse_support=True,
            enable_suspend=True,
        )
    
    def _create_pt_history(self) -> InMemoryHistory:
        """
        åå»º prompt_toolkit åå²å¯¹è±¡ / Create prompt_toolkit history object
        
        Returns:
            InMemoryHistory å¯¹è±¡ / InMemoryHistory object
        """
        pt_history = InMemoryHistory()
        for cmd in self.history.get_recent(100):
            pt_history.append_string(cmd)
        return pt_history
    
    def _create_key_bindings(self) -> KeyBindings:
        """
        åå»ºé®çç»å® / Create key bindings
        
        Returns:
            KeyBindings å¯¹è±¡ / KeyBindings object
        """
        return create_key_bindings(
            on_ctrl_b=self._handle_ctrl_b,
            on_ctrl_g=self._handle_ctrl_g,
        )
    
    def _handle_ctrl_b(self) -> bool:
        """
        å¤ç Ctrl+B / Handle Ctrl+B
        
        æ è®°å½åè¾å¥ä¸ºåå°æ§è¡?/ Mark current input for background execution
        
        Returns:
            æ¯å¦å·æ°çé¢ / Whether to refresh UI
        """
        self._background_requested = True
        return True
    
    def _handle_ctrl_g(self) -> bool:
        """
        å¤ç Ctrl+G / Handle Ctrl+G
        
        æå¼å¤é¨ç¼è¾å¨ç¼è¾å½åè¾å?/ Open external editor to edit current input
        
        Returns:
            æ¯å¦å·æ°çé¢ / Whether to refresh UI
        """
        saved, content = self.editor.edit(self._current_input)
        if saved and content:
            self._current_input = content
        return True
    
    def _detect_mode(self, text: str) -> InputMode:
        """
        æ£æµè¾å¥æ¨¡å¼?/ Detect input mode
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            è¾å¥æ¨¡å¼ / Input mode
        """
        if text.startswith("!"):
            return InputMode.BANG_HISTORY
        elif text.startswith("/"):
            return InputMode.SLASH_COMMAND
        return InputMode.NORMAL
    
    def _process_bang_history(self, text: str) -> str:
        """
        å¤ç ! åå²å½ä»¤è¯­æ³ / Process ! history command syntax
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            å¤çåçå½ä»¤ / Processed command
        """
        if text == "!!":
            last_cmd = self.history.get_by_index(-1)
            return last_cmd or text
        
        if text.startswith("!") and len(text) > 1:
            rest = text[1:]
            if rest.isdigit():
                cmd = self.history.get_by_index(int(rest))
                return cmd or text
            else:
                matches = self.history.search(rest, limit=1)
                return matches[0] if matches else text
        
        return text
    
    def prompt(
        self,
        message: str = "You",
        default: str = "",
        **kwargs,
    ) -> InputResult:
        """
        è·åç¨æ·è¾å¥ / Get user input
        
        Args:
            message: æç¤ºæ¶æ¯ / Prompt message
            default: é»è®¤å?/ Default value
            **kwargs: å¶ä»åæ° / Other arguments
            
        Returns:
            InputResult å¯¹è±¡ / InputResult object
        """
        self._background_requested = False
        self._current_input = default
        
        formatted_message = FormattedText([
            ("class:prompt", f"{message}: "),
        ])
        
        completer = self._get_completer()
        
        try:
            text = self._session.prompt(
                formatted_message,
                default=default,
                completer=completer,
                **kwargs,
            )
        except KeyboardInterrupt:
            return InputResult(
                text="",
                mode=InputMode.NORMAL,
            )
        except EOFError:
            return InputResult(
                text="exit",
                mode=InputMode.NORMAL,
            )
        
        mode = self._detect_mode(text)
        
        if mode == InputMode.BANG_HISTORY:
            text = self._process_bang_history(text)
            mode = InputMode.NORMAL
        
        if text.strip():
            self.history.add(text)
        
        return InputResult(
            text=text,
            mode=mode,
            background_requested=self._background_requested,
        )
    
    def _get_completer(self) -> Optional[Completer]:
        """
        è·åå½åè¡¥å¨å?/ Get current completer
        
        Returns:
            Completer å¯¹è±¡æ?None / Completer object or None
        """
        if self.slash_completer:
            return self.slash_completer
        return None
    
    def prompt_async(
        self,
        message: str = "You",
        default: str = "",
        **kwargs,
    ):
        """
        å¼æ­¥è·åç¨æ·è¾å¥ / Get user input asynchronously
        
        Args:
            message: æç¤ºæ¶æ¯ / Prompt message
            default: é»è®¤å?/ Default value
            **kwargs: å¶ä»åæ° / Other arguments
            
        Returns:
            åç¨ / Coroutine
        """
        return self._session.prompt_async(
            FormattedText([("class:prompt", f"{message}: ")]),
            default=default,
            **kwargs,
        )
    
    def update_completions(self, completions: List[str]) -> None:
        """
        æ´æ°è¡¥å¨åè¡¨ / Update completion list
        
        Args:
            completions: è¡¥å¨åè¡¨ / Completion list
        """
        pass
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        è·åä¼è¯ä¿¡æ¯ / Get session info
        
        Returns:
            ä¼è¯ä¿¡æ¯å­å¸ / Session info dict
        """
        return {
            "mode": self._mode.value,
            "history_count": len(self.history),
            "editor": self.editor.editor,
        }
