"""
chatå½ä»¤ - å¯å¨äº¤äºå¼å¯¹è¯?/ chat command - Start interactive chat

æä¾äº¤äºå¼å¯¹è¯çé¢ï¼æ¯æ / Provides interactive chat interface:
- èªç¶è¯­è¨äº¤äº / Natural language interaction
- ä»£ç çæåçè§?/ Code generation and understanding
- å¤è½®å¯¹è¯ / Multi-turn conversation
- ä¸ä¸æç¼å­?/ Context caching
- æèæ¨¡å¼?/ Thinking mode
- ä¼è¯ç®¡ç / Session management
- Slashå½ä»¤ / Slash commands
- éè¡æµå¼è¾åº / Line-by-line streaming output (v2.1.78)
- Ctrl+O å®æ¶æ¾ç¤ºæç»´å?/ Ctrl+O live thinking block (v2.1.0)
- æç¤ºå»ºè®® / Prompt suggestions (v2.0.70)
- IMEæ¯æ / IME support (v2.0.68)
- èªå¨å¯¹è¯åç¼© / Auto conversation compression (v0.2.47)
- ä¼è¯æ¾ç¤ºåç§° / Session display name (v2.1.76)
"""

import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from typing import Optional

from alonework.config import ConfigManager
from alonework.models import ModelRouter, DEEPSEEK_MODEL, ChatResponse, UsageInfo
from alonework.context import ContextManager
from alonework.utils.streaming import stream_response_line_by_line
from alonework.utils.thinking_block import ThinkingBlockDisplay
from alonework.utils.hyperlinks import wrap_file_paths_in_output, make_file_link
from alonework.utils.images import process_image_links_in_output
from alonework.utils.ime_support import IMEManager
from alonework.slash.commands.compact import auto_compact_check, show_compact_status
from alonework.configs.style_loader import get_style_config
from alonework.utils.welcome_screen import show_welcome, show_input_prompt, WelcomeScreen, StatusBar
from alonework.utils.status_bar import InteractiveStatusBar, StatusState, UsageInfo as StatusBarUsage

console = Console()


# ä¼è¯ææ¬è¿½è¸ª / Session cost tracking
_session_cost: float = 0.0

DEEPSEEK_INPUT_RATE = 0.001  # $0.001 / 1M tokens
DEEPSEEK_OUTPUT_RATE = 0.002  # $0.002 / 1M tokens


def format_usage(usage: UsageInfo | None) -> str:
    """æ ¼å¼åä½¿ç¨éä¿¡æ¯ / Format usage info"""
    if usage is None:
        return ""
    
    parts = []
    
    if usage.prompt_tokens > 0:
        parts.append(f"è¾å¥: {usage.prompt_tokens:,}")
    if usage.completion_tokens > 0:
        parts.append(f"è¾åº: {usage.completion_tokens:,}")
    
    if usage.prompt_cache_hit_tokens > 0:
        hit_rate = usage.cache_hit_rate * 100
        parts.append(f"ç¼å­å½ä¸­: {usage.prompt_cache_hit_tokens:,} ({hit_rate:.1f}%)")
    
    if usage.total_tokens > 0:
        parts.append(f"æ»è®¡: {usage.total_tokens:,}")
    
    return " | ".join(parts)


def format_session_cost() -> str:
    """æ ¼å¼åä¼è¯æ»ææ?/ Format total session cost"""
    global _session_cost
    if _session_cost <= 0:
        return ""
    return f"ä¼è¯ææ¬: ${_session_cost:.4f} / Session cost: ${_session_cost:.4f}"


