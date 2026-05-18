"""
鍚庡彴鏅鸿兘浣撹繍琛屽櫒 / Background Agent Runner

鏀寔鍦ㄥ悗鍙拌繍琛屾櫤鑳戒綋浠诲姟 / Supports running agent tasks in background
鐢ㄦ埛鍙互缁х画宸ヤ綔锛屾櫤鑳戒綋鍦ㄥ悗鍙版墽琛?/ User can continue working while agent runs in background
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from alonework.background.task import BackgroundTask, TaskStatus, TaskPriority
from alonework.background.manager import BackgroundManager


class AgentTaskType(Enum):
    """鏅鸿兘浣撲换鍔＄被鍨?/ Agent task type"""
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    FILE_PROCESSING = "file_processing"
    RAG_QUERY = "rag_query"
    CUSTOM = "custom"


@dataclass
class AgentTaskConfig:
    """鏅鸿兘浣撲换鍔￠厤缃?/ Agent task config"""
    task_type: AgentTaskType = AgentTaskType.CHAT
    model: str = "deepseek-chat"
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = False
    save_result: bool = True
    notify_on_complete: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackgroundAgentRunner:
    """
    鍚庡彴鏅鸿兘浣撹繍琛屽櫒 / Background Agent Runner
    
    鍦ㄥ悗鍙拌繍琛屾櫤鑳戒綋浠诲姟锛屾敮鎸佽繘搴﹁拷韪拰缁撴灉閫氱煡 / Runs agent tasks in background with progress tracking and result notification
    """
    
    def __init__(
        self,
        manager: Optional[BackgroundManager] = None,
        on_task_complete: Optional[Callable[[BackgroundTask], None]] = None,
        on_task_progress: Optional[Callable[[BackgroundTask, float], None]] = None,
    ):
        """
        鍒濆鍖栧悗鍙版櫤鑳戒綋杩愯鍣?/ Initialize background agent runner
        
        Args:
            manager: 鍚庡彴浠诲姟绠＄悊鍣?/ Background task manager
            on_task_complete: 浠诲姟瀹屾垚鍥炶皟 / Task complete callback
            on_task_progress: 浠诲姟杩涘害鍥炶皟 / Task progress callback
        """
        self.manager = manager or BackgroundManager()
        self.on_task_complete = on_task_complete
        self.on_task_progress = on_task_progress
        
        self._running_agents: Dict[str, asyncio.Task] = {}
        
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """璁剧疆鍐呴儴鍥炶皟 / Setup internal callbacks"""
        pass
    
    def _notify_complete(self, task: BackgroundTask, event: str) -> None:
        """
        閫氱煡浠诲姟瀹屾垚 / Notify task completion
        
        Args:
            task: 浠诲姟瀵硅薄 / Task object
            event: 浜嬩欢绫诲瀷 / Event type
        """
        if event == "completed" and self.on_task_complete:
            try:
                self.on_task_complete(task)
            except Exception:
                pass
    
    def submit_chat(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        config: Optional[AgentTaskConfig] = None,
    ) -> BackgroundTask:
        """
        鎻愪氦鑱婂ぉ浠诲姟 / Submit chat task
        
        Args:
            message: 娑堟伅鍐呭 / Message content
            context: 瀵硅瘽涓婁笅鏂?/ Conversation context
            config: 浠诲姟閰嶇疆 / Task config
            
        Returns:
            鍚庡彴浠诲姟 / Background task
        """
        config = config or AgentTaskConfig(task_type=AgentTaskType.CHAT)
        
        task = self.manager.create_task(
            name=f"chat_{datetime.utcnow().strftime('%H%M%S')}",
            command="agent.chat",
            description=f"Chat: {message[:50]}...",
            metadata={
                "task_type": config.task_type.value,
                "message": message,
                "context": context or [],
                "model": config.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
            },
        )
        
        return task
    
    def submit_code_generation(
        self,
        prompt: str,
        language: str = "python",
        file_path: Optional[str] = None,
        config: Optional[AgentTaskConfig] = None,
    ) -> BackgroundTask:
        """
        鎻愪氦浠ｇ爜鐢熸垚浠诲姟 / Submit code generation task
        
        Args:
            prompt: 鐢熸垚鎻愮ず / Generation prompt
            language: 缂栫▼璇█ / Programming language
            file_path: 杈撳嚭鏂囦欢璺緞 / Output file path
            config: 浠诲姟閰嶇疆 / Task config
            
        Returns:
            鍚庡彴浠诲姟 / Background task
        """
        config = config or AgentTaskConfig(task_type=AgentTaskType.CODE_GENERATION)
        
        task = self.manager.create_task(
            name=f"codegen_{datetime.utcnow().strftime('%H%M%S')}",
            command="agent.code_generation",
            description=f"Generate {language} code: {prompt[:50]}...",
            metadata={
                "task_type": config.task_type.value,
                "prompt": prompt,
                "language": language,
                "file_path": file_path,
                "model": config.model,
            },
        )
        
        return task
    
    def submit_code_review(
        self,
        code: str,
        file_path: Optional[str] = None,
        config: Optional[AgentTaskConfig] = None,
    ) -> BackgroundTask:
        """
        鎻愪氦浠ｇ爜瀹℃煡浠诲姟 / Submit code review task
        
        Args:
            code: 浠ｇ爜鍐呭 / Code content
            file_path: 鏂囦欢璺緞 / File path
            config: 浠诲姟閰嶇疆 / Task config
            
        Returns:
            鍚庡彴浠诲姟 / Background task
        """
        config = config or AgentTaskConfig(task_type=AgentTaskType.CODE_REVIEW)
        
        task = self.manager.create_task(
            name=f"review_{datetime.utcnow().strftime('%H%M%S')}",
            command="agent.code_review",
            description=f"Review code: {file_path or 'inline'}",
            metadata={
                "task_type": config.task_type.value,
                "code": code,
                "file_path": file_path,
                "model": config.model,
            },
        )
        
        return task
    
    def submit_file_processing(
        self,
        file_path: str,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        config: Optional[AgentTaskConfig] = None,
    ) -> BackgroundTask:
        """
        鎻愪氦鏂囦欢澶勭悊浠诲姟 / Submit file processing task
        
        Args:
            file_path: 鏂囦欢璺緞 / File path
            operation: 鎿嶄綔绫诲瀷 / Operation type
            params: 鎿嶄綔鍙傛暟 / Operation params
            config: 浠诲姟閰嶇疆 / Task config
            
        Returns:
            鍚庡彴浠诲姟 / Background task
        """
        config = config or AgentTaskConfig(task_type=AgentTaskType.FILE_PROCESSING)
        
        task = self.manager.create_task(
            name=f"process_{datetime.utcnow().strftime('%H%M%S')}",
            command="agent.file_processing",
            description=f"Process {file_path}: {operation}",
            metadata={
                "task_type": config.task_type.value,
                "file_path": file_path,
                "operation": operation,
                "params": params or {},
            },
        )
        
        return task
    
    def submit_rag_query(
        self,
        query: str,
        collection: Optional[str] = None,
        top_k: int = 5,
        config: Optional[AgentTaskConfig] = None,
    ) -> BackgroundTask:
        """
        鎻愪氦 RAG 鏌ヨ浠诲姟 / Submit RAG query task
        
        Args:
            query: 鏌ヨ瀛楃涓?/ Query string
            collection: 闆嗗悎鍚嶇О / Collection name
            top_k: 杩斿洖鏁伴噺 / Return count
            config: 浠诲姟閰嶇疆 / Task config
            
        Returns:
            鍚庡彴浠诲姟 / Background task
        """
        config = config or AgentTaskConfig(task_type=AgentTaskType.RAG_QUERY)
        
        task = self.manager.create_task(
            name=f"rag_{datetime.utcnow().strftime('%H%M%S')}",
            command="agent.rag_query",
            description=f"RAG query: {query[:50]}...",
            metadata={
                "task_type": config.task_type.value,
                "query": query,
                "collection": collection,
                "top_k": top_k,
            },
        )
        
        return task
    
    def get_running_tasks(self) -> List[BackgroundTask]:
        """
        鑾峰彇杩愯涓殑浠诲姟 / Get running tasks
        
        Returns:
            杩愯涓换鍔″垪琛?/ List of running tasks
        """
        return self.manager.list_tasks(status=TaskStatus.RUNNING)
    
    def get_pending_tasks(self) -> List[BackgroundTask]:
        """
        鑾峰彇寰呮墽琛屼换鍔?/ Get pending tasks
        
        Returns:
            寰呮墽琛屼换鍔″垪琛?/ List of pending tasks
        """
        return self.manager.list_tasks(status=TaskStatus.PENDING)
    
    def get_task_result(self, task_id: str) -> Optional[str]:
        """
        鑾峰彇浠诲姟缁撴灉 / Get task result
        
        Args:
            task_id: 浠诲姟ID / Task ID
            
        Returns:
            浠诲姟缁撴灉鎴?None / Task result or None
        """
        task = self.manager.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        鍙栨秷浠诲姟 / Cancel task
        
        Args:
            task_id: 浠诲姟ID / Task ID
            
        Returns:
            鏄惁鎴愬姛 / Whether successful
        """
        if task_id in self._running_agents:
            try:
                self._running_agents[task_id].cancel()
                del self._running_agents[task_id]
            except Exception:
                pass
        
        return self.manager.cancel_task(task_id)
    
    def get_runner_info(self) -> Dict[str, Any]:
        """
        鑾峰彇杩愯鍣ㄤ俊鎭?/ Get runner info
        
        Returns:
            杩愯鍣ㄤ俊鎭瓧鍏?/ Runner info dict
        """
        stats = self.manager.get_stats()
        return {
            "running_agents": len(self._running_agents),
            "stats": stats,
        }
