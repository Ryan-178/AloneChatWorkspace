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

# v2.1.80 新增命令 / New commands
from alonechat.slash.commands.copy import copy_command
from alonechat.slash.commands.diff_cmd import diff_command
from alonechat.slash.commands.effort import effort_command
from alonechat.slash.commands.files_cmd import files_command
from alonechat.slash.commands.hooks_cmd import hooks_command
from alonechat.slash.commands.memory_cmd import memory_command
from alonechat.slash.commands.rename_cmd import rename_command
from alonechat.slash.commands.resume_cmd import resume_command
from alonechat.slash.commands.session_cmd import session_command
from alonechat.slash.commands.skills_cmd import skills_command
from alonechat.slash.commands.tasks_cmd import tasks_command
from alonechat.slash.commands.tag_cmd import tag_command
from alonechat.slash.commands.theme_cmd import theme_command
from alonechat.slash.commands.color_cmd import color_command
from alonechat.slash.commands.feedback_cmd import feedback_command
from alonechat.slash.commands.fast_cmd import fast_command
from alonechat.slash.commands.output_style_cmd import output_style_command
from alonechat.slash.commands.share_cmd import share_command
from alonechat.slash.commands.stickers_cmd import stickers_command
from alonechat.slash.commands.upgrade_cmd import upgrade_command

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
    # v2.1.80 新增 / New
    "copy_command",
    "diff_command",
    "effort_command",
    "files_command",
    "hooks_command",
    "memory_command",
    "rename_command",
    "resume_command",
    "session_command",
    "skills_command",
    "tasks_command",
    "tag_command",
    "theme_command",
    "color_command",
    "feedback_command",
    "fast_command",
    "output_style_command",
    "share_command",
    "stickers_command",
    "upgrade_command",
]
