"""
文件生成服务

使用 DeepSeek 生成各种格式的文件
"""

from typing import Optional, Dict, Any
from pathlib import Path
import json

from .prompts import FILE_GENERATION_PROMPTS


class FileGeneratorService:
    """文件生成服务"""
    
    def __init__(self, deepseek_service=None):
        """
        初始化文件生成服务
        
        Args:
            deepseek_service: DeepSeek 服务实例
        """
        self.deepseek = deepseek_service
    
    def set_deepseek_service(self, service):
        """设置 DeepSeek 服务"""
        self.deepseek = service
    
    async def generate_ppt(
        self,
        user_request: str,
        context: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        生成 PPT 演示文稿
        
        Args:
            user_request: 用户需求描述
            context: 上下文信息
            output_path: 输出路径（可选）
            
        Returns:
            生成的幻灯片内容文本
        """
        
        if self.deepseek is None:
            return "[错误] DeepSeek 服务未初始化"
        
        # 构建提示词
        prompt = FILE_GENERATION_PROMPTS["ppt"].format(
            user_request=user_request,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": "你是演示文稿设计专家，擅长创建结构清晰、内容专业的PPT。"},
            {"role": "user", "content": prompt}
        ]
        
        # 调用 DeepSeek
        response = await self.deepseek.chat_completion(messages)
        slide_content = response["choices"][0]["message"]["content"]
        
        # 如果指定了输出路径，生成实际文件
        if output_path:
            from ..file_processors import get_processor
            processor = get_processor('.pptx')
            if processor:
                await processor.from_text(slide_content, output_path)
        
        return slide_content
    
    async def generate_excel(
        self,
        user_request: str,
        context: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        生成 Excel 数据报表
        
        Args:
            user_request: 用户需求描述
            context: 上下文信息
            output_path: 输出路径（可选）
            
        Returns:
            生成的数据内容文本
        """
        
        if self.deepseek is None:
            return "[错误] DeepSeek 服务未初始化"
        
        prompt = FILE_GENERATION_PROMPTS["excel"].format(
            user_request=user_request,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": "你是数据分析专家，擅长创建结构化的数据报表。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages)
        data_content = response["choices"][0]["message"]["content"]
        
        if output_path:
            from ..file_processors import get_processor
            processor = get_processor('.xlsx')
            if processor:
                await processor.from_text(data_content, output_path)
        
        return data_content
    
    async def generate_word_report(
        self,
        user_request: str,
        data: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        生成 Word 复盘报告
        
        Args:
            user_request: 用户需求描述
            data: 数据字典
            output_path: 输出路径（可选）
            
        Returns:
            生成的报告内容文本
        """
        
        if self.deepseek is None:
            return "[错误] DeepSeek 服务未初始化"
        
        # 将数据转换为文本上下文
        context = self._format_data_context(data) if data else None
        
        prompt = FILE_GENERATION_PROMPTS["report"].format(
            user_request=user_request,
            context=context or "无数据信息"
        )
        
        messages = [
            {"role": "system", "content": "你是报告撰写专家，擅长撰写专业、全面的复盘报告。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=4000)
        report_content = response["choices"][0]["message"]["content"]
        
        if output_path:
            from ..file_processors import get_processor
            processor = get_processor('.docx')
            if processor:
                await processor.from_text(report_content, output_path)
        
        return report_content
    
    async def generate_code(
        self,
        user_request: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> str:
        """
        生成代码
        
        Args:
            user_request: 用户需求描述
            language: 编程语言
            context: 上下文信息
            
        Returns:
            生成的代码
        """
        
        if self.deepseek is None:
            return "[错误] DeepSeek 服务未初始化"
        
        prompt = FILE_GENERATION_PROMPTS["code"].format(
            user_request=user_request,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": f"你是{language}编程专家，擅长编写高质量、可维护的代码。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        return response["choices"][0]["message"]["content"]
    
    async def analyze_data(
        self,
        data: Any,
        user_request: str = "请分析这份数据"
    ) -> str:
        """
        分析数据
        
        Args:
            data: 数据（可以是字符串或字典）
            user_request: 分析需求
            
        Returns:
            分析结果
        """
        
        if self.deepseek is None:
            return "[错误] DeepSeek 服务未初始化"
        
        # 格式化数据
        if isinstance(data, dict):
            data_str = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            data_str = str(data)
        
        prompt = FILE_GENERATION_PROMPTS["data_analysis"].format(
            data=data_str,
            user_request=user_request
        )
        
        messages = [
            {"role": "system", "content": "你是数据分析专家，擅长从数据中发现洞察和规律。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.deepseek.chat_completion(messages, max_tokens=3000)
        return response["choices"][0]["message"]["content"]
    
    def _format_data_context(self, data: Dict[str, Any]) -> str:
        """格式化数据上下文"""
        return json.dumps(data, ensure_ascii=False, indent=2)


# 全局实例
file_generator = FileGeneratorService()