def update_session_cost(usage: UsageInfo | None) -> None:
    """æ´æ°ä¼è¯ç´¯è®¡ææ¬ / Update cumulative session cost"""
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
    å¤çslashå½ä»¤ / Process slash command
    
    è¿å (handled, should_continue) / Returns (handled, should_continue)
    """
    if not user_input.startswith("/"):
        return False, True
    
    from alonework.slash import SlashCommandExecutor
    
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
    è¿è¡èå¤©å¾ªç¯ / Run chat loop
    
    æ ¸å¿èå¤©äº¤äºé»è¾ / Core chat interaction logic
    
    Args:
        stream: æ¯å¦å¯ç¨éè¡æµå¼è¾åº / Enable line-by-line streaming output (v2.1.78)
        enable_thinking_block: æ¯å¦å¯ç¨Ctrl+Oæç»´å?/ Enable Ctrl+O thinking block (v2.1.0)
        auto_compact: æ¯å¦å¯ç¨èªå¨åç¼© / Enable auto compact (v0.2.47)
        compact_threshold: èªå¨åç¼©éå?/ Auto compact threshold
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
    
    console.print("[bold green]AloneChat å·²å°±ç»ªï¼è¯·è¾å¥æ¨çæä»?.. / Ready, please enter your instruction...[/bold green]\n")
    
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
                console.print("\n[dim]åè§ï¼?/ Goodbye![/dim]")
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
                with console.status("[bold green]æèä¸­... / Thinking...[/bold green]"):
                    response = model_router.chat_with_reasoning(messages=messages)
                
                console.print()
                
                if isinstance(response, ChatResponse):
                    if show_reasoning and response.reasoning_content:
                        console.print("\n[dim][æèè¿ç¨?/ Reasoning Process][/dim]")
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
            
            console.print("\n" + "â" * 60 + "\n")
            
        except KeyboardInterrupt:
            thinking_display.close()
            console.print("\n\n[dim]å·²ä¸­æ?/ Interrupted[/dim]")
            break
        except Exception as e:
            console.print(f"\n[red]éè¯¯ / Error: {e}[/red]")
            console.print("[dim]è¯·éè¯æè¾å¥ 'exit' éå?/ Please retry or type 'exit' to quit[/dim]\n")


def _stream_chat_response(
    model_router: ModelRouter,
    messages: list[dict[str, str]],
    show_reasoning: bool = False,
    session_manager=None,
    thinking_display: Optional[ThinkingBlockDisplay] = None,
) -> str:
    """
    æµå¼è·åèå¤©ååº / Stream chat response
    
    æ¯æéè¡è¾åºåå®æ¶æç»´åæ¾ç¤?    Supports line-by-line output and live thinking block display
    
    Args:
        model_router: æ¨¡åè·¯ç±å?/ Model router
        messages: æ¶æ¯åè¡¨ / Message list
        show_reasoning: æ¯å¦æ¾ç¤ºæèè¿ç¨?/ Show reasoning process
        session_manager: ä¼è¯ç®¡çå?/ Session manager
        thinking_display: æç»´åæ¾ç¤ºå¨ / Thinking block display
        
    Returns:
        å®æ´ååºåå®¹ / Complete response content
    """
    reasoning_parts: list[str] = []
    content_parts: list[str] = []
    current_reasoning = ""
    
    try:
        stream_iter = model_router.stream_chat(messages=messages)
        
        for chunk in stream_iter:
            if chunk.startswith("[æè]") or chunk.startswith("[reasoning]"):
                token = chunk.replace("[æè]", "").replace("[reasoning]", "")
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
            session_manager.add_message("assistant", f"[æèè¿ç¨?Reasoning]: {full_reasoning}")
        
        return full_content
        
    except Exception as e:
        console.print(f"\n[red]æµå¼è¾åºéè¯¯ / Streaming error: {e}[/red]")
        if content_parts:
            return "".join(content_parts)
        raise


def start_interactive(obj: dict, session_manager=None) -> None:
    """
    å¯å¨äº¤äºæ¨¡å¼ / Start interactive mode
    
    ä»ä¸»å¥å£è°ç¨çäº¤äºæ¨¡å¼?/ Interactive mode called from main entry
    """
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]éè¯¯: æªæ¾å°éç½®æä»?/ Error: Config file not found[/red]")
        console.print("è¯·åè¿è¡ / Please run: [cyan]alonechat init[/cyan]")
        return
    
    auto_compact = obj.get("auto_compact", False)
    compact_threshold = obj.get("compact_threshold", 100)
    agent_config = obj.get("agent_config", {})
    
    from alonework import __version__
    from pathlib import Path
    
    version = __version__
    working_dir = str(Path.cwd())
    
    api_key_masked = None
    try:
        config = config_manager.load_config()
        if config.get("api_key"):
            key = config["api_key"]
            api_key_masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
    except Exception:
        pass
    
    show_welcome(
        version=version,
        model=DEEPSEEK_MODEL,
        working_dir=working_dir,
        api_key_masked=api_key_masked,
        compact=False,
    )
    
    console.print()
    
    if agent_config:
        console.print(f"ä»£çéç½® / Agent config: [cyan]{agent_config}[/cyan]")
    
    if auto_compact:
        console.print(f"èªå¨åç¼© / Auto compact: [cyan]å·²å¯ç? éå? {compact_threshold} æ¡æ¶æ¯[/cyan]")
    
    if session_manager and session_manager.current_session:
        session_info = session_manager.get_session_info()
        console.print(f"ä¼è¯åç§° / Session name: [cyan]{session_manager.current_session.get_name()}[/cyan]")
        console.print(f"ä¼è¯ID / Session ID: [cyan]{session_info['id'][:8]}...[/cyan]")
    
    initial_messages = []
    if session_manager:
        initial_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in session_manager.get_messages()
        ]
        if initial_messages:
            console.print(f"[dim]å·²å è½?{len(initial_messages)} æ¡åå²æ¶æ?/ Loaded {len(initial_messages)} history messages[/dim]\n")
    
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
    å¸¦åå§æ¥è¯¢å¯å¨äº¤äºæ¨¡å¼?/ Start interactive mode with initial query
    
    ä»ä¸»å¥å£å¸¦æ¥è¯¢å­ç¬¦ä¸²è°ç¨ / Called from main entry with query string
    """
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]éè¯¯: æªæ¾å°éç½®æä»?/ Error: Config file not found[/red]")
        console.print("è¯·åè¿è¡ / Please run: [cyan]alonechat init[/cyan]")
        return
    
    console.print(Panel.fit(
        "[bold cyan]AloneChat äº¤äºæ¨¡å¼ / Interactive Mode[/bold cyan]\n\n"
        f"[dim]æ¨¡å: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]è¾å¥ 'exit' æ?'quit' éå?/ Type 'exit' or 'quit' to exit[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n" + "â" * 60 + "\n")
    
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
    
    with console.status("[bold green]æèä¸­... / Thinking...[/bold green]"):
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
    
    console.print("\n" + "â" * 60 + "\n")
    
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
@click.option("--context", "-c", help="ä¸ä¸æçªå£å¤§å°?/ Context window size", type=int, default=1000000)
@click.option("--show-reasoning", is_flag=True, help="æ¾ç¤ºæèè¿ç¨?/ Show reasoning process")
@click.option("--show-usage", is_flag=True, default=True, help="æ¾ç¤ºä½¿ç¨é?/ Show usage")
@click.pass_obj
def chat_command(obj: dict, context: int, show_reasoning: bool, show_usage: bool) -> None:
    """
    å¯å¨äº¤äºå¼å¯¹è¯?/ Start interactive chat
    
    æä¾èªç¶è¯­è¨äº¤äºçé¢ï¼æ¯æä»£ç çæãçè§£åå¤è½®å¯¹è¯ / Provides natural language interface for code generation, understanding and multi-turn conversation
    """
    console.print(Panel.fit(
        "[bold cyan]AloneChat äº¤äºæ¨¡å¼ / Interactive Mode[/bold cyan]\n\n"
        "è¾å¥èªç¶è¯­è¨æä»¤ï¼AIå°å¸®å©æ¨ / Enter natural language, AI will help you:\n"
        "â?çæä»£ç  / Generate code\n"
        "â?çè§£ä»£ç  / Understand code\n"
        "â?éæä»£ç  / Refactor code\n"
        "â?ä¿®å¤éè¯¯ / Fix errors\n"
        "â?åç­é®é¢ / Answer questions\n\n"
        f"[dim]æ¨¡å: DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/dim]\n"
        "[dim]æèæ¨¡å¼? å·²å¯ç?(reasoning_effort=high)[/dim]\n"
        "[dim]ä¸ä¸æç¼å­? èªå¨å¯ç¨ (ç¼å­å½ä¸­çå¯è¾?9.98%)[/dim]\n"
        "[dim]è¾å¥ 'exit' æ?'quit' éå?/ Type 'exit' or 'quit' to exit[/dim]",
        border_style="cyan"
    ))
    
    config_manager: ConfigManager = obj["config_manager"]
    
    if not config_manager.config_path.exists():
        console.print("[red]éè¯¯: æªæ¾å°éç½®æä»?/ Error: Config file not found[/red]")
        console.print("è¯·åè¿è¡ / Please run: [cyan]alonechat init[/cyan]")
        return
    
    config = config_manager.load_config()
    
    console.print(f"\nä½¿ç¨æ¨¡å / Using model: [cyan]DeepSeek V4 Flash ({DEEPSEEK_MODEL})[/cyan]")
    console.print(f"æèå¼ºåº?/ Reasoning effort: [cyan]high[/cyan]")
    console.print(f"ä¸ä¸æçªå?/ Context window: [cyan]{context:,} tokens[/cyan]")
    console.print(f"ä¸ä¸æç¼å­?/ Context cache: [cyan]èªå¨å¯ç¨ / Auto enabled[/cyan]")
    console.print("\n" + "â" * 60 + "\n")
    
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
