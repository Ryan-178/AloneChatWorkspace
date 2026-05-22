"""
AloneChat CLI主入口 / AloneChat CLI Main Entry

提供命令行接口，支持 / Provides CLI interface for:
- init: 初始化项目配置 / Initialize project config
- chat: 启动交互式对话 / Start interactive chat
- generate: 代码生成 / Code generation
- test: 自动测试 / Auto testing
- commit: 智能提交 / Smart commit

新增功能 / New Features:
- -p/--print: 打印模式 / Print mode
- --continue: 继续会话 / Continue session
- -r/--resume: 恢复会话 / Resume session
- --output-format: 输出格式 / Output format
- --name: 设置会话显示名称 / Set session display name (v2.1.76)
- --agent: 覆盖代理设置 / Override agent settings (v2.0.59)
- --auto-compact: 自动压缩对话 / Auto compact conversation (v0.2.47)
- --worktree: 在隔离的 Git 工作树中启动 / Start in isolated Git worktree (v2.1.49)
- --add-dir: 附加目录（加载技能/插件/CLAUDE.md）/ Additional directories (v2.1.45)
- --no-stream: 禁用流式输出 / Disable streaming output (v2.1.78)
- --show-thinking: 启用Ctrl+O思维块 / Enable Ctrl+O thinking block (v2.1.0)
- --no-ime: 禁用IME支持 / Disable IME support (v2.0.68)
"""

import sys
import json as json_module
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from alonechat import __version__
from alonechat.commands import init, chat, generate, test, commit, data, workflow, env
from alonechat.config import ConfigManager
from alonechat.session import SessionManager

console = Console()


def parse_agent_config(agent_str: str) -> dict:
    """
    解析代理配置字符串 / Parse agent config string

    格式 / Format: key1=value1,key2=value2
    """
    if not agent_str:
        return {}

    config = {}
    for part in agent_str.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            config[key.strip()] = value.strip()
    return config


