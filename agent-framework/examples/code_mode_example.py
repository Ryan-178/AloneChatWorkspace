"""
CODE模式使用示例
"""
import asyncio
from agent_framework.agent.code_agent import CodeAgent, SearchSubAgent, PlanMode
from agent_framework.sandbox.enhanced_sandbox import (
    EnhancedSandbox,
    create_code_sandbox,
    create_mtc_sandbox,
)
from agent_framework.core.types import AgentMode, FilePermission


def example_sandbox_security():
    """沙箱安全示例"""
    print("\n=== 沙箱安全示例 ===")
    
    mtc_sandbox = create_mtc_sandbox()
    code_sandbox = create_code_sandbox()
    
    print("MTC沙箱配置:")
    print(f"  模式: {mtc_sandbox.mode.value}")
    print(f"  允许的权限: {[p.value for p in mtc_sandbox.allowed_permissions]}")
    print(f"  允许的命令数: {len(mtc_sandbox.allowed_commands)}")
    
    print("\nCODE沙箱配置:")
    print(f"  模式: {code_sandbox.mode.value}")
    print(f"  允许的权限: {[p.value for p in code_sandbox.allowed_permissions]}")
    print(f"  允许的命令数: {len(code_sandbox.allowed_commands)}")
    
    print("\n路径验证测试:")
    test_paths = [
        f"{code_sandbox.project_folder}/src/main.py",
        "/etc/passwd",
        "../../../secret.txt",
    ]
    for path in test_paths:
        is_valid = code_sandbox.validate_path(path)
        print(f"  {path[:40]}: {'✓ 有效' if is_valid else '✗ 无效'}")
    
    print("\n命令验证测试:")
    test_commands = [
        ["python", "script.py"],
        ["git", "status"],
        ["rm", "-rf", "/"],
        ["sudo", "apt", "update"],
    ]
    for cmd in test_commands:
        is_valid, error = code_sandbox.validate_command(cmd)
        status = "✓ 允许" if is_valid else f"✗ 拒绝: {error[:30]}"
        print(f"  {' '.join(cmd)}: {status}")


async def example_search_subagent():
    """Search子Agent示例"""
    print("\n=== Search子Agent示例 ===")
    
    class MockLLM:
        pass
    
    search_agent = SearchSubAgent(MockLLM())
    
    print("搜索项目中的Python文件...")
    result = await search_agent.search("main function", ".")
    print(f"搜索结果:\n{result[:200]}...")
    
    print(f"\n上下文隔离: {len(search_agent.isolated_context)} 条消息")


async def example_plan_mode():
    """Plan Mode示例"""
    print("\n=== Plan Mode示例 ===")
    
    class MockLLM:
        pass
    
    plan_mode = PlanMode(MockLLM())
    
    task = "实现用户认证功能，包括登录、注册和密码重置"
    print(f"任务: {task}")
    
    plan = await plan_mode.create_plan(task)
    
    print(f"\n任务分析:")
    print(f"  类型: {plan['analysis']['type']}")
    print(f"  预计时间: {plan['estimated_time']}")
    
    print(f"\n执行步骤:")
    for step in plan["steps"]:
        needs_search = " (需要搜索)" if step.get("needs_search") else ""
        print(f"  {step['step']}. {step['description']}{needs_search}")
    
    print(f"\n风险评估:")
    for risk in plan["risks"]:
        print(f"  - {risk['risk']}")
        print(f"    应对: {risk['mitigation']}")


def example_code_agent():
    """CODE Agent示例"""
    print("\n=== CODE Agent示例 ===")
    
    class MockLLM:
        def chat(self, messages):
            return type("Response", (), {"content": "这是模拟的代码响应"})()
    
    agent = CodeAgent(llm=MockLLM(), project_path=".")
    
    print(f"Agent模式: {agent.mode.value}")
    print(f"项目路径: {agent.project_path}")
    print(f"Search子Agent: {'启用' if agent.search_agent else '禁用'}")
    print(f"Plan Mode: {'启用' if agent.plan_mode else '禁用'}")


async def example_code_tools():
    """CODE工具示例"""
    print("\n=== CODE工具示例 ===")
    
    from agent_framework.tools.code.code_tools import (
        CodeGeneratorTool,
        DebugAnalyzerTool,
        LintTool,
        TestGeneratorTool,
    )
    
    gen_tool = CodeGeneratorTool()
    result = gen_tool.execute(
        language="python",
        description="计算斐波那契数列",
    )
    print("代码生成结果:")
    print(f"  成功: {result.success}")
    print(f"  代码:\n{result.data['code'][:200]}...")
    
    debug_tool = DebugAnalyzerTool()
    result = debug_tool.execute(
        error_message="TypeError: 'NoneType' object is not iterable on line 42",
        code_context="for item in data:\n    process(item)",
    )
    print("\n调试分析结果:")
    print(f"  成功: {result.success}")
    print(f"  错误类型: {result.data['error_type']}")
    print(f"  建议: {result.data['suggestion']}")
    
    lint_tool = LintTool()
    long_code = "x = " + "1 + " * 60 + "1\n"
    result = lint_tool.execute(code=long_code, language="python")
    print("\n代码检查结果:")
    print(f"  成功: {result.success}")
    print(f"  问题数: {result.data['issue_count']}")


def example_sandbox_file_operations():
    """沙箱文件操作示例"""
    print("\n=== 沙箱文件操作示例 ===")
    
    sandbox = create_code_sandbox()
    
    print("写入文件...")
    success, path = sandbox.write_file(
        f"{sandbox.project_folder}/test.py",
        "print('Hello, World!')"
    )
    print(f"  结果: {'成功' if success else '失败'}")
    print(f"  路径: {path}")
    
    print("\n读取文件...")
    success, content = sandbox.read_file(f"{sandbox.project_folder}/test.py")
    print(f"  结果: {'成功' if success else '失败'}")
    print(f"  内容: {content}")
    
    print("\n列出文件...")
    success, files = sandbox.list_files()
    print(f"  结果: {'成功' if success else '失败'}")
    print(f"  文件数: {len(files)}")
    
    print("\n沙箱信息:")
    info = sandbox.get_sandbox_info()
    for key, value in info.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} 项")
        else:
            print(f"  {key}: {value}")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("CODE模式使用示例")
    print("=" * 60)
    
    example_sandbox_security()
    asyncio.run(example_search_subagent())
    asyncio.run(example_plan_mode())
    example_code_agent()
    asyncio.run(example_code_tools())
    example_sandbox_file_operations()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
