"""
/stickers 命令 - 趣味贴纸 / Fun stickers

版本 / Version: 2.1.80
"""

import random
from rich.console import Console

console = Console()

STICKER_COLLECTIONS = {
    "success": [
        "🎉 任务完成！/ Task complete!",
        "✅ 搞定！/ Done!",
        "🚀 太棒了！/ Awesome!",
        "💪 干得漂亮！/ Well done!",
        "⭐ 完美！/ Perfect!",
        "🏆 胜利！/ Victory!",
        "🎊 恭喜！/ Congratulations!",
        "👌 一切顺利！/ All good!",
    ],
    "thinking": [
        "🤔 让我想想... / Let me think...",
        "💭 思考中... / Thinking...",
        "🧠 处理中... / Processing...",
        "🔍 分析中... / Analyzing...",
        "⏳ 请稍候... / Please wait...",
        "📝 整理思路... / Organizing thoughts...",
    ],
    "error": [
        "😅 出了点问题 / Something went wrong",
        "🐛 发现一个bug / Found a bug",
        "❌ 操作失败 / Operation failed",
        "💥 哎呀！/ Oops!",
        "🔧 需要修复 / Needs fixing",
    ],
    "encourage": [
        "💪 继续加油！/ Keep going!",
        "🌟 你做得很好！/ You're doing great!",
        "🔥 保持热情！/ Stay motivated!",
        "👍 不错的尝试！/ Nice try!",
        "🎯 接近目标了！/ Almost there!",
        "💡 好主意！/ Good idea!",
    ],
    "greeting": [
        "👋 你好！/ Hello!",
        "🌞 早上好！/ Good morning!",
        "🌙 晚上好！/ Good evening!",
        "☕ 来杯咖啡？/ Coffee?",
        "🎯 准备好了！/ Ready!",
    ],
    "random": [
        "🎲 随机贴纸 / Random sticker",
        "🌈 今天天气不错 / Nice weather today",
        "🎵 哼个小曲 / Humming a tune",
        "🎮 游戏时间 / Game time",
        "📚 学习使我快乐 / Learning is fun",
        "🎨 创意无限 / Unlimited creativity",
        "🌍 世界和平 / World peace",
        "🍀 好运！/ Good luck!",
        "🎵 ♪ ♫ ♬",
        "🌸 春天来了 / Spring is here",
    ],
}


def stickers_command(args: list, obj: dict, session_manager, registry, **kwargs) -> None:
    """
    趣味贴纸 / Fun stickers

    用法 / Usage:
        /stickers              随机贴纸 / Random sticker
        /stickers random       随机贴纸 / Random sticker
        /stickers list         列出所有集合 / List all collections
        /stickers <category>   指定类别 / Specific category
        /stickers send <name>  发送贴纸 / Send sticker

    可用集合 / Available collections:
        success, thinking, error, encourage, greeting, random
    """
    if not args or args[0] == "random":
        all_stickers = []
        for stickers in STICKER_COLLECTIONS.values():
            all_stickers.extend(stickers)
        sticker = random.choice(all_stickers)
        console.print(f"\n  {sticker}\n")
        return

    if args[0] == "list":
        console.print("[bold cyan]贴纸集合 / Sticker Collections[/bold cyan]\n")
        for name, stickers in STICKER_COLLECTIONS.items():
            console.print(f"  [yellow]{name}[/yellow] ({len(stickers)} 个)")
            for s in stickers[:3]:
                console.print(f"    {s}")
            if len(stickers) > 3:
                console.print(f"    [dim]... 还有 {len(stickers) - 3} 个 / {len(stickers) - 3} more[/dim]")
            console.print()
        return

    category = args[0].lower()
    if category in STICKER_COLLECTIONS:
        sticker = random.choice(STICKER_COLLECTIONS[category])
        console.print(f"\n  {sticker}\n")
        return

    all_stickers = []
    for stickers in STICKER_COLLECTIONS.values():
        all_stickers.extend(stickers)
    matches = [s for s in all_stickers if category in s.lower()]
    if matches:
        sticker = random.choice(matches)
        console.print(f"\n  {sticker}\n")
    else:
        sticker = random.choice(STICKER_COLLECTIONS["random"])
        console.print(f"\n  {sticker}\n")
        console.print(f"[dim]未找到类别 '{category}'，显示随机贴纸 / Category not found, showing random[/dim]")
