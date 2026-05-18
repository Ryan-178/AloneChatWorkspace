#!/usr/bin/env python3
"""
Skills CLI - 命令行工具
用于管理 Skills 的安装、卸载、搜索等

用法:
    npx skills add https://github.com/owner/repo --skill skill-name
    npx skills add https://github.com/owner/repo/tree/branch/skills/skill-name
    npx skills add https://skills.sh/owner/repo/skill-name
    npx skills list
    npx skills search query
    npx skills remove skill-name
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

from agent_framework.tools.skills_sh_client import (
    SkillsShClient,
    GitHubUrlParser,
    parse_skill_command,
    RemoteSkill,
)
from agent_framework.tools.skills_registry import SkillsRegistry
from agent_framework.tools.skills_marketplace import SkillsMarketplace


class SkillsCLI:
    """Skills CLI 管理器"""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path.home() / ".skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry = SkillsRegistry()
        self.marketplace = SkillsMarketplace(self.registry)
        self.client = SkillsShClient()
    
    async def close(self):
        """关闭客户端"""
        await self.client.close()
    
    def _get_skill_install_path(self, skill_name: str, global_install: bool = False) -> Path:
        """获取 skill 安装路径"""
        if global_install:
            return self.skills_dir / skill_name
        else:
            return Path.cwd() / ".skills" / skill_name
    
    async def add(
        self,
        url: str,
        skill_name: Optional[str] = None,
        branch: Optional[str] = None,
        global_install: bool = False,
        force: bool = False,
    ) -> bool:
        """
        从远程 URL 添加 skill
        
        Args:
            url: GitHub URL 或 skills.sh URL
            skill_name: 指定的 skill 名称
            branch: 指定的分支
            global_install: 是否全局安装
            force: 强制覆盖已存在的 skill
        
        Returns:
            是否成功
        """
        parsed = GitHubUrlParser.parse(url)
        
        if not parsed:
            print(f"❌ 无法解析 URL: {url}")
            return False
        
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
        
        print(f"📥 正在从 GitHub 下载: {owner}/{repo}/{skill_path} (分支: {branch})")
        
        files = await self.client.download_skill_content(owner, repo, skill_path, branch)
        
        if not files:
            print(f"❌ 下载失败: 未找到 skill 文件")
            return False
        
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
        
        install_path = self._get_skill_install_path(actual_skill_name, global_install)
        
        if install_path.exists() and not force:
            print(f"⚠️  Skill '{actual_skill_name}' 已存在于: {install_path}")
            print(f"   使用 --force 强制覆盖")
            return False
        
        install_path.mkdir(parents=True, exist_ok=True)
        
        for file_name, content in files.items():
            file_path = install_path / file_name
            file_path.write_text(content, encoding="utf-8")
            print(f"   ✅ {file_name}")
        
        print(f"\n✅ Skill '{actual_skill_name}' 安装成功!")
        print(f"   📁 路径: {install_path}")
        
        return True
    
    def list_skills(self, local_only: bool = True) -> None:
        """列出已安装的 skills"""
        print("📦 已安装的 Skills:\n")
        
        local_skills_dir = Path.cwd() / ".skills"
        global_skills_dir = self.skills_dir
        
        found = False
        
        if local_skills_dir.exists():
            for skill_dir in local_skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        print(f"   📂 {skill_dir.name} (本地)")
                        print(f"      路径: {skill_dir}")
                        found = True
        
        if global_skills_dir.exists():
            for skill_dir in global_skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        print(f"   📂 {skill_dir.name} (全局)")
                        print(f"      路径: {skill_dir}")
                        found = True
        
        if not found:
            print("   暂无已安装的 Skills")
            print("   使用 'skills add <url>' 安装新 skill")
    
    async def search(self, query: str) -> None:
        """搜索远程 skills"""
        print(f"🔍 搜索: {query}\n")
        
        skills = await self.client.search_skills_sh(query)
        
        if not skills:
            print("   未找到匹配的 Skills")
            return
        
        print(f"   找到 {len(skills)} 个 Skills:\n")
        
        for skill in skills:
            print(f"   📦 {skill.name}")
            print(f"      ID: {skill.id}")
            if skill.description:
                desc = skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
                print(f"      描述: {desc}")
            print(f"      ⭐ {skill.stars} stars | 📥 {skill.installs} 安装")
            print()
    
    def remove(self, skill_name: str) -> bool:
        """移除已安装的 skill"""
        local_path = Path.cwd() / ".skills" / skill_name
        global_path = self.skills_dir / skill_name
        
        removed = False
        
        if local_path.exists():
            import shutil
            shutil.rmtree(local_path)
            print(f"✅ 已移除本地 skill: {skill_name}")
            removed = True
        
        if global_path.exists():
            import shutil
            shutil.rmtree(global_path)
            print(f"✅ 已移除全局 skill: {skill_name}")
            removed = True
        
        if not removed:
            print(f"❌ 未找到 skill: {skill_name}")
            return False
        
        return True
    
    def help(self) -> None:
        """显示帮助信息"""
        print("""
Skills CLI - Skills 管理工具

用法:
    skills <command> [options]

命令:
    add <url>           从 GitHub 或 skills.sh 添加 skill
    list                列出已安装的 skills
    search <query>      搜索远程 skills
    remove <name>       移除已安装的 skill
    help                显示帮助信息

选项:
    --skill, -s <name>  指定 skill 名称
    --branch, -b <name> 指定 Git 分支
    --global, -g        全局安装
    --force, -f         强制覆盖

示例:
    # 从 GitHub 安装
    skills add https://github.com/vercel-labs/skills --skill find-skills
    
    # 从 skills.sh 安装
    skills add https://skills.sh/vercel-labs/skills/find-skills
    
    # 指定分支
    skills add https://github.com/owner/repo --skill my-skill --branch develop
    
    # 全局安装
    skills add https://github.com/owner/repo --skill my-skill --global
    
    # 搜索
    skills search react
    
    # 列出已安装
    skills list
    
    # 移除
    skills remove my-skill
""")


async def main(args: Optional[list] = None) -> int:
    """CLI 主入口"""
    if args is None:
        args = sys.argv[1:]
    
    parsed = parse_skill_command(args)
    cli = SkillsCLI()
    
    try:
        command = parsed["command"]
        
        if command == "add":
            if not parsed["url"]:
                print("❌ 错误: 需要指定 URL")
                print("   用法: skills add <url> --skill <name>")
                return 1
            
            success = await cli.add(
                url=parsed["url"],
                skill_name=parsed["skill_name"],
                branch=parsed["branch"],
                global_install=parsed["global"],
                force=parsed["force"],
            )
            return 0 if success else 1
        
        elif command == "list":
            cli.list_skills()
            return 0
        
        elif command == "search":
            if not parsed["query"]:
                print("❌ 错误: 需要指定搜索关键词")
                print("   用法: skills search <query>")
                return 1
            
            await cli.search(parsed["query"])
            return 0
        
        elif command == "remove":
            if not parsed["skill_name"]:
                print("❌ 错误: 需要指定 skill 名称")
                print("   用法: skills remove <name>")
                return 1
            
            success = cli.remove(parsed["skill_name"])
            return 0 if success else 1
        
        else:
            cli.help()
            return 0
    
    finally:
        await cli.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
