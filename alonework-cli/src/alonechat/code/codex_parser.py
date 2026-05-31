"""
CodexParser - 解析 Codex CLI 的 JSON 流式输出
Parses Codex CLI JSON streaming output into structured events.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CodexEventType(str, Enum):
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FILE_CHANGE = "file_change"
    ERROR = "error"
    COMPLETED = "completed"
    SESSION_ID = "session_id"
    TOKEN_USAGE = "token_usage"
    THINKING = "thinking"
    PLAN = "plan"
    APPROVAL_REQUEST = "approval_request"
    UNKNOWN = "unknown"


@dataclass
class ParsedEvent:
    event_type: CodexEventType
    content: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    file_path: Optional[str] = None
    diff: Optional[str] = None
    error_type: Optional[str] = None
    token_count: Optional[Dict[str, int]] = None


class CodexStreamParser:
    """解析 Codex CLI 的流式 JSON 输出"""

    def __init__(self):
        self._buffer: str = ""
        self._events: List[ParsedEvent] = []
        self._session_id: Optional[str] = None
        self._total_tokens: Dict[str, int] = {}

    def feed(self, data: str) -> List[ParsedEvent]:
        self._buffer += data
        events = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            parsed = self._parse_line(line)
            if parsed:
                events.append(parsed)
                self._events.append(parsed)
        return events

    def flush(self) -> List[ParsedEvent]:
        events = []
        if self._buffer.strip():
            parsed = self._parse_line(self._buffer.strip())
            if parsed:
                events.append(parsed)
                self._events.append(parsed)
        self._buffer = ""
        return events

    def _parse_line(self, line: str) -> Optional[ParsedEvent]:
        try:
            data = json.loads(line)
            return self._parse_json(data)
        except json.JSONDecodeError:
            return ParsedEvent(
                event_type=CodexEventType.MESSAGE,
                content=line,
                raw_data={"raw": line},
            )

    def _parse_json(self, data: Dict[str, Any]) -> ParsedEvent:
        event_type_str = data.get("type", "unknown")
        try:
            event_type = CodexEventType(event_type_str)
        except ValueError:
            event_type = CodexEventType.UNKNOWN

        if event_type == CodexEventType.SESSION_ID:
            self._session_id = data.get("session_id")
            return ParsedEvent(
                event_type=event_type,
                content=self._session_id or "",
                raw_data=data,
            )

        if event_type == CodexEventType.TOKEN_USAGE:
            usage = data.get("usage", {})
            self._total_tokens = usage
            return ParsedEvent(
                event_type=event_type,
                content="",
                raw_data=data,
                token_count=usage,
            )

        if event_type == CodexEventType.TOOL_CALL:
            return ParsedEvent(
                event_type=event_type,
                content=data.get("content", ""),
                raw_data=data,
                tool_name=data.get("tool_name") or data.get("name"),
                tool_args=data.get("arguments") or data.get("args"),
            )

        if event_type == CodexEventType.TOOL_RESULT:
            return ParsedEvent(
                event_type=event_type,
                content=data.get("content", ""),
                raw_data=data,
                tool_name=data.get("tool_name") or data.get("name"),
                tool_result=data.get("result") or data.get("content"),
            )

        if event_type == CodexEventType.FILE_CHANGE:
            return ParsedEvent(
                event_type=event_type,
                content=data.get("content", ""),
                raw_data=data,
                file_path=data.get("path") or data.get("file"),
                diff=data.get("diff"),
            )

        if event_type == CodexEventType.ERROR:
            return ParsedEvent(
                event_type=event_type,
                content=data.get("message") or data.get("content", ""),
                raw_data=data,
                error_type=data.get("error_type"),
            )

        return ParsedEvent(
            event_type=event_type,
            content=data.get("content", json.dumps(data)),
            raw_data=data,
        )

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def total_tokens(self) -> Dict[str, int]:
        return self._total_tokens

    @property
    def all_events(self) -> List[ParsedEvent]:
        return self._events.copy()

    def get_tool_calls(self) -> List[ParsedEvent]:
        return [e for e in self._events if e.event_type == CodexEventType.TOOL_CALL]

    def get_file_changes(self) -> List[ParsedEvent]:
        return [e for e in self._events if e.event_type == CodexEventType.FILE_CHANGE]

    def get_errors(self) -> List[ParsedEvent]:
        return [e for e in self._events if e.event_type == CodexEventType.ERROR]

    def get_messages(self) -> List[str]:
        return [
            e.content
            for e in self._events
            if e.event_type == CodexEventType.MESSAGE and e.content
        ]

    def get_full_output(self) -> str:
        messages = []
        for event in self._events:
            if event.event_type == CodexEventType.MESSAGE and event.content:
                messages.append(event.content)
            elif event.event_type == CodexEventType.TOOL_CALL:
                tool_info = f"[调用工具 {event.tool_name}]"
                if event.tool_args:
                    tool_info += f" {json.dumps(event.tool_args, ensure_ascii=False)}"
                messages.append(tool_info)
            elif event.event_type == CodexEventType.TOOL_RESULT:
                messages.append(f"[工具结果] {event.content}")
            elif event.event_type == CodexEventType.ERROR:
                messages.append(f"[错误] {event.content}")
        return "\n".join(messages)

    def reset(self) -> None:
        self._buffer = ""
        self._events.clear()
        self._session_id = None
        self._total_tokens = {}
