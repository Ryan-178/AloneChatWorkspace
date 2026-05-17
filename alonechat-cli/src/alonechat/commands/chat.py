"""
chat命令 - 启动交互式对话 / chat command - Start interactive chat

提供交互式对话界面，支持 / Provides interactive chat interface:
- 自然语言交互 / Natural language interaction
- 代码生成和理解 / Code generation and understanding
- 多轮对话 / Multi-turn conversation
- 上下文缓存 / Context caching
- 思考模式 / Thinking mode
- 会话管理 / Session management
- Slash命令 / Slash commands
"""

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter, DEEPSEEK_MODEL, ChatResponse, UsageInfo
from alonechat.context import ContextManager

console = Console()


def format_usage(usage: UsageInfo | None) -> str:
    """格式化使用量信息 / Format usage info"""
    if usage is None:
        return ""
    
    parts = []
    
    if usage.prompt_tokens > 0:
        parts.append(f"输入: {usage.prompt_tokens:,}")
    if usage.completion_tokens > 0:
        parts.append(f"输出: {usage.completion_tokens:,}")
    
    if usage.prompt_cache_hit_tokens > 0:
        hit_rate = usage.cache_hit_rate * 100
        parts.append(f"缓存命中: {usage.prompt_cache_hit_tokens:,} ({hit_rate:.1f}%)")
    
    if usage.total_tokens > 0:
        parts.append(f"总计: {usage.total_tokens:,}")
    
    return " | ".join(parts)


def process_slash_command(
    user_input: str,
    obj: dict,
    session_manager,
) -> tuple[bool, bool]:
    """
    处理slash命令 / Process slash command
    
    返回 (handled, should_continue) / Returns (handled, should_continue)
    """
    if not user_input.startswith("/"):
        return False, True
    
    from alonechat.slash import SlashCommandExecutor
    
    executor = SlashCommandExecutor(obj, session_manager)
    command = user_input[1:].split()[0] if len(user_input) > 1 else ""
    args = user_input[1:].split()[1:] if len(user_input.split()) > 1 else []
    
    result = executor.execute(command, args)
    
    if result == "exit":
        return True, False
    if result == "clear":
        return True, True
    
    return True, True


def run_chat_loop(
    obj: dict,
    config_manager: ConfigManager,
    context: int,
    show_reasoning: bool,
    show_usage: bool,
    session_manager,
    initial_messages: Optional[list] = None,
) -> None:
    """
    运行聊天循环 / Run chat loop
    
    核心聊天交互逻辑 / Core chat interaction logic
    """
    config = config_manager.load_config()
    model_router = ModelRouter(config)
    context_manager = ContextManager(max_tokens=context)
    
    messages: list[dict[str, str]] = initial_messages or []
    
    console.print("[bold green]AloneChat 已就绪，请输入您的指令... / Ready, please enter your instruction...[/bold green]\n")
    
    while True:
        try:
            user_input = Prompt.ask("[bold blue]You[/bold blue]")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("\n[dim]再见！ / Goodbye![/dim]")
                break
            
            if not user_input.strip():
                continue
            
            if user_input.startswith("/"):
                handled, should_continue = process_slash_command(user_input, obj, session_manager)
                if not should_continue:
                    break
                if handled:
                    continue
            
            messages.append({"role": "user", "content": user_input})
            if session_manager:
                session_manager.add_message("user", user_input)
            
            console.print("\n[bold green]AloneChat[/bold green]")
            
            with console.status("[bold green]思考中... / Thinking...[/bold green]"):
                response = model_router.chat_with_reasoning(
                    messages=messages,
                )
            
            console.print()
            
            if isinstance(response, ChatResponse):
                if show_reasoning and response.reasoning_content:
                    console.print("\n[dim][思考过程 / Reasoning Process][/dim]")
                    console.print(f"[dim]{response.reasoning_content}[/dim]\n")
                
                console.print(Markdown(response.content))
                
                messages.append({"role": "assistant", "content": response.content})
                if session_manager:
                    session_manager.add_message("assistant", response.content)
                
                if show_usage and response.usage:
                    usage_str = format_usage(response.usage)
                    if usage_str:
                        console.print(f"\n[dim]{usage_str}[/dim]")
            else:
                console.print(Markdown(str(response)))
                messages.append({"role": "assistant", "content": str(response)})
                if session_manager:
                    session_manager.add_message("assistant", str(response))
            
            console.print("\n" + "─" * 60 + "\n")
            
        except KeyboardInterrupt:
            console.print("\n\n[dim]已中断 / Interrupted[/dim]")
            break
        except Exception as e:
            console.print(f"\n[red]错误 / Error: {e}[/red]")
            console.print("[dim]请重试或输入 'exit' 退出 / Please retry or type 'exit' to quit[/dim]\n")


