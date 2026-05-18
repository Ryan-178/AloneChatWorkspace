"""
自定义Slash命令加载器 / Custom Slash Command Loader

从项目/用户目录加载自定义slash命令 / Loads custom slash commands from project/user directories
"""

import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from rich.console import Console

from alonechat.slash.registry import SlashCommand
from alonechat.slash.parser import SlashCommandParser

console = Console()


@dataclass
class CustomCommand:
    """自定义命令数据 / Custom command data"""
    name: str
    path: Path
    description: str = ""
    prompt: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    argument_hint: str = ""
    model: Optional[str] = None
    source: str = "project"  # project or user


class CustomCommandLoader:
    """自定义命令加载器 / Custom command loader"""
    
    PROJECT_DIR = ".alonechat/commands"
    USER_DIR = ".alonechat/commands"
    
    def __init__(self):
        self.project_dir = Path.cwd() / self.PROJECT_DIR
        self.user_dir = Path.home() / self.USER_DIR
        self._commands: dict[str, CustomCommand] = {}
    
    def load_all(self) -> list[CustomCommand]:
        """加载所有自定义命令 / Load all custom commands"""
        commands = []
        
        user_commands = self._load_from_dir(self.user_dir, "user")
        commands.extend(user_commands)
        
        project_commands = self._load_from_dir(self.project_dir, "project")
        commands.extend(project_commands)
        
        for cmd in commands:
            self._commands[cmd.name] = cmd
        
        return commands
    
    def _load_from_dir(self, directory: Path, source: str) -> list[CustomCommand]:
        """从目录加载命令 / Load commands from directory"""
        commands = []
        
        if not directory.exists():
            return commands
        
        for md_file in directory.rglob("*.md"):
            cmd = self._parse_command_file(md_file, source)
            if cmd:
                commands.append(cmd)
        
        return commands
    
    def _parse_command_file(self, file_path: Path, source: str) -> Optional[CustomCommand]:
        """解析命令文件 / Parse command file"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None
        
        frontmatter, prompt = SlashCommandParser.parse_frontmatter(content)
        
        name = file_path.stem
        
        relative_path = file_path.relative_to(
            self.user_dir if source == "user" else self.project_dir
        )
        if len(relative_path.parts) > 1:
            namespace = relative_path.parts[0]
            name = f"{namespace}:{name}"
        
        description = frontmatter.get("description", "")
        if not description and prompt:
            first_line = prompt.strip().split("\n")[0]
            description = first_line[:60] + "..." if len(first_line) > 60 else first_line
        
        return CustomCommand(
            name=name,
            path=file_path,
            description=description,
            prompt=prompt,
            allowed_tools=frontmatter.get("allowed-tools", []),
            argument_hint=frontmatter.get("argument-hint", ""),
            model=frontmatter.get("model"),
            source=source,
        )
    
    def get(self, name: str) -> Optional[CustomCommand]:
        """获取自定义命令 / Get custom command"""
        return self._commands.get(name)
    
    def list_commands(self) -> list[CustomCommand]:
        """列出所有自定义命令 / List all custom commands"""
        return list(self._commands.values())
    
    def to_slash_command(self, custom_cmd: CustomCommand) -> SlashCommand:
        """转换为SlashCommand / Convert to SlashCommand"""
        def handler(args: list, obj: dict, session_manager, registry, **kwargs):
            return execute_custom_command(custom_cmd, args, obj, session_manager)
        
        return SlashCommand(
            name=custom_cmd.name,
            description=f"{custom_cmd.description} ({custom_cmd.source})",
            handler=handler,
            usage=custom_cmd.argument_hint,
            category="custom",
        )


def execute_custom_command(
    custom_cmd: CustomCommand,
    args: list[str],
    obj: dict,
    session_manager,
) -> str:
    """
    执行自定义命令 / Execute custom command
    
    返回处理后的提示 / Returns processed prompt
    """
    prompt = custom_cmd.prompt
    
    prompt = SlashCommandParser.substitute_args(prompt, args)
    
    prompt = process_bash_commands(prompt)
    
    prompt = process_file_references(prompt)
    
    console.print(f"\n[cyan]执行自定义命令 / Executing custom command: /{custom_cmd.name}[/cyan]\n")
    
    return prompt


def process_bash_commands(prompt: str) -> str:
    """
    处理Bash命令执行 / Process bash command execution
    
    支持 !`command` 语法 / Supports !`command` syntax
    """
    pattern = r'!`([^`]+)`'
    
    def replace_bash(match):
        command = match.group(1)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip() if result.returncode == 0 else f"[Error: {result.stderr.strip()}]"
        except subprocess.TimeoutExpired:
            return "[Error: Command timed out]"
        except Exception as e:
            return f"[Error: {e}]"
    
    return re.sub(pattern, replace_bash, prompt)


def process_file_references(prompt: str) -> str:
    """
    处理文件引用 / Process file references
    
    支持 @file-path 语法 / Supports @file-path syntax
    """
    pattern = r'@([^\s\n]+)'
    
    def replace_file(match):
        file_path = Path(match.group(1))
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                return f"\n[File: {file_path}]\n```\n{content}\n```\n"
            except Exception as e:
                return f"[Error reading {file_path}: {e}]"
        return f"[File not found: {file_path}]"
    
    return re.sub(pattern, replace_file, prompt)
