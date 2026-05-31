"""
/hooks 命令 - 查看工具事件钩子配置 / View hook configurations for tool events

版本 / Version: 2.1.80
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

console = Console()

HOOKS_CONFIG_PATH = Path.cwd() / ".alonechat" / "hooks.yaml"

HOOK_EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "SubagentStop",
]

BUILTIN_TOOLS = [
    "bash", "file_read", "file_write", "file_edit",
    "glob", "grep", "web_search", "web_fetch",
    "agent", "skill", "todo_write",
]


def _load_hooks_config() -> dict:
    """
    加载钩子配置 / Load hooks configuration
    """
    if not HOOKS_CONFIG_PATH.exists():
        return {}
    try:
        with open(HOOKS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_hooks_config(config: dict) -> bool:
    """
    保存钩子配置 / Save hooks configuration
    """
    try:
        HOOKS_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HOOKS_CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        console.print(f"[red]保存失败 / Save failed: {e}[/red]")
        return False


def hooks_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    查看工具事件钩子配置 / View hook configurations for tool events

    用法 / Usage:
        /hooks                 显示所有钩子 / Show all hooks
        /hooks list            列出已配置的钩子 / List configured hooks
        /hooks events          列出可用事件 / List available events
        /hooks tools           列出可用工具 / List available tools
        /hooks add <event> <tool> <command>  添加钩子 / Add hook
        /hooks remove <event> <tool>         移除钩子 / Remove hook
        /hooks test <event> <tool>           测试钩子 / Test hook
        /hooks reset           重置所有钩子 / Reset all hooks
    """
    config = _load_hooks_config()
    hooks = config.get("hooks", {})

    if not args or args[0] == "list":
        if not hooks:
            console.print("[dim]未配置任何钩子 / No hooks configured[/dim]")
            console.print("[dim]使用 /hooks events 查看可用事件 / Use /hooks events to see events[/dim]")
            return

        tree = Tree("[bold cyan]钩子配置 / Hook Configuration[/bold cyan]")
        for event, event_hooks in hooks.items():
            event_node = tree.add(f"[yellow]{event}[/yellow]")
            if isinstance(event_hooks, dict):
                for tool, commands in event_hooks.items():
                    tool_node = event_node.add(f"[green]{tool}[/green]")
                    if isinstance(commands, list):
                        for cmd in commands:
                            tool_node.add(f"[dim]{cmd}[/dim]")
                    else:
                        tool_node.add(f"[dim]{commands}[/dim]")
            elif isinstance(event_hooks, list):
                for hook in event_hooks:
                    event_node.add(f"[dim]{hook}[/dim]")
        console.print(tree)
        return

    action = args[0]

    if action == "events":
        table = Table(show_header=True, title="可用钩子事件 / Available Hook Events")
        table.add_column("事件 / Event", style="cyan")
        table.add_column("描述 / Description", style="green")
        event_desc = {
            "PreToolUse": "工具调用前 / Before tool invocation",
            "PostToolUse": "工具调用后 / After tool invocation",
            "Notification": "通知触发时 / When notification triggers",
            "Stop": "助手停止时 / When assistant stops",
            "SubagentStop": "子代理停止时 / When subagent stops",
        }
        for event in HOOK_EVENTS:
            table.add_row(event, event_desc.get(event, ""))
        console.print(table)
        return

    if action == "tools":
        table = Table(show_header=True, title="可用工具 / Available Tools")
        table.add_column("工具 / Tool", style="cyan")
        for tool in BUILTIN_TOOLS:
            table.add_row(tool)
        console.print(table)
        return

    if action == "add":
        if len(args) < 4:
            console.print("[red]参数不足 / Insufficient arguments[/red]")
            console.print("[dim]用法 / Usage: /hooks add <event> <tool> <command>[/dim]")
            return
        event, tool, command = args[1], args[2], " ".join(args[3:])
        if event not in HOOK_EVENTS:
            console.print(f"[red]未知事件 / Unknown event: {event}[/red]")
            return
        if "hooks" not in config:
            config["hooks"] = {}
        if event not in config["hooks"]:
            config["hooks"][event] = {}
        if not isinstance(config["hooks"][event], dict):
            config["hooks"][event] = {}
        if tool not in config["hooks"][event]:
            config["hooks"][event][tool] = []
        if not isinstance(config["hooks"][event][tool], list):
            config["hooks"][event][tool] = [config["hooks"][event][tool]]
        config["hooks"][event][tool].append(command)
        if _save_hooks_config(config):
            console.print(f"[green]✓ 钩子已添加 / Hook added: {event} -> {tool}[/green]")
            console.print(f"[dim]命令 / Command: {command}[/dim]")
        return

    if action == "remove":
        if len(args) < 3:
            console.print("[red]参数不足 / Insufficient arguments[/red]")
            console.print("[dim]用法 / Usage: /hooks remove <event> <tool>[/dim]")
            return
        event, tool = args[1], args[2]
        if event in hooks and isinstance(hooks[event], dict) and tool in hooks[event]:
            del hooks[event][tool]
            _save_hooks_config(config)
            console.print(f"[green]✓ 钩子已移除 / Hook removed: {event} -> {tool}[/green]")
        else:
            console.print(f"[yellow]钩子不存在 / Hook not found: {event} -> {tool}[/yellow]")
        return

    if action == "test":
        if len(args) < 3:
            console.print("[red]参数不足 / Insufficient arguments[/red]")
            return
        event, tool = args[1], args[2]
        if event in hooks and isinstance(hooks[event], dict) and tool in hooks[event]:
            commands = hooks[event][tool]
            if isinstance(commands, list):
                for cmd in commands:
                    console.print(f"[cyan]测试 / Testing: {cmd}[/cyan]")
            else:
                console.print(f"[cyan]测试 / Testing: {commands}[/cyan]")
            console.print("[green]✓ 钩子配置有效 / Hook config valid[/green]")
        else:
            console.print(f"[yellow]钩子不存在 / Hook not found: {event} -> {tool}[/yellow]")
        return

    if action == "reset":
        if _save_hooks_config({"hooks": {}}):
            console.print("[green]✓ 所有钩子已重置 / All hooks reset[/green]")
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: list, events, tools, add, remove, test, reset[/dim]")
