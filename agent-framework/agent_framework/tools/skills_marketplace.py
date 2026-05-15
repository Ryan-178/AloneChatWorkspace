"""
Skills市场接口 - Skills Marketplace
管理Skills的安装、卸载、搜索等
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from agent_framework.tools.skills_registry import SkillsRegistry, SkillMetadata


class SkillRating(BaseModel):
    """Skill评价"""
    skill_name: str
    rating: float
    reviews: int
    comments: List[Dict[str, Any]]


class SkillsMarketplace:
    """Skills市场"""
    
    def __init__(self, registry: SkillsRegistry):
        self.registry = registry
        self._ratings: Dict[str, SkillRating] = {}
        self._installed: Dict[str, Dict[str, Any]] = {}
    
    def list_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """列出所有可用Skills"""
        skills = self.registry.list(category)
        
        result = []
        for metadata in skills:
            if enabled_only and not metadata.enabled:
                continue
            
            if tags:
                if not any(tag in metadata.tags for tag in tags):
                    continue
            
            skill_info = metadata.model_dump()
            skill_info["rating"] = self._ratings.get(metadata.name, SkillRating(
                skill_name=metadata.name,
                rating=0.0,
                reviews=0,
                comments=[],
            )).rating
            
            result.append(skill_info)
        
        return result
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索Skills"""
        results = self.registry.search(query)
        
        return [
            {
                **metadata.model_dump(),
                "rating": self._ratings.get(metadata.name, SkillRating(
                    skill_name=metadata.name,
                    rating=0.0,
                    reviews=0,
                    comments=[],
                )).rating,
            }
            for metadata in results
        ]
    
    def get_details(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Skill详情"""
        skill = self.registry.get(name)
        if not skill:
            return None
        
        metadata = skill.metadata
        rating = self._ratings.get(name, SkillRating(
            skill_name=name,
            rating=0.0,
            reviews=0,
            comments=[],
        ))
        
        return {
            **metadata.model_dump(),
            "rating": rating.rating,
            "reviews": rating.reviews,
            "comments": rating.comments[:10],
            "workflow_steps": len(skill.get_workflow()),
            "tools": [t.__class__.__name__ for t in skill.get_tools()],
            "templates": list(skill.get_templates().keys()),
        }
    
    def install(self, skill_path: str) -> Dict[str, Any]:
        """安装Skill"""
        skill = self.registry.load_skill(skill_path)
        
        if skill:
            self._installed[skill.metadata.name] = {
                "path": skill_path,
                "installed_at": datetime.utcnow().isoformat(),
                "version": skill.metadata.version,
            }
            
            return {
                "success": True,
                "skill": skill.metadata.name,
                "version": skill.metadata.version,
            }
        
        return {
            "success": False,
            "error": "无法加载Skill",
            "path": skill_path,
        }
    
    def uninstall(self, name: str) -> Dict[str, Any]:
        """卸载Skill"""
        success = self.registry.unregister(name)
        
        if success:
            if name in self._installed:
                del self._installed[name]
            if name in self._ratings:
                del self._ratings[name]
            
            return {"success": True, "skill": name}
        
        return {"success": False, "error": f"Skill '{name}' 不存在"}
    
    def get_ratings(self, name: str) -> Optional[Dict[str, Any]]:
        """获取Skill评价"""
        if name not in self._ratings:
            return None
        
        rating = self._ratings[name]
        return {
            "skill_name": rating.skill_name,
            "rating": rating.rating,
            "reviews": rating.reviews,
            "comments": rating.comments,
        }
    
    def add_rating(
        self,
        name: str,
        rating: float,
        comment: Optional[str] = None,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """添加评价"""
        if name not in self._ratings:
            self._ratings[name] = SkillRating(
                skill_name=name,
                rating=0.0,
                reviews=0,
                comments=[],
            )
        
        skill_rating = self._ratings[name]
        
        old_total = skill_rating.rating * skill_rating.reviews
        new_total = old_total + rating
        skill_rating.reviews += 1
        skill_rating.rating = new_total / skill_rating.reviews
        
        if comment:
            skill_rating.comments.append({
                "rating": rating,
                "comment": comment,
                "user": user or "anonymous",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return {
            "success": True,
            "skill_name": name,
            "new_rating": skill_rating.rating,
            "total_reviews": skill_rating.reviews,
        }
    
    def get_installed(self) -> List[Dict[str, Any]]:
        """获取已安装的Skills"""
        return [
            {
                "name": name,
                **info,
            }
            for name, info in self._installed.items()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取市场统计"""
        return {
            "total_skills": len(self.registry.list()),
            "installed_skills": len(self._installed),
            "rated_skills": len(self._ratings),
            "registry_stats": self.registry.get_stats(),
        }


from pydantic import BaseModel
