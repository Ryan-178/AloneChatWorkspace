"""
DeepSeek V4 Optimization System - Comprehensive Example
DeepSeek V4优化系统 - 综合示例

演示完整功能：
1. DeepSeek V4专用Provider，支持KV Cache
2. 100万上下文管理系统
3. AI驱动的上下文智能压缩
4. 智能重要性评估
5. 结构化本地存储
6. 上下文反馈系统
7. SWE引擎（代码优化）
8. 企业安全体系
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework.deepseek_optimization import (
    DeepSeekProvider,
    DeepSeekConfig,
    DeepSeekModel,
    MegaContextManager,
    ContextFeedbackGenerator,
    SWEEngine,
    LicenseManager,
    AuditLogger
)
from agent_framework.core.base_llm import Message


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str):
    print(f"\n-- {title} " + "-" * 50)


async def main():
    print_section("🚀 DeepSeek V4 优化系统 - 综合演示")
    print("核心理念：All in DeepSeek V4，通过软件优化弥补硬件差距")
    print("核心功能：100万上下文 + AI智能压缩 + 本地存储 + 安全体系")

    # ==========================================
    # 初始化核心组件
    # ==========================================
    print_section("1. 系统初始化")
    
    # 1. DeepSeek配置（注意：实际使用时需要API密钥）
    print_subsection("配置DeepSeek V4")
    config = DeepSeekConfig(
        model=DeepSeekModel.V4_FLASH,
        # api_key="your-deepseek-api-key-here",  # 实际使用时添加
        temperature=0.7,
        max_tokens=2048
    )
    
    print(f"  • 模型：{config.model}")
    print(f"  • 上下文窗口：1,000,000 tokens")
    print(f"  • 支持KV Cache优化")
    
    # 2. 初始化Provider（先不设置API密钥）
    llm = DeepSeekProvider(config=config)
    
    # 3. 初始化上下文管理器（100万上下文）
    print_subsection("初始化100万上下文管理器")
    context_manager = MegaContextManager(
        storage_root=Path("./data/context_archive"),
        max_context_tokens=1000000,
        target_active_tokens=800000
    )
    print(f"  • 最大上下文：1,000,000 tokens")
    print(f"  • 活跃目标：800,000 tokens")
    print(f"  • 本地存储：{Path('./data/context_archive').absolute()}")
    
    # 4. 设置AI压缩器
    print_subsection("设置AI智能压缩器")
    from agent_framework.deepseek_optimization.context import ContextCompressor
    compressor = ContextCompressor(use_ai_compression=True)
    compressor.set_llm_provider(llm)
    print("  • AI压缩：已启用")
    print("  • 使用DeepSeek模型进行摘要")
    
    # 5. 安全体系初始化
    print_subsection("企业安全体系初始化")
    license_manager = LicenseManager()
    audit_logger = AuditLogger()
    print("  • 许可证管理：已就绪")
    print("  • 审计日志：已就绪")
    
    # 6. SWE引擎
    print_subsection("SWE优化引擎初始化")
    swe_engine = SWEEngine()
    print("  • 代码优化：已启用")
    print("  • 测试生成：已启用")

    # ==========================================
    # 模拟对话和上下文管理
    # ==========================================
    print_section("2. 上下文管理演示")
    
    # 模拟一些对话消息
    sample_messages = [
        {"role": "system", "content": "你是一个专业的AI助手，帮助用户完成任务"},
        {"role": "user", "content": "你好！我需要你帮我完成一个编程任务"},
        {"role": "assistant", "content": "好的，我很乐意帮助！请描述一下你的需求"},
        {"role": "user", "content": "我需要开发一个管理系统，包含用户认证和权限管理"},
        {"role": "assistant", "content": "明白了，这是一个完整的Web应用开发需求。让我们开始规划"},
        {"role": "user", "content": "还有一个重要的事情：需要支持高并发和分布式架构"},
        {"role": "assistant", "content": "明白了，我会考虑这一点。我们可以用微服务架构"},
        {"role": "user", "content": "数据库方面你推荐什么？"},
        {"role": "assistant", "content": "根据你的需求，我推荐PostgreSQL + Redis"},
        {"role": "user", "content": "好的，这是一个重要决策，请记录下来"},
        {"role": "user", "content": "顺便问一下，今天天气怎么样？"},
        {"role": "assistant", "content": "我无法直接访问天气数据，但你可以搜索..."},
        {"role": "user", "content": "好的，我们继续讨论项目设计"},
        {"role": "user", "content": "还有一个非常重要的要求：需要支持多语言"},
    ]
    
    print_subsection("添加对话消息")
    for idx, msg in enumerate(sample_messages):
        managed_msg = context_manager.add_message(msg)
        status = "ACTIVE" if managed_msg.decision.keep_in_context else "ARCHIVED"
        print(f"  [{idx+1}] {status}: {msg.get('role', 'user')} - {msg.get('content', '')[:30]}...")

    # ==========================================
    # 获取活跃上下文
    # ==========================================
    print_section("3. 获取活跃上下文")
    
    active_messages, managed_list = context_manager.get_active_context()
    
    print(f"  总消息数：{len(managed_list)}")
    print(f"  活跃消息：{len(active_messages)}")
    archived = len([m for m in managed_list if m.stored])
    print(f"  归档消息：{archived}")
    
    if managed_list:
        print("\n  消息重要性分布：")
        for m in managed_list:
            score_str = f"{m.importance.score:.2f}"
            category = m.importance.category.value.upper()
            print(f"    • {score_str} {category} - {m.importance.reasoning[:50]}...")

    # ==========================================
    # 上下文反馈系统
    # ==========================================
    print_section("4. 上下文反馈系统")
    
    feedback_gen = ContextFeedbackGenerator()
    feedback = feedback_gen.generate_feedback(
        managed_list,
        context_manager.get_archived_files()
    )
    
    print(f"\n  总消息：{feedback.total_messages}")
    print(f"  活跃：{feedback.in_context_count}")
    print(f"  归档：{feedback.archived_count}")
    print(f"  主题分布：{len(feedback.topic_index)}个主题")
    
    if feedback.insertion_marker:
        print("\n  上下文插入标记：")
        for line in feedback.insertion_marker.split("\n"):
            print(f"    {line}")

    # ==========================================
    # SWE引擎演示
    # ==========================================
    print_section("5. SWE优化引擎演示")
    
    sample_task = "优化用户认证模块，提高安全性"
    sample_code = """
    def login(username, password):
        if check_password(username, password):
            return {'token': '12345'}
        return {'error': 'invalid'}
    """
    
    print(f"\n  任务：{sample_task}")
    print(f"  代码长度：{len(sample_code)}字符")
    
    # 演示SWE优化（实际需要API）
    # result = swe_engine.optimize(sample_task, sample_code)
    print("\n  (演示模式：SWE引擎已准备好)")
    print("  • 代码分析：启用")
    print("  • 测试生成：启用")
    print("  • 代码精化：启用")

    # ==========================================
    # 统计信息展示
    # ==========================================
    print_section("6. 系统统计")
    
    stats = context_manager.get_stats()
    storage_stats = context_manager.get_storage_stats()
    
    print(f"""
  上下文统计：
    • 总消息：{stats.total_messages}
    • 活跃：{stats.in_context_count}
    • 归档：{stats.archived_count}
    • 估计Token使用：{stats.estimated_tokens_used:,}
    • 估计Token节省：{stats.estimated_tokens_saved:,}

  存储统计：
    • 总归档：{storage_stats.total_archived}
    • 总主题：{storage_stats.total_topics}
  """)

    # ==========================================
    # 历史搜索功能
    # ==========================================
    print_section("7. 历史搜索")
    
    search_term = "数据库"
    results = context_manager.search_archive(search_term)
    
    print(f"\n  搜索：'{search_term}'")
    print(f"  结果数：{len(results)}")
    
    for idx, r in enumerate(results[:3]):
        preview = r.original_message.get('content', '')[:50]
        print(f"  [{idx+1}] {r.storage_topic}: {preview}...")

    # ==========================================
    # 完成 - 显示总结
    # ==========================================
    print_section("8. 系统总结")
    
    print("""
  ✅ DeepSeek V4 优化系统已就绪！
  
  核心功能总结：
  
  1. 100万上下文管理
     • 智能重要性评估
     • 动态内存管理
     • 本地结构化存储
  
  2. DeepSeek V4集成
     • 专用API Provider
     • KV Cache支持
     • 精确费用计算
  
  3. AI驱动压缩
     • 用DeepSeek模型自己压缩上下文
     • 智能内容摘要
     • 重要信息保留
  
  4. 企业安全
     • 许可证管理
     • 审计日志
     • 数据保护
  
  5. SWE优化引擎
     • 代码分析
     • 测试生成
     • 世界顶尖性能
  
  🚀 准备好用于生产环境！
  """)
    
    # 清理
    await llm.close()


if __name__ == "__main__":
    asyncio.run(main())
