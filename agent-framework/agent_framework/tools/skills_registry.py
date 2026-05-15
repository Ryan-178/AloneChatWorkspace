"""
Skills注册系统 - Skills Registry
管理和注册可复用的技能
"""
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field

from agent_framework.core.task import Task


class SkillMetadata(BaseModel):
    """Skill元数据"""
    name: str = Field(..., description="Skill名称")
    description: str = Field(..., description="Skill描述")
    version: str = Field(default="1.0.0", description="版本号")
    author: str = Field(default="unknown", description="作者")
    dependencies: List[str] = Field(default_factory=list, description="依赖的其他Skill")
    tags: List[str] = Field(default_factory=list, description="标签")
    category: str = Field(default="general", description="分类")
    enabled: bool = Field(default=True, description="是否启用")


class Skill:
    """Skill基类"""
    
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self._workflow: List[Callable] = []
        self._tools: List[Any] = []
        self._templates: Dict[str, str] = {}
    
    def get_workflow(self) -> List[Callable]:
        """获取工作流"""
        return self._workflow
    
    def get_tools(self) -> List[Any]:
        """获取工具列表"""
        return self._tools
    
    def get_templates(self) -> Dict[str, str]:
        """获取模板"""
        return self._templates
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Skill"""
        results = []
        for step in self._workflow:
            try:
                result = await step(context) if callable(step) else step
                results.append(result)
                context.update(result if isinstance(result, dict) else {})
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "partial_results": results,
                }
        
        return {
            "success": True,
            "results": results,
            "context": context,
        }


class SkillsRegistry:
    """Skills注册表"""
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, skill: Skill) -> None:
        """注册Skill"""
        name = skill.metadata.name
        
        if name in self._skills:
            raise ValueError(f"Skill '{name}' already registered")
        
        missing_deps = self.check_dependencies(skill.metadata.dependencies)
        if missing_deps:
            raise ValueError(f"Missing dependencies for '{name}': {missing_deps}")
        
        self._skills[name] = skill
        
        category = skill.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)
    
    def unregister(self, name: str) -> bool:
        """卸载Skill"""
        if name not in self._skills:
            return False
        
        skill = self._skills[name]
        category = skill.metadata.category
        
        del self._skills[name]
        
        if category in self._categories and name in self._categories[category]:
            self._categories[category].remove(name)
        
        return True
    
    def get(self, name: str) -> Optional[Skill]:
        """获取Skill"""
        return self._skills.get(name)
    
    def list(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """列出所有Skills"""
        if category:
            names = self._categories.get(category, [])
            return [self._skills[name].metadata for name in names if name in self._skills]
        
        return [skill.metadata for skill in self._skills.values()]
    
    def check_dependencies(self, dependencies: List[str]) -> List[str]:
        """检查Skill依赖"""
        missing = []
        for dep in dependencies:
            if dep not in self._skills:
                missing.append(dep)
        return missing
    
    def load_skill(self, skill_path: str) -> Optional[Skill]:
        """加载Skill模块"""
        try:
            path = Path(skill_path)
            if not path.exists():
                return None
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("skill_module", path / "__init__.py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "get_skill"):
                    skill = module.get_skill()
                    self.register(skill)
                    return skill
            
            return None
        except Exception:
            return None
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())
    
    def search(self, query: str) -> List[SkillMetadata]:
        """搜索Skills"""
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            metadata = skill.metadata
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append(metadata)
        
        return results
    
    def enable(self, name: str) -> bool:
        """启用Skill"""
        skill = self.get(name)
        if skill:
            skill.metadata.enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用Skill"""
        skill = self.get(name)
        if skill:
            skill.metadata.enabled = False
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_skills": len(self._skills),
            "total_categories": len(self._categories),
            "enabled_skills": sum(1 for s in self._skills.values() if s.metadata.enabled),
            "categories": {cat: len(skills) for cat, skills in self._categories.items()},
        }


