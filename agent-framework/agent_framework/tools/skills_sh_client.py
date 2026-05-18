"""
Skills.sh 和 GitHub 客户端
用于从远程仓库下载和安装 Skills
"""
import re
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field


class RemoteSkill(BaseModel):
    """远程 Skill 元数据"""
    id: str = Field(..., description="唯一标识，格式: owner/repo/skill-name")
    name: str = Field(..., description="Skill 名称")
    description: str = Field(default="", description="描述")
    owner: str = Field(..., description="GitHub owner")
    repo: str = Field(..., description="GitHub 仓库名")
    skill_path: str = Field(default="", description="Skill 在仓库中的路径")
    version: str = Field(default="1.0.0", description="版本")
    installs: int = Field(default=0, description="安装数")
    stars: int = Field(default=0, description="GitHub stars")
    url: str = Field(default="", description="skills.sh 链接")
    github_url: str = Field(..., description="GitHub 链接")
    raw_url: str = Field(default="", description="原始文件下载链接")


class GitHubUrlParser:
    """GitHub URL 解析器"""
    
    GITHUB_PATTERN = re.compile(
        r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)"
        r"(?:/(?:blob|tree)/(?P<branch>[^/]+))?"
        r"(?P<path>/.*)?"
    )
    
    SKILLS_SH_PATTERN = re.compile(
        r"https?://skills\.sh/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?P<skill_name>[^/]+)"
    )
    
    @classmethod
    def parse(cls, url: str) -> Optional[Dict[str, str]]:
        """解析 GitHub URL 或 skills.sh URL"""
        github_match = cls.GITHUB_PATTERN.match(url)
        if github_match:
            return {
                "type": "github",
                "owner": github_match.group("owner"),
                "repo": github_match.group("repo"),
                "branch": github_match.group("branch") or "main",
                "path": github_match.group("path") or "",
            }
        
        skills_match = cls.SKILLS_SH_PATTERN.match(url)
        if skills_match:
            return {
                "type": "skills_sh",
                "owner": skills_match.group("owner"),
                "repo": skills_match.group("repo"),
                "skill_name": skills_match.group("skill_name"),
            }
        
        return None
    
    @classmethod
    def to_raw_url(cls, owner: str, repo: str, path: str, branch: str = "main") -> str:
        """转换为 raw 文件 URL"""
        clean_path = path.lstrip("/")
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{clean_path}"
    
    @classmethod
    def to_api_url(cls, owner: str, repo: str, path: str = "", branch: str = "main") -> str:
        """转换为 GitHub API URL"""
        if path:
            clean_path = path.lstrip("/")
            return f"https://api.github.com/repos/{owner}/{repo}/contents/{clean_path}?ref={branch}"
        return f"https://api.github.com/repos/{owner}/{repo}/contents"


