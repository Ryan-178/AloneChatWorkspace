"""
Slash命令解析器 / Slash Command Parser

解析用户输入的slash命令 / Parses slash commands from user input
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommand:
    """解析后的命令 / Parsed command"""
    name: str
    args: list[str]
    raw: str
    is_valid: bool
    error: Optional[str] = None


class SlashCommandParser:
    """Slash命令解析器 / Slash Command Parser"""
    
    PREFIX = "/"
    
    @classmethod
    def is_slash_command(cls, text: str) -> bool:
        """检查是否为slash命令 / Check if text is a slash command"""
        return text.strip().startswith(cls.PREFIX)
    
    @classmethod
    def parse(cls, text: str) -> ParsedCommand:
        """解析命令 / Parse command"""
        text = text.strip()
        
        if not cls.is_slash_command(text):
            return ParsedCommand(
                name="",
                args=[],
                raw=text,
                is_valid=False,
                error="不是slash命令 / Not a slash command"
            )
        
        content = text[1:]
        
        if not content:
            return ParsedCommand(
                name="",
                args=[],
                raw=text,
                is_valid=False,
                error="命令名称为空 / Command name is empty"
            )
        
        parts = cls._split_args(content)
        
        if not parts:
            return ParsedCommand(
                name="",
                args=[],
                raw=text,
                is_valid=False,
                error="命令名称为空 / Command name is empty"
            )
        
        name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if not cls._is_valid_name(name):
            return ParsedCommand(
                name=name,
                args=args,
                raw=text,
                is_valid=False,
                error=f"无效的命令名称: {name} / Invalid command name: {name}"
            )
        
        return ParsedCommand(
            name=name,
            args=args,
            raw=text,
            is_valid=True
        )
    
    @classmethod
    def _split_args(cls, text: str) -> list[str]:
        """分割参数 / Split arguments"""
        parts = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in text:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == ' ' and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    @classmethod
    def _is_valid_name(cls, name: str) -> bool:
        """检查命令名称是否有效 / Check if command name is valid"""
        if not name:
            return False
        pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')
        return bool(pattern.match(name))
    
    @classmethod
    def parse_frontmatter(cls, content: str) -> tuple[dict, str]:
        """
        解析Frontmatter / Parse frontmatter
        
        返回 (frontmatter_dict, remaining_content) / Returns (frontmatter_dict, remaining_content)
        """
        if not content.startswith("---"):
            return {}, content
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        
        frontmatter_str = parts[1].strip()
        remaining = parts[2].strip()
        
        frontmatter = {}
        for line in frontmatter_str.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip() for v in value[1:-1].split(",")]
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                
                frontmatter[key] = value
        
        return frontmatter, remaining
    
    @classmethod
    def substitute_args(cls, template: str, args: list[str]) -> str:
        """
        替换参数 / Substitute arguments
        
        支持 $ARGUMENTS, $1, $2, ... / Supports $ARGUMENTS, $1, $2, ...
        """
        result = template
        
        all_args = " ".join(args)
        result = result.replace("$ARGUMENTS", all_args)
        
        for i, arg in enumerate(args, 1):
            result = result.replace(f"${i}", arg)
        
        return result
