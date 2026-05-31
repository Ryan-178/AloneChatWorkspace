"""
LSP类型定义 / LSP Type Definitions

基于LSP 3.16规范
Based on LSP 3.16 specification
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Position(BaseModel):
    """
    文档中的位置 / Position in a document
    """
    line: int
    character: int

    def to_lsp(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}

    @classmethod
    def from_lsp(cls, data: Dict[str, int]) -> "Position":
        return cls(line=data["line"], character=data["character"])


class Range(BaseModel):
    """
    文档中的范围 / Range in a document
    """
    start: Position
    end: Position

    def to_lsp(self) -> Dict[str, Any]:
        return {
            "start": self.start.to_lsp(),
            "end": self.end.to_lsp(),
        }

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "Range":
        return cls(
            start=Position.from_lsp(data["start"]),
            end=Position.from_lsp(data["end"]),
        )


class Location(BaseModel):
    """
    位置引用 / Location reference
    """
    uri: str
    range: Range

    def to_lsp(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "range": self.range.to_lsp(),
        }

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "Location":
        return cls(
            uri=data["uri"],
            range=Range.from_lsp(data["range"]),
        )


class DiagnosticSeverity(int, Enum):
    """
    诊断严重程度 / Diagnostic severity
    """
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4

    def to_str(self) -> str:
        mapping = {
            DiagnosticSeverity.ERROR: "error",
            DiagnosticSeverity.WARNING: "warning",
            DiagnosticSeverity.INFORMATION: "info",
            DiagnosticSeverity.HINT: "hint",
        }
        return mapping.get(self, "info")


class DiagnosticRelatedInformation(BaseModel):
    """
    诊断相关信息 / Diagnostic related information
    """
    location: Location
    message: str

    def to_lsp(self) -> Dict[str, Any]:
        return {
            "location": self.location.to_lsp(),
            "message": self.message,
        }

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "DiagnosticRelatedInformation":
        return cls(
            location=Location.from_lsp(data["location"]),
            message=data["message"],
        )


class Diagnostic(BaseModel):
    """
    诊断结果 / Diagnostic result
    """
    range: Range
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None
    code_description: Optional[str] = None
    source: Optional[str] = None
    message: str
    tags: List[int] = []
    related_information: List[DiagnosticRelatedInformation] = []
    data: Optional[Any] = None

    def to_lsp(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "range": self.range.to_lsp(),
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.code is not None:
            result["code"] = self.code
        if self.source is not None:
            result["source"] = self.source
        if self.tags:
            result["tags"] = self.tags
        if self.related_information:
            result["relatedInformation"] = [
                info.to_lsp() for info in self.related_information
            ]
        return result

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "Diagnostic":
        severity_value = data.get("severity", 1)
        severity = DiagnosticSeverity(severity_value)
        return cls(
            range=Range.from_lsp(data["range"]),
            severity=severity,
            code=data.get("code"),
            source=data.get("source"),
            message=data["message"],
            tags=data.get("tags", []),
            related_information=[
                DiagnosticRelatedInformation.from_lsp(info)
                for info in data.get("relatedInformation", [])
            ],
        )

    def is_error(self) -> bool:
        return self.severity == DiagnosticSeverity.ERROR

    def is_warning(self) -> bool:
        return self.severity == DiagnosticSeverity.WARNING

    def to_display_string(self) -> str:
        severity_str = self.severity.to_str()
        source_str = f"[{self.source}] " if self.source else ""
        code_str = f"({self.code}) " if self.code else ""
        return f"{severity_str.upper()}: {source_str}{code_str}{self.message}"


class TextDocumentItem(BaseModel):
    """
    文本文档项 / Text document item
    """
    uri: str
    language_id: str
    version: int
    text: str


class TextDocumentIdentifier(BaseModel):
    """
    文本文档标识符 / Text document identifier
    """
    uri: str


class VersionedTextDocumentIdentifier(BaseModel):
    """
    带版本的文本文档标识符 / Versioned text document identifier
    """
    uri: str
    version: int


class TextDocumentContentChangeEvent(BaseModel):
    """
    文档内容变更事件 / Text document content change event
    """
    range: Optional[Range] = None
    range_length: Optional[int] = None
    text: str


class PublishDiagnosticsParams(BaseModel):
    """
    发布诊断参数 / Publish diagnostics params
    """
    uri: str
    diagnostics: List[Diagnostic]
    version: Optional[int] = None

    @classmethod
    def from_lsp(cls, data: Dict[str, Any]) -> "PublishDiagnosticsParams":
        return cls(
            uri=data["uri"],
            diagnostics=[
                Diagnostic.from_lsp(d) for d in data.get("diagnostics", [])
            ],
            version=data.get("version"),
        )
