"""
Message Ranker
消息重要性评估器 - 多维度评分与分类
"""
import re
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ImportanceCategory(str, Enum):
    """重要性分类"""
    CRITICAL = "critical"    # 核心内容，必须保留
    IMPORTANT = "important"  # 重要内容，建议保留
    NORMAL = "normal"        # 普通内容，可压缩
    LOW = "low"              # 低重要性，可归档
    TRIVIAL = "trivial"      # 细枝末节，建议归档


@dataclass
class MessageImportance:
    """消息重要性评分"""
    score: float  # 0.0-1.0 综合得分
    category: ImportanceCategory
    reasoning: str
    topics: List[str]
    timestamp: datetime
    decay_rate: float = 0.01
    dimensions: Dict[str, float] = field(default_factory=dict)


@dataclass
class RankConfig:
    """评分配置"""
    # 各维度权重
    weights: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.35,
        "recency": 0.25,
        "role": 0.15,
        "length": 0.1,
        "topics": 0.15
    })
    
    # 分类阈值
    thresholds: Dict[ImportanceCategory, float] = field(default_factory=lambda: {
        ImportanceCategory.CRITICAL: 0.8,
        ImportanceCategory.IMPORTANT: 0.6,
        ImportanceCategory.NORMAL: 0.4,
        ImportanceCategory.LOW: 0.2
    })
    
    # 时间衰减配置
    decay_hours: float = 24.0
    decay_factor: float = 0.95
    
    # 关键词列表
    critical_keywords: List[str] = field(default_factory=lambda: [
        "important", "critical", "urgent", "essential", "key",
        "必须", "重要", "紧急", "核心", "关键", "务必", "记住"
    ])
    
    important_keywords: List[str] = field(default_factory=lambda: [
        "note", "remember", "consider", "think", "plan",
        "注意", "记得", "考虑", "思考", "计划", "备忘"
    ])


