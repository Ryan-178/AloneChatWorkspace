"""
研究Agent模块 / Research Agent Module

负责信息检索、文档阅读和知识收集
Responsible for information retrieval, document reading and knowledge collection
"""

from typing import Any
from datetime import datetime

from .base import WorkerAgent


class ResearchAgent(WorkerAgent):
    """
    研究Agent / Research Agent
    
    负责信息检索、文档阅读和知识收集
    Responsible for information retrieval, document reading and knowledge collection
    
    不做训练，只记录交互数据
    No training, only records interaction data
    """
    
    def __init__(
        self,
        environment: Any,
        model: Any = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化研究Agent / Initialize research agent
        
        Args:
            environment: 环境实例 / Environment instance
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        config = config or {}
        config["tools"] = config.get("tools", [
            "web_search",
            "document_read",
            "api",
            "file_ops",
        ])
        
        super().__init__(
            agent_id="research_agent",
            environment=environment,
            model=model,
            config=config,
        )
        
        self.search_tools = self.config.get("search_tools", ["web", "local"])
    
    async def execute(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行研究相关子任务 / Execute research-related subtask
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            执行结果 / Execution result
        """
        self.set_status("working")
        self.current_task = subtask.id
        
        try:
            task_type = subtask.params.get("action", "search")
            
            if task_type == "search":
                result = await self._search(subtask, context)
            elif task_type == "read":
                result = await self._read_document(subtask, context)
            elif task_type == "summarize":
                result = await self._summarize(subtask, context)
            elif task_type == "collect":
                result = await self._collect_knowledge(subtask, context)
            else:
                result = await self._search(subtask, context)
            
            self.add_history(f"execute:{task_type}", result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "subtask_id": subtask.id,
            }
        finally:
            self.set_status("idle")
            self.current_task = None
    
    async def _search(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        搜索信息 / Search information
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            搜索结果 / Search result
        """
        query = subtask.params.get("query", subtask.description)
        search_type = subtask.params.get("search_type", "web")
        
        prompt = f"""搜索以下信息：

查询: {query}
搜索类型: {search_type}

请提供搜索关键词和可能的来源。
"""
        
        thought = await self.think(prompt, context)
        
        success, result = await self.act(
            "tool_call",
            {
                "name": "search",
                "query": query,
                "search_type": search_type,
            }
        )
        
        return {
            "success": success,
            "results": result,
            "query": query,
            "search_type": search_type,
            "subtask_id": subtask.id,
        }
    
    async def _read_document(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        阅读文档 / Read document
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            阅读结果 / Reading result
        """
        document_path = subtask.params.get("document_path")
        extract_type = subtask.params.get("extract_type", "full")
        
        success, result = await self.act(
            "file_operation",
            {
                "name": "read",
                "path": document_path,
            }
        )
        
        if success and result:
            prompt = f"""分析以下文档内容：

文档路径: {document_path}
提取类型: {extract_type}
内容: {result[:5000] if len(str(result)) > 5000 else result}

请提取关键信息并总结。
"""
            
            thought = await self.think(prompt, context)
        else:
            thought = ""
        
        return {
            "success": success,
            "content": result,
            "summary": thought,
            "document_path": document_path,
            "subtask_id": subtask.id,
        }
    
    async def _summarize(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        总结信息 / Summarize information
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            总结结果 / Summary result
        """
        content = subtask.params.get("content", "")
        summary_type = subtask.params.get("summary_type", "brief")
        
        prompt = f"""总结以下内容：

内容: {content[:5000] if len(content) > 5000 else content}
总结类型: {summary_type}

请提供简洁明了的总结。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "summary": thought,
            "summary_type": summary_type,
            "subtask_id": subtask.id,
        }
    
    async def _collect_knowledge(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        收集知识 / Collect knowledge
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            收集结果 / Collection result
        """
        topic = subtask.params.get("topic", subtask.description)
        sources = subtask.params.get("sources", [])
        
        prompt = f"""收集关于以下主题的知识：

主题: {topic}
来源: {sources if sources else '自动搜索'}

请收集并整理相关知识。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "knowledge": thought,
            "topic": topic,
            "sources": sources,
            "subtask_id": subtask.id,
        }
    
    def can_handle(self, task_type: str) -> bool:
        """
        检查是否能处理该类型任务 / Check if can handle task type
        
        Args:
            task_type: 任务类型 / Task type
            
        Returns:
            是否能处理 / Whether can handle
        """
        return task_type in ["research", "search", "read", "summarize", "collect"]
