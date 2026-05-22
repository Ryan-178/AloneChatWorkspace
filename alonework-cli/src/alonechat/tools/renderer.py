"""
工具渲染器 - Tool Renderer

使用Rich美化工具输出
Beautify tool output with Rich
"""

from typing import Any, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree


console = Console()


class ToolRenderer:
    """
    工具渲染器 - Tool Renderer
    
    使用Rich美化工具执行结果的显示
    Beautify tool execution result display with Rich
    
    功能 / Features:
    - 工具调用显示
    - 结果格式化
    - 错误高亮
    - 文件路径超链接
    """
    
    @staticmethod
    def render_tool_call(
        tool_name: str,
        params: Dict[str, Any],
    ) -> None:
        """
        渲染工具调用 / Render tool call
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        """
        params_text = Text()
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 100:
                display_value = value[:100] + "..."
            else:
                display_value = str(value)
            params_text.append(f"\n  {key}: ", style="cyan")
            params_text.append(display_value, style="white")
        
        console.print(Panel(
            params_text,
            title=f"[bold yellow]🔧 {tool_name}[/bold yellow]",
            border_style="yellow",
        ))
    
    @staticmethod
    def render_result(
        tool_name: str,
        result: Dict[str, Any],
    ) -> None:
        """
        渲染执行结果 / Render execution result
        
        Args:
            tool_name: 工具名称 / Tool name
            result: 执行结果 / Execution result
        """
        success = result.get("success", False)
        
        if success:
            ToolRenderer._render_success(tool_name, result)
        else:
            ToolRenderer._render_error(tool_name, result)
    
    @staticmethod
    def _render_success(tool_name: str, result: Dict[str, Any]) -> None:
        """
        渲染成功结果 / Render success result
        
        Args:
            tool_name: 工具名称 / Tool name
            result: 执行结果 / Execution result
        """
        if tool_name == "file_read":
            content = result.get("content", "")
            path = result.get("path", "")
            
            console.print(f"[green]✓ 读取文件成功 / File read successfully[/green]")
            console.print(f"[dim]路径: {path}[/dim]")
            
            if len(content) > 1000:
                console.print(Panel(
                    content[:1000] + "\n... (truncated)",
                    title="文件内容 / File Content",
                    border_style="green",
                ))
            else:
                console.print(Panel(
                    content,
                    title="文件内容 / File Content",
                    border_style="green",
                ))
        
        elif tool_name == "file_write":
            path = result.get("path", "")
            size = result.get("size", 0)
            console.print(f"[green]✓ 写入文件成功 / File written successfully[/green]")
            console.print(f"[dim]路径: {path}, 大小: {size} bytes[/dim]")
        
        elif tool_name == "file_edit":
            path = result.get("path", "")
            replacements = result.get("replacements", 0)
            console.print(f"[green]✓ 编辑文件成功 / File edited successfully[/green]")
            console.print(f"[dim]路径: {path}, 替换次数: {replacements}[/dim]")
        
        elif tool_name == "shell":
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            return_code = result.get("return_code", 0)
            
            console.print(f"[green]✓ Shell命令执行成功 / Shell command executed[/green]")
            console.print(f"[dim]返回码: {return_code}[/dim]")
            
            if stdout:
                console.print(Panel(
                    stdout[:2000] if len(stdout) > 2000 else stdout,
                    title="标准输出 / stdout",
                    border_style="green",
                ))
            if stderr:
                console.print(Panel(
                    stderr[:1000] if len(stderr) > 1000 else stderr,
                    title="标准错误 / stderr",
                    border_style="yellow",
                ))
        
        elif tool_name == "git_status":
            output = result.get("output", "")
            console.print(f"[green]✓ Git状态 / Git Status[/green]")
            console.print(output)
        
        elif tool_name == "git_diff":
            diff = result.get("diff", "")
            console.print(f"[green]✓ Git差异 / Git Diff[/green]")
            if diff:
                syntax = Syntax(diff, "diff", theme="monokai")
                console.print(syntax)
            else:
                console.print("[dim]无差异 / No differences[/dim]")
        
        elif tool_name == "file_search":
            matches = result.get("matches", [])
            total = result.get("total", 0)
            engine = result.get("engine", "unknown")
            
            console.print(f"[green]✓ 搜索完成 / Search completed[/green]")
            console.print(f"[dim]找到 {total} 个匹配 (引擎: {engine})[/dim]")
            
            if matches:
                table = Table(title="搜索结果 / Search Results")
                table.add_column("文件 / File", style="cyan")
                table.add_column("行 / Line", style="yellow")
                table.add_column("内容 / Content", style="white")
                
                for match in matches[:20]:
                    table.add_row(
                        match.get("file", ""),
                        str(match.get("line", 0)),
                        match.get("content", "")[:80],
                    )
                
                console.print(table)
        
        else:
            console.print(f"[green]✓ {tool_name} 执行成功[/green]")
            if result:
                for key, value in result.items():
                    if key != "success":
                        console.print(f"[dim]{key}: {value}[/dim]")
    
    @staticmethod
    def _render_error(tool_name: str, result: Dict[str, Any]) -> None:
        """
        渲染错误结果 / Render error result
        
        Args:
            tool_name: 工具名称 / Tool name
            result: 执行结果 / Execution result
        """
        error = result.get("error", "Unknown error")
        
        console.print(Panel(
            error,
            title=f"[bold red]✗ {tool_name} 执行失败 / Execution Failed[/bold red]",
            border_style="red",
        ))
    
    @staticmethod
    def render_tool_list(tools: Dict[str, Any]) -> None:
        """
        渲染工具列表 / Render tool list
        
        Args:
            tools: 工具字典 / Tool dictionary
        """
        table = Table(title="可用工具 / Available Tools")
        table.add_column("名称 / Name", style="cyan")
        table.add_column("分类 / Category", style="yellow")
        table.add_column("权限 / Permission", style="magenta")
        table.add_column("描述 / Description", style="white")
        
        for name, tool in tools.items():
            table.add_row(
                name,
                tool.get("category", "general"),
                tool.get("permission_level", "read"),
                tool.get("description", "")[:50],
            )
        
        console.print(table)
