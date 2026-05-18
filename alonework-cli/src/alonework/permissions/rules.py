"""
æéè§å / Permission Rules

å®ä¹æéè§ååæ¨¡å¼?/ Defines permission rules and modes
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PermissionMode(Enum):
    """æéæ¨¡å¼ / Permission mode"""
    ACCEPT = "accept"       # èªå¨æ¥åææ?/ Accept all
    PLAN = "plan"           # è®¡åæ¨¡å¼ / Plan mode
    REVIEW = "review"       # å®¡æ¥æ¨¡å¼ / Review mode
    DEFAULT = "default"     # é»è®¤æ¨¡å¼ï¼éä¸ªæç¤ºï¼? Default mode (prompt each)


class PermissionAction(Enum):
    """æéå¨ä½ / Permission action"""
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"


@dataclass
class PermissionRule:
    """
    æéè§å / Permission rule
    
    å®ä¹å¯¹ç¹å®å·¥å·çæé / Defines permission for specific tool
    """
    tool: str               # å·¥å·åç§°ææ¨¡å¼?/ Tool name or pattern
    action: PermissionAction  # æéå¨ä½ / Permission action
    scope: Optional[str] = None  # ä½ç¨åï¼å¦ç¹å®å½ä»¤ï¼/ Scope (e.g., specific command)
    
    def matches(self, tool_name: str, command: Optional[str] = None) -> bool:
        """æ£æ¥æ¯å¦å¹é?/ Check if matches"""
        if self.tool == "*":
            return True
        
        if self.tool.endswith("*"):
            prefix = self.tool[:-1]
            if tool_name.startswith(prefix):
                return True
        
        if self.tool == tool_name:
            if self.scope is None:
                return True
            if command and self.scope in command:
                return True
        
        return False


DEFAULT_ALLOWED_TOOLS: list[str] = [
    "Read",
    "Glob",
    "Grep",
    "LS",
]

DEFAULT_DENIED_TOOLS: list[str] = []

TOOL_DESCRIPTIONS: dict[str, str] = {
    "Read": "è¯»åæä»¶ / Read files",
    "Write": "åå¥æä»¶ / Write files",
    "Edit": "ç¼è¾æä»¶ / Edit files",
    "Delete": "å é¤æä»¶ / Delete files",
    "Bash": "æ§è¡å½ä»¤ / Execute commands",
    "Glob": "æç´¢æä»¶ / Search files",
    "Grep": "æç´¢åå®¹ / Search content",
    "LS": "ååºç®å½ / List directory",
    "WebSearch": "ç½ç»æç´¢ / Web search",
    "WebFetch": "è·åç½é¡µ / Fetch web page",
}
