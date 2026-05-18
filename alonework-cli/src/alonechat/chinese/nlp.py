"""
中文NLP模块 / Chinese NLP Module

提供 / Provides:
- 中文分词 / Chinese word segmentation
- 实体识别 / Entity recognition
- 语义分析 / Semantic analysis
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

import yaml


@dataclass
class Entity:
    """实体数据类 / Entity Data Class"""
    type: str
    text: str
    start: int
    end: int
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


@dataclass
class SegmentedText:
    """分词结果 / Segmentation Result"""
    words: List[str]
    entities: List[Entity] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "words": self.words,
            "entities": [e.to_dict() for e in self.entities],
        }


class ChineseConfigLoader:
    """中文配置加载器 / Chinese Config Loader"""
    
    _instance: Optional["ChineseConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "configs" / "chinese_config.yaml"
        
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"chinese": {"nlp": {}}}
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @classmethod
    def get_instance(cls) -> "ChineseConfigLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


chinese_config = ChineseConfigLoader.get_instance()


class ChineseTokenizer:
    """
    中文分词器 / Chinese Tokenizer
    
    支持中英文混合分词 / Support mixed Chinese-English tokenization
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.segmentation", {})
        self._user_dict = self._load_user_dict()
    
    def _load_user_dict(self) -> set:
        """加载用户词典 / Load user dictionary"""
        user_dict_path = self._config.get("user_dict_path")
        
        if user_dict_path:
            path = Path(user_dict_path).expanduser()
            if path.exists():
                return set(path.read_text(encoding="utf-8").strip().split("\n"))
        
        return set()
    
    def segment(self, text: str) -> List[str]:
        """
        分词 / Segment text
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            分词结果 / Segmentation result
        """
        words = []
        
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        english_pattern = re.compile(r'[a-zA-Z]+')
        number_pattern = re.compile(r'\d+')
        symbol_pattern = re.compile(r'[^\w\s\u4e00-\u9fff]')
        
        last_end = 0
        
        for match in chinese_pattern.finditer(text):
            if match.start() > last_end:
                non_chinese = text[last_end:match.start()]
                words.extend(self._segment_non_chinese(non_chinese))
            
            chinese_text = match.group()
            words.extend(self._segment_chinese(chinese_text))
            last_end = match.end()
        
        if last_end < len(text):
            remaining = text[last_end:]
            words.extend(self._segment_non_chinese(remaining))
        
        return [w for w in words if w.strip()]
    
    def _segment_chinese(self, text: str) -> List[str]:
        """分词中文 / Segment Chinese text"""
        if text in self._user_dict:
            return [text]
        
        words = []
        i = 0
        
        while i < len(text):
            max_word = None
            
            for j in range(min(4, len(text) - i), 0, -1):
                word = text[i:i+j]
                if word in self._user_dict or j == 1:
                    max_word = word
                    break
            
            if max_word:
                words.append(max_word)
                i += len(max_word)
            else:
                words.append(text[i])
                i += 1
        
        return words
    
    def _segment_non_chinese(self, text: str) -> List[str]:
        """分词非中文 / Segment non-Chinese text"""
        words = []
        
        patterns = [
            (re.compile(r'[a-zA-Z]+'), lambda m: m.group()),
            (re.compile(r'\d+'), lambda m: m.group()),
            (re.compile(r'[^\w\s]'), lambda m: m.group()),
        ]
        
        last_end = 0
        
        for pattern, extractor in patterns:
            for match in pattern.finditer(text):
                if match.start() >= last_end:
                    if match.start() > last_end:
                        space_text = text[last_end:match.start()].strip()
                        if space_text:
                            words.append(space_text)
                    words.append(extractor(match))
                    last_end = match.end()
        
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                words.append(remaining)
        
        return words


