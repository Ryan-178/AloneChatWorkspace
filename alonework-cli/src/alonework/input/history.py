"""
å½ä»¤åå²ç®¡ç / Command History Management

ç®¡ç Bash å½ä»¤åå²ï¼æ¯ææç´¢åè¡¥å¨ / Manages bash command history with search and completion
æ°æ®å­å¨å?YAML æä»¶ä¸?/ Data stored in YAML file
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml


class CommandHistory:
    """
    å½ä»¤åå²ç®¡çå?/ Command History Manager
    
    å­å¨åç®¡çç¨æ·è¾å¥çå½ä»¤åå² / Stores and manages user input command history
    ä½¿ç¨ YAML æä»¶æä¹å?/ Persisted using YAML file
    """
    
    DEFAULT_HISTORY_FILE = Path.home() / ".alonechat" / "history.yaml"
    MAX_HISTORY_SIZE = 1000
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        åå§åå½ä»¤åå²ç®¡çå¨ / Initialize command history manager
        
        Args:
            history_file: åå²æä»¶è·¯å¾ / Path to history file
        """
        self.history_file = history_file or self.DEFAULT_HISTORY_FILE
        self._ensure_history_file()
        self._history: List[Dict[str, Any]] = self._load_history()
    
    def _ensure_history_file(self) -> None:
        """ç¡®ä¿åå²æä»¶å­å¨ / Ensure history file exists"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save_history([])
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """
        ä»?YAML æä»¶å è½½åå² / Load history from YAML file
        
        Returns:
            åå²è®°å½åè¡¨ / List of history records
        """
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("commands", [])
        except Exception:
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """
        ä¿å­åå²å?YAML æä»¶ / Save history to YAML file
        
        Args:
            history: åå²è®°å½åè¡¨ / List of history records
        """
        try:
            data = {
                "version": 1,
                "commands": history,
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.history_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception:
            pass
    
    def add(self, command: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        æ·»å å½ä»¤å°åå?/ Add command to history
        
        Args:
            command: å½ä»¤å­ç¬¦ä¸?/ Command string
            metadata: å¯éåæ°æ® / Optional metadata
        """
        if not command.strip():
            return
        
        entry = {
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        self._history.append(entry)
        
        if len(self._history) > self.MAX_HISTORY_SIZE:
            self._history = self._history[-self.MAX_HISTORY_SIZE:]
        
        self._save_history(self._history)
    
    def search(self, prefix: str, limit: int = 10) -> List[str]:
        """
        æç´¢åå²å½ä»¤ / Search history commands
        
        Args:
            prefix: æç´¢åç¼ / Search prefix
            limit: è¿åæ°ééå¶ / Return limit
            
        Returns:
            å¹éçå½ä»¤åè¡?/ List of matching commands
        """
        if not prefix:
            return [entry["command"] for entry in self._history[-limit:]]
        
        prefix_lower = prefix.lower()
        matches = []
        
        for entry in reversed(self._history):
            if entry["command"].lower().startswith(prefix_lower):
                if entry["command"] not in matches:
                    matches.append(entry["command"])
                if len(matches) >= limit:
                    break
        
        return matches
    
    def search_fuzzy(self, query: str, limit: int = 10) -> List[str]:
        """
        æ¨¡ç³æç´¢åå²å½ä»¤ / Fuzzy search history commands
        
        Args:
            query: æç´¢æ¥è¯¢ / Search query
            limit: è¿åæ°ééå¶ / Return limit
            
        Returns:
            å¹éçå½ä»¤åè¡?/ List of matching commands
        """
        if not query:
            return [entry["command"] for entry in self._history[-limit:]]
        
        query_lower = query.lower()
        matches = []
        
        for entry in reversed(self._history):
            if query_lower in entry["command"].lower():
                if entry["command"] not in matches:
                    matches.append(entry["command"])
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_all(self) -> List[str]:
        """
        è·åææåå²å½ä»?/ Get all history commands
        
        Returns:
            ææå½ä»¤åè¡?/ List of all commands
        """
        return [entry["command"] for entry in self._history]
    
    def get_recent(self, count: int = 10) -> List[str]:
        """
        è·åæè¿çå½ä»¤ / Get recent commands
        
        Args:
            count: æ°é / Count
            
        Returns:
            æè¿çå½ä»¤åè¡¨ / List of recent commands
        """
        return [entry["command"] for entry in self._history[-count:]]
    
    def clear(self) -> None:
        """æ¸ç©ºåå² / Clear history"""
        self._history = []
        self._save_history([])
    
    def get_by_index(self, index: int) -> Optional[str]:
        """
        éè¿ç´¢å¼è·åå½ä»¤ï¼æ¯æè´ç´¢å¼ï¼?/ Get command by index (supports negative index)
        
        ç±»ä¼¼ Bash ç?!n è¯­æ³ / Similar to Bash !n syntax
        
        Args:
            index: å½ä»¤ç´¢å¼ / Command index
            
        Returns:
            å½ä»¤å­ç¬¦ä¸²æ None / Command string or None
        """
        try:
            if index > 0:
                return self._history[index - 1]["command"]
            else:
                return self._history[index]["command"]
        except IndexError:
            return None
    
    def __len__(self) -> int:
        """è¿ååå²è®°å½æ°é / Return history count"""
        return len(self._history)
    
    def __iter__(self):
        """è¿­ä»£åå²å½ä»¤ / Iterate over history commands"""
        return iter(entry["command"] for entry in self._history)
