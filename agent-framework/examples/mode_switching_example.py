"""
Mode Switching Example - 模式切换示例 - Mode Switching Example
演示如何使用CODE模式和WORK模式
Demonstrates how to use CODE mode and WORK mode
"""
import asyncio
from agent_framework import (
    Agent,
    ExecutionMode,
    create_agent,
    create_mode_manager,
    create_router,
    AgentModeManager,
    ModeRouter,
)


def example_basic_usage():
    """
    示例1: 基本使用 - Example 1: Basic Usage
    """
    print("\n" + "="*60)
    print("示例1: 基本使用 / Example 1: Basic Usage")
    print("="*60)
    
    agent = Agent(mode="work")
    
    print(f"当前模式 / Current mode: {agent.mode}")
    print(f"是否WORK模式 / Is WORK mode: {agent.is_work_mode}")
    print(f"是否CODE模式 / Is CODE mode: {agent.is_code_mode}")


def example_mode_switch():
    """
    示例2: 模式切换 - Example 2: Mode Switching
    """
    print("\n" + "="*60)
    print("示例2: 模式切换 / Example 2: Mode Switching")
    print("="*60)
    
    agent = Agent(mode="work")
    print(f"初始模式 / Initial mode: {agent.mode}")
    
    result = agent.switch_mode("code", reason="用户选择编程模式 / User selected code mode")
    print(f"切换结果 / Switch result: {result}")
    print(f"切换后模式 / Mode after switch: {agent.mode}")
    
    result = agent.switch_mode("work", reason="用户选择工作模式 / User selected work mode")
    print(f"切换结果 / Switch result: {result}")
    print(f"切换后模式 / Mode after switch: {agent.mode}")


def example_auto_routing():
    """
    示例3: 自动路由检测 - Example 3: Auto Routing Detection
    """
    print("\n" + "="*60)
    print("示例3: 自动路由检测 / Example 3: Auto Routing Detection")
    print("="*60)
    
    agent = Agent(auto_detect=True)
    
    tasks = [
        "帮我写一个Python快速排序函数",
        "生成一份项目进度报告",
        "修复这个bug：IndexError in list index",
        "分析这份销售数据并生成图表",
        "重构这段代码，提高可读性",
        "翻译这篇技术文档为中文",
    ]
    
    for task in tasks:
        routing = agent.route(task)
        print(f"\n任务 / Task: {task[:30]}...")
        print(f"  推荐模式 / Recommended mode: {routing['recommended_mode']}")
        print(f"  任务类别 / Category: {routing['category']}")
        print(f"  置信度 / Confidence: {routing['confidence']:.2f}")


def example_mode_manager():
    """
    示例4: 直接使用ModeManager - Example 4: Direct ModeManager Usage
    """
    print("\n" + "="*60)
    print("示例4: 直接使用ModeManager / Example 4: Direct ModeManager Usage")
    print("="*60)
    
    manager = create_mode_manager(mode="work", auto_detect_mode=True)
    
    print(f"当前模式 / Current mode: {manager.current_mode.value}")
    
    mode_info = manager.get_mode_info()
    print(f"模式信息 / Mode info:")
    print(f"  - 当前模式 / Current: {mode_info['current_mode']}")
    print(f"  - 允许切换 / Allow switch: {mode_info['allow_mode_switch']}")
    print(f"  - 自动检测 / Auto detect: {mode_info['auto_detect_mode']}")


def example_router():
    """
    示例5: 直接使用ModeRouter - Example 5: Direct ModeRouter Usage
    """
    print("\n" + "="*60)
    print("示例5: 直接使用ModeRouter / Example 5: Direct ModeRouter Usage")
    print("="*60)
    
    router = create_router(initial_mode="work", enable_auto_routing=True)
    
    task = "实现一个REST API接口"
    routing_info = router.get_routing_info(task)
    
    print(f"任务 / Task: {task}")
    print(f"路由结果 / Routing result:")
    print(f"  - 推荐模式 / Recommended mode: {routing_info['recommended_mode']}")
    print(f"  - 任务类别 / Category: {routing_info['category']}")
    print(f"  - 置信度 / Confidence: {routing_info['confidence']:.2f}")
    print(f"  - 原因 / Reasons: {routing_info['reasons']}")


def example_config_from_yaml():
    """
    示例6: 从配置文件加载 - Example 6: Load from Config File
    """
    print("\n" + "="*60)
    print("示例6: 从配置文件加载 / Example 6: Load from Config File")
    print("="*60)
    
    from agent_framework.config import AgentConfig
    
    try:
        config = AgentConfig.from_yaml("config.yaml")
        print(f"默认模式 / Default mode: {config.mode.default_mode}")
        print(f"允许模式切换 / Allow mode switch: {config.mode.allow_mode_switch}")
        print(f"CODE配置 / CODE config:")
        print(f"  - 使用CodexBridge: {config.mode.code_config.use_codex_bridge}")
        print(f"  - 启用搜索Agent: {config.mode.code_config.enable_search_agent}")
        print(f"WORK配置 / WORK config:")
        print(f"  - 启用意图澄清: {config.mode.mtc_config.intent_clarification_enabled}")
    except Exception as e:
        print(f"配置加载示例 / Config load example: {e}")


def main():
    """
    运行所有示例 - Run all examples
    """
    print("\n" + "="*60)
    print("Agent Framework 模式切换示例")
    print("Agent Framework Mode Switching Examples")
    print("="*60)
    
    example_basic_usage()
    example_mode_switch()
    example_auto_routing()
    example_mode_manager()
    example_router()
    example_config_from_yaml()
    
    print("\n" + "="*60)
    print("所有示例运行完成 / All examples completed")
    print("="*60)


if __name__ == "__main__":
    main()
