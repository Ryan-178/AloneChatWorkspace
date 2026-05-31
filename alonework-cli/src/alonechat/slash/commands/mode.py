"""
/mode 斜杠命令 - /mode Slash Command

切换交互模式 / Switch interaction mode

用法 / Usage:
    /mode plan   - 切换到只读探索模式 / Switch to read-only exploration mode
    /mode agent  - 切换到默认交互模式 / Switch to default interaction mode
    /mode yolo   - 切换到自动批准模式 / Switch to auto-approve mode
    /mode        - 显示当前模式 / Show current mode
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from alonechat.core.types import InteractionMode


console = Console()


def handle_mode_command(
    args: list[str],
    mode_manager,
) -> str:
    """
    处理 /mode 命令 / Handle /mode command
    
    Args:
        args: 命令参数 / Command arguments
        mode_manager: 模式管理器 / Mode manager
    
    Returns:
        命令结果 / Command result
    """
    if not args:
        return _show_current_mode(mode_manager)
    
    mode_arg = args[0].lower()
    
    if mode_arg == "plan":
        return _switch_mode(mode_manager, InteractionMode.PLAN)
    elif mode_arg == "agent":
        return _switch_mode(mode_manager, InteractionMode.AGENT)
    elif mode_arg == "yolo":
        return _switch_mode(mode_manager, InteractionMode.YOLO)
    elif mode_arg == "cycle":
        new_mode = mode_manager.cycle_mode()
        return f"模式已切换到: {new_mode.value.upper()} / Mode switched to: {new_mode.value.upper()}"
    elif mode_arg in ["help", "-h", "--help"]:
        return _show_help()
    else:
        return f"[red]未知模式: {mode_arg} / Unknown mode: {mode_arg}[/red]\n" \
               f"可用模式: plan, agent, yolo / Available modes: plan, agent, yolo"


def _show_current_mode(mode_manager) -> str:
    """
    显示当前模式 / Show current mode
    
    Args:
        mode_manager: 模式管理器 / Mode manager
    
    Returns:
        当前模式信息 / Current mode info
    """
    mode_info = mode_manager.to_dict()
    
    table = Table(title="当前交互模式 / Current Interaction Mode")
    table.add_column("属性 / Property", style="cyan")
    table.add_column("值 / Value", style="green")
    
    table.add_row("模式 / Mode", f"{mode_info['icon']} {mode_info['mode'].upper()}")
    table.add_row("描述 / Description", mode_info['description'])
    table.add_row("自动批准 / Auto-approve", str(mode_info['auto_approve_tools']))
    
    if mode_info['allowed_tools']:
        table.add_row("允许工具 / Allowed Tools", ", ".join(mode_info['allowed_tools']))
    else:
        table.add_row("允许工具 / Allowed Tools", "全部 / All")
    
    if mode_info['require_confirmation']:
        table.add_row("需确认 / Require Confirmation", ", ".join(mode_info['require_confirmation']))
    else:
        table.add_row("需确认 / Require Confirmation", "无 / None")
    
    console.print(table)
    return ""


def _switch_mode(mode_manager, new_mode: InteractionMode) -> str:
    """
    切换模式 / Switch mode
    
    Args:
        mode_manager: 模式管理器 / Mode manager
        new_mode: 新模式 / New mode
    
    Returns:
        切换结果 / Switch result
    """
    old_mode = mode_manager.mode
    success = mode_manager.set_mode(new_mode)
    
    if success:
        return ""
    else:
        return f"[red]切换模式失败 / Failed to switch mode[/red]"


def _show_help() -> str:
    """
    显示帮助信息 / Show help info
    
    Returns:
        帮助信息 / Help info
    """
    help_text = """
[bold cyan]/mode 命令帮助 / /mode Command Help[/bold cyan]

[bold]用法 / Usage:[/bold]
  /mode          显示当前模式 / Show current mode
  /mode plan     只读探索模式 / Read-only exploration mode
  /mode agent    默认交互模式 / Default interaction mode
  /mode yolo     自动批准模式 / Auto-approve mode
  /mode cycle    循环切换模式 / Cycle through modes

[bold]模式说明 / Mode Descriptions:[/bold]

  [blue]🔍 PLAN[/blue]    只读探索模式
           - 仅允许读取和搜索操作
           - 适合代码分析和理解
           - Read-only exploration mode
           - Only read and search operations allowed
           - Suitable for code analysis and understanding

  [green]🤖 AGENT[/green]  默认交互模式
           - 危险操作需要用户确认
           - 平衡安全性和效率
           - Default interaction mode
           - Dangerous operations require confirmation
           - Balance between safety and efficiency

  [yellow]🚀 YOLO[/yellow]   自动批准模式
           - 所有操作自动执行
           - 适合信任的工作区
           - Auto-approve mode
           - All operations execute automatically
           - Suitable for trusted workspaces

[bold]快捷键 / Shortcuts:[/bold]
  Ctrl+M        切换模式 / Toggle mode
  Ctrl+Shift+P  PLAN模式 / PLAN mode
  Ctrl+Shift+A  AGENT模式 / AGENT mode
  Ctrl+Shift+Y  YOLO模式 / YOLO mode
"""
    console.print(Panel(help_text, border_style="cyan"))
    return ""
