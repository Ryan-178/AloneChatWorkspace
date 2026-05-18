"""
终端界面测试脚本 / Terminal UI Test Script
测试新的Claude风格界面 / Test new Claude-style interface
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from alonechat.utils.welcome_screen import show_welcome, WelcomeScreen, StatusBar
from alonechat.utils.status_bar import InteractiveStatusBar, StatusState, UsageInfo

console = Console()


def test_welcome_screen():
    """测试欢迎界面 / Test welcome screen"""
    console.print("\n[bold]测试欢迎界面 / Testing Welcome Screen[/bold]\n")
    
    show_welcome(
        version="0.1.0",
        model="deepseek-v4-flash",
        working_dir=str(Path.cwd()),
        api_key_masked="sk-de2c0...8530",
        compact=False,
    )


def test_compact_welcome():
    """测试紧凑欢迎界面 / Test compact welcome screen"""
    console.print("\n[bold]测试紧凑欢迎界面 / Testing Compact Welcome Screen[/bold]\n")
    
    show_welcome(
        version="0.1.0",
        model="deepseek-v4-flash",
        working_dir=str(Path.cwd()),
        api_key_masked="sk-de2c0...8530",
        compact=True,
    )


def test_status_bar():
    """测试状态栏 / Test status bar"""
    console.print("\n[bold]测试状态栏 / Testing Status Bar[/bold]\n")
    
    bar = InteractiveStatusBar(
        model="deepseek-v4-flash",
        effort="high",
        logged_in=True,
        session_name="测试会话",
    )
    
    bar.set_state(StatusState.IDLE)
    bar.print()
    
    console.print("\n")
    
    bar.set_state(StatusState.THINKING)
    bar.print()
    
    console.print("\n")
    
    usage = UsageInfo(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500,
        cache_hit_rate=0.85,
    )
    bar.set_usage(usage)
    bar.set_state(StatusState.STREAMING)
    bar.print()


def test_all():
    """运行所有测试 / Run all tests"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]    AloneChat 终端界面测试 / Terminal UI Test[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    test_welcome_screen()
    
    console.print("\n" + "═" * 60 + "\n")
    
    test_compact_welcome()
    
    console.print("\n" + "═" * 60 + "\n")
    
    test_status_bar()
    
    console.print("\n[bold green]测试完成！/ Test Complete![/bold green]")


if __name__ == "__main__":
    test_all()