def start_interactive(obj: dict, session_manager=None) -> None:
    """
    启动交互模式 / Start interactive mode
    
    从主入口调用的交互模式 / Interactive mode called from main entry
    """
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]错误: 未找到配置文件 / Error: Config file not found[/red]")
        console.print("请先运行 / Please run: [cyan]alonechat init[/cyan]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]AloneChat 交互模式 / Interactive Mode[/bold cyan]\n\n"
        "输入自然语言指令，AI将帮助您 / Enter natural language, AI will help you:\n"
        "• 生成代码 / Generate code\n"
        "• 理解代码 / Understand code\n"
        "• 重构代码 / Refactor code\n"
        "• 修复错误 / Fix errors\n"
        "• 回答问题 / Answer questions\n\n"
        f"[dim]模型: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]思考模式: 已启用 (reasoning_effort=high)[/dim]\n"
        "[dim]上下文缓存: 自动启用 (缓存命中率可达99.98%)[/dim]\n"
        "[dim]输入 'exit' 或 'quit' 退出 / Type 'exit' or 'quit' to exit[/dim]\n"
        "[dim]输入 '/help' 查看slash命令 / Type '/help' for slash commands[/dim]",
        border_style="cyan"
    ))
    
    console.print(f"\n使用模型 / Using model: [cyan]DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/cyan]")
    console.print(f"思考强度 / Reasoning effort: [cyan]high[/cyan]")
    console.print(f"上下文窗口 / Context window: [cyan]{1000000:,} tokens[/cyan]")
    console.print(f"上下文缓存 / Context cache: [cyan]自动启用 / Auto enabled[/cyan]")
    
    if session_manager and session_manager.current_session:
        session_info = session_manager.get_session_info()
        console.print(f"会话ID / Session ID: [cyan]{session_info['id'][:8]}...[/cyan]")
    
    console.print("\n" + "─" * 60 + "\n")
    
    initial_messages = []
    if session_manager:
        initial_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in session_manager.get_messages()
        ]
        if initial_messages:
            console.print(f"[dim]已加载 {len(initial_messages)} 条历史消息 / Loaded {len(initial_messages)} history messages[/dim]\n")
    
    run_chat_loop(
        obj=obj,
        config_manager=config_manager,
        context=1000000,
        show_reasoning=False,
        show_usage=True,
        session_manager=session_manager,
        initial_messages=initial_messages,
    )


def start_interactive_with_query(obj: dict, initial_query: str, session_manager=None) -> None:
    """
    带初始查询启动交互模式 / Start interactive mode with initial query
    
    从主入口带查询字符串调用 / Called from main entry with query string
    """
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]错误: 未找到配置文件 / Error: Config file not found[/red]")
        console.print("请先运行 / Please run: [cyan]alonechat init[/cyan]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]AloneChat 交互模式 / Interactive Mode[/bold cyan]\n\n"
        f"[dim]模型: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]输入 'exit' 或 'quit' 退出 / Type 'exit' or 'quit' to exit[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n" + "─" * 60 + "\n")
    
    initial_messages = []
    if session_manager:
        initial_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in session_manager.get_messages()
        ]
    
    config = config_manager.load_config()
    model_router = ModelRouter(config)
    
    messages = initial_messages.copy()
    messages.append({"role": "user", "content": initial_query})
    if session_manager:
        session_manager.add_message("user", initial_query)
    
    console.print(f"[bold blue]You[/bold blue]: {initial_query}\n")
    console.print("[bold green]AloneChat[/bold green]")
    
    with console.status("[bold green]思考中... / Thinking...[/bold green]"):
        response = model_router.chat_with_reasoning(messages=messages)
    
    console.print()
    
    if isinstance(response, ChatResponse):
        console.print(Markdown(response.content))
        messages.append({"role": "assistant", "content": response.content})
        if session_manager:
            session_manager.add_message("assistant", response.content)
    else:
        console.print(Markdown(str(response)))
        messages.append({"role": "assistant", "content": str(response)})
        if session_manager:
            session_manager.add_message("assistant", str(response))
    
    console.print("\n" + "─" * 60 + "\n")
    
    run_chat_loop(
        obj=obj,
        config_manager=config_manager,
        context=1000000,
        show_reasoning=False,
        show_usage=True,
        session_manager=session_manager,
        initial_messages=messages,
    )


@click.command()
@click.option("--context", "-c", help="上下文窗口大小 / Context window size", type=int, default=1000000)
@click.option("--show-reasoning", is_flag=True, help="显示思考过程 / Show reasoning process")
@click.option("--show-usage", is_flag=True, default=True, help="显示使用量 / Show usage")
@click.pass_obj
def chat_command(obj: dict, context: int, show_reasoning: bool, show_usage: bool) -> None:
    """
    启动交互式对话 / Start interactive chat
    
    提供自然语言交互界面，支持代码生成、理解和多轮对话 / Provides natural language interface for code generation, understanding and multi-turn conversation
    """
    console.print(Panel.fit(
        "[bold cyan]AloneChat 交互模式 / Interactive Mode[/bold cyan]\n\n"
        "输入自然语言指令，AI将帮助您 / Enter natural language, AI will help you:\n"
        "• 生成代码 / Generate code\n"
        "• 理解代码 / Understand code\n"
        "• 重构代码 / Refactor code\n"
        "• 修复错误 / Fix errors\n"
        "• 回答问题 / Answer questions\n\n"
        f"[dim]模型: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]思考模式: 已启用 (reasoning_effort=high)[/dim]\n"
        "[dim]上下文缓存: 自动启用 (缓存命中率可达99.98%)[/dim]\n"
        "[dim]输入 'exit' 或 'quit' 退出 / Type 'exit' or 'quit' to exit[/dim]",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]错误: 未找到配置文件 / Error: Config file not found[/red]")
        console.print("请先运行 / Please run: [cyan]alonechat init[/cyan]")
        return
    
    config = config_manager.load_config()
    
    console.print(f"\n使用模型 / Using model: [cyan]DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/cyan]")
    console.print(f"思考强度 / Reasoning effort: [cyan]high[/cyan]")
    console.print(f"上下文窗口 / Context window: [cyan]{context:,} tokens[/cyan]")
    console.print(f"上下文缓存 / Context cache: [cyan]自动启用 / Auto enabled[/cyan]")
    console.print("\n" + "─" * 60 + "\n")
    
    session_manager = obj.get("session_manager")
    
    run_chat_loop(
        obj=obj,
        config_manager=config_manager,
        context=context,
        show_reasoning=show_reasoning,
        show_usage=show_usage,
        session_manager=session_manager,
        initial_messages=None,
    )
