"""
Skills 执行器

执行各种技能
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .registry import skill_registry


class SkillExecutor:
    """技能执行器"""
    
    def __init__(self, deepseek_service=None):
        """
        初始化技能执行器
        
        Args:
            deepseek_service: DeepSeek 服务实例
        """
        self.deepseek = deepseek_service
    
    def set_deepseek_service(self, service):
        """设置 DeepSeek 服务"""
        self.deepseek = service
    
    async def execute(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果
        """
        
        skill = skill_registry.get(skill_id)
        if not skill:
            return {"error": f"技能不存在: {skill_id}"}
        
        # 根据技能类型执行
        try:
            if skill_id == "web_reading":
                return await self._execute_web_reading(input_data, context)
            
            elif skill_id == "research_analysis":
                return await self._execute_research(input_data, context)
            
            elif skill_id == "data_mining":
                return await self._execute_data_mining(input_data, context)
            
            elif skill_id == "data_cleaning":
                return await self._execute_data_cleaning(input_data, context)
            
            elif skill_id == "presentation_generation":
                return await self._execute_ppt_generation(input_data, context)
            
            elif skill_id == "spreadsheet_generation":
                return await self._execute_excel_generation(input_data, context)
            
            elif skill_id == "document_generation":
                return await self._execute_doc_generation(input_data, context)
            
            elif skill_id == "ocr_processing":
                return await self._execute_ocr(input_data, context)
            
            elif skill_id == "code_generation":
                return await self._execute_code_generation(input_data, context)
            
            elif skill_id == "code_review":
                return await self._execute_code_review(input_data, context)
            
            else:
                return await self._execute_generic(skill, input_data, context)
                
        except Exception as e:
            return {
                "error": str(e),
                "skill": skill_id
            }
    
    async def _execute_web_reading(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行网页读取"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        url = input_data.get("url", "")
        query = input_data.get("query", "")
        
        prompt = f"""请分析以下网页内容：

URL: {url}
用户查询: {query}

上下文: {context or '无'}

请提供：
1. 网页主题
2. 关键信息提取
3. 内容摘要
4. 相关数据点
"""
        
        messages = [
            {"role": "system", "content": "你是网页内容分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        
        return {
            "skill": "web_reading",
            "result": response["choices"][0]["message"]["content"],
            "url": url
        }
    
    async def _execute_research(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行调研分析"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        topic = input_data.get("topic", "")
        requirements = input_data.get("requirements", "")
        
        prompt = f"""请对以下主题进行深度调研分析：

主题: {topic}
要求: {requirements}

上下文: {context or '无'}

请提供：
1. 背景介绍
2. 现状分析
3. 关键发现
4. 建议结论
"""
        
        messages = [
            {"role": "system", "content": "你是调研分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        
        return {
            "skill": "research_analysis",
            "result": response["choices"][0]["message"]["content"]
        }
    
    async def _execute_data_mining(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行数据挖掘"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        import json
        
        data = input_data.get("data", {})
        analysis_type = input_data.get("analysis_type", "general")
        
        prompt = f"""请对以下数据进行挖掘分析：

分析类型: {analysis_type}

数据:
{json.dumps(data, ensure_ascii=False, indent=2)}

上下文: {json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}

请提供：
1. 数据概览
2. 模式发现
3. 异常检测
4. 关键洞察
5. 可视化建议
"""
        
        messages = [
            {"role": "system", "content": "你是数据挖掘专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        
        return {
            "skill": "data_mining",
            "result": response["choices"][0]["message"]["content"]
        }
    
    async def _execute_data_cleaning(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行数据清洗"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        import json
        
        data = input_data.get("data", {})
        rules = input_data.get("rules", [])
        
        prompt = f"""请对以下数据进行清洗：

数据:
{json.dumps(data, ensure_ascii=False, indent=2)}

清洗规则: {rules or '自动检测'}

请提供：
1. 数据质量报告
2. 清洗建议
3. 清洗后的数据描述
"""
        
        messages = [
            {"role": "system", "content": "你是数据清洗专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        
        return {
            "skill": "data_cleaning",
            "result": response["choices"][0]["message"]["content"]
        }
    
    async def _execute_ppt_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 PPT 生成"""
        
        from ..file_generators import file_generator
        
        request = input_data.get("request", "")
        context_str = str(context) if context else None
        
        content = await file_generator.generate_ppt(
            user_request=request,
            context=context_str
        )
        
        return {
            "skill": "presentation_generation",
            "content": content,
            "format": "pptx"
        }
    
    async def _execute_excel_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 Excel 生成"""
        
        from ..file_generators import file_generator
        
        request = input_data.get("request", "")
        data = input_data.get("data")
        
        content = await file_generator.generate_excel(
            user_request=request,
            context=str(data) if data else str(context)
        )
        
        return {
            "skill": "spreadsheet_generation",
            "content": content,
            "format": "xlsx"
        }
    
    async def _execute_doc_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行文档生成"""
        
        from ..file_generators import file_generator
        
        request = input_data.get("request", "")
        data = input_data.get("data", context)
        
        content = await file_generator.generate_word_report(
            user_request=request,
            data=data
        )
        
        return {
            "skill": "document_generation",
            "content": content,
            "format": "docx"
        }
    
    async def _execute_ocr(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行 OCR"""
        
        from ..file_processors import get_processor
        from pathlib import Path
        
        image_path = input_data.get("image_path", "")
        
        if not image_path:
            return {"error": "未提供图片路径"}
        
        processor = get_processor('.png')  # 使用图片处理器
        
        if processor is None:
            return {"error": "OCR 处理器未初始化"}
        
        try:
            text = await processor.to_text(Path(image_path))
            
            return {
                "skill": "ocr_processing",
                "result": text,
                "image_path": image_path
            }
        except Exception as e:
            return {
                "error": str(e),
                "skill": "ocr_processing"
            }
    
    async def _execute_code_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行代码生成"""
        
        from ..file_generators import file_generator
        
        request = input_data.get("request", "")
        language = input_data.get("language", "python")
        
        code = await file_generator.generate_code(
            user_request=request,
            language=language,
            context=str(context) if context else None
        )
        
        return {
            "skill": "code_generation",
            "code": code,
            "language": language
        }
    
    async def _execute_code_review(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行代码审查"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        code = input_data.get("code", "")
        language = input_data.get("language", "python")
        
        prompt = f"""请审查以下{language}代码：

```
{code}
```

请提供：
1. 代码质量评估
2. 潜在问题
3. 安全风险
4. 性能优化建议
5. 最佳实践建议
"""
        
        messages = [
            {"role": "system", "content": f"你是{language}代码审查专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        
        return {
            "skill": "code_review",
            "result": response["choices"][0]["message"]["content"],
            "language": language
        }
    
    async def _execute_generic(
        self,
        skill: Any,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行通用技能"""
        
        if self.deepseek is None:
            return {"error": "DeepSeek 服务未初始化"}
        
        import json
        
        prompt = f"""请执行以下技能：

技能名称: {skill.name}
技能描述: {skill.description}

输入数据:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

上下文:
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}
"""
        
        messages = [
            {"role": "system", "content": f"你是{skill.name}专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        
        return {
            "skill": skill.id,
            "result": response["choices"][0]["message"]["content"]
        }


# 全局执行器实例
skill_executor = SkillExecutor()
