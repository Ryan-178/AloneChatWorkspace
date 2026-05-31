"""
Skills 注册中心

管理和注册所有可用技能
"""

from typing import Dict, Any, Callable, Optional, List
from pydantic import BaseModel


class SkillDefinition(BaseModel):
    """技能定义"""
    
    id: str
    name: str
    description: str
    icon: str
    category: str
    input_types: List[str]
    output_types: List[str]
    required_tools: List[str]
    executor: Optional[Callable] = None
    
    class Config:
        arbitrary_types_allowed = True


class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        """注册内置技能"""
        
        # 信息获取类
        self.register(SkillDefinition(
            id="web_reading",
            name="网页读取",
            description="读取网页内容，提取关键信息，支持中文和英文网页",
            icon="Globe",
            category="information",
            input_types=["url", "text"],
            output_types=["text", "json"],
            required_tools=["web_search", "file_reader"]
        ))
        
        self.register(SkillDefinition(
            id="research_analysis",
            name="调研分析",
            description="深度调研分析，生成专业报告，支持多源信息整合",
            icon="Search",
            category="analysis",
            input_types=["text", "data"],
            output_types=["document", "report"],
            required_tools=["web_search", "data_processor"]
        ))
        
        # 数据处理类
        self.register(SkillDefinition(
            id="data_mining",
            name="数据挖掘",
            description="数据挖掘与分析，发现数据洞察，支持统计分析和可视化建议",
            icon="BarChart",
            category="analysis",
            input_types=["file", "data"],
            output_types=["report", "chart", "spreadsheet"],
            required_tools=["data_processor", "chart_generator"]
        ))
        
        self.register(SkillDefinition(
            id="data_cleaning",
            name="数据清洗",
            description="数据清洗和预处理，处理缺失值、异常值、重复数据",
            icon="Filter",
            category="analysis",
            input_types=["data"],
            output_types=["data"],
            required_tools=["data_processor"]
        ))
        
        # 文件处理类
        self.register(SkillDefinition(
            id="file_management",
            name="文件管理",
            description="文件处理、格式转换、内容编辑，支持多种文件格式",
            icon="FileText",
            category="productivity",
            input_types=["file"],
            output_types=["file"],
            required_tools=["file_reader", "file_writer"]
        ))
        
        self.register(SkillDefinition(
            id="ocr_processing",
            name="OCR识别",
            description="图片文字识别，支持中英文，提取图片中的文本内容",
            icon="Scan",
            category="processing",
            input_types=["image"],
            output_types=["text"],
            required_tools=["ocr"]
        ))
        
        # 文档生成类
        self.register(SkillDefinition(
            id="presentation_generation",
            name="PPT生成",
            description="自动生成专业演示文稿，支持多种模板和风格",
            icon="Presentation",
            category="generation",
            input_types=["text", "data"],
            output_types=["pptx"],
            required_tools=["file_writer"]
        ))
        
        self.register(SkillDefinition(
            id="spreadsheet_generation",
            name="Excel生成",
            description="自动生成数据报表，支持公式、图表、格式化",
            icon="Table",
            category="generation",
            input_types=["data", "text"],
            output_types=["xlsx"],
            required_tools=["file_writer", "data_processor"]
        ))
        
        self.register(SkillDefinition(
            id="document_generation",
            name="文档生成",
            description="自动生成专业文档报告，支持多种文档结构",
            icon="FileText",
            category="generation",
            input_types=["text", "data"],
            output_types=["docx", "pdf"],
            required_tools=["file_writer"]
        ))
        
        # 代码类
        self.register(SkillDefinition(
            id="code_generation",
            name="代码生成",
            description="生成高质量代码，支持多种编程语言",
            icon="Code",
            category="development",
            input_types=["text"],
            output_types=["code"],
            required_tools=[]
        ))
        
        self.register(SkillDefinition(
            id="code_review",
            name="代码审查",
            description="代码审查和优化建议，发现潜在问题",
            icon="GitBranch",
            category="development",
            input_types=["code"],
            output_types=["report"],
            required_tools=[]
        ))
    
    def register(self, skill: SkillDefinition):
        """
        注册技能
        
        Args:
            skill: 技能定义
        """
        self._skills[skill.id] = skill
    
    def unregister(self, skill_id: str) -> bool:
        """
        注销技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            是否成功
        """
        if skill_id in self._skills:
            del self._skills[skill_id]
            return True
        return False
    
    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        """
        获取技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            技能定义
        """
        return self._skills.get(skill_id)
    
    def list_all(self) -> List[SkillDefinition]:
        """
        列出所有技能
        
        Returns:
            技能列表
        """
        return list(self._skills.values())
    
    def get_by_category(self, category: str) -> List[SkillDefinition]:
        """
        按类别获取技能
        
        Args:
            category: 类别名称
            
        Returns:
            技能列表
        """
        return [s for s in self._skills.values() if s.category == category]
    
    def get_categories(self) -> List[str]:
        """
        获取所有类别
        
        Returns:
            类别列表
        """
        categories = set(s.category for s in self._skills.values())
        return sorted(list(categories))
    
    def search(self, query: str) -> List[SkillDefinition]:
        """
        搜索技能
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的技能列表
        """
        query = query.lower()
        results = []
        
        for skill in self._skills.values():
            if (query in skill.name.lower() or 
                query in skill.description.lower() or
                query in skill.category.lower()):
                results.append(skill)
        
        return results


# 全局注册中心实例
skill_registry = SkillRegistry()
