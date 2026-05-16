# 🦞 Agent Gateway - 快速开始

生产级Agent运行时网关，参考OpenClaw设计！

## 快速开始

### 1. 安装依赖

```bash
cd agent-framework
pip install -e .
# 或者安装额外依赖
pip install fastapi uvicorn websockets httpx
```

## 运行Gateway

```bash
python gateway_main.py
```

Gateway将在 `http://localhost:18789` 启动!

## 测试Gateway

### 健康检查

```bash
curl http://localhost:18789/health
```

### 查看状态

```bash
curl http://localhost:18789/status
```

### 查看统计信息

```bash
curl http://localhost:18789/stats
```

## WebSocket测试

运行测试客户端：

```bash
# 终端1 - 启动Gateway
python gateway_main.py

# 终端2 - 运行测试
python test_websocket_client.py
```

## WebSocket API 协议

### 连接初始化

```json
{
  "user_id": "your_user_id",
  "session_key": "optional_session_key"
}
```

### 发送消息

```json
{
  "type": "message",
  "body": "你好，帮我计算25+36*2",
  "user_id": "user123"
}
```

### 接收消息类型

- `connected` - 连接确认
- `thinking` - Agent思考中
- `stream` - 流式内容
- `acting` - 执行工具
- `observation` - 工具执行结果
- `final` - 最终答案
- `error` - 错误
- `busy` - 忙碌
- `pong` - PING响应
- `info` - 信息

### 重置会话

```json
{
  "type": "reset"
}
```

## 内置工具

1. **calculator** - 数学计算
2. **current_time** - 获取当前时间
3. **web_search** - 网络搜索(模拟)

## 项目结构

```
agent_framework/gateway/
├── __init__.py      # 导出模块
├── core.py          # Gateway核心
├── types.py         # 数据模型
├── session.py      # 会话管理
├── router.py       # 消息路由
├── tools.py        # 工具系统
└── agent.py        # ReAct Agent
```

## 使用示例

### 编程方式使用

```python
from agent_framework.gateway import (
    AgentGateway,
    GatewayConfig,
    MsgContext,
)

# 1. 创建Gateway配置
config = GatewayConfig(
    host="0.0.0.0",
    port=18789,
    debug=True,
)

# 2. 创建Agent
from agent_framework.gateway import ReActAgent

agent = ReActAgent()

# 3. 运行Agent
result = await agent.run("计算25+36*2")
print(result.final_answer)
```

## 配置LLM

在环境变量中配置API Key：

```bash
export OPENAI_API_KEY="your-key-here"
# 或者使用 .env 文件
```

## 下一步

- 查看 docs/ 文件夹下的详细文档！
- 继续实现更多工具和技能系统！

---

🦞 Let's go!
