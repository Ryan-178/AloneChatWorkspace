"""
Data Protection Manager
数据保护管理器 - PII和敏感信息保护
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PIIPattern:
    """PII模式定义"""
    name: str
    pattern: str
    mask_format: str = "***REDACTED***"


class DataProtectionManager:
    """
    数据保护管理器
    用于识别和处理PII（个人身份信息）和敏感数据
    """

    # 预定义的PII模式
    DEFAULT_PII_PATTERNS = [
        PIIPattern(
            name="email",
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            mask_format="***REDACTED_EMAIL***"
        ),
        PIIPattern(
            name="phone",
            pattern=r"\b(?:\+\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
            mask_format="***REDACTED_PHONE***"
        ),
        PIIPattern(
            name="ssn",
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",
            mask_format="***REDACTED_SSN***"
        ),
        PIIPattern(
            name="ip_address",
            pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            mask_format="***REDACTED_IP***"
        ),
        PIIPattern(
            name="credit_card",
            # 使用更安全的正则，避免灾难性回溯
            # 匹配 13-16 位数字，可选的空格或横线分隔
            pattern=r"\b(?:\d{4}[- ]?){3}\d{1,4}\b|\b\d{13,16}\b",
            mask_format="***REDACTED_CC***"
        ),
    ]

    def __init__(self, custom_patterns: List[PIIPattern] = None):
        self.patterns = self.DEFAULT_PII_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        
        self._compiled_patterns = {
            p.name: re.compile(p.pattern) for p in self.patterns
        }

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """检测文本中的PII"""
        detections = []
        
        for pattern in self.patterns:
            matches = list(self._compiled_patterns[pattern.name].finditer(text))
            for match in matches:
                detections.append({
                    "type": pattern.name,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        
        return detections

    def mask_pii(self, text: str) -> str:
        """遮蔽文本中的PII"""
        masked = text
        
        for pattern in self.patterns:
            masked = self._compiled_patterns[pattern.name].sub(
                pattern.mask_format, masked
            )
        
        return masked

    def is_sensitive(self, text: str) -> bool:
        """检查文本是否包含敏感信息"""
        return len(self.detect_pii(text)) > 0

    def sanitize_output(self, text: str) -> str:
        """输出内容消毒，移除敏感信息"""
        return self.mask_pii(text)

    def add_custom_pattern(self, pattern: PIIPattern):
        """添加自定义PII模式"""
        self.patterns.append(pattern)
        self._compiled_patterns[pattern.name] = re.compile(pattern.pattern)
