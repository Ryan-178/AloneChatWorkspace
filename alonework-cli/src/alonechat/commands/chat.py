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
- 逐行流式输出 / Line-by-line streaming output (v2.1.78)
- Ctrl+O 实时显示思维块 / Ctrl+O live thinking block (v2.1.0)
- 提示建议 / Prompt suggestions (v2.0.70)
- IME支持 / IME support (v2.0.68)
- 自动对话压缩 / Auto conversation compression (v0.2.47)
- 会话显示名称 / Session display name (v2.1.76)
"""

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from typing import Optional

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter, DEEPSEEK_MODEL, ChatResponse, UsageInfo
from alonechat.context import ContextManager
from alonechat.utils.streaming import stream_response_line_by_line
from alonechat.utils.thinking_block import ThinkingBlockDisplay
from alonechat.utils.hyperlinks import wrap_file_paths_in_output, make_file_link
from alonechat.utils.images import process_image_links_in_output
from alonechat.utils.ime_support import IMEManager
from alonechat.slash.commands.compact import auto_compact_check, show_compact_status
from alonechat.configs.style_loader import get_style_config

console = Console()


# 会话成本追踪 / Session cost tracking
_session_cost: float = 0.0

DEEPSEEK_INPUT_RATE = 0.001  # $0.001 / 1M tokens
DEEPSEEK_OUTPUT_RATE = 0.002  # $0.002 / 1M tokens


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


def format_session_cost() -> str:
    """格式化会话总成本 / Format total session cost"""
    global _session_cost
    if _session_cost <= 0:
        return ""
    return f"会话成本: ${_session_cost:.4f} / Session cost: ${_session_cost:.4f}"


def update_session_cost(usage: UsageInfo | None) -> None:
    """更新会话累计成本 / Update cumulative session cost"""
    global _session_cost
    if usage is None:
        return
    
    input_cost = usage.prompt_tokens * DEEPSEEK_INPUT_RATE / 1_000_000
    output_cost = usage.completion_tokens * DEEPSEEK_OUTPUT_RATE / 1_000_000
    _session_cost += input_cost + output_cost


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
    stream: bool = True,
    enable_thinking_block: bool = False,
    auto_compact: bool = False,
    compact_threshold: int = 100,
) -> None:
    """
    运行聊天循环 / Run chat loop
    
    核心聊天交互逻辑 / Core chat interaction logic
    
    Args:
        stream: 是否启用逐行流式输出 / Enable line-by-line streaming output (v2.1.78)
        enable_thinking_block: 是否启用Ctrl+O思维块 / Enable Ctrl+O thinking block (v2.1.0)
        auto_compact: 是否启用自动压缩 / Enable auto compact (v0.2.47)
        compact_threshold: 自动压缩阈值 / Auto compact threshold
    """
    config = config_manager.load_config()
    model_router = ModelRouter(config)
    context_manager = ContextManager(max_tokens=context)
    
    messages: list[dict[str, str]] = initial_messages or []
    
    thinking_display = ThinkingBlockDisplay(console)
    ime_manager = IMEManager()
    
    style_config = get_style_config()
    
    if auto_compact and session_manager and session_manager.current_session:
        session_manager.current_session.metadata["auto_compact"] = True
        session_manager.current_session.metadata["compact_threshold"] = compact_threshold
        session_manager.save_current_session()
    
    console.print("[bold green]AloneChat 已就绪，请输入您的指令... / Ready, please enter your instruction...[/bold green]\n")
    
    while True:
        try:
            auto_compact_check(session_manager, threshold=compact_threshold)
            
            ime_manager.before_input()
            session_name = ""
            if session_manager and session_manager.current_session:
                session_name = f"[{session_manager.current_session.get_name()}] "
            prompt_text = f"[bold blue]{session_name}You[/bold blue]"
            user_input = Prompt.ask(prompt_text)
            ime_manager.after_input()
            
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
            
            if stream:
                full_content = _stream_chat_response(
                    model_router=model_router,
                    messages=messages,
                    show_reasoning=show_reasoning,
                    session_manager=session_manager,
                    thinking_display=thinking_display if enable_thinking_block else None,
                )
            else:
                with console.status("[bold green]思考中... / Thinking...[/bold green]"):
                    response = model_router.chat_with_reasoning(messages=messages)
                
                console.print()
                
                if isinstance(response, ChatResponse):
                    if show_reasoning and response.reasoning_content:
                        console.print("\n[dim][思考过程 / Reasoning Process][/dim]")
                        console.print(f"[dim]{response.reasoning_content}[/dim]\n")
                    
                    full_content = response.content
                    console.print(Markdown(full_content))
                    
                    if show_usage and response.usage:
                        usage_str = format_usage(response.usage)
                        if usage_str:
                            console.print(f"\n[dim]{usage_str}[/dim]")
                        update_session_cost(response.usage)
                        cost_str = format_session_cost()
                        if cost_str:
                            console.print(f"[dim]{cost_str}[/dim]")
                else:
                    full_content = str(response)
                    console.print(Markdown(full_content))
            
            wrapped_content = wrap_file_paths_in_output(full_content)
            img_content = process_image_links_in_output(wrapped_content)
            
            messages.append({"role": "assistant", "content": full_content})
            if session_manager:
                session_manager.add_message("assistant", full_content)
            
            console.print("\n" + "─" * 60 + "\n")
            
        except KeyboardInterrupt:
            thinking_display.close()
            console.print("\n\n[dim]已中断 / Interrupted[/dim]")
            break
        except Exception as e:
            console.print(f"\n[red]错误 / Error: {e}[/red]")
            console.print("[dim]请重试或输入 'exit' 退出 / Please retry or type 'exit' to quit[/dim]\n")


def _stream_chat_response(
    model_router: ModelRouter,
    messages: list[dict[str, str]],
    show_reasoning: bool = False,
    session_manager=None,
    thinking_display: Optional[ThinkingBlockDisplay] = None,
) -> str:
    """
    流式获取聊天响应 / Stream chat response
    
    支持逐行输出和实时思维块显示
    Supports line-by-line output and live thinking block display
    
    Args:
        model_router: 模型路由器 / Model router
        messages: 消息列表 / Message list
        show_reasoning: 是否显示思考过程 / Show reasoning process
        session_manager: 会话管理器 / Session manager
        thinking_display: 思维块显示器 / Thinking block display
        
    Returns:
        完整响应内容 / Complete response content
    """
    reasoning_parts: list[str] = []
    content_parts: list[str] = []
    current_reasoning = ""
    
    try:
        stream_iter = model_router.stream_chat(messages=messages)
        
        for chunk in stream_iter:
            if chunk.startswith("[思考]") or chunk.startswith("[reasoning]"):
                token = chunk.replace("[思考]", "").replace("[reasoning]", "")
                reasoning_parts.append(token)
                current_reasoning += token
                
                if thinking_display and thinking_display.is_visible:
                    thinking_display.feed_reasoning(token)
                
                if show_reasoning:
                    console.print(f"[dim]{token}[/dim]", end="")
            else:
                if current_reasoning:
                    if show_reasoning:
                        console.print()
                    current_reasoning = ""
                
                content_parts.append(chunk)
                console.print(chunk, end="")
        
        console.print()
        
        full_content = "".join(content_parts)
        
        if reasoning_parts and session_manager:
            full_reasoning = "".join(reasoning_parts)
            session_manager.add_message("assistant", f"[思考过程/Reasoning]: {full_reasoning}")
        
        return full_content
        
    except Exception as e:
        console.print(f"\n[red]流式输出错误 / Streaming error: {e}[/red]")
        if content_parts:
            return "".join(content_parts)
        raise


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
    
    session_name_display = ""
    if obj.get("session_name"):
        session_name_display = f"\n[dim]会话名称 / Session name: {obj['session_name']}[/dim]"
    
    auto_compact = obj.get("auto_compact", False)
    compact_threshold = obj.get("compact_threshold", 100)
    agent_config = obj.get("agent_config", {})
    
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
        f"[dim]输入 'exit' 或 'quit' 退出 / Type 'exit' or 'quit' to exit[/dim]"
        f"{session_name_display}",
        border_style="cyan"
    ))
    
    console.print(f"\n使用模型 / Using model: [cyan]DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/cyan]")
    console.print(f"思考强度 / Reasoning effort: [cyan]high[/cyan]")
    console.print(f"上下文窗口 / Context window: [cyan]{1000000:,} tokens[/cyan]")
    console.print(f"上下文缓存 / Context cache: [cyan]自动启用 / Auto enabled[/cyan]")
    
    if agent_config:
        console.print(f"代理配置 / Agent config: [cyan]{agent_config}[/cyan]")
    
    if auto_compact:
        console.print(f"自动压缩 / Auto compact: [cyan]已启用, 阈值: {compact_threshold} 条消息[/cyan]")
    
    if session_manager and session_manager.current_session:
        session_info = session_manager.get_session_info()
        console.print(f"会话名称 / Session name: [cyan]{session_manager.current_session.get_name()}[/cyan]")
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
        auto_compact=auto_compact,
        compact_threshold=compact_threshold,
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