class DocumentGenerationSkill(Skill):
    """文档生成Skill"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="document_generation",
            description="生成各类专业文档，支持Markdown、Word、PDF等格式",
            version="1.0.0",
            author="system",
            dependencies=[],
            tags=["document", "generation", "writing"],
            category="document",
        )
        super().__init__(metadata)
        
        self._templates = {
            "report": "# {title}\n\n## 概述\n\n{summary}\n\n## 详细内容\n\n{content}\n\n## 结论\n\n{conclusion}",
            "proposal": "# {title}\n\n## 背景\n\n{background}\n\n## 方案\n\n{solution}\n\n## 预期效果\n\n{expected}",
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        title = context.get("title", "未命名文档")
        content = context.get("content", "")
        template_name = context.get("template", "report")
        
        template = self._templates.get(template_name, "{content}")
        
        try:
            document = template.format(
                title=title,
                content=content,
                summary=context.get("summary", ""),
                conclusion=context.get("conclusion", ""),
                background=context.get("background", ""),
                solution=context.get("solution", ""),
                expected=context.get("expected", ""),
            )
        except KeyError:
            document = content
        
        return {
            "success": True,
            "document": document,
            "title": title,
            "template": template_name,
        }


class DataAnalysisSkill(Skill):
    """数据分析Skill"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="data_analysis",
            description="执行数据分析，包括统计计算、趋势分析、可视化",
            version="1.0.0",
            author="system",
            dependencies=[],
            tags=["data", "analysis", "statistics"],
            category="data",
        )
        super().__init__(metadata)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        data = context.get("data", [])
        analysis_type = context.get("analysis_type", "summary")
        
        if not data:
            return {"success": False, "error": "数据为空"}
        
        if analysis_type == "summary":
            if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
                n = len(data)
                total = sum(data)
                mean = total / n
                sorted_data = sorted(data)
                median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n//2-1] + sorted_data[n//2]) / 2
                
                result = {
                    "count": n,
                    "sum": total,
                    "mean": mean,
                    "median": median,
                    "min": min(data),
                    "max": max(data),
                }
            else:
                result = {"data": data, "type": type(data).__name__}
        else:
            result = {"data": data, "analysis_type": analysis_type}
        
        return {"success": True, "analysis": result}


class WebResearchSkill(Skill):
    """网络调研Skill"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="web_research",
            description="执行网络信息搜索和整理",
            version="1.0.0",
            author="system",
            dependencies=[],
            tags=["research", "search", "web"],
            category="research",
        )
        super().__init__(metadata)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get("query", "")
        num_results = context.get("num_results", 5)
        
        results = [
            {
                "title": f"搜索结果 {i+1}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"关于 '{query}' 的相关信息...",
            }
            for i in range(num_results)
        ]
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results),
        }


class PPTGenerationSkill(Skill):
    """PPT生成Skill"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="ppt_generation",
            description="自动生成演示文稿",
            version="1.0.0",
            author="system",
            dependencies=[],
            tags=["ppt", "presentation", "slides"],
            category="document",
        )
        super().__init__(metadata)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        title = context.get("title", "演示文稿")
        slides = context.get("slides", [])
        
        if not slides:
            slides = [
                {"title": "封面", "content": title},
                {"title": "概述", "content": "内容概述"},
                {"title": "总结", "content": "谢谢观看"},
            ]
        
        return {
            "success": True,
            "title": title,
            "slides": slides,
            "total_slides": len(slides),
        }


class ReportGenerationSkill(Skill):
    """报告生成Skill"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="report_generation",
            description="生成专业分析报告",
            version="1.0.0",
            author="system",
            dependencies=[],
            tags=["report", "analysis", "document"],
            category="document",
        )
        super().__init__(metadata)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        title = context.get("title", "分析报告")
        sections = context.get("sections", [])
        
        report_lines = [f"# {title}", ""]
        
        for section in sections:
            section_title = section.get("title", "")
            section_content = section.get("content", "")
            report_lines.append(f"## {section_title}")
            report_lines.append(f"{section_content}")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        return {
            "success": True,
            "report": report,
            "title": title,
            "sections": len(sections),
        }


def register_builtin_skills(registry: SkillsRegistry) -> None:
    """注册内置Skills"""
    registry.register(DocumentGenerationSkill())
    registry.register(DataAnalysisSkill())
    registry.register(WebResearchSkill())
    registry.register(PPTGenerationSkill())
    registry.register(ReportGenerationSkill())
