"""
代码Agent模块 / Code Agent Module

负责代码生成、修改和重构
Responsible for code generation, modification and refactoring
"""

from typing import Any
from datetime import datetime

from .base import WorkerAgent


class CodeAgent(WorkerAgent):
    """
    代码Agent / Code Agent
    
    负责代码生成、修改和重构
    Responsible for code generation, modification and refactoring
    
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
        初始化代码Agent / Initialize code agent
        
        Args:
            environment: 环境实例 / Environment instance
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        config = config or {}
        config["tools"] = config.get("tools", [
            "file_ops",
            "code_execute",
            "git",
            "linter",
        ])
        
        super().__init__(
            agent_id="code_agent",
            environment=environment,
            model=model,
            config=config,
        )
        
        self.languages = self.config.get("languages", [
            "python",
            "javascript",
            "typescript",
        ])
    
    async def execute(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行代码相关子任务 / Execute code-related subtask
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            执行结果 / Execution result
        """
        self.set_status("working")
        self.current_task = subtask.id
        
        try:
            task_type = subtask.params.get("action", "generate")
            
            if task_type == "generate":
                result = await self._generate_code(subtask, context)
            elif task_type == "modify":
                result = await self._modify_code(subtask, context)
            elif task_type == "refactor":
                result = await self._refactor_code(subtask, context)
            elif task_type == "review":
                result = await self._review_code(subtask, context)
            else:
                result = await self._generate_code(subtask, context)
            
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
    
    async def _generate_code(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        生成代码 / Generate code
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            生成结果 / Generation result
        """
        description = subtask.description
        language = subtask.params.get("language", "python")
        file_path = subtask.params.get("file_path")
        
        prompt = f"""生成以下代码：

任务描述: {description}
编程语言: {language}

请生成完整、可运行的代码，包含必要的注释和错误处理。
"""
        
        thought = await self.think(prompt, context)
        
        success, result = await self.act(
            "code_generate",
            {
                "name": "generate",
                "code": thought,
                "language": language,
                "file_path": file_path,
            }
        )
        
        return {
            "success": success,
            "code": thought,
            "language": language,
            "file_path": file_path,
            "subtask_id": subtask.id,
        }
    
    async def _modify_code(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        修改代码 / Modify code
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            修改结果 / Modification result
        """
        file_path = subtask.params.get("file_path")
        changes = subtask.params.get("changes", subtask.description)
        
        prompt = f"""修改以下代码：

文件路径: {file_path}
修改要求: {changes}

请输出修改后的完整代码。
"""
        
        thought = await self.think(prompt, context)
        
        success, result = await self.act(
            "file_operation",
            {
                "name": "write",
                "path": file_path,
                "content": thought,
            }
        )
        
        return {
            "success": success,
            "file_path": file_path,
            "changes": changes,
            "subtask_id": subtask.id,
        }
    
    async def _refactor_code(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        重构代码 / Refactor code
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            重构结果 / Refactoring result
        """
        file_path = subtask.params.get("file_path")
        refactor_type = subtask.params.get("refactor_type", "general")
        
        prompt = f"""重构以下代码：

文件路径: {file_path}
重构类型: {refactor_type}
重构目标: {subtask.description}

请输出重构后的代码，确保功能不变但代码质量提升。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "refactored_code": thought,
            "file_path": file_path,
            "subtask_id": subtask.id,
        }
    
    async def _review_code(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        审查代码 / Review code
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            审查结果 / Review result
        """
        file_path = subtask.params.get("file_path")
        
        prompt = f"""审查以下代码：

文件路径: {file_path}

请提供详细的代码审查报告，包括：
1. 代码质量评估
2. 潜在问题
3. 改进建议
4. 最佳实践建议
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "review": thought,
            "file_path": file_path,
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
        return task_type in ["code", "generate", "modify", "refactor", "review"]
