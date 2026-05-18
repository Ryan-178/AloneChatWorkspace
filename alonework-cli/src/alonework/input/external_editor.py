"""
å¤é¨ç¼è¾å¨éæ?/ External Editor Integration

æ¯æå¨ç³»ç»ç¼è¾å¨ä¸­ç¼è¾æç¤ºè¯ / Supports editing prompts in system editor
æ?Ctrl+G è§¦å / Triggered by Ctrl+G
"""

import os
import platform
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class ExternalEditor:
    """
    å¤é¨ç¼è¾å¨ç®¡çå¨ / External Editor Manager
    
    æ£æµå¹¶å¯å¨ç³»ç»ç¼è¾å¨ç¼è¾åå®?/ Detects and launches system editor to edit content
    """
    
    DEFAULT_EDITORS = {
        "windows": ["code", "notepad++", "notepad"],
        "linux": ["code", "vim", "nano", "gedit"],
        "darwin": ["code", "vim", "nano", "TextEdit"],
    }
    
    def __init__(self, editor: Optional[str] = None):
        """
        åå§åå¤é¨ç¼è¾å¨ / Initialize external editor
        
        Args:
            editor: æå®ç¼è¾å¨å½ä»?/ Specified editor command
        """
        self.platform = platform.system().lower()
        self._editor = editor or self._detect_editor()
        self._temp_dir = Path(tempfile.gettempdir()) / "alonechat_editor"
        self._temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _detect_editor(self) -> str:
        """
        èªå¨æ£æµç³»ç»ç¼è¾å¨ / Auto-detect system editor
        
        ä¼åçº?/ Priority:
        1. $EDITOR ç¯å¢åé / $EDITOR environment variable
        2. $VISUAL ç¯å¢åé / $VISUAL environment variable
        3. å¹³å°é»è®¤ç¼è¾å¨åè¡?/ Platform default editor list
        
        Returns:
            ç¼è¾å¨å½ä»?/ Editor command
        """
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
        if editor:
            return editor
        
        default_editors = self.DEFAULT_EDITORS.get(self.platform, self.DEFAULT_EDITORS["linux"])
        
        for editor_cmd in default_editors:
            if self._is_editor_available(editor_cmd):
                return editor_cmd
        
        if self.platform == "windows":
            return "notepad"
        return "vi"
    
    def _is_editor_available(self, editor: str) -> bool:
        """
        æ£æ¥ç¼è¾å¨æ¯å¦å¯ç¨ / Check if editor is available
        
        Args:
            editor: ç¼è¾å¨å½ä»?/ Editor command
            
        Returns:
            æ¯å¦å¯ç¨ / Whether available
        """
        try:
            if self.platform == "windows":
                result = subprocess.run(
                    ["where", editor],
                    capture_output=True,
                    timeout=5,
                )
            else:
                result = subprocess.run(
                    ["which", editor],
                    capture_output=True,
                    timeout=5,
                )
            return result.returncode == 0
        except Exception:
            return False
    
    @property
    def editor(self) -> str:
        """è·åå½åç¼è¾å?/ Get current editor"""
        return self._editor
    
    def set_editor(self, editor: str) -> bool:
        """
        è®¾ç½®ç¼è¾å?/ Set editor
        
        Args:
            editor: ç¼è¾å¨å½ä»?/ Editor command
            
        Returns:
            æ¯å¦è®¾ç½®æå / Whether set successfully
        """
        if self._is_editor_available(editor):
            self._editor = editor
            return True
        return False
    
    def _create_temp_file(self, content: str = "") -> Path:
        """
        åå»ºä¸´æ¶æä»¶ / Create temporary file
        
        Args:
            content: åå§åå®¹ / Initial content
            
        Returns:
            ä¸´æ¶æä»¶è·¯å¾ / Temporary file path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        temp_file = self._temp_dir / f"prompt_{timestamp}.md"
        temp_file.write_text(content, encoding="utf-8")
        return temp_file
    
    def edit(self, initial_content: str = "") -> Tuple[bool, str]:
        """
        å¨å¤é¨ç¼è¾å¨ä¸­ç¼è¾åå®?/ Edit content in external editor
        
        Args:
            initial_content: åå§åå®¹ / Initial content
            
        Returns:
            (æ¯å¦ä¿å­, ç¼è¾ååå®? / (saved, content)
        """
        temp_file = self._create_temp_file(initial_content)
        original_mtime = temp_file.stat().st_mtime
        
        try:
            if self.platform == "windows":
                subprocess.run(
                    [self._editor, str(temp_file)],
                    check=False,
                )
            else:
                subprocess.run(
                    [self._editor, str(temp_file)],
                    check=False,
                )
            
            new_mtime = temp_file.stat().st_mtime
            saved = new_mtime != original_mtime
            
            content = temp_file.read_text(encoding="utf-8")
            
            return saved, content.strip()
        
        except Exception as e:
            return False, f"ç¼è¾å¨éè¯?/ Editor error: {e}"
        
        finally:
            try:
                temp_file.unlink()
            except Exception:
                pass
    
    def edit_and_wait(self, initial_content: str = "", timeout: int = 300) -> Tuple[bool, str]:
        """
        å¨å¤é¨ç¼è¾å¨ä¸­ç¼è¾åå®¹ï¼å¸¦è¶æ¶ï¼ / Edit content in external editor with timeout
        
        Args:
            initial_content: åå§åå®¹ / Initial content
            timeout: è¶æ¶ç§æ° / Timeout in seconds
            
        Returns:
            (æ¯å¦ä¿å­, ç¼è¾ååå®? / (saved, content)
        """
        temp_file = self._create_temp_file(initial_content)
        original_mtime = temp_file.stat().st_mtime
        
        try:
            if self.platform == "windows":
                proc = subprocess.Popen(
                    [self._editor, str(temp_file)],
                )
            else:
                proc = subprocess.Popen(
                    [self._editor, str(temp_file)],
                )
            
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                return False, "ç¼è¾è¶æ¶ / Edit timeout"
            
            new_mtime = temp_file.stat().st_mtime
            saved = new_mtime != original_mtime
            
            content = temp_file.read_text(encoding="utf-8")
            
            return saved, content.strip()
        
        except Exception as e:
            return False, f"ç¼è¾å¨éè¯?/ Editor error: {e}"
        
        finally:
            try:
                temp_file.unlink()
            except Exception:
                pass
    
    def get_editor_info(self) -> dict:
        """
        è·åç¼è¾å¨ä¿¡æ?/ Get editor info
        
        Returns:
            ç¼è¾å¨ä¿¡æ¯å­å?/ Editor info dict
        """
        return {
            "editor": self._editor,
            "platform": self.platform,
            "available": self._is_editor_available(self._editor),
            "temp_dir": str(self._temp_dir),
        }
