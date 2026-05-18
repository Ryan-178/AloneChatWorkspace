"""
中文模块 / Chinese Module

提供 / Provides:
- 中文NLP / Chinese NLP
- 代码风格 / Code style
- 注释生成 / Comment generation
"""

from alonework.chinese.nlp import (
    ChineseTokenizer,
    EntityRecognizer,
    SemanticAnalyzer,
    ChineseNLP,
    Entity,
    SegmentedText,
    chinese_config,
)
from alonework.chinese.code_style import (
    NamingAdvisor,
    CommentGenerator,
    ChineseCodeStyle,
    StyleSuggestion,
    style_config,
)

__all__ = [
    "ChineseTokenizer",
    "EntityRecognizer",
    "SemanticAnalyzer",
    "ChineseNLP",
    "Entity",
    "SegmentedText",
    "chinese_config",
    "NamingAdvisor",
    "CommentGenerator",
    "ChineseCodeStyle",
    "StyleSuggestion",
    "style_config",
]