class MessageRanker:
    """
    消息重要性评估器
    多维度智能评分系统
    """
    
    def __init__(self, config: Optional[RankConfig] = None):
        self.config = config or RankConfig()
        self.topic_extractor = TopicExtractor()
    
    def rank_message(
        self,
        message: Dict[str, Any],
        message_index: int,
        total_messages: int
    ) -> MessageImportance:
        """
        评估单条消息的重要性
        
        Args:
            message: 消息字典
            message_index: 消息索引
            total_messages: 总消息数
            
        Returns:
            MessageImportance: 重要性评分结果
        """
        dimensions = {}
        
        # 1. 语义重要性 (35%)
        dimensions["semantic"] = self._score_semantic(message)
        
        # 2. 时间衰减 (25%)
        dimensions["recency"] = self._score_recency(message_index, total_messages)
        
        # 3. 角色权重 (15%)
        dimensions["role"] = self._score_role(message)
        
        # 4. 内容长度 (10%)
        dimensions["length"] = self._score_length(message)
        
        # 5. 主题识别 (15%)
        topics = self.topic_extractor.extract_topics(message)
        dimensions["topics"] = self._score_topics(topics)
        
        # 加权计算综合得分
        total_score = sum(
            v * self.config.weights[k]
            for k, v in dimensions.items()
        )
        total_score = max(0.0, min(1.0, total_score))
        
        # 确定分类
        category = self._determine_category(total_score)
        
        # 生成推理说明
        reasoning = self._generate_reasoning(dimensions, total_score, category)
        
        timestamp = message.get("timestamp", datetime.now())
        
        return MessageImportance(
            score=total_score,
            category=category,
            reasoning=reasoning,
            topics=topics,
            timestamp=timestamp,
            dimensions=dimensions
        )
    
    def _score_semantic(self, message: Dict[str, Any]) -> float:
        """语义重要性评分"""
        content = message.get("content", "").lower()
        
        # 检查关键词
        critical_count = sum(
            1 for kw in self.config.critical_keywords if kw in content
        )
        important_count = sum(
            1 for kw in self.config.important_keywords if kw in content
        )
        
        # 检查是否有代码、链接等
        has_code = "```" in content
        has_link = "http" in content or "www" in content
        
        score = 0.5
        score += critical_count * 0.15
        score += important_count * 0.08
        
        if has_code:
            score += 0.12
        if has_link:
            score += 0.08
        
        return min(1.0, score)
    
    def _score_recency(self, message_index: int, total_messages: int) -> float:
        """时间衰减评分"""
        if total_messages == 0:
            return 0.5
        
        # 越新的消息越重要
        recency = 1.0 - (message_index / total_messages)
        
        # 非线性衰减 - 最近消息更重要
        return recency ** 0.7
    
    def _score_role(self, message: Dict[str, Any]) -> float:
        """角色权重评分"""
        role = message.get("role", "user")
        
        if role == "system":
            return 1.0
        elif role == "assistant":
            return 0.7
        elif role == "user":
            return 0.6
        else:
            return 0.5
    
    def _score_length(self, message: Dict[str, Any]) -> float:
        """内容长度评分"""
        content = message.get("content", "")
        length = len(content)
        
        if length == 0:
            return 0.1
        
        # S型曲线 - 中等长度最佳
        if length < 20:
            return 0.3 + (length / 20) * 0.3
        elif length < 500:
            return 0.6 + (length / 500) * 0.3
        else:
            return 0.9 - min(0.4, (length - 500) / 2000)
    
    def _score_topics(self, topics: List[str]) -> float:
        """主题相关性评分"""
        # 有主题的消息更重要
        if not topics:
            return 0.4
        elif len(topics) == 1:
            return 0.7
        else:
            return 0.85
    
    def _determine_category(self, score: float) -> ImportanceCategory:
        """根据得分确定分类"""
        thresholds = self.config.thresholds
        
        if score >= thresholds[ImportanceCategory.CRITICAL]:
            return ImportanceCategory.CRITICAL
        elif score >= thresholds[ImportanceCategory.IMPORTANT]:
            return ImportanceCategory.IMPORTANT
        elif score >= thresholds[ImportanceCategory.NORMAL]:
            return ImportanceCategory.NORMAL
        elif score >= thresholds[ImportanceCategory.LOW]:
            return ImportanceCategory.LOW
        else:
            return ImportanceCategory.TRIVIAL
    
    def _generate_reasoning(
        self,
        dimensions: Dict[str, float],
        total_score: float,
        category: ImportanceCategory
    ) -> str:
        """生成推理说明"""
        reasons = []
        
        if dimensions.get("semantic", 0) > 0.7:
            reasons.append("包含重要关键词或结构")
        if dimensions.get("recency", 0) > 0.8:
            reasons.append("最近对话")
        if dimensions.get("role", 0) == 1.0:
            reasons.append("系统指令")
        if dimensions.get("length", 0) > 0.7:
            reasons.append("内容充实")
        
        if not reasons:
            reasons.append("普通对话内容")
        
        return f"综合评分 {total_score:.2f} ({category.value}): {'; '.join(reasons)}"


class TopicExtractor:
    """主题提取器"""
    
    def __init__(self):
        # 简单的主题关键词库
        self.topic_keywords = {
            "编程": ["code", "程序", "bug", "修复", "api", "function", "开发", "调试"],
            "商业": ["business", "marketing", "sales", "公司", "项目", "客户"],
            "研究": ["research", "study", "paper", "论文", "数据", "分析"],
            "技术": ["tech", "系统", "架构", "设计", "技术", "优化"],
            "日常": ["hello", "hi", "谢谢", "感谢", "好的", "再见"]
        }
    
    def extract_topics(self, message: Dict[str, Any]) -> List[str]:
        """提取主题"""
        content = message.get("content", "").lower()
        topics = []
        
        for topic, keywords in self.topic_keywords.items():
            for kw in keywords:
                if kw.lower() in content:
                    topics.append(topic)
                    break
        
        if not topics:
            topics.append("一般对话")
        
        return list(set(topics))
