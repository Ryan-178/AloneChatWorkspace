"""
Error Fixer Module - 错误自动修复模块
Auto Error Fixing Module
"""
from alonechat.services.error_fixer.fixer import (
    ErrorFixer,
    ErrorDiagnostic,
    FixStrategy,
    ErrorType,
    ErrorSeverity,
    DiagnosticError,
    FixSuggestion,
    FixResult,
    ErrorPattern,
)

__all__ = [
    "ErrorFixer",
    "ErrorDiagnostic",
    "FixStrategy",
    "ErrorType",
    "ErrorSeverity",
    "DiagnosticError",
    "FixSuggestion",
    "FixResult",
    "ErrorPattern",
]
