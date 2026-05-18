"""
示例：使用AloneChat SDK进行代码生成
"""

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter

# 初始化配置
config_manager = ConfigManager()
config = config_manager.load_config()

# 创建模型路由器
model_router = ModelRouter(config)

# 生成代码
response = model_router.chat(
    model="deepseek",
    messages=[
        {"role": "user", "content": "写一个Python函数，计算列表的平均值"}
    ],
    stream=False
)

print(response)

# 流式输出
print("\n流式输出：")
for chunk in model_router.chat(
    model="deepseek",
    messages=[
        {"role": "user", "content": "写一个Python类，表示一个简单的栈"}
    ],
    stream=True
):
    print(chunk, end="", flush=True)
print()
