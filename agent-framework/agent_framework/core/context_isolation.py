"""
上下文隔离机制 / Context Isolation Mechanism

实现结构化摘要生成、按需读取协议
Implements structured summary generation, on-demand read protocol
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextSummary:
    """
    上下文摘要 / Context Summary

    压缩后的结构化摘要，包含关键信息和文件路径引用
    Compressed structured summary with key information and file path references
    """
    id: str = ""
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0
    key_points: List[str] = field(default_factory=list)
    file_references: Dict[str, str] = field(default_factory=dict)  # path -> description
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "compression_ratio": self.compression_ratio,
            "key_points": self.key_points,
            "file_references": self.file_references,
            "metadata": self.metadata,
        }


@dataclass
class ContextChunk:
    """
    上下文块 / Context Chunk

    表示一个可按需读取的上下文单元
    Represents a context unit that can be read on demand
    """
    chunk_id: str = ""
    content_type: str = ""  # code, text, conversation, etc.
    source_path: Optional[str] = None
    line_range: Optional[tuple] = None  # (start, end)
    summary: str = ""
    full_content: Optional[str] = None
    size: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "chunk_id": self.chunk_id,
            "content_type": self.content_type,
            "source_path": self.source_path,
            "line_range": self.line_range,
            "summary": self.summary,
            "size": self.size,
            "has_full_content": self.full_content is not None,
        }


class ContextIsolationManager:
    """
    上下文隔离管理器 / Context Isolation Manager

    功能：
    - 结构化摘要生成：将完整上下文压缩为结构化摘要
    - 按需读取协议：Agent只持有职责相关上下文，需要时通过文件路径读取完整内容
    - Token使用优化：减少重复传递大段内容

    Features:
    - Structured summary generation: Compresses full context into structured summaries
    - On-demand read protocol: Agents only hold relevant context, read full content via file paths when needed
    - Token usage optimization: Reduces repeated transmission of large content chunks
    """

    def __init__(
        self,
        max_context_size: int = 100000,  # ~100K tokens equivalent
        compression_target: float = 0.3,  # Target 30% of original size
        cache_enabled: bool = True,
    ):
        self.max_context_size = max_context_size
        self.compression_target = compression_target
        self.cache_enabled = cache_enabled
        self._summaries: Dict[str, ContextSummary] = {}
        self._chunks: Dict[str, ContextChunk] = {}
        self._access_count: Dict[str, int] = {}

    async def create_summary(
        self,
        context_id: str,
        content: str,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextSummary:
        """
        创建上下文摘要 / Create context summary

        Args:
            context_id: 上下文ID
            content: 原始内容
            content_type: 内容类型
            metadata: 元数据

        Returns:
            生成的摘要
        """
        original_size = len(content)

        if content_type == "code":
            summary = await self._summarize_code(content)
        elif content_type == "conversation":
            summary = await self._summarize_conversation(content)
        else:
            summary = await self._summarize_text(content)

        ctx_summary = ContextSummary(
            id=context_id,
            original_size=original_size,
            compressed_size=len(str(summary)),
            compression_ratio=1 - (len(str(summary)) / original_size) if original_size > 0 else 0,
            key_points=summary.get("key_points", []),
            file_references=summary.get("file_references", {}),
            metadata=metadata or {},
        )

        self._summaries[context_id] = ctx_summary
        logger.info(
            f"Created summary for {context_id}: "
            f"{original_size} -> {ctx_summary.compressed_size} "
            f"({ctx_summary.compression_ratio:.1%} reduction)"
        )

        return ctx_summary

    async def _summarize_code(self, code: str) -> Dict[str, Any]:
        """总结代码 / Summarize code"""
        lines = code.split("\n")
        key_points = []
        file_refs = {}

        for i, line in enumerate(lines[:50]):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("async def "):
                key_points.append(f"L{i+1}: {stripped[:80]}")
            elif stripped.startswith("#") and len(stripped) > 10:
                key_points.append(f"L{i+1}: {stripped[:80]}")

        if len(lines) > 50:
            key_points.append(f"... ({len(lines)} total lines)")

        return {"key_points": key_points, "file_references": file_refs}

    async def _summarize_conversation(self, conversation: str) -> Dict[str, Any]:
        """总结对话 / Summarize conversation"""
        lines = conversation.split("\n")
        key_points = []
        file_refs = {}

        for i, line in enumerate(lines):
            if line.strip().startswith("[") and ":" in line:
                key_points.append(f"{line.strip()[:100]}")

        if not key_points:
            key_points.append(conversation[:200] + ("..." if len(conversation) > 200 else ""))
            key_points.append(f"Total length: {len(conversation)} chars")

        return {"key_points": key_points[-20:], "file_references": file_refs}

    async def _summarize_text(self, text: str) -> Dict[str, Any]:
        """总结文本 / Summarize text"""
        sentences = text.split(".")
        key_points = []
        file_refs = []

        for i, sentence in enumerate(sentences[:15]):
            s = sentence.strip()
            if len(s) > 20:
                key_points.append(s[:100])

        if len(sentences) > 15:
            key_points.append(f"... ({len(sentences)} total sentences)")

        return {"key_points": key_points, "file_references": {}}

    async def create_chunk(
        self,
        chunk_id: str,
        content: str,
        content_type: str = "text",
        source_path: Optional[str] = None,
        line_range: Optional[tuple] = None,
        store_full: bool = False,
    ) -> ContextChunk:
        """
        创建上下文块 / Create context chunk

        Args:
            chunk_id: 块ID
            content: 内容
            content_type: 内容类型
            source_path: 源文件路径
            line_range: 行范围
            store_full: 是否存储完整内容

        Returns:
            创建的上下文块
        """
        chunk = ContextChunk(
            chunk_id=chunk_id,
            content_type=content_type,
            source_path=source_path,
            line_range=line_range,
            summary=content[:200] + ("..." if len(content) > 200 else ""),
            full_content=content if store_full else None,
            size=len(content),
        )

        self._chunks[chunk_id] = chunk
        return chunk

    async def get_chunk_content(self, chunk_id: str) -> Optional[str]:
        """
        获取块的完整内容 / Get full content of chunk

        如果没有缓存完整内容，尝试从源文件读取
        If no cached full content, try reading from source file
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            return None

        self._access_count[chunk_id] = self._access_count.get(chunk_id, 0) + 1
        chunk.last_accessed = datetime.utcnow()

        if chunk.full_content is not None:
            return chunk.full_content

        if chunk.source_path:
            try:
                path = Path(chunk.source_path)
                if path.exists():
                    content = path.read_text(encoding="utf-8")
                    if chunk.line_range:
                        lines = content.split("\n")
                        start, end = chunk.line_range
                        content = "\n".join(lines[start:end])
                    chunk.full_content = content
                    return content
            except Exception as e:
                logger.warning(f"Failed to read {chunk.source_path}: {e}")

        return chunk.summary

    async def get_summary_for_agent(
        self,
        agent_role: str,
        task_description: str,
        relevant_context_ids: List[str],
    ) -> Dict[str, Any]:
        """
        为特定Agent获取相关摘要 / Get relevant summary for specific Agent

        根据角色和任务描述，选择最相关的上下文摘要
        Based on role and task description, select most relevant context summaries
        """
        relevant_summaries = []
        total_size = 0

        for ctx_id in relevant_context_ids:
            summary = self._summaries.get(ctx_id)
            if summary:
                relevant_summaries.append(summary.to_dict())
                total_size += summary.compressed_size

                if total_size > self.max_context_size * 0.8:
                    break

        return {
            "agent_role": agent_role,
            "task_description": task_description,
            "summaries": relevant_summaries,
            "total_compressed_size": total_size,
            "summary_count": len(relevant_summaries),
        }

    def get_access_statistics(self) -> Dict[str, Any]:
        """
        获取访问统计 / Get access statistics

        返回哪些上下文被频繁访问
        Returns which contexts are frequently accessed
        """
        sorted_access = sorted(
            self._access_count.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:20]

        return {
            "total_summaries": len(self._summaries),
            "total_chunks": len(self._chunks),
            "top_accessed_chunks": [
                {"chunk_id": cid, "count": count}
                for cid, count in sorted_access
            ],
        }

    def clear_cache(self, older_than_hours: int = 1) -> int:
        """
        清除过期缓存 / Clear expired cache

        Args:
            older_than_hours: 超过多少小时的缓存视为过期

        Returns:
            清除的条目数
        """
        cutoff = datetime.utcnow().timestamp() - (older_than_hours * 3600)
        removed = 0

        chunks_to_remove = []
        for chunk_id, chunk in self._chunks.items():
            if chunk.last_accessed and chunk.last_accessed.timestamp() < cutoff:
                chunks_to_remove.append(chunk_id)

        for chunk_id in chunks_to_remove:
            del self._chunks[chunk_id]
            removed += 1

        logger.info(f"Cleared {removed} expired context chunks")
        return removed