def execute_print_mode(
    query: str,
    config_manager: ConfigManager,
    session_manager: SessionManager,
    output_format: str,
    pipe_input: str | None,
    verbose: bool,
) -> None:
    """
    执行打印模式 / Execute print mode

    非交互模式下执行查询并输出结果 / Execute query in non-interactive mode and output result
    """
    from alonechat.models import ModelRouter, ChatResponse

    config = config_manager.load_config()
    model_router = ModelRouter(config)

    messages = session_manager.get_messages()

    user_content = query
    if pipe_input:
        user_content = f"{pipe_input}\n\n{query}" if query else pipe_input

    messages.append({"role": "user", "content": user_content})

    try:
        response = model_router.chat_with_reasoning(messages=messages)

        if isinstance(response, ChatResponse):
            content = response.content
            usage = response.usage
        else:
            content = str(response)
            usage = None

        session_manager.add_message("user", user_content)
        session_manager.add_message("assistant", content)

        if output_format == "json":
            result = {
                "content": content,
                "session_id": session_manager.current_session.id if session_manager.current_session else None,
            }
            if usage:
                result["usage"] = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
            console.print(json_module.dumps(result, ensure_ascii=False, indent=2))
        else:
            console.print(content)

    except Exception as e:
        if output_format == "json":
            console.print(json_module.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            console.print(f"[red]错误 / Error: {e}[/red]")
        sys.exit(1)


def setup_cli_enhancements(
    worktree_dir: str | None,
    additional_dirs: tuple[str, ...] | None,
    verbose: bool,
) -> object | None:
    """
    设置 CLI 增强功能 / Setup CLI enhancements

    初始化工作树、附加目录、规则加载等 / Initialize worktree, add-dir, rules loading etc.

    Args:
        worktree_dir: 工作树目录 / Worktree directory
        additional_dirs: 附加目录列表 / Additional directories list
        verbose: 是否详细输出 / Whether verbose

    Returns:
        CLI 增强管理器实例 / CLI enhancements manager instance, or None
    """
    try:
        from agent_framework.cli_enhancements import CliEnhancementsManager

        manager = CliEnhancementsManager()

        add_dirs_list = list(additional_dirs) if additional_dirs else None

        state = manager.setup(
            worktree_dir=worktree_dir,
            additional_dirs=add_dirs_list,
        )

        if verbose:
            if state.worktree_active:
                console.print(f"[dim]工作树已创建 / Worktree created: {state.worktree_dir}[/dim]")
            if state.additional_dirs:
                for d in state.additional_dirs:
                    console.print(f"[dim]附加目录 / Additional dir: {d}[/dim]")
            if state.discovered_skills:
                console.print(f"[dim]发现的技能 / Discovered skills: {len(state.discovered_skills)}[/dim]")
                for skill in state.discovered_skills:
                    console.print(f"  - {skill.get('name', 'unknown')}: {skill.get('description', '')}")
            if state.rules:
                console.print(f"[dim]已加载规则 / Rules loaded: {len(state.rules)}[/dim]")
                for rule in state.rules:
                    console.print(f"  - {rule.get('name', 'unknown')} ({rule.get('condition', '')})")
            if state.claude_md_content:
                console.print(f"[dim]CLAUDE.md 已加载 / CLAUDE.md loaded[/dim]")

        return manager

    except ImportError as e:
        if verbose:
            console.print(f"[yellow]CLI 增强模块不可用 / CLI enhancements not available: {e}[/yellow]")
        return None
    except Exception as e:
        if verbose:
            console.print(f"[yellow]CLI 增强初始化失败 / CLI enhancements init failed: {e}[/yellow]")
        return None


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="AloneChat")
@click.option("--config", help="配置文件路径 / Config file path", type=click.Path())
@click.option("--verbose", "-v", is_flag=True, help="详细输出 / Verbose output")
@click.option("--print", "-p", "print_mode", is_flag=True, help="打印模式（非交互）/ Print mode (non-interactive)")
@click.option("--continue", "-C", "continue_session", is_flag=True, help="继续最近的会话 / Continue latest session")
@click.option("--resume", "-r", "resume_session", help="恢复指定会话 / Resume specific session by ID")
@click.option("--output-format", type=click.Choice(["text", "json", "stream-json"]), default="text", help="输出格式 / Output format")
@click.option("--model", "-m", "model_name", help="指定模型（固定为deepseek-v4-flash）/ Specify model (fixed to deepseek-v4-flash)")
@click.option("--system-prompt", help="替换系统提示 / Replace system prompt")
@click.option("--append-system-prompt", help="追加系统提示 / Append system prompt")
@click.option("--name", "session_name", help="设置会话显示名称 / Set session display name (v2.1.76)")
@click.option("--agent", "agent_config", help="覆盖代理设置（格式：key1=value1,key2=value2）/ Override agent settings (v2.0.59)")
@click.option("--auto-compact", is_flag=True, help="启用自动对话压缩 / Enable auto conversation compression (v0.2.47)")
@click.option("--compact-threshold", default=100, help="自动压缩阈值（消息数）/ Auto compact threshold (message count)")
@click.option("--worktree", "worktree_dir", help="在隔离的 Git 工作树中启动（指定路径）/ Start in isolated Git worktree (specify path, v2.1.49)", type=click.Path())
@click.option("--add-dir", "additional_dirs", help="附加目录（可多次使用）/ Additional directories (can be used multiple times, v2.1.45)", type=click.Path(exists=True), multiple=True)
@click.option("--no-stream", is_flag=True, help="禁用逐行流式输出 / Disable line-by-line streaming (v2.1.78)")
@click.option("--show-thinking", is_flag=True, help="启用Ctrl+O实时显示思维块 / Enable Ctrl+O live thinking display (v2.1.0)")
@click.option("--no-ime", is_flag=True, help="禁用IME输入法支持 / Disable IME input support (v2.0.68)")
@click.option("--mode", "interaction_mode", type=click.Choice(["plan", "agent", "yolo"]), default="agent", help="交互模式 (plan/agent/yolo) / Interaction mode (v0.3.0)")
@click.argument("query", required=False)
@click.pass_context
def main(
    ctx: click.Context,
    config: str | None,
    verbose: bool,
    print_mode: bool,
    continue_session: bool,
    resume_session: str | None,
    output_format: str,
    model_name: str | None,
    system_prompt: str | None,
    append_system_prompt: str | None,
    session_name: str | None,
    agent_config: str | None,
    auto_compact: bool,
    compact_threshold: int,
    worktree_dir: str | None,
    additional_dirs: tuple[str, ...] | None,
    no_stream: bool,
    show_thinking: bool,
    no_ime: bool,
    interaction_mode: str,
    query: str | None,
) -> None:
    """
    AloneChat - 国产化、终端原生、深度中文优化的AI编程Agent

    \b
    核心特性 / Core Features:
    - 🔒 隐私保护：代码完全本地化 / Privacy: Code stays local
    - 🚀 本地优先：核心功能本地运行 / Local-first: Core runs locally
    - 🌐 离线支持：支持本地模型 / Offline: Local model support
    - 🇨🇳 中文优化：深度中文理解 / Chinese: Deep Chinese understanding

    \b
    快速开始 / Quick Start:
    $ alonechat init          # 初始化配置 / Initialize config
    $ alonechat chat          # 启动对话 / Start chat
    $ alonechat generate      # 生成代码 / Generate code
    $ alonechat -p "query"    # 打印模式 / Print mode
    $ alonechat -C            # 继续会话 / Continue session
    $ alonechat --name "我的会话"  # 设置会话名称 / Set session name
    $ alonechat --agent model=deepseek-v3  # 覆盖代理设置 / Override agent
    $ alonechat --no-stream   # 禁用流式输出 / Disable streaming (v2.1.78)

    \b
    数据管理 / Data Management:
    $ alonechat data collect           # 收集交互数据 / Collect interaction data
    $ alonechat data list              # 列出已收集数据 / List collected data
    $ alonechat data export            # 导出训练数据 / Export training data
    $ alonechat data quality           # 评估数据质量 / Evaluate data quality
    $ alonechat data stats             # 数据统计 / Data statistics
    $ alonechat data clean             # 清理数据 / Clean up data

    \b
    工作流编排 / Workflow Orchestration:
    $ alonechat workflow list          # 列出工作流 / List workflows
    $ alonechat workflow create        # 创建工作流 / Create workflow
    $ alonechat workflow run <id>      # 执行工作流 / Execute workflow
    $ alonechat workflow plan "task"   # 规划任务 / Plan task
    $ alonechat workflow delete <id>   # 删除工作流 / Delete workflow

    \b
    环境管理 / Environment Management:
    $ alonechat env status             # 查看环境状态 / View environment status
    $ alonechat env reset              # 重置环境 / Reset environment
    $ alonechat env checkpoint         # 创建检查点 / Create checkpoint
    $ alonechat env restore <name>     # 恢复检查点 / Restore checkpoint
    $ alonechat env sandbox            # 沙箱管理 / Sandbox management
    $ alonechat env tree               # 显示状态树 / Display state tree

    \b
    CLI 增强 / CLI Enhancements:
    $ alonechat --worktree /path/to/worktree  # 在隔离工作树中启动 / Start in isolated worktree (v2.1.49)
    $ alonechat --add-dir /path/to/dir1 --add-dir /path/to/dir2  # 附加目录 / Additional dirs (v2.1.45)
    $ alonechat --show-thinking  # 启用实时思维块显示 / Enable live thinking display (v2.1.0)
    """
    ctx.ensure_object(dict)

    parsed_agent_config = parse_agent_config(agent_config) if agent_config else {}

    ctx.obj["verbose"] = verbose
    ctx.obj["config_manager"] = ConfigManager(config_path=config)
    ctx.obj["session_manager"] = SessionManager()
    ctx.obj["output_format"] = output_format
    ctx.obj["model_name"] = model_name
    ctx.obj["system_prompt"] = system_prompt
    ctx.obj["append_system_prompt"] = append_system_prompt
    ctx.obj["session_name"] = session_name
    ctx.obj["agent_config"] = parsed_agent_config
    ctx.obj["auto_compact"] = auto_compact
    ctx.obj["compact_threshold"] = compact_threshold
    ctx.obj["no_stream"] = no_stream
    ctx.obj["show_thinking"] = show_thinking
    ctx.obj["no_ime"] = no_ime
    
    from alonechat.modes import CliModeManager, InteractionMode
    mode_manager = CliModeManager(verbose=verbose)
    mode_manager.set_mode(InteractionMode(interaction_mode))
    ctx.obj["mode_manager"] = mode_manager

    if verbose:
        console.print(f"[dim]AloneChat v{__version__}[/dim]")
        if config:
            console.print(f"[dim]配置文件 / Config: {config}[/dim]")
        if session_name:
            console.print(f"[dim]会话名称 / Session name: {session_name}[/dim]")
        if agent_config:
            console.print(f"[dim]代理配置 / Agent config: {parsed_agent_config}[/dim]")
        if auto_compact:
            console.print(f"[dim]自动压缩已启用，阈值: {compact_threshold} 条消息 / Auto compact enabled, threshold: {compact_threshold} messages[/dim]")
        if worktree_dir:
            console.print(f"[dim]工作树模式 / Worktree mode: {worktree_dir}[/dim]")
        if additional_dirs:
            console.print(f"[dim]附加目录 / Additional dirs: {', '.join(additional_dirs)}[/dim]")
        if show_thinking:
            console.print(f"[dim]思维块显示已启用 / Thinking display enabled[/dim]")
        if no_stream:
            console.print(f"[dim]流式输出已禁用 / Streaming disabled[/dim]")
        if no_ime:
            console.print(f"[dim]IME支持已禁用 / IME support disabled[/dim]")
        if interaction_mode != "agent":
            console.print(f"[dim]交互模式 / Interaction mode: {interaction_mode}[/dim]")

    cli_enhancements_manager = setup_cli_enhancements(
        worktree_dir=worktree_dir,
        additional_dirs=additional_dirs,
        verbose=verbose,
    )

    ctx.obj["cli_enhancements"] = cli_enhancements_manager

    if ctx.invoked_subcommand is None:
        session_manager: SessionManager = ctx.obj["session_manager"]
        config_manager: ConfigManager = ctx.obj["config_manager"]

        if resume_session:
            session = session_manager.resume_session(resume_session)
            if session:
                if verbose:
                    console.print(f"[dim]已恢复会话 / Resumed session: {session.get_name()}[/dim]")
            else:
                console.print(f"[red]未找到会话 / Session not found: {resume_session}[/red]")
                sys.exit(1)

        elif continue_session:
            session = session_manager.continue_session()
            if session:
                if verbose:
                    console.print(f"[dim]已继续会话 / Continued session: {session.get_name()}[/dim]")
            else:
                if verbose:
                    console.print("[dim]未找到历史会话，将创建新会话 / No session found, creating new[/dim]")
                session_manager.create_session(
                    display_name=session_name,
                    agent_config=parsed_agent_config,
                )

        pipe_input = session_manager.read_pipe_input()

        if print_mode or pipe_input:
            if not query and not pipe_input:
                console.print("[red]错误: 打印模式需要提供查询 / Error: Print mode requires query[/red]")
                sys.exit(1)

            if session_manager.current_session is None:
                session_manager.create_session(
                    display_name=session_name,
                    agent_config=parsed_agent_config,
                )

            execute_print_mode(
                query=query or "",
                config_manager=config_manager,
                session_manager=session_manager,
                output_format=output_format,
                pipe_input=pipe_input,
                verbose=verbose,
            )
            return

        if query:
            from alonechat.commands.chat import start_interactive_with_query
            start_interactive_with_query(
                ctx.obj,
                initial_query=query,
                session_manager=session_manager,
            )
            return

        from alonechat.commands.chat import start_interactive
        start_interactive(ctx.obj, session_manager=session_manager)


main.add_command(init.init_command, name="init")
main.add_command(chat.chat_command, name="chat")
main.add_command(generate.generate_command, name="generate")
main.add_command(test.test_command, name="test")
main.add_command(commit.commit_command, name="commit")
main.add_command(data.data_commands, name="data")
main.add_command(workflow.workflow_commands, name="workflow")
main.add_command(env.env_commands, name="env")

from alonechat.mcp.cli import mcp_command
main.add_command(mcp_command, name="mcp")

from alonechat.commands.agent import agent_commands
main.add_command(agent_commands, name="agent")


if __name__ == "__main__":
    main()