class EntityRecognizer:
    """
    实体识别器 / Entity Recognizer
    
    识别代码相关实体 / Recognize code-related entities
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.entity_recognition.types", [])
        self._patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, List[re.Pattern]]:
        """构建识别模式 / Build recognition patterns"""
        patterns = {}
        
        for entity_type in self._config:
            type_name = entity_type.get("type")
            type_patterns = entity_type.get("patterns", [])
            
            compiled = []
            for p in type_patterns:
                try:
                    compiled.append(re.compile(re.escape(p), re.IGNORECASE))
                except Exception:
                    pass
            
            patterns[type_name] = compiled
        
        return patterns
    
    def recognize(self, text: str) -> List[Entity]:
        """
        识别实体 / Recognize entities
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            实体列表 / Entity list
        """
        entities = []
        
        for entity_type, patterns in self._patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entities.append(Entity(
                        type=entity_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                    ))
        
        entities.sort(key=lambda e: e.start)
        
        return entities
    
    def extract_names(self, text: str) -> Dict[str, List[str]]:
        """
        提取名称 / Extract names
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            按类型分组的名称 / Names grouped by type
        """
        entities = self.recognize(text)
        
        result: Dict[str, List[str]] = {}
        for entity in entities:
            if entity.type not in result:
                result[entity.type] = []
            result[entity.type].append(entity.text)
        
        return result


class SemanticAnalyzer:
    """
    语义分析器 / Semantic Analyzer
    
    分析文本语义 / Analyze text semantics
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.semantic_analysis", {})
        self._similarity_threshold = self._config.get("similarity_threshold", 0.7)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算相似度 / Calculate similarity
        
        Args:
            text1: 文本1 / Text 1
            text2: 文本2 / Text 2
            
        Returns:
            相似度 / Similarity
        """
        tokenizer = ChineseTokenizer()
        
        words1 = set(tokenizer.segment(text1))
        words2 = set(tokenizer.segment(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        提取关键词 / Extract keywords
        
        Args:
            text: 输入文本 / Input text
            top_k: 返回数量 / Number to return
            
        Returns:
            关键词列表 / Keyword list
        """
        tokenizer = ChineseTokenizer()
        words = tokenizer.segment(text)
        
        stop_words = self._get_stop_words()
        filtered = [w for w in words if w not in stop_words and len(w) > 1]
        
        counter = Counter(filtered)
        
        return counter.most_common(top_k)
    
    def _get_stop_words(self) -> set:
        """获取停用词 / Get stop words"""
        return {
            "的", "是", "在", "有", "和", "了", "不", "这", "那", "就",
            "也", "都", "会", "要", "能", "可以", "应该", "需要", "一个",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
        }
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        分析意图 / Analyze intent
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            意图分析结果 / Intent analysis result
        """
        intent_keywords = {
            "generate": ["生成", "创建", "写", "实现", "generate", "create", "write"],
            "modify": ["修改", "更新", "改变", "modify", "update", "change"],
            "delete": ["删除", "移除", "delete", "remove"],
            "query": ["查询", "获取", "读取", "query", "get", "read", "fetch"],
            "analyze": ["分析", "检查", "审查", "analyze", "check", "review"],
            "explain": ["解释", "说明", "describe", "explain"],
            "test": ["测试", "test"],
            "refactor": ["重构", "优化", "refactor", "optimize"],
        }
        
        text_lower = text.lower()
        
        scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            return {
                "intent": best_intent,
                "confidence": scores[best_intent] / len(intent_keywords[best_intent]),
                "all_scores": scores,
            }
        
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "all_scores": {},
        }


class ChineseNLP:
    """
    中文NLP综合工具 / Chinese NLP Comprehensive Tool
    """
    
    def __init__(self):
        self.tokenizer = ChineseTokenizer()
        self.entity_recognizer = EntityRecognizer()
        self.semantic_analyzer = SemanticAnalyzer()
    
    def process(self, text: str) -> SegmentedText:
        """
        处理文本 / Process text
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            处理结果 / Processing result
        """
        words = self.tokenizer.segment(text)
        entities = self.entity_recognizer.recognize(text)
        
        return SegmentedText(words=words, entities=entities)
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        综合分析 / Comprehensive analysis
        
        Args:
            text: 输入文本 / Input text
            
        Returns:
            分析结果 / Analysis result
        """
        segmented = self.process(text)
        keywords = self.semantic_analyzer.extract_keywords(text)
        intent = self.semantic_analyzer.analyze_intent(text)
        
        return {
            "words": segmented.words,
            "entities": [e.to_dict() for e in segmented.entities],
            "keywords": keywords,
            "intent": intent,
        }