class AgentContextContainer:
    """
    Agent上下文容器 / Agent Context Container

    每个Agent独立的上下文容器，只包含职责相关的上下文
    Independent context container for each Agent, only contains role-relevant context
    """

    def __init__(self, agent_id: str, role: str, isolation_manager: ContextIsolationManager):
        self.agent_id = agent_id
        self.role = role
        self._isolation_manager = isolation_manager
        self._relevant_context_ids: List[str] = []
        self._local_context: Dict[str, Any] = {}

    async def add_relevant_context(self, context_id: str) -> None:
        """添加相关上下文ID / Add relevant context ID"""
        if context_id not in self._relevant_context_ids:
            self._relevant_context_ids.append(context_id)

    async def remove_relevant_context(self, context_id: str) -> None:
        """移除相关上下文ID / Remove relevant context ID"""
        if context_id in self._relevant_context_ids:
            self._relevant_context_ids.remove(context_id)

    async def get_context_summary(self, task_description: str) -> Dict[str, Any]:
        """获取上下文摘要 / Get context summary"""
        return await self._isolation_manager.get_summary_for_agent(
            agent_role=self.role,
            task_description=task_description,
            relevant_context_ids=self._relevant_context_ids,
        )

    async def read_full_context(self, chunk_id: str) -> Optional[str]:
        """读取完整上下文 / Read full context"""
        return await self._isolation_manager.get_chunk_content(chunk_id)

    def set_local_data(self, key: str, value: Any) -> None:
        """设置本地数据 / Set local data"""
        self._local_context[key] = value

    def get_local_data(self, key: str, default: Any = None) -> Any:
        """获取本地数据 / Get local data"""
        return self._local_context.get(key, default)

    @property
    def context_count(self) -> int:
        """相关上下文数量 / Number of relevant contexts"""
        return len(self._relevant_context_ids)
