"""
测试Agent模块 / Test Agent Module

负责测试生成、执行和验证
Responsible for test generation, execution and verification
"""

from typing import Any
from datetime import datetime

from .base import WorkerAgent


class TestAgent(WorkerAgent):
    """
    测试Agent / Test Agent
    
    负责测试生成、执行和验证
    Responsible for test generation, execution and verification
    
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
        初始化测试Agent / Initialize test agent
        
        Args:
            environment: 环境实例 / Environment instance
            model: 模型实例 / Model instance
            config: 配置字典 / Configuration dictionary
        """
        config = config or {}
        config["tools"] = config.get("tools", [
            "pytest",
            "coverage",
            "code_execute",
            "file_ops",
        ])
        
        super().__init__(
            agent_id="test_agent",
            environment=environment,
            model=model,
            config=config,
        )
        
        self.test_frameworks = self.config.get("frameworks", [
            "pytest",
            "unittest",
            "jest",
        ])
    
    async def execute(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行测试相关子任务 / Execute test-related subtask
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            执行结果 / Execution result
        """
        self.set_status("working")
        self.current_task = subtask.id
        
        try:
            task_type = subtask.params.get("action", "run")
            
            if task_type == "generate":
                result = await self._generate_tests(subtask, context)
            elif task_type == "run":
                result = await self._run_tests(subtask, context)
            elif task_type == "verify":
                result = await self._verify(subtask, context)
            elif task_type == "coverage":
                result = await self._check_coverage(subtask, context)
            else:
                result = await self._run_tests(subtask, context)
            
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
    
    async def _generate_tests(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        生成测试 / Generate tests
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            生成结果 / Generation result
        """
        target = subtask.params.get("target")
        test_type = subtask.params.get("test_type", "unit")
        framework = subtask.params.get("framework", "pytest")
        
        prompt = f"""为以下代码生成测试：

目标: {target}
测试类型: {test_type}
测试框架: {framework}
描述: {subtask.description}

请生成完整的测试代码，包含边界情况和异常处理测试。
"""
        
        thought = await self.think(prompt, context)
        
        return {
            "success": True,
            "test_code": thought,
            "target": target,
            "test_type": test_type,
            "framework": framework,
            "subtask_id": subtask.id,
        }
    
    async def _run_tests(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        运行测试 / Run tests
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            运行结果 / Run result
        """
        test_path = subtask.params.get("test_path")
        framework = subtask.params.get("framework", "pytest")
        
        success, result = await self.act(
            "code_execute",
            {
                "name": "run_tests",
                "command": f"{framework} {test_path}" if test_path else framework,
                "test_path": test_path,
            }
        )
        
        passed = 0
        failed = 0
        if result:
            if isinstance(result, dict):
                passed = result.get("passed", 0)
                failed = result.get("failed", 0)
        
        return {
            "success": success and failed == 0,
            "result": result,
            "passed": passed,
            "failed": failed,
            "test_path": test_path,
            "framework": framework,
            "subtask_id": subtask.id,
        }
    
    async def _verify(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        验证结果 / Verify result
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            验证结果 / Verification result
        """
        expected = subtask.params.get("expected")
        actual = subtask.params.get("actual")
        
        if context:
            for key, value in context.items():
                if isinstance(value, dict) and "output" in value:
                    actual = value["output"]
                    break
        
        prompt = f"""验证以下结果：

期望结果: {expected}
实际结果: {actual}

请判断结果是否正确，并说明原因。
"""
        
        thought = await self.think(prompt, context)
        
        is_correct = str(expected) == str(actual) if expected and actual else False
        
        return {
            "success": is_correct,
            "expected": expected,
            "actual": actual,
            "analysis": thought,
            "subtask_id": subtask.id,
        }
    
    async def _check_coverage(
        self,
        subtask: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        检查覆盖率 / Check coverage
        
        Args:
            subtask: 子任务对象 / Subtask object
            context: 执行上下文 / Execution context
            
        Returns:
            覆盖率结果 / Coverage result
        """
        target = subtask.params.get("target")
        
        success, result = await self.act(
            "tool_call",
            {
                "name": "coverage",
                "target": target,
            }
        )
        
        coverage_percent = 0
        if result:
            if isinstance(result, dict):
                coverage_percent = result.get("coverage", 0)
            elif isinstance(result, (int, float)):
                coverage_percent = result
        
        return {
            "success": success,
            "coverage": coverage_percent,
            "target": target,
            "details": result,
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
        return task_type in ["test", "generate", "run", "verify", "coverage"]
