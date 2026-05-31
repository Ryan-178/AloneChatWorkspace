"""
LSP (Language Server Protocol) 集成模块
LSP Integration Module

提供实时代码诊断、补全、跳转等功能
Provides real-time code diagnostics, completion, navigation, etc.
"""

from .types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
    Location,
    DiagnosticRelatedInformation,
)
from .client import LSPClient
from .manager import LSPManager

__all__ = [
    "Diagnostic",
    "DiagnosticSeverity",
    "Position",
    "Range",
    "Location",
    "DiagnosticRelatedInformation",
    "LSPClient",
    "LSPManager",
]
