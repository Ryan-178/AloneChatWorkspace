"""
Context Compressor
智能上下文压缩 - 使用DeepSeek模型
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """压缩结果"""
    original_messages: List[Dict]
    compressed_messages: List[Dict]
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    kept_ratio: float
    summary: str = ""
    ai_generated: bool = True


class ContextCompressor:
    """
    上下文压缩器
    使用DeepSeek模型智能压缩和摘要
    """
    
    def __init__(
        self,
        min_compression_ratio: float = 0.5,
        preserve_last_n: int = 5,
        use_ai_compression: bool = True
    ):
        self.min_compression_ratio = min_compression_ratio
        self.preserve_last_n = preserve_last_n
        self.use_ai_compression = use_ai_compression
        
        # 延迟导入，避免循环依赖
        self._llm_provider = None
    
    def set_llm_provider(self, provider):
        """设置DeepSeek Provider"""
        self._llm_provider = provider
    
    def compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        current_tokens: int
    ) -> CompressionResult:
        """压缩上下文 - 优先使用AI"""
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                kept_ratio=1.0,
                summary="无需压缩",
                ai_generated=False
            )
        
        # 保留最后N条消息
        preserved = messages[-self.preserve_last_n:] if messages else []
        
        # 压缩早期的消息
        early_messages = messages[:-self.preserve_last_n] if len(messages) > self.preserve_last_n else []
        
        if self.use_ai_compression and self._llm_provider and early_messages:
            # 使用DeepSeek AI智能压缩
            compressed_early = self._ai_summarize_with_llm(early_messages)
            summary_text = "AI智能压缩"
        else:
            # 降级方案：简单摘要
            compressed_early = self._fallback_summarize(early_messages)
            summary_text = "基础摘要压缩"
        
        final_messages = compressed_early + preserved
        
        # 估算压缩后的token数
        compressed_tokens = int(current_tokens * 0.4)
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=final_messages,
            original_tokens=current_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / current_tokens,
            kept_ratio=len(final_messages) / max(len(messages), 1),
            summary=summary_text,
            ai_generated=self.use_ai_compression and self._llm_provider and early_messages
        )
    
    async def acompress(
        self,
        messages: List[Dict],
        target_tokens: int,
        current_tokens: int
    ) -> CompressionResult:
        """异步压缩"""
        if current_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=list(messages),
                original_tokens=current_tokens,
                compressed_tokens=current_tokens,
                compression_ratio=1.0,
                kept_ratio=1.0,
                summary="无需压缩",
                ai_generated=False
            )
        
        preserved = messages[-self.preserve_last_n:] if messages else []
        early_messages = messages[:-self.preserve_last_n] if len(messages) > self.preserve_last_n else []
        
        if self.use_ai_compression and self._llm_provider and early_messages:
            compressed_early = await self._ai_summarize_with_llm_async(early_messages)
            summary_text = "AI智能压缩"
        else:
            compressed_early = self._fallback_summarize(early_messages)
            summary_text = "基础摘要压缩"
        
        final_messages = compressed_early + preserved
        compressed_tokens = int(current_tokens * 0.4)
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=final_messages,
            original_tokens=current_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / current_tokens,
            kept_ratio=len(final_messages) / max(len(messages), 1),
            summary=summary_text,
            ai_generated=self.use_ai_compression and self._llm_provider and early_messages
        )
    
    def _ai_summarize_with_llm(self, messages: List[Dict]) -> List[Dict]:
        """用DeepSeek模型智能摘要"""
        from agent_framework.core.base_llm import Message
        
        # 构建提示
        context_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        system_prompt = """你是一个智能上下文摘要器。你的任务是：
1. 智能分析历史对话，保留重要信息
2. 识别关键主题、决策、任务和上下文
3. 生成一个简洁但包含所有必要信息的摘要
4. 保持摘要格式自然，适合作为对话上下文使用
5. 特别关注：任务描述、关键决策、重要信息"""
        
        summary_prompt = f"""请智能摘要以下对话历史，保留所有重要信息：

{context_text}

请生成摘要，保留关键信息。"""
        
        # 调用LLM
        if self._llm_provider:
            try:
                llm_messages = [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=summary_prompt)
                ]
                result = self._llm_provider.chat(llm_messages)
                return [{"role": "system", "content": f"[对话智能摘要]\n{result.content}"}]
            except Exception as e:
                return self._fallback_summarize(messages)
        else:
            return self._fallback_summarize(messages)
    
    async def _ai_summarize_with_llm_async(self, messages: List[Dict]) -> List[Dict]:
        """异步AI摘要"""
        from agent_framework.core.base_llm import Message
        
        context_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        system_prompt = """你是一个智能上下文摘要器。你的任务是：
1. 智能分析历史对话，保留重要信息
2. 识别关键主题、决策、任务和上下文
3. 生成一个简洁但包含所有必要信息的摘要
4. 保持摘要格式自然，适合作为对话上下文使用
5. 特别关注：任务描述、关键决策、重要信息"""
        
        summary_prompt = f"""请智能摘要以下对话历史，保留所有重要信息：

{context_text}

请生成摘要，保留关键信息。"""
        
        if self._llm_provider:
            try:
                llm_messages = [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=summary_prompt)
                ]
                result = await self._llm_provider.chat_async(llm_messages)
                return [{"role": "system", "content": f"[对话智能摘要]\n{result.content}"}]
            except Exception as e:
                return self._fallback_summarize(messages)
        else:
            return self._fallback_summarize(messages)
    
    def _fallback_summarize(self, messages: List[Dict]) -> List[Dict]:
        """降级方案：简单摘要"""
        if not messages:
            return []
        
        # 尝试简单的元数据摘要
        count = len(messages)
        topics = []
        for msg in messages:
            content = msg.get('content', '')[:50]
            if content:
                topics.append(content[:30])
                if len(topics) >= 5:
                    break
        
        summary_content = (
            f"[历史对话摘要] 共{count}条消息，"
            f"主要内容包括：{', '.join(topics[:3])}"
        )
        if len(topics) > 3:
            summary_content += f"... 更多内容已归档"
        
        return [{"role": "system", "content": summary_content}]
