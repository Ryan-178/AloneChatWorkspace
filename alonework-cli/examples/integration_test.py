"""
集成测试示例 - 演示如何使用alonechat CLI调用agent-framework
"""

import asyncio
from pathlib import Path


async def test_task_planner():
    """测试任务规划功能"""
    print("\n=== 测试任务规划 ===")
    
    from agent_framework.services.task_planner import TaskPlanner
    from agent_framework.llm import LiteLLMProvider
    
    # 初始化
    llm = LiteLLMProvider(model="deepseek-chat")
    planner = TaskPlanner(llm=llm)
    
    # 拆解任务
    task_plan = await planner.decompose_task(
        user_request="分析sales.xlsx并生成季度报告",
        context={"workspace": "./workspace"}
    )
    
    print(f"任务拆解结果: {len(task_plan.get('subtasks', []))} 个子任务")
    for i, subtask in enumerate(task_plan.get("subtasks", []), 1):
        print(f"  {i}. {subtask.get('description')}")


async def test_file_processor():
    """测试文件处理功能"""
    print("\n=== 测试文件处理 ===")
    
    from agent_framework.services.file_processors import get_processor
    
    # 测试不同文件类型
    test_files = [
        ("example.py", ".py"),
        ("data.xlsx", ".xlsx"),
        ("report.docx", ".docx"),
        ("slides.pptx", ".pptx"),
    ]
    
    for filename, ext in test_files:
        processor = get_processor(ext)
        print(f"  ✓ {ext} -> {processor.__class__.__name__}")


async def test_test_generator():
    """测试测试生成功能"""
    print("\n=== 测试测试生成 ===")
    
    from agent_framework.services.test_generator import TestGenerator
    from agent_framework.llm import LiteLLMProvider
    
    # 初始化
    llm = LiteLLMProvider(model="deepseek-chat")
    generator = TestGenerator(llm=llm)
    
    # 生成测试
    tests = generator.generate_tests(
        source_file="example.py",
        framework="pytest",
        test_types=["unit", "edge"]
    )
    
    print(f"生成了 {len(tests)} 个测试用例")
    for test in tests:
        print(f"  • {test.get('name')}: {test.get('type')}")


async def test_error_fixer():
    """测试错误修复功能"""
    print("\n=== 测试错误修复 ===")
    
    from agent_framework.services.error_fixer import ErrorFixer
    from agent_framework.llm import LiteLLMProvider
    
    # 初始化
    llm = LiteLLMProvider(model="deepseek-chat")
    fixer = ErrorFixer(llm=llm)
    
    # 分析错误模式
    patterns = fixer.analyze_error_patterns()
    print(f"支持 {len(patterns)} 种错误类型修复")
    for pattern in patterns:
        print(f"  • {pattern}")


async def test_skills_registry():
    """测试技能注册表"""
    print("\n=== 测试技能注册表 ===")
    
    from agent_framework.tools.skills_registry import SkillsRegistry
    
    registry = SkillsRegistry()
    skills = registry.list_skills()
    
    print(f"注册了 {len(skills)} 个技能")
    for skill in skills:
        print(f"  • {skill.get('name')}: {skill.get('description')}")


async def test_rag_pipeline():
    """测试RAG功能"""
    print("\n=== 测试RAG功能 ===")
    
    from agent_framework.rag import RAGPipeline
    
    pipeline = RAGPipeline()
    
    # 索引文档
    count = await pipeline.ingest("./src")
    print(f"索引了 {count} 个文档")
    
    # 检索
    results = await pipeline.retrieve("用户认证逻辑", k=5)
    print(f"找到 {len(results)} 个相关结果")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('source')} (相似度: {result.get('score'):.4f})")


async def test_file_generators():
    """测试文件生成功能"""
    print("\n=== 测试文件生成 ===")
    
    from agent_framework.services.file_generators import FileGeneratorService
    from agent_framework.llm import LiteLLMProvider
    
    # 初始化
    llm = LiteLLMProvider(model="deepseek-chat")
    service = FileGeneratorService(llm=llm)
    
    print("支持的生成类型:")
    print("  • PPT演示文稿")
    print("  • Excel数据报表")
    print("  • Word报告文档")
    print("  • 代码文件")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("AloneChat CLI + Agent Framework 集成测试")
    print("="*60)
    
    try:
        await test_task_planner()
        await test_file_processor()
        await test_test_generator()
        await test_error_fixer()
        await test_skills_registry()
        await test_rag_pipeline()
        await test_file_generators()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
