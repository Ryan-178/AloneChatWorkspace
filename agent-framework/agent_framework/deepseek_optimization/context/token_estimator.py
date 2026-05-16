"""
Token Estimator
精确Token估算器 - 支持多种编码方案和内容类型
"""
import re
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field


class EncodingType(str, Enum):
    CL100K_BASE = "cl100k_base"
    P50K_BASE = "p50k_base"
    P50K_EDIT = "p50k_edit"
    R50K_BASE = "r50k_base"


class EstimationMode(str, Enum):
    FAST = "fast"
    ACCURATE = "accurate"
    AUTO = "auto"


@dataclass
class TokenEstimate:
    token_count: int
    char_count: int
    estimation_mode: EstimationMode
    encoding_type: Optional[EncodingType] = None
    content_type: str = "text"
    confidence: float = 1.0
    breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class TokenBudget:
    total_budget: int
    used: int = 0
    reserved: int = 0
    
    @property
    def available(self) -> int:
        return max(0, self.total_budget - self.used - self.reserved)
    
    @property
    def usage_ratio(self) -> float:
        if self.total_budget == 0:
            return 0.0
        return (self.used + self.reserved) / self.total_budget


class TokenEstimator:
    """
    精确Token估算器
    支持tiktoken精确计算和快速估算两种模式
    """
    
    MODEL_TOKEN_LIMITS = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "gpt-3.5-turbo": 16385,
        "deepseek-v3": 64000,
        "deepseek-v4": 1000000,
        "deepseek-v4-flash": 1000000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        "claude-3-haiku": 200000,
    }
    
    DEFAULT_ENCODING = EncodingType.CL100K_BASE
    
    def __init__(
        self,
        mode: EstimationMode = EstimationMode.AUTO,
        encoding: Optional[EncodingType] = None,
        fallback_ratio: float = 0.25,
    ):
        self.mode = mode
        self.encoding = encoding or self.DEFAULT_ENCODING
        self.fallback_ratio = fallback_ratio
        
        self._tiktoken_encoder = None
        self._tiktoken_available = self._check_tiktoken()
        
        if self.mode == EstimationMode.AUTO:
            self._effective_mode = EstimationMode.ACCURATE if self._tiktoken_available else EstimationMode.FAST
        else:
            self._effective_mode = self.mode
    
    def _check_tiktoken(self) -> bool:
        try:
            import tiktoken
            return True
        except ImportError:
            return False
    
    def _get_encoder(self):
        if self._tiktoken_encoder is None and self._tiktoken_available:
            import tiktoken
            self._tiktoken_encoder = tiktoken.get_encoding(self.encoding.value)
        return self._tiktoken_encoder
    
    def estimate(
        self,
        content: Union[str, List[str], Dict[str, Any]],
        content_type: Optional[str] = None
    ) -> TokenEstimate:
        if isinstance(content, dict):
            return self._estimate_message(content)
        elif isinstance(content, list):
            return self._estimate_messages(content)
        else:
            return self._estimate_text(content, content_type)
    
    def _estimate_text(
        self,
        text: str,
        content_type: Optional[str] = None
    ) -> TokenEstimate:
        if not text:
            return TokenEstimate(
                token_count=0,
                char_count=0,
                estimation_mode=self._effective_mode,
                content_type=content_type or "empty"
            )
        
        detected_type = content_type or self._detect_content_type(text)
        
        if self._effective_mode == EstimationMode.ACCURATE:
            return self._accurate_estimate(text, detected_type)
        else:
            return self._fast_estimate(text, detected_type)
    
    def _accurate_estimate(self, text: str, content_type: str) -> TokenEstimate:
        encoder = self._get_encoder()
        
        if encoder is not None:
            tokens = encoder.encode(text)
            token_count = len(tokens)
            confidence = 1.0
        else:
            token_count, confidence = self._enhanced_estimate(text, content_type)
        
        breakdown = self._get_breakdown(text, content_type)
        
        return TokenEstimate(
            token_count=token_count,
            char_count=len(text),
            estimation_mode=EstimationMode.ACCURATE,
            encoding_type=self.encoding,
            content_type=content_type,
            confidence=confidence,
            breakdown=breakdown
        )
    
    def _fast_estimate(self, text: str, content_type: str) -> TokenEstimate:
        token_count, confidence = self._enhanced_estimate(text, content_type)
        breakdown = self._get_breakdown(text, content_type)
        
        return TokenEstimate(
            token_count=token_count,
            char_count=len(text),
            estimation_mode=EstimationMode.FAST,
            content_type=content_type,
            confidence=confidence,
            breakdown=breakdown
        )
    
    def _enhanced_estimate(self, text: str, content_type: str) -> tuple:
        base_ratio = self._get_base_ratio(content_type)
        
        char_count = len(text)
        base_estimate = int(char_count * base_ratio)
        
        code_blocks = len(re.findall(r'```[\s\S]*?```', text))
        inline_code = len(re.findall(r'`[^`]+`', text))
        links = len(re.findall(r'https?://\S+', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        adjustments = 0
        adjustments += code_blocks * 10
        adjustments += inline_code * 2
        adjustments += links * 5
        
        if chinese_chars > 0:
            chinese_ratio = chinese_chars / max(char_count, 1)
            base_estimate = int(base_estimate * (1 + chinese_ratio * 0.5))
        
        total_estimate = base_estimate + adjustments
        confidence = 0.85 if content_type == "code" else 0.9
        
        return total_estimate, confidence
    
    def _get_base_ratio(self, content_type: str) -> float:
        ratios = {
            "text": 0.25,
            "code": 0.3,
            "markdown": 0.27,
            "json": 0.28,
            "mixed": 0.28,
        }
        return ratios.get(content_type, 0.25)
    
    def _detect_content_type(self, text: str) -> str:
        if '```' in text:
            return "code"
        if text.strip().startswith('{') or text.strip().startswith('['):
            try:
                import json
                json.loads(text)
                return "json"
            except:
                pass
        if any(marker in text for marker in ['#', '##', '**', '-', '|']):
            return "markdown"
        return "text"
    
    def _get_breakdown(self, text: str, content_type: str) -> Dict[str, int]:
        breakdown = {}
        
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        if code_blocks:
            breakdown['code_blocks'] = sum(len(block) for block in code_blocks)
        
        inline_code = re.findall(r'`[^`]+`', text)
        if inline_code:
            breakdown['inline_code'] = sum(len(code) for code in inline_code)
        
        links = re.findall(r'https?://\S+', text)
        if links:
            breakdown['links'] = len(links)
        
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if chinese_chars:
            breakdown['chinese_chars'] = len(chinese_chars)
        
        return breakdown
    
    def _estimate_message(self, message: Dict[str, Any]) -> TokenEstimate:
        content = message.get("content", "")
        role = message.get("role", "user")
        
        role_tokens = 4
        
        content_estimate = self._estimate_text(str(content))
        
        total_tokens = role_tokens + content_estimate.token_count
        
        breakdown = content_estimate.breakdown.copy()
        breakdown['role'] = role_tokens
        
        return TokenEstimate(
            token_count=total_tokens,
            char_count=len(str(content)) + len(role),
            estimation_mode=content_estimate.estimation_mode,
            encoding_type=content_estimate.encoding_type,
            content_type="message",
            confidence=content_estimate.confidence,
            breakdown=breakdown
        )
    
    def _estimate_messages(self, messages: List[Dict[str, Any]]) -> TokenEstimate:
        total_tokens = 0
        total_chars = 0
        combined_breakdown: Dict[str, int] = {}
        
        for message in messages:
            estimate = self._estimate_message(message)
            total_tokens += estimate.token_count
            total_chars += estimate.char_count
            
            for key, value in estimate.breakdown.items():
                combined_breakdown[key] = combined_breakdown.get(key, 0) + value
        
        total_tokens += 3
        
        return TokenEstimate(
            token_count=total_tokens,
            char_count=total_chars,
            estimation_mode=self._effective_mode,
            encoding_type=self.encoding if self._effective_mode == EstimationMode.ACCURATE else None,
            content_type="messages",
            confidence=0.9,
            breakdown=combined_breakdown
        )
    
    def estimate_messages(self, messages: List[Dict[str, Any]]) -> int:
        return self.estimate(messages).token_count
    
    def get_model_limit(self, model: str) -> int:
        for key, limit in self.MODEL_TOKEN_LIMITS.items():
            if key.lower() in model.lower():
                return limit
        return 8192
    
    def create_budget(
        self,
        model: str,
        reserve_ratio: float = 0.1
    ) -> TokenBudget:
        total = self.get_model_limit(model)
        reserved = int(total * reserve_ratio)
        return TokenBudget(total_budget=total, reserved=reserved)
    
    def check_budget(
        self,
        messages: List[Dict[str, Any]],
        budget: TokenBudget
    ) -> Dict[str, Any]:
        estimate = self.estimate(messages)
        would_exceed = estimate.token_count > budget.available
        remaining = budget.available - estimate.token_count
        
        return {
            "token_count": estimate.token_count,
            "budget_available": budget.available,
            "remaining": remaining,
            "would_exceed": would_exceed,
            "usage_ratio": estimate.token_count / budget.total_budget if budget.total_budget > 0 else 0,
            "estimate": estimate
        }
    
    def select_messages_for_budget(
        self,
        messages: List[Dict[str, Any]],
        budget: TokenBudget,
        preserve_last: int = 2
    ) -> List[Dict[str, Any]]:
        if not messages:
            return []
        
        preserved = messages[-preserve_last:] if len(messages) > preserve_last else messages
        preserved_tokens = self.estimate_messages(preserved)
        
        if preserved_tokens > budget.available:
            return preserved
        
        remaining_budget = budget.available - preserved_tokens
        selected = []
        current_tokens = 0
        
        for message in reversed(messages[:-preserve_last] if len(messages) > preserve_last else []):
            msg_tokens = self.estimate([message]).token_count
            if current_tokens + msg_tokens <= remaining_budget:
                selected.insert(0, message)
                current_tokens += msg_tokens
            else:
                break
        
        return selected + preserved
