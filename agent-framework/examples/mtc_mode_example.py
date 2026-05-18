"""
MTC模式使用示例
"""
import asyncio
from agent_framework.agent.mtc_agent import MTCAgent
from agent_framework.agent.intent_clarifier import IntentClarifier
from agent_framework.agent.task_planner import TaskPlanner
from agent_framework.tools.skills_registry import SkillsRegistry, register_builtin_skills
from agent_framework.core.types import AgentMode


def example_intent_clarification():
    """意图澄清示例"""
    print("\n=== 意图澄清示例 ===")
    
    clarifier = IntentClarifier(llm=None, max_questions=3)
    
    task = "帮我写个文档"
    
    if clarifier.should_clarify(task):
        print(f"任务需要澄清: {task}")
        
        questions = clarifier.generate_questions(task)
        print(f"\n生成的问题 ({len(questions)}个):")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q.text}")
            if q.options:
                print(f"     选项: {', '.join(q.options)}")
        
        answers = {
            "output_format": "PDF",
            "detail_level": "标准详细（3-5页）",
        }
        clarifier.collect_answers(answers)
        
        integrated = clarifier.integrate(task)
        print(f"\n整合后的需求:\n{integrated}")
    else:
        print(f"任务足够清晰: {task}")


def example_task_planning():
    """任务规划示例"""
    print("\n=== 任务规划示例 ===")
    
    planner = TaskPlanner()
    
    task = "写一份详细的项目分析报告"
    
    complexity = planner.estimate_complexity(task)
    print(f"任务复杂度: {complexity}")
    
    subtasks = planner.decompose(task)
    print(f"\n分解为 {len(subtasks)} 个子任务:")
    for i, subtask in enumerate(subtasks, 1):
        deps = [d.task_id[:8] for d in subtask.dependencies]
        print(f"  {i}. {subtask.description}")
        if deps:
            print(f"     依赖: {deps}")
    
    execution_order = planner.get_execution_order(subtasks)
    print(f"\n执行顺序 ({len(execution_order)} 层):")
    for i, layer in enumerate(execution_order, 1):
        layer_desc = [t.description[:20] for t in layer]
        print(f"  层{i}: {layer_desc}")


async def example_skills_execution():
    """Skills执行示例"""
    print("\n=== Skills执行示例 ===")
    
    registry = SkillsRegistry()
    register_builtin_skills(registry)
    
    print(f"已注册的Skills: {[s.name for s in registry.list()]}")
    
    doc_skill = registry.get("document_generation")
    result = await doc_skill.execute({
        "title": "项目报告",
        "content": "这是项目报告的主要内容...",
        "template": "report",
    })
    print(f"\n文档生成结果:")
    print(f"  成功: {result['success']}")
    print(f"  标题: {result['title']}")
    print(f"  文档长度: {len(result['document'])} 字符")
    
    data_skill = registry.get("data_analysis")
    result = await data_skill.execute({
        "data": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "analysis_type": "summary",
    })
    print(f"\n数据分析结果:")
    print(f"  成功: {result['success']}")
    print(f"  分析结果: {result['analysis']}")


def example_mtc_agent():
    """MTC Agent示例"""
    print("\n=== MTC Agent示例 ===")
    
    class MockLLM:
        def chat(self, messages):
            return type("Response", (), {"content": "这是模拟的AI响应"})()
    
    agent = MTCAgent(llm=MockLLM())
    
    print(f"Agent模式: {agent.mode.value}")
    print(f"意图澄清启用: {agent.clarification_enabled}")
    
    clarification = agent.clarify_intent("帮我处理一下数据")
    print(f"\n意图澄清结果:")
    print(f"  需要澄清: {clarification['needs_clarification']}")
    
    planning = agent.plan_task("生成一份销售数据分析报告")
    print(f"\n任务规划结果:")
    print(f"  需要规划: {planning['needs_planning']}")
    print(f"  复杂度: {planning['complexity']}")
    if planning['needs_planning']:
        print(f"  子任务数: {len(planning['subtasks'])}")


def example_skills_marketplace():
    """Skills市场示例"""
    print("\n=== Skills市场示例 ===")
    
    from agent_framework.tools.skills_marketplace import SkillsMarketplace
    
    registry = SkillsRegistry()
    register_builtin_skills(registry)
    
    marketplace = SkillsMarketplace(registry)
    
    skills = marketplace.list_skills()
    print(f"可用Skills数量: {len(skills)}")
    
    search_results = marketplace.search("文档")
    print(f"\n搜索'文档'的结果: {[s['name'] for s in search_results]}")
    
    details = marketplace.get_details("document_generation")
    print(f"\nSkill详情:")
    print(f"  名称: {details['name']}")
    print(f"  描述: {details['description']}")
    print(f"  版本: {details['version']}")
    print(f"  分类: {details['category']}")
    
    stats = marketplace.get_stats()
    print(f"\n市场统计:")
    print(f"  总Skills数: {stats['total_skills']}")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("MTC模式使用示例")
    print("=" * 60)
    
    example_intent_clarification()
    example_task_planning()
    asyncio.run(example_skills_execution())
    example_mtc_agent()
    example_skills_marketplace()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
