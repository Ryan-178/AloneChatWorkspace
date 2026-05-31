"""
Window Manager
上下文窗口管理
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from collections import deque


@dataclass
class WindowStats:
    """窗口统计"""
    total_context_length: int = 0
    current_window_length: int = 0
    messages_kept: int = 0
    messages_compressed: int = 0
    compression_ratio: float = 1.0


class WindowManager:
    """
    智能上下文窗口管理
    """

    def __init__(
        self,
        max_tokens: int = 128000,
        reserve_response_tokens: int = 8192,
    ):
        self.max_tokens = max_tokens
        self.reserve_response_tokens = reserve_response_tokens
        self._message_history: deque = deque(maxlen=1000)
        self.stats = WindowStats()

    def add_message(self, message: Dict, token_count: int):
        """添加消息"""
        self._message_history.append(
            {"message": message, "tokens": token_count}
        )
        self.stats.total_context_length += token_count
        self.stats.current_window_length += token_count

    def manage_window(self, current_tokens: int) -> List[Dict]:
        """管理窗口大小"""
        available = self.max_tokens - self.reserve_response_tokens - current_tokens

        selected = []
        used = 0

        # 从最新的消息开始选择
        for item in reversed(self._message_history):
            if used + item["tokens"] <= available:
                selected.insert(0, item["message"])
                used += item["tokens"]
            else:
                self.stats.messages_compressed += 1
                break

        self.stats.messages_kept = len(selected)
        self.stats.compression_ratio = used / max(self.stats.current_window_length, 1)

        return selected

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "total_tokens": self.stats.total_context_length,
            "window_tokens": self.stats.current_window_length,
            "messages_kept": self.stats.messages_kept,
            "compression_ratio": self.stats.compression_ratio,
        }
