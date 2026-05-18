"""
任务规划器

智能拆解和执行复杂任务
"""

import json
import re
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from .prompts import TASK_DECOMPOSITION_PROMPT, TASK_EXECUTION_PROMPT


class TaskPlanner:
    """智能任务规划器"""
    
    def __init__(self, deepseek_service=None):
        """
        初始化任务规划器
        
        Args:
            deepseek_service: DeepSeek 服务实例
        """
        self.deepseek = deepseek_service
    
    def set_deepseek_service(self, service):
        """设置 DeepSeek 服务"""
        self.deepseek = service
    
    async def decompose_task(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        拆解用户任务
        
        Args:
            user_request: 用户需求描述
            context: 上下文信息
            
        Returns:
            任务计划字典
        """
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        # 构建完整的需求描述
        full_request = user_request
        if context:
            full_request += f"\n\n上下文信息：{json.dumps(context, ensure_ascii=False)}"
        
        messages = [
            {
                "role": "system",
                "content": "你是任务规划专家，擅长将复杂需求拆解为可执行的子任务。请严格按照JSON格式输出。"
            },
            {
                "role": "user",
                "content": TASK_DECOMPOSITION_PROMPT.format(user_request=full_request)
            }
        ]
        
        response = await self.deepseek.chat_completion(messages, temperature=0.3)
        content = response["choices"][0]["message"]["content"]
        
        # 解析 JSON
        task_plan = self._extract_json(content)
        
        return task_plan
    
    async def execute_task_plan(
        self,
        task_plan: Dict[str, Any],
        workspace_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        执行任务计划
        
        Args:
            task_plan: 任务计划
            workspace_id: 工作区ID
            progress_callback: 进度回调函数
            
        Returns:
            执行结果
        """
        
        results = {}
        subtasks = task_plan.get("subtasks", [])
        execution_order = task_plan.get("execution_order", [])
        
        # 如果没有执行顺序，按子任务顺序执行
        if not execution_order:
            execution_order = [t["id"] for t in subtasks]
        
        for task_id in execution_order:
            # 查找任务
            task = next((t for t in subtasks if t["id"] == task_id), None)
            if not task:
                continue
            
            # 检查依赖是否完成
            dependencies = task.get("dependencies", [])
            deps_satisfied = all(dep in results for dep in dependencies)
            
            if not deps_satisfied:
                if progress_callback:
                    await progress_callback(task_id, "skipped", "依赖未满足")
                continue
            
            # 执行子任务
            if progress_callback:
                await progress_callback(task_id, "started", task)
            
            try:
                result = await self._execute_subtask(
                    task,
                    results,
                    workspace_id
                )
                results[task_id] = result
                
                if progress_callback:
                    await progress_callback(task_id, "completed", result)
                    
            except Exception as e:
                error_msg = str(e)
                results[task_id] = {"error": error_msg}
                
                if progress_callback:
                    await progress_callback(task_id, "failed", error_msg)
        
        return {
            "main_task": task_plan.get("main_task", ""),
            "results": results,
            "final_output": task_plan.get("final_output", "")
        }
    
    async def _execute_subtask(
        self,
        task: Dict[str, Any],
        previous_results: Dict[str, Any],
        workspace_id: str
    ) -> Any:
        """
        执行单个子任务
        
        Args:
            task: 任务定义
            previous_results: 之前任务的结果
            workspace_id: 工作区ID
            
        Returns:
            执行结果
        """
        
        skill = task.get("skill", "")
        description = task.get("description", "")
        tools = task.get("tools", [])
        
        # 根据技能调用对应的服务
        if skill == "document_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_word_report(
                description,
                context=previous_results
            )
        
        elif skill == "presentation_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_ppt(
                description,
                context=str(previous_results)
            )
        
        elif skill == "spreadsheet_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_excel(
                description,
                context=str(previous_results)
            )
        
        elif skill == "data_analysis":
            return await self._execute_data_analysis(task, previous_results)
        
        elif skill == "web_reading":
            return await self._execute_web_reading(task, previous_results)
        
        elif skill == "ocr_processing":
            return await self._execute_ocr(task, previous_results)
        
        elif skill == "code_generation":
            return await self._execute_code_generation(task, previous_results)
        
        else:
            # 通用任务执行
            return await self._execute_generic(task, previous_results)
    
    async def _execute_data_analysis(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行数据分析任务"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        prompt = f"""请执行以下数据分析任务：

任务描述：{task.get('description', '')}

上下文数据：{json.dumps(context, ensure_ascii=False, indent=2)}

请提供：
1. 分析过程
2. 关键发现
3. 数据洞察
4. 可视化建议
"""
        
        messages = [
            {"role": "system", "content": "你是数据分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        
        return {
            "analysis": response["choices"][0]["message"]["content"],
            "task_id": task.get("id")
        }
    
    async def _execute_web_reading(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行网页读取任务"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        description = task.get("description", "")
        
        prompt = f"""请分析以下网页内容或搜索需求：

{description}

上下文：{json.dumps(context, ensure_ascii=False, indent=2)}

请提供：
1. 关键信息提取
2. 内容摘要
3. 相关数据点
"""
        
        messages = [
            {"role": "system", "content": "你是网页内容分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        
        return {
            "result": response["choices"][0]["message"]["content"],
            "task_id": task.get("id")
        }
    
    async def _execute_ocr(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 OCR 任务"""
        
        from ..file_processors import get_processor
        
        description = task.get("description", "")
        
        # 尝试从描述中提取文件路径
        # 这里简化处理，实际应用中需要更复杂的解析
        
        return {
            "result": f"OCR 任务: {description}",
            "task_id": task.get("id"),
            "note": "需要指定图片文件路径"
        }
    
    async def _execute_code_generation(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行代码生成任务"""
        
        from ..file_generators import file_generator
        
        description = task.get("description", "")
        
        code = await file_generator.generate_code(
            user_request=description,
            context=str(context)
        )
        
        return {
            "code": code,
            "task_id": task.get("id")
        }
    
    async def _execute_generic(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行通用任务"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        description = task.get("description", "")
        skill = task.get("skill", "unknown")
        
        prompt = TASK_EXECUTION_PROMPT.format(
            task_name=task.get("name", ""),
            task_description=description,
            skill=skill,
            tools=task.get("tools", []),
            context=json.dumps(context, ensure_ascii=False, indent=2)
        )
        
        messages = [
            {"role": "system", "content": f"你是{skill}专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        
        return {
            "result": response["choices"][0]["message"]["content"],
            "task_id": task.get("id"),
            "skill": skill
        }
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取 JSON"""
        
        # 查找 JSON 代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # 尝试查找裸 JSON
            json_start = text.find('{')
            json_end = text.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_str = text[json_start:json_end+1]
            else:
                return {"error": "无法解析 JSON", "raw_text": text}
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            return {"error": f"JSON 解析错误: {str(e)}", "raw_text": text}


# 全局实例
task_planner = TaskPlanner()
