"""
内置Slash命令 / Built-in Slash Commands

提供核心slash命令实现 / Provides core slash command implementations

新增命令 / New Commands:
- fork_command: 分叉会话 / Fork session (v2.1.77)
- branch_command: 管理分支 / Manage branches (v2.1.77)
- context_command: 上下文分析 / Context analysis (v2.1.74)
- stats_command: 使用统计 / Usage statistics (v2.1.6)
- plan_command: 创建执行计划 / Create execution plan (v2.1.72)
- remote_control_command: 远程桥接 / Remote bridge (v2.1.79)
- reload_plugins_command: 重新加载插件 / Reload plugins (v2.1.69)
- debug_command: 排查会话故障 / Troubleshoot session (v2.1.30)
- keybindings_command: 键盘快捷键 / Keyboard shortcuts (v2.1.18)
- claude_api_command: Claude API技能 / Claude API skill (v2.1.69)
- terminal_setup_command: 终端配置 / Terminal setup (v2.0.74)
- todos_command: 待办事项 / Todo list (v1.0.94)
- export_command: 导出对话 / Export conversation (v1.0.44)
"""

from alonechat.slash.commands.clear import clear_command
from alonechat.slash.commands.compact import compact_command
from alonechat.slash.commands.config import config_command
from alonechat.slash.commands.context import context_command
from alonechat.slash.commands.cost import cost_command
from alonechat.slash.commands.doctor import doctor_command
from alonechat.slash.commands.help import help_command
from alonechat.slash.commands.model import model_command
from alonechat.slash.commands.review import review_command
from alonechat.slash.commands.stats import stats_command
from alonechat.slash.commands.status import status_command
from alonechat.slash.commands.usage import usage_command
from alonechat.slash.commands.fork import fork_command, branch_command
from alonechat.slash.commands.plan import plan_command
from alonechat.slash.commands.remote_control import remote_control_command
from alonechat.slash.commands.reload_plugins import reload_plugins_command
from alonechat.slash.commands.debug import debug_command
from alonechat.slash.commands.keybindings import keybindings_command
from alonechat.slash.commands.claude_api import claude_api_command
from alonechat.slash.commands.terminal_setup import terminal_setup_command
from alonechat.slash.commands.todos import todos_command
from alonechat.slash.commands.export import export_command
from alonechat.slash.commands.mode import handle_mode_command

__all__ = [
    "clear_command",
    "compact_command",
    "config_command",
    "context_command",
    "cost_command",
    "doctor_command",
    "help_command",
    "model_command",
    "review_command",
    "stats_command",
    "status_command",
    "usage_command",
    "fork_command",
    "branch_command",
    "plan_command",
    "remote_control_command",
    "reload_plugins_command",
    "debug_command",
    "keybindings_command",
    "claude_api_command",
    "terminal_setup_command",
    "todos_command",
    "export_command",
    "handle_mode_command",
]
