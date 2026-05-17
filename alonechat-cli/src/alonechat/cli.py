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
"""

import sys
import json as json_module
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from alonechat import __version__
from alonechat.commands import init, chat, generate, test, commit
from alonechat.config import ConfigManager
from alonechat.session import SessionManager

console = Console()


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


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="AloneChat")
@click.option("--config", help="配置文件路径 / Config file path", type=click.Path())
@click.option("--verbose", "-v", is_flag=True, help="详细输出 / Verbose output")
@click.option("--print", "-p", "print_mode", is_flag=True, help="打印模式（非交互）/ Print mode (non-interactive)")
@click.option("--continue", "-C", "continue_session", is_flag=True, help="继续最近的会话 / Continue latest session")
@click.option("--resume", "-r", "resume_session", help="恢复指定会话 / Resume specific session by ID")
@click.option("--output-format", type=click.Choice(["text", "json", "stream-json"]), default="text", help="输出格式 / Output format")
@click.option("--model", "-m", "model_name", help="指定模型 / Specify model")
@click.option("--system-prompt", help="替换系统提示 / Replace system prompt")
@click.option("--append-system-prompt", help="追加系统提示 / Append system prompt")
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
    """
    ctx.ensure_object(dict)
    
    ctx.obj["verbose"] = verbose
    ctx.obj["config_manager"] = ConfigManager(config_path=config)
    ctx.obj["session_manager"] = SessionManager()
    ctx.obj["output_format"] = output_format
    ctx.obj["model_name"] = model_name
    ctx.obj["system_prompt"] = system_prompt
    ctx.obj["append_system_prompt"] = append_system_prompt
    
    if verbose:
        console.print(f"[dim]AloneChat v{__version__}[/dim]")
        if config:
            console.print(f"[dim]配置文件 / Config: {config}[/dim]")
    
    if ctx.invoked_subcommand is None:
        session_manager: SessionManager = ctx.obj["session_manager"]
        config_manager: ConfigManager = ctx.obj["config_manager"]
        
        if resume_session:
            session = session_manager.resume_session(resume_session)
            if session:
                if verbose:
                    console.print(f"[dim]已恢复会话 / Resumed session: {session.id}[/dim]")
            else:
                console.print(f"[red]未找到会话 / Session not found: {resume_session}[/red]")
                sys.exit(1)
        
        elif continue_session:
            session = session_manager.continue_session()
            if session:
                if verbose:
                    console.print(f"[dim]已继续会话 / Continued session: {session.id}[/dim]")
            else:
                if verbose:
                    console.print("[dim]未找到历史会话，将创建新会话 / No session found, creating new[/dim]")
                session_manager.create_session()
        
        pipe_input = session_manager.read_pipe_input()
        
        if print_mode or pipe_input:
            if not query and not pipe_input:
                console.print("[red]错误: 打印模式需要提供查询 / Error: Print mode requires query[/red]")
                sys.exit(1)
            
            if session_manager.current_session is None:
                session_manager.create_session()
            
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

from alonechat.mcp.cli import mcp_command
main.add_command(mcp_command, name="mcp")


if __name__ == "__main__":
    main()
