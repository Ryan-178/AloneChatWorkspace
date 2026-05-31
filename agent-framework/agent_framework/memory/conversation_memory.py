from typing import Any, Dict, List, Optional

from agent_framework.core.base_memory import BaseMemory, MemoryEntry


class ConversationMemory(BaseMemory):
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._messages: List[MemoryEntry] = []

    def add(self, entry: MemoryEntry) -> None:
        self._messages.append(entry)
        self._truncate()

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry = MemoryEntry(
            content=content,
            metadata={"role": role, **(metadata or {})},
        )
        self.add(entry)

    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        return self._messages[-k:]

    def get_messages(self, limit: Optional[int] = None) -> List[MemoryEntry]:
        msgs = self._messages
        if limit:
            msgs = msgs[-limit:]
        return list(msgs)

    def clear(self) -> None:
        self._messages.clear()

    def _truncate(self) -> None:
        if len(self._messages) > self.window_size:
            self._messages = self._messages[-self.window_size:]

    def summarize(self, llm=None) -> str:
        if not self._messages:
            return ""
        if llm is None:
            lines = []
            for m in self._messages:
                role = m.metadata.get("role", "unknown")
                lines.append(f"{role}: {m.content}")
            return "\n".join(lines)

        from agent_framework.core.base_llm import Message
        history_text = "\n".join(
            f"{m.metadata.get('role', 'unknown')}: {m.content}" for m in self._messages
        )
        prompt = f"Summarize the following conversation concisely:\n\n{history_text}"
        response = llm.chat([Message(role="user", content=prompt)])
        return response.content
