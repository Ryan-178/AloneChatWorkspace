"""
示例：多轮对话和上下文管理
"""

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter
from alonechat.context import ContextManager

# 初始化
config_manager = ConfigManager()
config = config_manager.load_config()
model_router = ModelRouter(config)
context_manager = ContextManager(max_tokens=128000)

# 多轮对话
questions = [
    "写一个Python函数，计算斐波那契数列",
    "给这个函数添加类型注解和文档字符串",
    "添加错误处理，确保输入为正整数",
    "写一个测试函数验证这个函数的正确性"
]

for question in questions:
    print(f"\n问题: {question}")
    print("-" * 60)
    
    # 添加用户消息到上下文
    context_manager.add_message("user", question)
    
    # 获取响应
    response = model_router.chat(
        model="deepseek",
        messages=context_manager.get_messages(),
        stream=False
    )
    
    # 添加助手响应到上下文
    context_manager.add_message("assistant", response)
    
    print(response)
    print("=" * 60)

print(f"\n当前上下文token数: {context_manager.current_tokens:,}")
