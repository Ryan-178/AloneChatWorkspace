"""
ä¸­æNLPæ¨¡å / Chinese NLP Module

æä¾ / Provides:
- ä¸­æåè¯ / Chinese word segmentation
- å®ä½è¯å« / Entity recognition
- è¯­ä¹åæ / Semantic analysis
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

import yaml


@dataclass
class Entity:
    """å®ä½æ°æ®ç±?/ Entity Data Class"""
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
    """åè¯ç»æ / Segmentation Result"""
    words: List[str]
    entities: List[Entity] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "words": self.words,
            "entities": [e.to_dict() for e in self.entities],
        }


class ChineseConfigLoader:
    """ä¸­æéç½®å è½½å?/ Chinese Config Loader"""
    
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
    ä¸­æåè¯å?/ Chinese Tokenizer
    
    æ¯æä¸­è±ææ··ååè¯?/ Support mixed Chinese-English tokenization
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.segmentation", {})
        self._user_dict = self._load_user_dict()
    
    def _load_user_dict(self) -> set:
        """å è½½ç¨æ·è¯å¸ / Load user dictionary"""
        user_dict_path = self._config.get("user_dict_path")
        
        if user_dict_path:
            path = Path(user_dict_path).expanduser()
            if path.exists():
                return set(path.read_text(encoding="utf-8").strip().split("\n"))
        
        return set()
    
    def segment(self, text: str) -> List[str]:
        """
        åè¯ / Segment text
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            åè¯ç»æ / Segmentation result
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
        """åè¯ä¸­æ / Segment Chinese text"""
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
        """åè¯éä¸­æ?/ Segment non-Chinese text"""
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
    å®ä½è¯å«å?/ Entity Recognizer
    
    è¯å«ä»£ç ç¸å³å®ä½ / Recognize code-related entities
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.entity_recognition.types", [])
        self._patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, List[re.Pattern]]:
        """æå»ºè¯å«æ¨¡å¼ / Build recognition patterns"""
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
        è¯å«å®ä½ / Recognize entities
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            å®ä½åè¡¨ / Entity list
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
        æååç§° / Extract names
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            æç±»ååç»çåç§° / Names grouped by type
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
    è¯­ä¹åæå?/ Semantic Analyzer
    
    åæææ¬è¯­ä¹ / Analyze text semantics
    """
    
    def __init__(self):
        self._config = chinese_config.get("chinese.nlp.semantic_analysis", {})
        self._similarity_threshold = self._config.get("similarity_threshold", 0.7)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        è®¡ç®ç¸ä¼¼åº?/ Calculate similarity
        
        Args:
            text1: ææ¬1 / Text 1
            text2: ææ¬2 / Text 2
            
        Returns:
            ç¸ä¼¼åº?/ Similarity
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
        æåå³é®è¯?/ Extract keywords
        
        Args:
            text: è¾å¥ææ¬ / Input text
            top_k: è¿åæ°é / Number to return
            
        Returns:
            å³é®è¯åè¡?/ Keyword list
        """
        tokenizer = ChineseTokenizer()
        words = tokenizer.segment(text)
        
        stop_words = self._get_stop_words()
        filtered = [w for w in words if w not in stop_words and len(w) > 1]
        
        counter = Counter(filtered)
        
        return counter.most_common(top_k)
    
    def _get_stop_words(self) -> set:
        """è·ååç¨è¯?/ Get stop words"""
        return {
            "ç?, "æ?, "å?, "æ?, "å?, "äº?, "ä¸?, "è¿?, "é?, "å°?,
            "ä¹?, "é?, "ä¼?, "è¦?, "è?, "å¯ä»¥", "åºè¯¥", "éè¦?, "ä¸ä¸?,
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
        }
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        åææå¾ / Analyze intent
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            æå¾åæç»æ / Intent analysis result
        """
        intent_keywords = {
            "generate": ["çæ", "åå»º", "å?, "å®ç°", "generate", "create", "write"],
            "modify": ["ä¿®æ¹", "æ´æ°", "æ¹å", "modify", "update", "change"],
            "delete": ["å é¤", "ç§»é¤", "delete", "remove"],
            "query": ["æ¥è¯¢", "è·å", "è¯»å", "query", "get", "read", "fetch"],
            "analyze": ["åæ", "æ£æ?, "å®¡æ¥", "analyze", "check", "review"],
            "explain": ["è§£é", "è¯´æ", "describe", "explain"],
            "test": ["æµè¯", "test"],
            "refactor": ["éæ", "ä¼å", "refactor", "optimize"],
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
    ä¸­æNLPç»¼åå·¥å· / Chinese NLP Comprehensive Tool
    """
    
    def __init__(self):
        self.tokenizer = ChineseTokenizer()
        self.entity_recognizer = EntityRecognizer()
        self.semantic_analyzer = SemanticAnalyzer()
    
    def process(self, text: str) -> SegmentedText:
        """
        å¤çææ¬ / Process text
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            å¤çç»æ / Processing result
        """
        words = self.tokenizer.segment(text)
        entities = self.entity_recognizer.recognize(text)
        
        return SegmentedText(words=words, entities=entities)
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        ç»¼ååæ / Comprehensive analysis
        
        Args:
            text: è¾å¥ææ¬ / Input text
            
        Returns:
            åæç»æ / Analysis result
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
