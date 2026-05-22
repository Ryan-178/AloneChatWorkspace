"""
数据Agent模块 / Data Agent Module

负责数据处理、分析和转换
Responsible for data processing, analysis and transformation
"""

from typing import Any
from datetime import datetime

from .base import WorkerAgent


class DataAgent(WorkerAgent):
    """
    数据Agent / Data Agent
    
    负责数据处理、分析和转换
    Responsible for data processing, analysis and transformation
    
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
        初始化数据Agent / Initialize data agent
        
        Args:
            environment: 环境实例 / Environment instance
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        config = config or {}
        config["tools"] = config.get("tools", [
            "database",
            "spreadsheet",
            "api",
            "file_ops",
        ])
        
        super().__init__(
            agent_id="data_agent",
            environment=environment,
            model=model,
            config=config,
        )
        
        self.datasources = self.config.get("datasources", [])
    
    async def execute(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行数据相关子任务 / Execute data-related subtask
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            执行结果 / Execution result
        """
        self.set_status("working")
        self.current_task = subtask.id
        
        try:
            task_type = subtask.params.get("action", "process")
            
            if task_type == "process":
                result = await self._process_data(subtask, context)
            elif task_type == "analyze":
                result = await self._analyze_data(subtask, context)
            elif task_type == "transform":
                result = await self._transform_data(subtask, context)
            elif task_type == "query":
                result = await self._query_data(subtask, context)
            else:
                result = await self._process_data(subtask, context)
            
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
    
    async def _process_data(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        处理数据 / Process data
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            处理结果 / Processing result
        """
        source = subtask.params.get("source")
        operation = subtask.params.get("operation", "read")
        
        prompt = f"""处理数据：

数据源: {source}
操作: {operation}
描述: {subtask.description}

请提供数据处理的具体步骤和代码。
"""
        
        thought = await self.think(prompt, context)
        
        success, result = await self.act(
            "tool_call",
            {
                "name": "data_process",
                "source": source,
                "operation": operation,
            }
        )
        
        return {
            "success": success,
            "result": result,
            "source": source,
            "operation": operation,
            "subtask_id": subtask.id,
        }
    
    async def _analyze_data(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        分析数据 / Analyze data
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            分析结果 / Analysis result
        """
        source = subtask.params.get("source")
        analysis_type = subtask.params.get("analysis_type", "general")
        
        prompt = f"""分析数据：

数据源: {source}
分析类型: {analysis_type}
描述: {subtask.description}

请提供数据分析的具体方法和结果。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "analysis": thought,
            "source": source,
            "analysis_type": analysis_type,
            "subtask_id": subtask.id,
        }
    
    async def _transform_data(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        转换数据 / Transform data
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            转换结果 / Transformation result
        """
        source = subtask.params.get("source")
        target_format = subtask.params.get("target_format")
        
        prompt = f"""转换数据：

数据源: {source}
目标格式: {target_format}
描述: {subtask.description}

请提供数据转换的具体步骤。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "transformation": thought,
            "source": source,
            "target_format": target_format,
            "subtask_id": subtask.id,
        }
    
    async def _query_data(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        查询数据 / Query data
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            查询结果 / Query result
        """
        source = subtask.params.get("source")
        query = subtask.params.get("query", subtask.description)
        
        prompt = f"""查询数据：

数据源: {source}
查询: {query}

请提供查询的具体实现。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "query_result": thought,
            "source": source,
            "query": query,
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
        return task_type in ["data", "process", "analyze", "transform", "query"]
