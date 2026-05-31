"""
Feedback Generator
上下文反馈系统 - 生成存储位置指示
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from .message_ranker import ImportanceCategory
from .mega_context_manager import ManagedMessage


@dataclass
class ContextFeedback:
    """上下文反馈"""
    total_messages: int
    in_context_count: int
    archived_count: int
    archived_files: List[Path]
    topic_index: Dict[str, int]
    summary: str
    insertion_marker: str  # 插入到对话中的标记文本


class ContextFeedbackGenerator:
    """
    上下文反馈生成器
    生成清晰的存储位置指示
    """
    
    def __init__(
        self,
        show_detailed_stats: bool = True,
        show_topic_breakdown: bool = True,
        marker_position: str = "start"  # "start", "end"
    ):
        self.show_detailed_stats = show_detailed_stats
        self.show_topic_breakdown = show_topic_breakdown
        self.marker_position = marker_position
    
    def generate_feedback(
        self,
        managed_messages: List[ManagedMessage],
        archived_files: List[Path]
    ) -> ContextFeedback:
        """
        生成完整的上下文反馈
        
        Args:
            managed_messages: 受管理的消息列表
            archived_files: 归档文件列表
            
        Returns:
            ContextFeedback: 完整反馈
        """
        # 统计信息
        total = len(managed_messages)
        in_context = sum(
            1 for m in managed_messages
            if getattr(m, "keep_in_context", True)
        )
        archived = sum(
            1 for m in managed_messages
            if m.stored
        )
        
        # 主题索引
        topic_index = self._build_topic_index(managed_messages)
        
        # 生成摘要
        summary = self._generate_summary(
            total,
            in_context,
            archived,
            topic_index,
            archived_files
        )
        
        # 生成插入标记
        insertion_marker = self._generate_insertion_marker(
            total,
            in_context,
            archived,
            topic_index,
            archived_files
        )
        
        return ContextFeedback(
            total_messages=total,
            in_context_count=in_context,
            archived_count=archived,
            archived_files=archived_files,
            topic_index=topic_index,
            summary=summary,
            insertion_marker=insertion_marker
        )
    
    def _build_topic_index(
        self,
        managed_messages: List[ManagedMessage]
    ) -> Dict[str, int]:
        """构建主题索引"""
        topic_index: Dict[str, int] = {}
        
        for m in managed_messages:
            for topic in m.importance.topics:
                if topic not in topic_index:
                    topic_index[topic] = 0
                topic_index[topic] += 1
        
        return topic_index
    
    def _generate_summary(
        self,
        total: int,
        in_context: int,
        archived: int,
        topic_index: Dict[str, int],
        archived_files: List[Path]
    ) -> str:
        """生成摘要"""
        parts = []
        
        # 基本统计
        parts.append(f"📊 对话摘要: 共 {total} 条消息")
        parts.append(f"  • 活跃上下文: {in_context} 条")
        parts.append(f"  • 本地归档: {archived} 条")
        
        if archived_files:
            parts.append(f"  • 归档文件: {len(archived_files)} 个")
        
        # 主题分布
        if self.show_topic_breakdown and topic_index:
            parts.append("\n📂 主题分布:")
            sorted_topics = sorted(
                topic_index.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for topic, count in sorted_topics[:5]:
                parts.append(f"  • {topic}: {count} 条")
        
        # 令牌估算
        parts.append("\n💾 上下文管理:")
        parts.append("  重要消息保留在活跃上下文")
        parts.append("  细节内容智能归档到本地存储")
        parts.append("  可通过搜索功能检索历史内容")
        
        return "\n".join(parts)
    
    def _generate_insertion_marker(
        self,
        total: int,
        in_context: int,
        archived: int,
        topic_index: Dict[str, int],
        archived_files: List[Path]
    ) -> str:
        """生成插入到对话中的标记"""
        if archived == 0:
            return ""
        
        # 简洁但清晰的标记
        marker_parts = [
            "---",
            "📦 本地存储提示",
            f"共 {total} 条对话: {in_context} 条活跃, {archived} 条已归档"
        ]
        
        if archived_files:
            marker_parts.append(f"归档文件: {len(archived_files)} 个")
        
        # 主题提示
        if topic_index:
            top_topics = list(topic_index.keys())[:3]
            if top_topics:
                marker_parts.append(f"主题: {', '.join(top_topics)}")
        
        marker_parts.extend([
            "可搜索关键词检索历史内容",
            "---"
        ])
        
        return "\n".join(marker_parts)
    
    def generate_detailed_report(
        self,
        managed_messages: List[ManagedMessage],
        archived_files: List[Path]
    ) -> str:
        """生成详细报告"""
        if not self.show_detailed_stats:
            return "详细统计已禁用"
        
        lines = []
        lines.append("="*60)
        lines.append(" 上下文状态详细报告")
        lines.append("="*60)
        
        # 时间戳
        lines.append(f"\n📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 总体统计
        total = len(managed_messages)
        in_context = sum(
            1 for m in managed_messages
            if getattr(m, "keep_in_context", True)
        )
        archived = sum(
            1 for m in managed_messages
            if m.stored
        )
        
        lines.append(f"\n📊 总览:")
        lines.append(f"  总消息: {total}")
        lines.append(f"  活跃: {in_context}")
        lines.append(f"  归档: {archived}")
        
        # 重要性分布
        importance_counts = {}
        for m in managed_messages:
            cat = m.importance.category.value
            importance_counts[cat] = importance_counts.get(cat, 0) + 1
        
        lines.append(f"\n📋 重要性分布:")
        for cat in ["critical", "important", "normal", "low", "trivial"]:
            count = importance_counts.get(cat, 0)
            lines.append(f"  {cat}: {count} 条")
        
        # 归档文件列表
        if archived_files:
            lines.append(f"\n💾 归档文件列表:")
            for i, f in enumerate(archived_files[:10], 1):
                lines.append(f"  {i}. {f}")
            if len(archived_files) > 10:
                lines.append(f"  ... 还有 {len(archived_files) - 10} 个文件")
        
        lines.append("\n" + "="*60)
        return "\n".join(lines)
