"""
国际化模块 / Locale Module

多语言支持
Multi-language support
"""

from .i18n import (
    I18n,
    LocaleInfo,
    SUPPORTED_LOCALES,
    get_i18n,
    t,
)

__all__ = [
    "I18n",
    "LocaleInfo",
    "SUPPORTED_LOCALES",
    "get_i18n",
    "t",
]
