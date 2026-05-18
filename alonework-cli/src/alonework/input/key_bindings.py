"""
é®çç»å®å®ä¹ / Keyboard Bindings Definition

å®ä¹ CLI äº¤äºä¸­çå¿«æ·é?/ Defines keyboard shortcuts in CLI interaction
- Ctrl+B: åå°åå½åä»»å?/ Background current task
- Ctrl+G: æå¼å¤é¨ç¼è¾å?/ Open external editor
- Tab: å½ä»¤è¡¥å¨ / Command completion
- !: åå²å½ä»¤æç´¢ / History command search
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from typing import Callable, Optional, Any


class KeyBindingManager:
    """
    é®çç»å®ç®¡çå?/ Key Binding Manager
    
    ç®¡çææå¿«æ·é®ç»å® / Manages all keyboard shortcut bindings
    """
    
    def __init__(
        self,
        on_ctrl_b: Optional[Callable[[], Any]] = None,
        on_ctrl_g: Optional[Callable[[], Any]] = None,
        on_ctrl_c: Optional[Callable[[], Any]] = None,
    ):
        """
        åå§åé®çç»å®ç®¡çå¨ / Initialize key binding manager
        
        Args:
            on_ctrl_b: Ctrl+B åè° / Ctrl+B callback
            on_ctrl_g: Ctrl+G åè° / Ctrl+G callback
            on_ctrl_c: Ctrl+C åè° / Ctrl+C callback
        """
        self.on_ctrl_b = on_ctrl_b
        self.on_ctrl_g = on_ctrl_g
        self.on_ctrl_c = on_ctrl_c
        self._kb = KeyBindings()
        self._setup_bindings()
    
    def _setup_bindings(self) -> None:
        """è®¾ç½®é®çç»å® / Setup keyboard bindings"""
        
        @self._kb.add("c-b")
        def _(event):
            """Ctrl+B: åå°åå½åä»»å?/ Background current task"""
            if self.on_ctrl_b:
                result = self.on_ctrl_b()
                if result:
                    event.app.invalidate()
        
        @self._kb.add("c-g")
        def _(event):
            """Ctrl+G: æå¼å¤é¨ç¼è¾å?/ Open external editor"""
            if self.on_ctrl_g:
                result = self.on_ctrl_g()
                if result:
                    event.app.invalidate()
        
        @self._kb.add("c-c")
        def _(event):
            """Ctrl+C: ä¸­æ­æåæ¶?/ Interrupt or cancel"""
            if self.on_ctrl_c:
                self.on_ctrl_c()
            else:
                event.app.exit(exception=KeyboardInterrupt)
    
    @property
    def key_bindings(self) -> KeyBindings:
        """è·å prompt_toolkit KeyBindings å¯¹è±¡ / Get prompt_toolkit KeyBindings object"""
        return self._kb
    
    def add_binding(
        self,
        key: str,
        handler: Callable,
        filter: Optional[Condition] = None,
    ) -> None:
        """
        æ·»å èªå®ä¹ç»å®?/ Add custom binding
        
        Args:
            key: æé®åºå / Key sequence
            handler: å¤çå½æ° / Handler function
            filter: å¯éè¿æ»¤å¨ / Optional filter
        """
        if filter:
            self._kb.add(key, filter=filter)(lambda e: handler())
        else:
            self._kb.add(key)(lambda e: handler())


def create_key_bindings(
    on_ctrl_b: Optional[Callable] = None,
    on_ctrl_g: Optional[Callable] = None,
    on_ctrl_c: Optional[Callable] = None,
) -> KeyBindings:
    """
    åå»ºé®çç»å® / Create key bindings
    
    Args:
        on_ctrl_b: Ctrl+B åè° / Ctrl+B callback
        on_ctrl_g: Ctrl+G åè° / Ctrl+G callback
        on_ctrl_c: Ctrl+C åè° / Ctrl+C callback
        
    Returns:
        KeyBindings å¯¹è±¡ / KeyBindings object
    """
    manager = KeyBindingManager(
        on_ctrl_b=on_ctrl_b,
        on_ctrl_g=on_ctrl_g,
        on_ctrl_c=on_ctrl_c,
    )
    return manager.key_bindings
