"""
智能提交模块 / Smart Commit Module

提供 / Provides:
- 自动生成commit消息 / Auto generate commit message
- 变更分析 / Change analysis
- 交互式提交 / Interactive commit
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from alonechat.git.git_manager import GitManager, git_config
from alonechat.models import ModelRouter
from alonechat.config import ConfigManager


class SmartCommit:
    """智能提交器 / Smart Committer"""
    
    def __init__(
        self,
        git_manager: Optional[GitManager] = None,
        console: Optional[Console] = None,
    ):
        self.git = git_manager or GitManager()
        self.console = console or Console()
    
    def analyze_and_suggest(self) -> Dict[str, Any]:
        """分析变更并建议提交信息 / Analyze changes and suggest commit info"""
        analysis = self.git.analyze_changes()
        
        if not analysis.get("has_changes"):
            return analysis
        
        changes = analysis.get("files", [])
        
        commit_type = self.git.suggest_commit_type(changes)
        
        scope = self._detect_scope(changes)
        
        description = self._generate_description(changes, analysis)
        
        analysis["suggested"] = {
            "type": commit_type,
            "scope": scope,
            "description": description,
            "message": self.git.generate_commit_message(
                changes,
                commit_type=commit_type,
                scope=scope,
                description=description,
            ),
        }
        
        return analysis
    
    def _detect_scope(self, changes: List) -> Optional[str]:
        """检测变更范围 / Detect change scope"""
        paths = [Path(c.path) for c in changes]
        
        common_parts = None
        for p in paths:
            parts = p.parts[:-1]
            if common_parts is None:
                common_parts = parts
            else:
                common_parts = [a for a, b in zip(common_parts, parts) if a == b]
        
        if common_parts:
            return common_parts[0]
        
        return None
    
    def _generate_description(self, changes: List, analysis: Dict) -> str:
        """生成描述 / Generate description"""
        by_ext = analysis.get("by_extension", {})
        
        if len(by_ext) == 1:
            ext = list(by_ext.keys())[0]
            count = by_ext[ext]
            
            ext_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".go": "Go",
                ".rs": "Rust",
                ".java": "Java",
                ".md": "文档",
                ".yaml": "配置",
                ".yml": "配置",
                ".json": "配置",
            }
            
            lang = ext_map.get(ext, ext)
            return f"更新 {count} 个{lang}文件"
        
        total = len(changes)
        return f"更新 {total} 个文件"
    
    def interactive_commit(self) -> bool:
        """交互式提交 / Interactive commit"""
        if not self.git.is_git_repo():
            self.console.print("[red]错误: 不是Git仓库 / Error: Not a git repository[/red]")
            return False
        
        analysis = self.analyze_and_suggest()
        
        if not analysis.get("has_changes"):
            self.console.print(f"[yellow]{analysis.get('summary', '没有变更')}[/yellow]")
            return False
        
        self.console.print(self.git.render_status())
        
        suggested = analysis.get("suggested", {})
        
        self.console.print("\n[bold]建议的提交信息 / Suggested commit message:[/bold]")
        self.console.print(f"  [cyan]{suggested.get('message', '')}[/cyan]\n")
        
        commit_types = git_config.get("git.commit.types", [])
        
        self.console.print("[bold]提交类型 / Commit types:[/bold]")
        for ct in commit_types:
            key = ct.get("key", "")
            desc = ct.get("description", "")
            emoji = ct.get("emoji", "")
            self.console.print(f"  {emoji} [green]{key}[/green]: {desc}")
        
        use_suggested = Confirm.ask(
            "\n使用建议的提交信息？ / Use suggested commit message?",
            default=True,
        )
        
        if use_suggested:
            message = suggested.get("message", "")
        else:
            commit_type = Prompt.ask(
                "提交类型 / Commit type",
                default=suggested.get("type", "feat"),
            )
            
            scope = Prompt.ask(
                "范围 (可选) / Scope (optional)",
                default=suggested.get("scope", ""),
            )
            
            description = Prompt.ask(
                "描述 / Description",
                default=suggested.get("description", ""),
            )
            
            message = self.git.generate_commit_message(
                analysis.get("files", []),
                commit_type=commit_type,
                scope=scope or None,
                description=description,
            )
        
        add_all = Confirm.ask(
            "添加所有文件？ / Add all files?",
            default=True,
        )
        
        success, msg = self.git.commit(message, add_all=add_all)
        
        if success:
            self.console.print(f"\n[green]✓ {msg}[/green]")
            
            if Confirm.ask("\n推送到远程？ / Push to remote?", default=False):
                branch = self.git.get_current_branch()
                push_success, push_msg = self.git.push(branch=branch, set_upstream=True)
                
                if push_success:
                    self.console.print(f"[green]✓ {push_msg}[/green]")
                else:
                    self.console.print(f"[red]✗ {push_msg}[/red]")
            
            return True
        else:
            self.console.print(f"\n[red]✗ {msg}[/red]")
            return False
    
    def ai_enhanced_commit(
        self,
        config_manager: ConfigManager,
        model: Optional[str] = None,
    ) -> bool:
        """AI增强提交 / AI enhanced commit"""
        if not self.git.is_git_repo():
            self.console.print("[red]错误: 不是Git仓库 / Error: Not a git repository[/red]")
            return False
        
        analysis = self.git.analyze_changes()
        
        if not analysis.get("has_changes"):
            self.console.print(f"[yellow]{analysis.get('summary', '没有变更')}[/yellow]")
            return False
        
        diff = self.git.get_diff()
        
        config = config_manager.load_config()
        selected_model = model or config.get("model", {}).get("default", "deepseek")
        
        model_router = ModelRouter(config)
        
        prompt = f"""分析以下Git变更并生成一个符合Conventional Commits规范的提交消息。

变更统计:
- 总文件数: {analysis.get('total_files', 0)}
- 按类型: {analysis.get('by_type', {})}
- 按扩展名: {analysis.get('by_extension', {})}

Git Diff (前2000字符):
{diff[:2000]}

请生成:
1. commit类型 (feat/fix/docs/style/refactor/perf/test/chore)
2. scope (可选，表示影响范围)
3. 简短描述 (不超过50字符)

格式: type(scope): description
只输出提交消息，不要其他内容。"""
        
        with self.console.status("[bold green]AI分析中... / AI analyzing...[/bold green]"):
            try:
                ai_message = model_router.chat(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                )
            except Exception as e:
                self.console.print(f"[red]AI分析失败: {e}[/red]")
                return self.interactive_commit()
        
        self.console.print(f"\n[bold]AI建议的提交消息 / AI suggested commit message:[/bold]")
        self.console.print(f"  [cyan]{ai_message}[/cyan]\n")
        
        use_ai = Confirm.ask(
            "使用AI建议？ / Use AI suggestion?",
            default=True,
        )
        
        if use_ai:
            message = ai_message
        else:
            return self.interactive_commit()
        
        success, msg = self.git.commit(message, add_all=True)
        
        if success:
            self.console.print(f"\n[green]✓ {msg}[/green]")
            return True
        else:
            self.console.print(f"\n[red]✗ {msg}[/red]")
            return False
