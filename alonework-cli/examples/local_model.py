"""
示例：使用本地Ollama模型（完全离线）
"""

from alonechat.config import ConfigManager
from alonechat.models import ModelRouter

# 初始化配置
config_manager = ConfigManager()
config = config_manager.load_config()

# 创建模型路由器
model_router = ModelRouter(config)

# 使用本地Ollama模型
response = model_router.chat(
    model="ollama",
    messages=[
        {"role": "user", "content": "写一个Python函数，实现快速排序算法"}
    ],
    stream=False
)

print(response)
