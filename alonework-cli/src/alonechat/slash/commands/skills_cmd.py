"""
/skills 命令 - 管理技能 / Manage skills

套用agent-framework的技能系统 / Uses agent-framework's skills system

版本 / Version: 2.1.80
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _load_alonechat_skills() -> list[dict]:
    """
    从alonechat加载技能 / Load skills from alonechat
    """
    try:
        from alonechat.tools.skills_registry import SkillsRegistry
        registry = SkillsRegistry()
        return registry.list_skills() if hasattr(registry, "list_skills") else []
    except ImportError:
        return []
    except Exception:
        return []


def _load_local_skills() -> list[dict]:
    """
    加载本地技能目录 / Load local skills directory
    """
    from pathlib import Path
    skills_dir = Path.cwd() / ".alonechat" / "skills"
    if not skills_dir.exists():
        return []

    skills = []
    for skill_file in skills_dir.glob("*.md"):
        content = skill_file.read_text(encoding="utf-8")
        name = skill_file.stem
        description = ""
        for line in content.split("\n"):
            if line.strip() and not line.startswith("#"):
                description = line.strip()[:80]
                break
        skills.append({
            "name": name,
            "description": description,
            "source": "local",
            "path": str(skill_file),
        })
    return skills


def _load_custom_commands() -> list[dict]:
    """
    加载自定义命令 / Load custom commands
    """
    from pathlib import Path
    commands_dir = Path.cwd() / ".alonechat" / "commands"
    if not commands_dir.exists():
        return []

    commands = []
    for cmd_file in commands_dir.glob("*.md"):
        content = cmd_file.read_text(encoding="utf-8")
        name = cmd_file.stem
        description = ""
        for line in content.split("\n"):
            if line.strip() and not line.startswith("#"):
                description = line.strip()[:80]
                break
        commands.append({
            "name": name,
            "description": description,
            "source": "custom_command",
            "path": str(cmd_file),
        })
    return commands


def skills_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    管理技能 / Manage skills

    用法 / Usage:
        /skills                 列出所有技能 / List all skills
        /skills list            列出所有技能 / List all skills
        /skills install <name>  安装技能 / Install skill
        /skills remove <name>   移除技能 / Remove skill
        /skills reload          重新加载技能 / Reload skills
        /skills info <name>     技能详情 / Skill details
        /skills search <query>  搜索技能 / Search skills
        /skills sources         技能来源 / Skill sources

    技能来源 / Skill Sources:
        - alonechat: 框架内置技能 / Framework built-in skills
        - local: .alonechat/skills/ 目录 / Local skills directory
        - custom_command: .alonechat/commands/ 目录 / Custom commands
    """
    af_skills = _load_agent_framework_skills()
    local_skills = _load_local_skills()
    custom_cmds = _load_custom_commands()

    if not args or args[0] == "list":
        all_skills = af_skills + local_skills + custom_cmds

        if not all_skills:
            console.print("[dim]未发现任何技能 / No skills found[/dim]")
            console.print("[dim]技能目录 / Skills dir: .alonechat/skills/[/dim]")
            console.print("[dim]命令目录 / Commands dir: .alonechat/commands/[/dim]")
            return

        table = Table(show_header=True, title="技能列表 / Skills List")
        table.add_column("#", style="dim", width=4)
        table.add_column("名称 / Name", style="cyan")
        table.add_column("描述 / Description", style="green")
        table.add_column("来源 / Source", style="yellow")

        for i, skill in enumerate(all_skills, 1):
            table.add_row(
                str(i),
                skill.get("name", "-"),
                skill.get("description", "")[:50],
                skill.get("source", "unknown"),
            )

        console.print(table)
        console.print(f"\n[dim]共 {len(all_skills)} 个技能 / Total {len(all_skills)} skills[/dim]")
        console.print(f"[dim]  agent-framework: {len(af_skills)} | local: {len(local_skills)} | custom: {len(custom_cmds)}[/dim]")
        return

    action = args[0]

    if action == "sources":
        console.print(Panel(
            f"[bold]技能来源 / Skill Sources[/bold]\n\n"
            f"1. alonechat 内置 / Built-in: {len(af_skills)} 个\n"
            f"   路径 / Path: alonechat/tools/\n\n"
            f"2. 本地技能目录 / Local skills: {len(local_skills)} 个\n"
            f"   路径 / Path: .alonechat/skills/\n\n"
            f"3. 自定义命令 / Custom commands: {len(custom_cmds)} 个\n"
            f"   路径 / Path: .alonechat/commands/",
            border_style="cyan",
        ))
        return

    if action == "search":
        query = " ".join(args[1:]).lower() if len(args) > 1 else ""
        if not query:
            console.print("[red]请指定搜索词 / Please specify search query[/red]")
            return
        all_skills = af_skills + local_skills + custom_cmds
        matches = [
            s for s in all_skills
            if query in s.get("name", "").lower() or query in s.get("description", "").lower()
        ]
        if matches:
            table = Table(show_header=True, title=f"搜索结果 / Search: '{query}'")
            table.add_column("名称 / Name", style="cyan")
            table.add_column("描述 / Description", style="green")
            table.add_column("来源 / Source", style="yellow")
            for s in matches:
                table.add_row(s.get("name", "-"), s.get("description", "")[:50], s.get("source", "-"))
            console.print(table)
        else:
            console.print(f"[yellow]未找到匹配技能 / No matching skills: {query}[/yellow]")
        return

    if action == "info":
        if len(args) < 2:
            console.print("[red]请指定技能名称 / Please specify skill name[/red]")
            return
        name = args[1].lower()
        all_skills = af_skills + local_skills + custom_cmds
        found = [s for s in all_skills if name in s.get("name", "").lower()]
        if found:
            skill = found[0]
            console.print(Panel(
                f"[bold]{skill.get('name', '-')}[/bold]\n\n"
                f"描述 / Description: {skill.get('description', '-')}\n"
                f"来源 / Source: {skill.get('source', '-')}\n"
                f"路径 / Path: {skill.get('path', '-')}",
                border_style="cyan",
            ))
        else:
            console.print(f"[red]未找到技能 / Skill not found: {args[1]}[/red]")
        return

    if action == "reload":
        console.print("[cyan]重新加载技能... / Reloading skills...[/cyan]")
        af_skills = _load_alonechat_skills()
        local_skills = _load_local_skills()
        custom_cmds = _load_custom_commands()
        total = len(af_skills) + len(local_skills) + len(custom_cmds)
        console.print(f"[green]✓ 技能已重新加载 / Skills reloaded: {total} 个[/green]")
        return

    if action == "install":
        console.print("[dim]技能安装功能开发中 / Skill install feature in development[/dim]")
        return

    if action == "remove":
        console.print("[dim]技能移除功能开发中 / Skill remove feature in development[/dim]")
        return

    console.print(f"[red]未知操作 / Unknown action: {action}[/red]")
    console.print("[dim]可用操作 / Available: list, sources, search, info, reload, install, remove[/dim]")
