"""
文本文件处理器

处理 TXT、MD、JSON、XML 等纯文本文件
"""

from pathlib import Path
from typing import Any, Dict
import json
import xml.dom.minidom as minidom
from .base_processor import BaseFileProcessor


class TextProcessor(BaseFileProcessor):
    """文本文件处理器"""
    
    async def to_text(self, file_path: Path) -> str:
        """将文本文件转换为结构化文本表示"""
        
        ext = file_path.suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        text_parts = [
            f"[文本文件: {file_path.name}]\n",
            f"格式: {ext}\n",
            f"大小: {len(content)} 字符\n\n",
        ]
        
        if ext == '.json':
            text_parts.append(self._format_json(content))
        elif ext == '.xml':
            text_parts.append(self._format_xml(content))
        elif ext == '.md':
            text_parts.append(self._format_markdown(content))
        else:
            text_parts.append("=== 文件内容 ===\n")
            text_parts.append(content)
        
        return "".join(text_parts)
    
    def _format_json(self, content: str) -> str:
        """格式化 JSON 内容"""
        try:
            data = json.loads(content)
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
            return f"=== JSON 结构 ===\n```json\n{formatted}\n```\n"
        except json.JSONDecodeError:
            return f"=== JSON 内容（解析失败）===\n{content}\n"
    
    def _format_xml(self, content: str) -> str:
        """格式化 XML 内容"""
        try:
            dom = minidom.parseString(content)
            formatted = dom.toprettyxml(indent="  ")
            return f"=== XML 结构 ===\n```xml\n{formatted}\n```\n"
        except:
            return f"=== XML 内容 ===\n{content}\n"
    
    def _format_markdown(self, content: str) -> str:
        """格式化 Markdown 内容"""
        lines = content.split('\n')
        headings = [l for l in lines if l.startswith('#')]
        
        text_parts = ["=== Markdown 文档 ===\n"]
        
        if headings:
            text_parts.append("\n文档大纲:\n")
            for h in headings:
                level = h.count('#')
                title = h.lstrip('#').strip()
                indent = "  " * (level - 1)
                text_parts.append(f"{indent}- {title}\n")
        
        text_parts.append(f"\n```markdown\n{content}\n```\n")
        
        return "".join(text_parts)
    
    async def from_text(self, text: str, output_path: Path) -> bool:
        """保存文本到文件"""
        
        # 提取代码块内容（如果有）
        import re
        
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            content = matches[0]
        else:
            content = text
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def get_supported_extensions(self) -> list[str]:
        return ['.txt', '.md', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.log']