class SkillsShClient:
    """Skills.sh 和 GitHub 客户端"""
    
    SKILLS_SH_API = "https://skills.sh/api"
    GITHUB_API = "https://api.github.com"
    RAW_GITHUB = "https://raw.githubusercontent.com"
    
    def __init__(self, timeout: float = 30.0):
        self._client = httpx.AsyncClient(timeout=timeout)
        self._sync_client = httpx.Client(timeout=timeout)
    
    async def close(self):
        """关闭客户端"""
        await self._client.aclose()
        self._sync_client.close()
    
    async def search_skills_sh(self, query: str) -> List[RemoteSkill]:
        """搜索 skills.sh 上的 skill"""
        try:
            response = await self._client.get(
                f"{self.SKILLS_SH_API}/search",
                params={"q": query}
            )
            response.raise_for_status()
            data = response.json()
            
            skills = []
            for item in data.get("skills", []):
                skill = RemoteSkill(
                    id=f"{item['owner']}/{item['repo']}/{item['name']}",
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    owner=item["owner"],
                    repo=item["repo"],
                    url=item.get("url", ""),
                    github_url=item.get("github_url", ""),
                    installs=item.get("installs", 0),
                    stars=item.get("stars", 0),
                )
                skills.append(skill)
            
            return skills
        except Exception:
            return []
    
    async def get_github_skill(
        self,
        owner: str,
        repo: str,
        skill_name: Optional[str] = None,
        branch: str = "main",
    ) -> Optional[RemoteSkill]:
        """从 GitHub 获取 skill 信息"""
        try:
            if skill_name:
                skill_path = f"skills/{skill_name}"
            else:
                skill_path = "skills"
            
            api_url = GitHubUrlParser.to_api_url(owner, repo, skill_path, branch)
            response = await self._client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                for item in data:
                    if item.get("type") == "dir":
                        name = item.get("name", "")
                        skill_md_url = GitHubUrlParser.to_raw_url(
                            owner, repo, f"{skill_path}/{name}/SKILL.md", branch
                        )
                        return RemoteSkill(
                            id=f"{owner}/{repo}/{name}",
                            name=name,
                            owner=owner,
                            repo=repo,
                            skill_path=f"{skill_path}/{name}",
                            github_url=f"https://github.com/{owner}/{repo}",
                            raw_url=skill_md_url,
                        )
            else:
                name = skill_name or repo
                return RemoteSkill(
                    id=f"{owner}/{repo}/{name}",
                    name=name,
                    owner=owner,
                    repo=repo,
                    skill_path=skill_path,
                    github_url=f"https://github.com/{owner}/{repo}",
                    raw_url=GitHubUrlParser.to_raw_url(owner, repo, f"{skill_path}/SKILL.md", branch),
                )
            
            return None
        except Exception:
            return None
    
    async def download_skill_content(
        self,
        owner: str,
        repo: str,
        skill_path: str,
        branch: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """下载 skill 的所有文件内容"""
        try:
            api_url = GitHubUrlParser.to_api_url(owner, repo, skill_path, branch)
            response = await self._client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            files = {}
            
            if isinstance(data, list):
                for item in data:
                    if item.get("type") == "file":
                        file_name = item.get("name", "")
                        download_url = item.get("download_url", "")
                        if download_url:
                            file_response = await self._client.get(download_url)
                            if file_response.status_code == 200:
                                files[file_name] = file_response.text
            elif isinstance(data, dict) and data.get("type") == "file":
                download_url = data.get("download_url", "")
                if download_url:
                    file_response = await self._client.get(download_url)
                    if file_response.status_code == 200:
                        files[data.get("name", "SKILL.md")] = file_response.text
            
            return files if files else None
        except Exception:
            return None
    
    async def download_skill_md(
        self,
        owner: str,
        repo: str,
        skill_path: str,
        branch: str = "main",
    ) -> Optional[str]:
        """只下载 SKILL.md 文件"""
        try:
            skill_md_path = f"{skill_path}/SKILL.md" if not skill_path.endswith("SKILL.md") else skill_path
            raw_url = GitHubUrlParser.to_raw_url(owner, repo, skill_md_path, branch)
            response = await self._client.get(raw_url)
            response.raise_for_status()
            return response.text
        except Exception:
            return None
    
    def download_skill_sync(
        self,
        owner: str,
        repo: str,
        skill_path: str,
        branch: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """同步下载 skill 文件"""
        try:
            api_url = GitHubUrlParser.to_api_url(owner, repo, skill_path, branch)
            response = self._sync_client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            files = {}
            
            if isinstance(data, list):
                for item in data:
                    if item.get("type") == "file":
                        file_name = item.get("name", "")
                        download_url = item.get("download_url", "")
                        if download_url:
                            file_response = self._sync_client.get(download_url)
                            if file_response.status_code == 200:
                                files[file_name] = file_response.text
            elif isinstance(data, dict) and data.get("type") == "file":
                download_url = data.get("download_url", "")
                if download_url:
                    file_response = self._sync_client.get(download_url)
                    if file_response.status_code == 200:
                        files[data.get("name", "SKILL.md")] = file_response.text
            
            return files if files else None
        except Exception:
            return None
    
    async def get_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """获取 GitHub 仓库信息"""
        try:
            response = await self._client.get(f"{self.GITHUB_API}/repos/{owner}/{repo}")
            response.raise_for_status()
            data = response.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "description": data.get("description", ""),
                "default_branch": data.get("default_branch", "main"),
            }
        except Exception:
            return None


def parse_skill_command(args: List[str]) -> Dict[str, Any]:
    """
    解析 skill 命令参数
    
    支持格式:
    - npx skills add https://github.com/owner/repo --skill skill-name
    - npx skills add https://github.com/owner/repo/tree/branch/skills/skill-name
    - npx skills add https://skills.sh/owner/repo/skill-name
    - npx skills list
    - npx skills search query
    - npx skills remove skill-name
    
    返回:
    {
        "command": "add" | "list" | "search" | "remove" | "help",
        "url": str | None,
        "skill_name": str | None,
        "branch": str | None,
        "query": str | None,
        "global": bool,
        "force": bool,
    }
    """
    result = {
        "command": "help",
        "url": None,
        "skill_name": None,
        "branch": None,
        "query": None,
        "global": False,
        "force": False,
    }
    
    if not args:
        return result
    
    command = args[0].lower()
    result["command"] = command
    
    i = 1
    while i < len(args):
        arg = args[i]
        
        if arg in ("--skill", "-s") and i + 1 < len(args):
            result["skill_name"] = args[i + 1]
            i += 2
        elif arg in ("--branch", "-b") and i + 1 < len(args):
            result["branch"] = args[i + 1]
            i += 2
        elif arg in ("--global", "-g"):
            result["global"] = True
            i += 1
        elif arg in ("--force", "-f"):
            result["force"] = True
            i += 1
        elif arg.startswith("--"):
            i += 1
            if i < len(args) and not args[i].startswith("-"):
                i += 1
        elif not result["url"] and not result["query"]:
            if command in ("add", "install"):
                result["url"] = arg
            elif command in ("search", "find"):
                result["query"] = arg
            elif command in ("remove", "uninstall", "delete"):
                result["skill_name"] = arg
            i += 1
        else:
            i += 1
    
    return result
