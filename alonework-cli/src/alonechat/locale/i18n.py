"""
国际化模块 / Internationalization Module

支持 en/zh-Hans/ja/pt-BR 等多语言
Supports en/zh-Hans/ja/pt-BR and more languages
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class LocaleInfo:
    """
    语言区域信息 / Locale Information
    """
    code: str
    name: str
    native_name: str
    rtl: bool = False


SUPPORTED_LOCALES = {
    "en": LocaleInfo("en", "English", "English"),
    "zh-Hans": LocaleInfo("zh-Hans", "Chinese (Simplified)", "简体中文"),
    "zh-Hant": LocaleInfo("zh-Hant", "Chinese (Traditional)", "繁體中文"),
    "ja": LocaleInfo("ja", "Japanese", "日本語"),
    "ko": LocaleInfo("ko", "Korean", "한국어"),
    "pt-BR": LocaleInfo("pt-BR", "Portuguese (Brazil)", "Português (Brasil)"),
    "es": LocaleInfo("es", "Spanish", "Español"),
    "fr": LocaleInfo("fr", "French", "Français"),
    "de": LocaleInfo("de", "German", "Deutsch"),
    "ru": LocaleInfo("ru", "Russian", "Русский"),
}


class I18n:
    """
    国际化管理器 / Internationalization Manager

    功能：
    - 多语言翻译
    - 语言自动检测
    - 翻译键回退
    - 插值支持

    Features:
    - Multi-language translation
    - Auto language detection
    - Translation key fallback
    - Interpolation support
    """

    def __init__(
        self,
        locale: str = "en",
        fallback_locale: str = "en",
        translations_dir: Optional[str] = None,
    ):
        self._locale = locale
        self._fallback_locale = fallback_locale
        self._translations_dir = Path(translations_dir) if translations_dir else None
        self._translations: Dict[str, Dict[str, str]] = {}
        self._loaded = False

    async def initialize(self) -> None:
        """
        初始化i18n / Initialize i18n
        """
        if self._translations_dir is None:
            self._translations_dir = Path(__file__).parent.parent / "configs" / "locales"

        self._translations = {}

        if self._translations_dir.exists():
            for locale_file in self._translations_dir.glob("*.json"):
                locale_code = locale_file.stem
                try:
                    with open(locale_file, "r", encoding="utf-8") as f:
                        self._translations[locale_code] = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load translations from {locale_file}: {e}")

            for locale_file in self._translations_dir.glob("*.yaml"):
                locale_code = locale_file.stem
                try:
                    with open(locale_file, "r", encoding="utf-8") as f:
                        self._translations[locale_code] = yaml.safe_load(f) or {}
                except Exception as e:
                    logger.warning(f"Failed to load translations from {locale_file}: {e}")

        if not self._translations:
            logger.warning("No translations loaded, using fallback mode")
            self._translations = {"en": {}}

        self._loaded = True
        logger.info(f"I18n initialized with locale: {self._locale}, loaded {len(self._translations)} locales")

    @property
    def locale(self) -> str:
        """获取当前语言 / Get current locale"""
        return self._locale

    @locale.setter
    def locale(self, value: str) -> None:
        """设置当前语言 / Set current locale"""
        if value in SUPPORTED_LOCALES:
            self._locale = value
        else:
            logger.warning(f"Unsupported locale: {value}, keeping {self._locale}")

    def t(
        self,
        key: str,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        翻译 / Translate

        Args:
            key: 翻译键
            default: 默认值
            **kwargs: 插值参数

        Returns:
            翻译后的字符串
        """
        if not self._loaded:
            return default or key

        translations = self._translations.get(self._locale, {})
        text = translations.get(key)

        if text is None:
            fallback = self._translations.get(self._fallback_locale, {})
            text = fallback.get(key)

        if text is None:
            return default or key

        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def get_supported_locales(self) -> Dict[str, LocaleInfo]:
        """
        获取支持的语言列表 / Get supported locales
        """
        return SUPPORTED_LOCALES.copy()

    def get_locale_info(self, locale: Optional[str] = None) -> Optional[LocaleInfo]:
        """
        获取语言信息 / Get locale info
        """
        code = locale or self._locale
        return SUPPORTED_LOCALES.get(code)

    def is_rtl(self, locale: Optional[str] = None) -> bool:
        """
        检查是否是RTL语言 / Check if is RTL locale
        """
        info = self.get_locale_info(locale)
        return info.rtl if info else False

    def format_number(self, number: float, locale: Optional[str] = None) -> str:
        """
        格式化数字 / Format number
        """
        loc = locale or self._locale

        if loc.startswith("zh") or loc == "ja" or loc == "ko":
            return f"{number:,.0f}"
        elif loc == "pt-BR" or loc.startswith("es") or loc == "fr" or loc == "de":
            return f"{number:,.0f}".replace(",", " ").replace(".", ",")
        else:
            return f"{number:,.0f}"

    def format_currency(
        self,
        amount: float,
        currency: str = "USD",
        locale: Optional[str] = None,
    ) -> str:
        """
        格式化货币 / Format currency
        """
        loc = locale or self._locale

        if loc.startswith("zh"):
            return f"¥{amount:.2f}"
        elif loc == "ja":
            return f"¥{amount:.0f}"
        elif loc == "pt-BR":
            return f"R${amount:.2f}".replace(".", ",")
        elif loc.startswith("es"):
            return f"{amount:.2f} €".replace(".", ",")
        elif loc == "de":
            return f"{amount:.2f} €".replace(".", ",")
        else:
            return f"${amount:.2f}"

    def format_datetime(
        self,
        dt: Any,
        format: str = "medium",
        locale: Optional[str] = None,
    ) -> str:
        """
        格式化日期时间 / Format datetime
        """
        loc = locale or self._locale

        if hasattr(dt, "strftime"):
            if loc.startswith("zh"):
                if format == "short":
                    return dt.strftime("%m/%d %H:%M")
                elif format == "medium":
                    return dt.strftime("%Y年%m月%d日 %H:%M")
                else:
                    return dt.strftime("%Y年%m月%d日 %H:%M:%S")
            elif loc == "ja":
                if format == "short":
                    return dt.strftime("%m/%d %H:%M")
                elif format == "medium":
                    return dt.strftime("%Y年%m月%d日 %H:%M")
                else:
                    return dt.strftime("%Y年%m月%d日 %H:%M:%S")
            else:
                if format == "short":
                    return dt.strftime("%m/%d %H:%M")
                elif format == "medium":
                    return dt.strftime("%b %d, %Y %H:%M")
                else:
                    return dt.strftime("%B %d, %Y %H:%M:%S")

        return str(dt)

    def get_available_locales(self) -> List[str]:
        """
        获取已加载的语言列表 / Get loaded locales
        """
        return list(self._translations.keys())


_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """
    获取全局i18n实例 / Get global i18n instance
    """
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n


def t(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """
    快捷翻译函数 / Quick translation function
    """
    return get_i18n().t(key, default, **kwargs)
