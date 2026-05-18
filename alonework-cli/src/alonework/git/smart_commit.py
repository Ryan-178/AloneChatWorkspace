"""
æºè½æäº¤æ¨¡å / Smart Commit Module

æä¾ / Provides:
- èªå¨çæcommitæ¶æ¯ / Auto generate commit message
- åæ´åæ / Change analysis
- äº¤äºå¼æäº?/ Interactive commit
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from alonework.git.git_manager import GitManager, git_config
from alonework.models import ModelRouter
from alonework.config import ConfigManager


class SmartCommit:
    """æºè½æäº¤å?/ Smart Committer"""
    
    def __init__(
        self,
        git_manager: Optional[GitManager] = None,
        console: Optional[Console] = None,
    ):
        self.git = git_manager or GitManager()
        self.console = console or Console()
    
    def analyze_and_suggest(self) -> Dict[str, Any]:
        """åæåæ´å¹¶å»ºè®®æäº¤ä¿¡æ?/ Analyze changes and suggest commit info"""
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
        """æ£æµåæ´èå?/ Detect change scope"""
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
        """çææè¿° / Generate description"""
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
                ".md": "ææ¡£",
                ".yaml": "éç½®",
                ".yml": "éç½®",
                ".json": "éç½®",
            }
            
            lang = ext_map.get(ext, ext)
            return f"æ´æ° {count} ä¸ª{lang}æä»¶"
        
        total = len(changes)
        return f"æ´æ° {total} ä¸ªæä»?
    
    def interactive_commit(self) -> bool:
        """äº¤äºå¼æäº?/ Interactive commit"""
        if not self.git.is_git_repo():
            self.console.print("[red]éè¯¯: ä¸æ¯Gitä»åº / Error: Not a git repository[/red]")
            return False
        
        analysis = self.analyze_and_suggest()
        
        if not analysis.get("has_changes"):
            self.console.print(f"[yellow]{analysis.get('summary', 'æ²¡æåæ´')}[/yellow]")
            return False
        
        self.console.print(self.git.render_status())
        
        suggested = analysis.get("suggested", {})
        
        self.console.print("\n[bold]å»ºè®®çæäº¤ä¿¡æ?/ Suggested commit message:[/bold]")
        self.console.print(f"  [cyan]{suggested.get('message', '')}[/cyan]\n")
        
        commit_types = git_config.get("git.commit.types", [])
        
        self.console.print("[bold]æäº¤ç±»å / Commit types:[/bold]")
        for ct in commit_types:
            key = ct.get("key", "")
            desc = ct.get("description", "")
            emoji = ct.get("emoji", "")
            self.console.print(f"  {emoji} [green]{key}[/green]: {desc}")
        
        use_suggested = Confirm.ask(
            "\nä½¿ç¨å»ºè®®çæäº¤ä¿¡æ¯ï¼ / Use suggested commit message?",
            default=True,
        )
        
        if use_suggested:
            message = suggested.get("message", "")
        else:
            commit_type = Prompt.ask(
                "æäº¤ç±»å / Commit type",
                default=suggested.get("type", "feat"),
            )
            
            scope = Prompt.ask(
                "èå´ (å¯é? / Scope (optional)",
                default=suggested.get("scope", ""),
            )
            
            description = Prompt.ask(
                "æè¿° / Description",
                default=suggested.get("description", ""),
            )
            
            message = self.git.generate_commit_message(
                analysis.get("files", []),
                commit_type=commit_type,
                scope=scope or None,
                description=description,
            )
        
        add_all = Confirm.ask(
            "æ·»å æææä»¶ï¼ / Add all files?",
            default=True,
        )
        
        success, msg = self.git.commit(message, add_all=add_all)
        
        if success:
            self.console.print(f"\n[green]â?{msg}[/green]")
            
            if Confirm.ask("\næ¨éå°è¿ç¨ï¼?/ Push to remote?", default=False):
                branch = self.git.get_current_branch()
                push_success, push_msg = self.git.push(branch=branch, set_upstream=True)
                
                if push_success:
                    self.console.print(f"[green]â?{push_msg}[/green]")
                else:
                    self.console.print(f"[red]â?{push_msg}[/red]")
            
            return True
        else:
            self.console.print(f"\n[red]â?{msg}[/red]")
            return False
    
    def ai_enhanced_commit(
        self,
        config_manager: ConfigManager,
        model: Optional[str] = None,
    ) -> bool:
        """AIå¢å¼ºæäº¤ / AI enhanced commit"""
        if not self.git.is_git_repo():
            self.console.print("[red]éè¯¯: ä¸æ¯Gitä»åº / Error: Not a git repository[/red]")
            return False
        
        analysis = self.git.analyze_changes()
        
        if not analysis.get("has_changes"):
            self.console.print(f"[yellow]{analysis.get('summary', 'æ²¡æåæ´')}[/yellow]")
            return False
        
        diff = self.git.get_diff()
        
        config = config_manager.load_config()
        selected_model = model or config.get("model", {}).get("default", "deepseek")
        
        model_router = ModelRouter(config)
        
        prompt = f"""åæä»¥ä¸Gitåæ´å¹¶çæä¸ä¸ªç¬¦åConventional Commitsè§èçæäº¤æ¶æ¯ã?
åæ´ç»è®¡:
- æ»æä»¶æ°: {analysis.get('total_files', 0)}
- æç±»å? {analysis.get('by_type', {})}
- ææ©å±å: {analysis.get('by_extension', {})}

Git Diff (å?000å­ç¬¦):
{diff[:2000]}

è¯·çæ?
1. commitç±»å (feat/fix/docs/style/refactor/perf/test/chore)
2. scope (å¯éï¼è¡¨ç¤ºå½±åèå´)
3. ç®ç­æè¿?(ä¸è¶è¿?0å­ç¬¦)

æ ¼å¼: type(scope): description
åªè¾åºæäº¤æ¶æ¯ï¼ä¸è¦å¶ä»åå®¹ã?""
        
        with self.console.status("[bold green]AIåæä¸?.. / AI analyzing...[/bold green]"):
            try:
                ai_message = model_router.chat(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                )
            except Exception as e:
                self.console.print(f"[red]AIåæå¤±è´¥: {e}[/red]")
                return self.interactive_commit()
        
        self.console.print(f"\n[bold]AIå»ºè®®çæäº¤æ¶æ?/ AI suggested commit message:[/bold]")
        self.console.print(f"  [cyan]{ai_message}[/cyan]\n")
        
        use_ai = Confirm.ask(
            "ä½¿ç¨AIå»ºè®®ï¼?/ Use AI suggestion?",
            default=True,
        )
        
        if use_ai:
            message = ai_message
        else:
            return self.interactive_commit()
        
        success, msg = self.git.commit(message, add_all=True)
        
        if success:
            self.console.print(f"\n[green]â?{msg}[/green]")
            return True
        else:
            self.console.print(f"\n[red]â?{msg}[/red]")
            return False
