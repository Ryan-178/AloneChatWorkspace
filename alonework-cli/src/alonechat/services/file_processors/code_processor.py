"""
代码处理器

处理各种编程语言源代码文件
"""

from pathlib import Path
from typing import Any, Dict, List
from .base_processor import BaseFileProcessor


class CodeProcessor(BaseFileProcessor):
    """代码文件处理器"""
    
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript (React)',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C Header',
        '.hpp': 'C++ Header',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.cs': 'C#',
        '.vb': 'Visual Basic',
        '.r': 'R',
        '.m': 'MATLAB',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.ps1': 'PowerShell',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.ex': 'Elixir',
        '.erl': 'Erlang',
        '.clj': 'Clojure',
        '.hs': 'Haskell',
        '.ml': 'OCaml',
        '.vue': 'Vue',
        '.svelte': 'Svelte',
    }
    
    async def to_text(self, file_path: Path) -> str:
        """将代码文件转换为文本表示"""
        
        ext = file_path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'Unknown')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                code = f.read()
        
        # 分析代码结构
        lines = code.splitlines()
        
        text_parts = [
            f"[代码文件: {file_path.name}]\n",
            f"语言: {language}\n",
            f"行数: {len(lines)}\n",
            f"字符数: {len(code)}\n\n",
        ]
        
        # 提取代码结构（简化版）
        structure = self._analyze_structure(code, language)
        if structure:
            text_parts.append("=== 代码结构 ===\n")
            text_parts.append(structure)
            text_parts.append("\n\n")
        
        # 完整代码
        text_parts.append(f"=== 完整代码 ===\n")
        text_parts.append(f"```{language.lower()}\n")
        text_parts.append(code)
        text_parts.append("\n```\n")
        
        return "".join(text_parts)
    
    def _analyze_structure(self, code: str, language: str) -> str:
        """分析代码结构"""
        
        import re
        
        structure_parts = []
        
        # Python
        if language == 'Python':
            # 提取类和函数定义
            classes = re.findall(r'^class\s+(\w+)', code, re.MULTILINE)
            functions = re.findall(r'^def\s+(\w+)', code, re.MULTILINE)
            
            if classes:
                structure_parts.append("类:\n")
                for cls in classes:
                    structure_parts.append(f"  - {cls}\n")
            
            if functions:
                structure_parts.append("函数:\n")
                for func in functions:
                    structure_parts.append(f"  - {func}()\n")
        
        # JavaScript/TypeScript
        elif language in ['JavaScript', 'TypeScript', 'JavaScript (React)', 'TypeScript (React)']:
            # 提取函数和类
            functions = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', code)
            classes = re.findall(r'class\s+(\w+)', code)
            
            if classes:
                structure_parts.append("类:\n")
                for cls in classes:
                    structure_parts.append(f"  - {cls}\n")
            
            if functions:
                structure_parts.append("函数:\n")
                for func in functions:
                    name = func[0] or func[1]
                    if name:
                        structure_parts.append(f"  - {name}()\n")
        
        # Java
        elif language == 'Java':
            classes = re.findall(r'class\s+(\w+)', code)
            methods = re.findall(r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(', code)
            
            if classes:
                structure_parts.append("类:\n")
                for cls in classes:
                    structure_parts.append(f"  - {cls}\n")
            
            if methods:
                structure_parts.append("方法:\n")
                for method in methods[:10]:  # 限制数量
                    structure_parts.append(f"  - {method}()\n")
        
        return "".join(structure_parts) if structure_parts else ""
    
    async def from_text(self, text: str, output_path: Path) -> bool:
        """从代码文本生成文件"""
        
        import re
        
        # 提取代码块内容
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            code = matches[0]
        else:
            # 如果没有代码块，使用原始文本
            code = text
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return True
    
    def get_supported_extensions(self) -> list[str]:
        return list(self.LANGUAGE_MAP.keys())
