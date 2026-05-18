"""
上下文管理模块

负责：
- 对话历史管理
- 上下文窗口控制
- 上下文压缩
"""

from typing import Any
from collections import deque


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_tokens: int = 128000):
        """
        初始化上下文管理器
        
        Args:
            max_tokens: 最大token数
        """
        self.max_tokens = max_tokens
        self.messages: deque[dict[str, str]] = deque()
        self.current_tokens = 0
    
    def add_message(self, role: str, content: str) -> None:
        """
        添加消息
        
        Args:
            role: 角色 (user/assistant)
            content: 内容
        """
        message = {"role": role, "content": content}
        message_tokens = self._estimate_tokens(content)
        
        while self.current_tokens + message_tokens > self.max_tokens and self.messages:
            removed = self.messages.popleft()
            self.current_tokens -= self._estimate_tokens(removed["content"])
        
        self.messages.append(message)
        self.current_tokens += message_tokens
    
    def get_messages(self) -> list[dict[str, str]]:
        """
        获取所有消息
        
        Returns:
            消息列表
        """
        return list(self.messages)
    
    def clear(self) -> None:
        """清空上下文"""
        self.messages.clear()
        self.current_tokens = 0
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算token数
        
        简单估算：中文约1.5字符/token，英文约4字符/token
        
        Args:
            text: 文本
            
        Returns:
            token数
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return int(chinese_chars / 1.5 + other_chars / 4)
