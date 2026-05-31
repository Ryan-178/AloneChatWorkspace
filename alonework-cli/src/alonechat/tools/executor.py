"""
工具执行器 - Tool Executor

执行工具并处理审批流程
Execute tools and handle approval flow
"""

from typing import Any, Dict, Optional, Type
from rich.console import Console

from alonechat.core.base_tool import BaseTool
from alonechat.core.types import InteractionMode


console = Console()


class ToolExecutor:
    """
    工具执行器 - Tool Executor
    
    管理工具的执行和审批流程
    Manages tool execution and approval flow
    
    功能 / Features:
    - 工具注册和发现
    - 审批流程集成
    - 执行结果处理
    - 错误处理
    """
    
    def __init__(self, mode_manager=None, verbose: bool = False):
        """
        初始化工具执行器 / Initialize tool executor
        
        Args:
            mode_manager: 模式管理器 / Mode manager
            verbose: 是否显示详细信息 / Whether to show verbose info
        """
        self.mode_manager = mode_manager
        self.verbose = verbose
        self._tools: Dict[str, BaseTool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self) -> None:
        """
        注册内置工具 / Register builtin tools
        """
        from alonechat.tools.builtin.shell import ShellTool
        from alonechat.tools.builtin.file import (
            FileReadTool,
            FileWriteTool,
            FileEditTool,
            FileDeleteTool,
            FileSearchTool,
        )
        from alonechat.tools.builtin.git import (
            GitStatusTool,
            GitDiffTool,
            GitCommitTool,
            GitBranchTool,
        )
        
        self.register_tool(ShellTool())
        self.register_tool(FileReadTool())
        self.register_tool(FileWriteTool())
        self.register_tool(FileEditTool())
        self.register_tool(FileDeleteTool())
        self.register_tool(FileSearchTool())
        self.register_tool(GitStatusTool())
        self.register_tool(GitDiffTool())
        self.register_tool(GitCommitTool())
        self.register_tool(GitBranchTool())
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        注册工具 / Register tool
        
        Args:
            tool: 工具实例 / Tool instance
        """
        self._tools[tool.name] = tool
        if self.verbose:
            console.print(f"[dim]Registered tool: {tool.name}[/dim]")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具 / Get tool
        
        Args:
            name: 工具名称 / Tool name
        
        Returns:
            工具实例 / Tool instance
        """
        return self._tools.get(name)
    
    def list_tools(self) -> Dict[str, BaseTool]:
        """
        列出所有工具 / List all tools
        
        Returns:
            工具字典 / Tool dictionary
        """
        return self._tools.copy()
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行工具 / Execute tool
        
        Args:
            tool_name: 工具名称 / Tool name
            params: 工具参数 / Tool parameters
        
        Returns:
            执行结果 / Execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
            }
        
        if self.mode_manager:
            if not self.mode_manager.check_tool_permission(tool_name, params):
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not allowed in current mode",
                }
            
            if self.mode_manager.needs_confirmation(tool_name):
                approved = await self.mode_manager.request_approval(tool_name, params)
                if not approved:
                    return {
                        "success": False,
                        "error": "Tool execution cancelled by user",
                    }
        
        try:
            result = tool.execute(**params)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息 / Get tool info
        
        Args:
            name: 工具名称 / Tool name
        
        Returns:
            工具信息 / Tool info
        """
        tool = self.get_tool(name)
        if tool:
            return tool.to_dict()
        return None
    
    def get_tools_by_category(self, category: str) -> Dict[str, BaseTool]:
        """
        按分类获取工具 / Get tools by category
        
        Args:
            category: 工具分类 / Tool category
        
        Returns:
            工具字典 / Tool dictionary
        """
        return {
            name: tool
            for name, tool in self._tools.items()
            if tool.category == category
        }
    
    def get_tools_by_permission(self, permission: str) -> Dict[str, BaseTool]:
        """
        按权限级别获取工具 / Get tools by permission level
        
        Args:
            permission: 权限级别 / Permission level
        
        Returns:
            工具字典 / Tool dictionary
        """
        return {
            name: tool
            for name, tool in self._tools.items()
            if tool.permission_level == permission
        }
