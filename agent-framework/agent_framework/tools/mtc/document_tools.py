"""
MTC工具集 - More Than Coding Tools
面向非开发用户的通用办公工具
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import os

from agent_framework.core.base_tool import BaseTool, ToolResult


class DocumentGeneratorTool(BaseTool):
    """文档生成工具"""
    
    name = "document_generator"
    description = "生成各类文档，支持Markdown、Word、PDF等格式"
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "文档标题"},
            "content": {"type": "string", "description": "文档内容"},
            "format": {"type": "string", "enum": ["markdown", "word", "pdf"], "description": "输出格式"},
            "output_path": {"type": "string", "description": "输出文件路径"},
        },
        "required": ["title", "content"],
    }
    
    def execute(self, title: str, content: str, format: str = "markdown", output_path: Optional[str] = None) -> ToolResult:
        try:
            if format == "markdown":
                doc_content = f"# {title}\n\n{content}"
                ext = ".md"
            elif format == "word":
                doc_content = f"{title}\n\n{content}"
                ext = ".docx"
            elif format == "pdf":
                doc_content = f"{title}\n\n{content}"
                ext = ".pdf"
            else:
                doc_content = content
                ext = ".txt"
            
            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(doc_content)
                return ToolResult(success=True, data={"path": str(path), "content": doc_content})
            
            return ToolResult(success=True, data={"content": doc_content, "format": format})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DataAnalysisTool(BaseTool):
    """数据分析工具"""
    
    name = "data_analysis"
    description = "执行数据分析，包括统计计算、趋势分析等"
    parameters = {
        "type": "object",
        "properties": {
            "data": {"type": "array", "description": "数据数组"},
            "analysis_type": {"type": "string", "enum": ["summary", "trend", "correlation"], "description": "分析类型"},
        },
        "required": ["data"],
    }
    
    def execute(self, data: List[float], analysis_type: str = "summary") -> ToolResult:
        try:
            if not data:
                return ToolResult(success=False, error="数据为空")
            
            if analysis_type == "summary":
                n = len(data)
                total = sum(data)
                mean = total / n
                sorted_data = sorted(data)
                median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n//2-1] + sorted_data[n//2]) / 2
                variance = sum((x - mean) ** 2 for x in data) / n
                std_dev = variance ** 0.5
                
                result = {
                    "count": n,
                    "sum": total,
                    "mean": mean,
                    "median": median,
                    "min": min(data),
                    "max": max(data),
                    "std_dev": std_dev,
                }
            elif analysis_type == "trend":
                if len(data) < 2:
                    return ToolResult(success=False, error="数据点不足，无法分析趋势")
                trend = "上升" if data[-1] > data[0] else "下降" if data[-1] < data[0] else "平稳"
                change_rate = (data[-1] - data[0]) / data[0] * 100 if data[0] != 0 else 0
                result = {"trend": trend, "change_rate": change_rate}
            else:
                result = {"data": data, "analysis_type": analysis_type}
            
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    name = "web_search"
    description = "执行网络搜索，获取相关信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "num_results": {"type": "integer", "description": "返回结果数量"},
        },
        "required": ["query"],
    }
    
    def execute(self, query: str, num_results: int = 5) -> ToolResult:
        try:
            results = [
                {"title": f"搜索结果 {i+1}", "url": f"https://example.com/result{i+1}", "snippet": f"关于 '{query}' 的相关信息..."}
                for i in range(min(num_results, 5))
            ]
            return ToolResult(success=True, data={"query": query, "results": results})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileReaderTool(BaseTool):
    """文件读取工具"""
    
    name = "file_reader"
    description = "读取文件内容"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件路径"},
            "encoding": {"type": "string", "description": "文件编码"},
        },
        "required": ["file_path"],
    }
    
    def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(success=False, error=f"文件不存在: {file_path}")
            
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            return ToolResult(success=True, data={
                "path": str(path),
                "content": content,
                "size": len(content),
                "lines": content.count("\n") + 1,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileWriterTool(BaseTool):
    """文件写入工具"""
    
    name = "file_writer"
    description = "写入文件内容"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "写入内容"},
            "mode": {"type": "string", "enum": ["write", "append"], "description": "写入模式"},
        },
        "required": ["file_path", "content"],
    }
    
    def execute(self, file_path: str, content: str, mode: str = "write") -> ToolResult:
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            write_mode = "w" if mode == "write" else "a"
            with open(path, write_mode, encoding="utf-8") as f:
                f.write(content)
            
            return ToolResult(success=True, data={
                "path": str(path),
                "size": len(content),
                "mode": mode,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileListTool(BaseTool):
    """文件列表工具"""
    
    name = "file_list"
    description = "列出目录中的文件"
    parameters = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "目录路径"},
            "pattern": {"type": "string", "description": "文件匹配模式"},
        },
        "required": ["directory"],
    }
    
    def execute(self, directory: str, pattern: str = "*") -> ToolResult:
        try:
            path = Path(directory)
            if not path.exists():
                return ToolResult(success=False, error=f"目录不存在: {directory}")
            
            files = []
            for f in path.glob(pattern):
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "is_dir": f.is_dir(),
                    "size": f.stat().st_size if f.is_file() else 0,
                })
            
            return ToolResult(success=True, data={"directory": str(path), "files": files, "count": len(files)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SummaryGeneratorTool(BaseTool):
    """摘要生成工具"""
    
    name = "summary_generator"
    description = "生成文本摘要"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "原始文本"},
            "max_length": {"type": "integer", "description": "摘要最大长度"},
        },
        "required": ["text"],
    }
    
    def execute(self, text: str, max_length: int = 200) -> ToolResult:
        try:
            sentences = text.replace("。", ".\n").replace("！", "!\n").replace("？", "?\n").split("\n")
            sentences = [s.strip() for s in sentences if s.strip()]
            
            summary = ""
            for sentence in sentences:
                if len(summary) + len(sentence) <= max_length:
                    summary += sentence
                else:
                    break
            
            if not summary and sentences:
                summary = sentences[0][:max_length]
            
            return ToolResult(success=True, data={
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register_mtc_tools(registry) -> None:
    """注册所有MTC工具到工具注册表"""
    registry.register(DocumentGeneratorTool())
    registry.register(DataAnalysisTool())
    registry.register(WebSearchTool())
    registry.register(FileReaderTool())
    registry.register(FileWriterTool())
    registry.register(FileListTool())
    registry.register(SummaryGeneratorTool())
