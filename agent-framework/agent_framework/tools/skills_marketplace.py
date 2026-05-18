"""
Skills市场接口 - Skills Marketplace
管理Skills的安装、卸载、搜索等
支持从远程仓库（GitHub/skills.sh）安装

增强功能 / Enhanced Features:
- 按名称、描述、市场过滤 / Filter by name, description, marketplace
- 多条件组合搜索 / Multi-condition combined search
- 排序和分页 / Sorting and pagination

版本 / Version: 2.0.73
"""
import shutil
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from enum import Enum

from agent_framework.tools.skills_registry import SkillsRegistry, SkillMetadata
from agent_framework.tools.skills_sh_client import (
    SkillsShClient,
    GitHubUrlParser,
    RemoteSkill,
)


class SearchFilter(BaseModel):
    """搜索过滤器 / Search filter"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    marketplace: Optional[str] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    enabled_only: bool = True


class SortBy(str, Enum):
    """排序方式 / Sort by"""
    NAME = "name"
    RATING = "rating"
    INSTALLS = "installs"
    UPDATED = "updated"
    CREATED = "created"


class SkillRating(BaseModel):
    """Skill评价"""
    skill_name: str
    rating: float
    reviews: int
    comments: List[Dict[str, Any]]


class SkillsMarketplace:
    """
    Skills市场 / Skills Marketplace
    
    增强功能 / Enhanced Features:
    - advanced_search(): 高级搜索 / Advanced search
    - search_by_name(): 按名称搜索 / Search by name
    - search_by_description(): 按描述搜索 / Search by description
    - search_by_marketplace(): 按市场搜索 / Search by marketplace
    """
    
    def __init__(self, registry: SkillsRegistry, skills_dir: Optional[Path] = None):
        self.registry = registry
        self._ratings: Dict[str, SkillRating] = {}
        self._installed: Dict[str, Dict[str, Any]] = {}
        self._remote_client = SkillsShClient()
        self._skills_dir = skills_dir or Path.home() / ".skills"
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self._marketplaces: Dict[str, Dict[str, Any]] = {}
    
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
    
    def advanced_search(
        self,
        filter: Optional[SearchFilter] = None,
        sort_by: SortBy = SortBy.NAME,
        reverse: bool = False,
        limit: int = 50,
        offset: int = 0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        高级搜索 / Advanced search
        
        支持多条件组合搜索、排序和分页 / Supports multi-condition search, sorting and pagination
        
        Args:
            filter: 搜索过滤器 / Search filter
            sort_by: 排序方式 / Sort by
            reverse: 是否倒序 / Whether reverse
            limit: 结果数量限制 / Result limit
            offset: 偏移量 / Offset
            **kwargs: 直接指定过滤条件 / Direct filter conditions
        
        Returns:
            搜索结果列表 / Search results
        """
        if filter is None:
            filter = SearchFilter(**kwargs)
        
        all_skills = self.registry.list()
        results = []
        
        for metadata in all_skills:
            if filter.enabled_only and not metadata.enabled:
                continue
            
            if filter.name and filter.name.lower() not in metadata.name.lower():
                continue
            
            if filter.description and filter.description.lower() not in metadata.description.lower():
                continue
            
            if filter.category and metadata.category != filter.category:
                continue
            
            if filter.tags:
                if not any(tag in metadata.tags for tag in filter.tags):
                    continue
            
            if filter.author and filter.author.lower() not in metadata.author.lower():
                continue
            
            rating = self._ratings.get(metadata.name, SkillRating(
                skill_name=metadata.name,
                rating=0.0,
                reviews=0,
                comments=[],
            )).rating
            
            if filter.min_rating is not None and rating < filter.min_rating:
                continue
            
            if filter.max_rating is not None and rating > filter.max_rating:
                continue
            
            skill_info = metadata.model_dump()
            skill_info["rating"] = rating
            skill_info["installed"] = metadata.name in self._installed
            
            if filter.marketplace:
                installed_info = self._installed.get(metadata.name, {})
                source = installed_info.get("source", "")
                if filter.marketplace.lower() not in source.lower():
                    continue
            
            results.append(skill_info)
        
        results = self._sort_results(results, sort_by, reverse)
        
        return results[offset:offset + limit]
    
    def _sort_results(
        self,
        results: List[Dict[str, Any]],
        sort_by: SortBy,
        reverse: bool
    ) -> List[Dict[str, Any]]:
        """排序结果 / Sort results"""
        key_map = {
            SortBy.NAME: lambda x: x.get("name", ""),
            SortBy.RATING: lambda x: x.get("rating", 0),
            SortBy.INSTALLS: lambda x: x.get("installs", 0),
            SortBy.UPDATED: lambda x: x.get("updated_at", ""),
            SortBy.CREATED: lambda x: x.get("created_at", ""),
        }
        
        key_func = key_map.get(sort_by, key_map[SortBy.NAME])
        return sorted(results, key=key_func, reverse=reverse)
    
    def search_by_name(
        self,
        name: str,
        exact: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        按名称搜索 / Search by name
        
        Args:
            name: 名称关键词 / Name keyword
            exact: 是否精确匹配 / Whether exact match
            limit: 结果数量限制 / Result limit
        
        Returns:
            搜索结果 / Search results
        """
        filter = SearchFilter(enabled_only=False)
        all_skills = self.registry.list()
        results = []
        
        for metadata in all_skills:
            if exact:
                if metadata.name != name:
                    continue
            else:
                if name.lower() not in metadata.name.lower():
                    continue
            
            skill_info = metadata.model_dump()
            skill_info["rating"] = self._ratings.get(metadata.name, SkillRating(
                skill_name=metadata.name,
                rating=0.0,
                reviews=0,
                comments=[],
            )).rating
            results.append(skill_info)
        
        return results[:limit]
    
    def search_by_description(
        self,
        description: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        按描述搜索 / Search by description
        
        Args:
            description: 描述关键词 / Description keyword
            limit: 结果数量限制 / Result limit
        
        Returns:
            搜索结果 / Search results
        """
        return self.advanced_search(
            filter=SearchFilter(description=description, enabled_only=False),
            limit=limit,
        )
    
    def search_by_marketplace(
        self,
        marketplace: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        按市场搜索 / Search by marketplace
        
        搜索从特定市场安装的技能 / Search skills installed from specific marketplace
        
        Args:
            marketplace: 市场名称（如 github, skills.sh）/ Marketplace name
            limit: 结果数量限制 / Result limit
        
        Returns:
            搜索结果 / Search results
        """
        results = []
        
        for name, info in self._installed.items():
            source = info.get("source", "")
            if marketplace.lower() in source.lower():
                skill = self.registry.get(name)
                if skill:
                    skill_info = skill.metadata.model_dump()
                    skill_info["rating"] = self._ratings.get(name, SkillRating(
                        skill_name=name,
                        rating=0.0,
                        reviews=0,
                        comments=[],
                    )).rating
                    skill_info["installed"] = True
                    skill_info["install_info"] = info
                    results.append(skill_info)
        
        return results[:limit]
    
    def search_combined(
        self,
        query: str,
        search_in: List[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        组合搜索 / Combined search
        
        同时在名称、描述、标签中搜索 / Search in name, description, tags simultaneously
        
        Args:
            query: 搜索关键词 / Search query
            search_in: 搜索范围（name, description, tags）/ Search scope
            limit: 结果数量限制 / Result limit
        
        Returns:
            搜索结果 / Search results
        """
        if search_in is None:
            search_in = ["name", "description", "tags"]
        
        all_skills = self.registry.list()
        results = []
        query_lower = query.lower()
        
        for metadata in all_skills:
            score = 0
            
            if "name" in search_in and query_lower in metadata.name.lower():
                score += 10
            
            if "description" in search_in and query_lower in metadata.description.lower():
                score += 5
            
            if "tags" in search_in:
                for tag in metadata.tags:
                    if query_lower in tag.lower():
                        score += 3
            
            if score > 0:
                skill_info = metadata.model_dump()
                skill_info["rating"] = self._ratings.get(metadata.name, SkillRating(
                    skill_name=metadata.name,
                    rating=0.0,
                    reviews=0,
                    comments=[],
                )).rating
                skill_info["search_score"] = score
                results.append(skill_info)
        
        results.sort(key=lambda x: x.get("search_score", 0), reverse=True)
        
        return results[:limit]
    
    def register_marketplace(self, name: str, url: str, **kwargs) -> None:
        """
        注册市场 / Register marketplace
        
        Args:
            name: 市场名称 / Marketplace name
            url: 市场URL / Marketplace URL
            **kwargs: 其他配置 / Other config
        """
        self._marketplaces[name] = {
            "name": name,
            "url": url,
            **kwargs,
        }
    
    def list_marketplaces(self) -> List[Dict[str, Any]]:
        """列出所有市场 / List all marketplaces"""
        return list(self._marketplaces.values())
    
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
    
    async def search_remote(self, query: str) -> List[RemoteSkill]:
        """搜索远程 Skills (skills.sh)"""
        return await self._remote_client.search_skills_sh(query)
    
    async def get_remote_skill(
        self,
        owner: str,
        repo: str,
        skill_name: Optional[str] = None,
        branch: str = "main",
    ) -> Optional[RemoteSkill]:
        """获取远程 Skill 信息"""
        return await self._remote_client.get_github_skill(owner, repo, skill_name, branch)
    
    async def install_from_remote(
        self,
        url: str,
        skill_name: Optional[str] = None,
        branch: Optional[str] = None,
        global_install: bool = False,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        从远程 URL 安装 Skill
        
        Args:
            url: GitHub URL 或 skills.sh URL
            skill_name: 指定的 skill 名称
            branch: 指定的分支
            global_install: 是否全局安装
            force: 强制覆盖已存在的 skill
        
        Returns:
            安装结果
        """
        parsed = GitHubUrlParser.parse(url)
        
        if not parsed:
            return {
                "success": False,
                "error": f"无法解析 URL: {url}",
            }
        
        owner = parsed["owner"]
        repo = parsed["repo"]
        
        if parsed["type"] == "github":
            branch = branch or parsed.get("branch", "main")
            path = parsed.get("path", "")
            
            if skill_name:
                skill_path = f"skills/{skill_name}"
            elif path and "/skills/" in path:
                parts = path.split("/skills/")
                if len(parts) > 1:
                    skill_path = f"skills/{parts[1].strip('/')}"
                else:
                    skill_path = "skills"
            else:
                skill_path = "skills"
        else:
            branch = branch or "main"
            skill_name = skill_name or parsed.get("skill_name", "")
            skill_path = f"skills/{skill_name}" if skill_name else "skills"
        
        files = await self._remote_client.download_skill_content(owner, repo, skill_path, branch)
        
        if not files:
            return {
                "success": False,
                "error": "下载失败: 未找到 skill 文件",
            }
        
        skill_md_content = files.get("SKILL.md")
        if not skill_md_content:
            for name, content in files.items():
                if name.lower() == "skill.md":
                    skill_md_content = content
                    break
        
        actual_skill_name = skill_name
        if not actual_skill_name:
            if skill_md_content:
                import re
                name_match = re.search(r"^name:\s*(.+)$", skill_md_content, re.MULTILINE)
                if name_match:
                    actual_skill_name = name_match.group(1).strip()
            
            if not actual_skill_name:
                actual_skill_name = skill_path.split("/")[-1] or repo
        
        if global_install:
            install_path = self._skills_dir / actual_skill_name
        else:
            install_path = Path.cwd() / ".skills" / actual_skill_name
        
        if install_path.exists() and not force:
            return {
                "success": False,
                "error": f"Skill '{actual_skill_name}' 已存在",
                "path": str(install_path),
                "hint": "使用 force=True 强制覆盖",
            }
        
        install_path.mkdir(parents=True, exist_ok=True)
        
        installed_files = []
        for file_name, content in files.items():
            file_path = install_path / file_name
            file_path.write_text(content, encoding="utf-8")
            installed_files.append(file_name)
        
        self._installed[actual_skill_name] = {
            "path": str(install_path),
            "installed_at": datetime.utcnow().isoformat(),
            "source": f"github:{owner}/{repo}",
            "branch": branch,
            "files": installed_files,
        }
        
        return {
            "success": True,
            "skill": actual_skill_name,
            "path": str(install_path),
            "files": installed_files,
            "source": f"github:{owner}/{repo}",
        }
    
    def uninstall_remote(self, name: str) -> Dict[str, Any]:
        """卸载远程安装的 Skill"""
        local_path = Path.cwd() / ".skills" / name
        global_path = self._skills_dir / name
        
        removed_paths = []
        
        if local_path.exists():
            shutil.rmtree(local_path)
            removed_paths.append(str(local_path))
        
        if global_path.exists():
            shutil.rmtree(global_path)
            removed_paths.append(str(global_path))
        
        if not removed_paths:
            return {
                "success": False,
                "error": f"Skill '{name}' 未找到",
            }
        
        if name in self._installed:
            del self._installed[name]
        
        return {
            "success": True,
            "skill": name,
            "removed_paths": removed_paths,
        }
    
    def list_installed_remote(self) -> List[Dict[str, Any]]:
        """列出远程安装的 Skills"""
        result = []
        
        local_skills_dir = Path.cwd() / ".skills"
        global_skills_dir = self._skills_dir
        
        for skills_dir, scope in [(local_skills_dir, "local"), (global_skills_dir, "global")]:
            if skills_dir.exists():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        if skill_md.exists():
                            info = {
                                "name": skill_dir.name,
                                "path": str(skill_dir),
                                "scope": scope,
                            }
                            if skill_dir.name in self._installed:
                                info.update(self._installed[skill_dir.name])
                            result.append(info)
        
        return result
    
    async def close(self):
        """关闭客户端"""
        await self._remote_client.close()
