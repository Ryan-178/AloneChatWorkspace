"""
åå°æ§è¡ç³»ç» / Background Execution System

æä¾åå°ä»»å¡ç®¡çè½å / Provides background task management:
- åå°ä»»å¡èªå¨æ£æµååå°å?/ Auto-detect and background long-running tasks
- åå°æºè½ä½æ¯æ?/ Background agent support
- ä»»å¡ç¶æè¿½è¸?/ Task status tracking
"""

from alonework.background.manager import BackgroundManager
from alonework.background.task import BackgroundTask, TaskStatus
from alonework.background.agent_runner import BackgroundAgentRunner

__all__ = [
    "BackgroundManager",
    "BackgroundTask",
    "TaskStatus",
    "BackgroundAgentRunner",
]
