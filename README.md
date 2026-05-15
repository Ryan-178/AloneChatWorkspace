# AloneChat Workspace

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**生产级 AI Agent 协作平台**

实时聊天 × 智能Agent × RAG检索 × 多Agent编排

[快速开始](#快速开始) · [文档](#文档) · [示例](#使用示例) · [路线图](#路线图)

</div>

---

## 简介

**AloneChat Workspace** 是一个集成了实时聊天应用与生产级 AI Agent 框架的全栈协作平台。

### 核心能力

| 能力 | 说明 |
|------|------|
| **实时聊天** | WebSocket 即时通讯，支持私聊、群组、消息历史、文件共享 |
| **Agent 网关** | 生产级 Agent 运行时，支持 ReAct 推理、工具调用、会话管理 |
| **多 Agent 编排** | Multi-Agent 团队协作，支持顺序讨论、广播、DAG 工作流 |
| **RAG 检索** | ChromaDB 向量存储，支持文档加载、分块、嵌入、检索 |
| **MCP 市场** | Model Context Protocol 服务器管理，动态扩展 Agent 能力 |
| **DeepSeek 优化** | 百万级上下文优化：语义缓存、消息压缩、重要性排序 |
| **意图澄清** | MTC 模式：自动识别模糊需求，生成追问表单，任务分解 |

---

## 项目结构

```
AloneChat-workspace/
├── chat-app/                     # 实时聊天应用
│   ├── backend/                  # FastAPI 后端
│   │   ├── main.py               # 应用入口
│   │   ├── auth.py               # JWT 认证
│   │   ├── models.py             # 数据模型
│   │   ├── websocket_manager.py  # WebSocket 管理
│   │   ├── routers/              # API 路由
│   │   │   ├── agent.py          # Agent 对话路由
│   │   │   ├── mcp_marketplace.py # MCP 市场路由
│   │   │   └── workspaces.py     # 工作区路由
│   │   ├── services/             # 业务服务
│   │   └── tests/                # 测试用例
│   └── frontend/                 # Next.js 前端
│       ├── src/app/              # 页面路由
│       ├── src/components/       # React 组件
│       │   ├── agent-chat.tsx    # Agent 对话组件
│       │   ├── agent-panel.tsx   # Agent 面板
│       │   └── chat-layout.tsx   # 聊天布局
│       └── package.json
│
├── agent-framework/              # AI Agent 框架
│   ├── agent_framework/          # 核心包
│   │   ├── core/                 # 核心抽象
│   │   │   ├── base_agent.py     # Agent 基类
│   │   │   ├── base_llm.py       # LLM 基类
│   │   │   ├── agent_bus.py      # Agent 消息总线
│   │   │   └── orchestrator.py   # 编排器
│   │   ├── agent/                # Agent 实现
│   │   │   ├── react_agent.py    # ReAct Agent
│   │   │   ├── multi_agent.py    # 多 Agent 团队
│   │   │   ├── mtc_agent.py      # MTC Agent (意图澄清)
│   │   │   └── intent_clarifier.py # 意图澄清器
│   │   ├── gateway/              # Agent 网关
│   │   │   ├── core.py           # 网关核心
│   │   │   ├── session.py        # 会话管理
│   │   │   ├── router.py         # 消息路由
│   │   │   └── tools.py          # 工具系统
│   │   ├── llm/                  # LLM 提供商
│   │   │   └── litellm_provider.py # LiteLLM 统一网关
│   │   ├── memory/               # 记忆系统
│   │   │   ├── conversation_memory.py # 对话记忆
│   │   │   └── vector_memory.py  # 向量记忆
│   │   ├── rag/                  # RAG 流水线
│   │   │   ├── loader.py         # 文档加载
│   │   │   ├── splitter.py       # 文本分块
│   │   │   ├── embedding.py      # 向量嵌入
│   │   │   ├── retriever.py      # 检索器
│   │   │   └── pipeline.py       # RAG 流水线
│   │   ├── tools/                # 工具系统
│   │   │   ├── registry.py       # 工具注册表
│   │   │   ├── builtin/          # 内置工具
│   │   │   │   ├── calculator.py # 计算器
│   │   │   │   ├── current_time.py # 当前时间
│   │   │   │   └── web_search.py # 网络搜索
│   │   │   └── skills_registry.py # Skills 注册
│   │   ├── deepseek_optimization/ # DeepSeek 优化
│   │   │   ├── cache/            # 缓存系统
│   │   │   │   ├── semantic_cache.py # 语义缓存
│   │   │   │   ├── vector_cache.py   # 向量缓存
│   │   │   │   └── cache_engine.py   # 缓存引擎
│   │   │   ├── context/          # 上下文管理
│   │   │   │   ├── message_ranker.py      # 消息排序
│   │   │   │   ├── context_compressor.py  # 上下文压缩
│   │   │   │   ├── mega_context_manager.py # 百万上下文管理
│   │   │   │   └── window_manager.py      # 窗口管理
│   │   │   ├── llm/              # DeepSeek 提供商
│   │   │   │   ├── deepseek_provider.py # DeepSeek API
│   │   │   │   └── model_config.py      # 模型配置
│   │   │   ├── mcp_marketplace/  # MCP 市场
│   │   │   │   ├── client.py     # MCP 客户端
│   │   │   │   ├── registry.py   # MCP 注册表
│   │   │   │   └── loader.py     # MCP 加载器
│   │   │   ├── security/         # 安全模块
│   │   │   │   ├── audit_logger.py     # 审计日志
│   │   │   │   ├── data_protection.py  # 数据保护
│   │   │   │   └── encryption.py       # 加密
│   │   │   └── swe/              # 软件工程 Agent
│   │   │       └── swe_engine.py # SWE 引擎
│   │   ├── orchestration/        # 编排系统
│   │   │   ├── sequential.py     # 顺序执行
│   │   │   ├── parallel.py       # 并行执行
│   │   │   └── dag.py            # DAG 工作流
│   │   ├── observability/        # 可观测性
│   │   │   ├── logger.py         # 日志
│   │   │   ├── metrics.py        # 指标
│   │   │   └── tracer.py         # 追踪
│   │   ├── sandbox/              # 沙箱执行
│   │   │   └── subprocess_sandbox.py
│   │   ├── security/             # 安全
│   │   │   └── rate_limiter.py   # 限流
│   │   └── config.py             # 配置管理
│   ├── examples/                 # 使用示例
│   │   ├── deepseek_complete_example.py
│   │   ├── deepseek_comprehensive.py
│   │   └── mtc_mode_example.py
│   ├── tests/                    # 测试用例
│   ├── gateway_main.py           # 网关启动脚本
│   ├── config.yaml               # 配置文件
│   └── pyproject.toml
│
├── docs/                         # 文档
│   ├── 轻量级Agent框架架构设计.md
│   ├── 生产级Agent网关架构设计.md
│   └── superpowers/plans/        # 功能计划
│
├── bugs/                         # Bug 追踪
│   ├── README.md
│   └── SECURITY_VULNERABILITIES.md
│
├── Makefile                      # 构建脚本
├── SECURITY_AUDIT_REPORT.md      # 安全审计报告
├── MCP_MARKETPLACE_SETUP_GUIDE.md # MCP 安装指南
└── RELEASE_NOTE_v0.1.0.md        # 发布说明
```

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.109+ | 高性能异步 Web 框架 |
| SQLAlchemy | 2.0 | ORM 与数据库交互 |
| Alembic | 1.13 | 数据库迁移 |
| PostgreSQL | 16+ | 关系型数据库 |
| Redis | 7+ | 缓存与消息队列 |
| WebSockets | 12.0 | 实时双向通讯 |
| PyJWT | - | 身份认证 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16 | React 全栈框架 |
| React | 19 | UI 库 |
| Tailwind CSS | 4 | 原子化 CSS |
| shadcn/ui | - | 组件库 |
| Radix UI | - | 无头组件 |
| Tiptap | 2.11 | 富文本编辑 |
| Dexie | 4.0 | IndexedDB 封装 |

### Agent 框架

| 技术 | 版本 | 用途 |
|------|------|------|
| LiteLLM | 1.40+ | 多模型 LLM 统一网关 |
| ChromaDB | 0.4+ | 向量数据库 |
| NetworkX | 3.2+ | DAG 工作流编排 |
| Tenacity | 8.2+ | 重试与容错 |
| Pydantic | 2.5+ | 数据验证 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+

### 1. 克隆仓库

```bash
git clone https://github.com/xiaodu-duhongrui/AloneChat-workspace.git
cd AloneChat-workspace
```

### 2. 安装依赖

```bash
# 使用 Makefile（推荐）
make install

# 或手动安装
pip install -r chat-app/backend/requirements.txt
pip install -e agent-framework
cd chat-app/frontend && npm install
```

### 3. 配置环境变量

```bash
# 后端配置
cp chat-app/backend/.env.example chat-app/backend/.env

# Agent 框架配置
cp agent-framework/.env.example agent-framework/.env
```

编辑 `.env` 文件：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production

# LLM（支持 OpenAI / DeepSeek / Anthropic 等）
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=sk-your-api-key
LLM_API_BASE=https://api.deepseek.com/v1
```

### 4. 初始化数据库

```bash
make db-init
```

### 5. 启动服务

```bash
# 同时启动后端和前端
make dev

# 或分别启动
make dev-backend   # http://localhost:8000
make dev-frontend  # http://localhost:3000

# 启动 Agent 网关
cd agent-framework && python gateway_main.py  # http://localhost:18789
```

---

## 使用示例

### ReAct Agent

```python
from agent_framework.agent.react_agent import ReActAgent
from agent_framework.llm.litellm_provider import LiteLLMProvider
from agent_framework.tools.registry import ToolRegistry
from agent_framework.tools.builtin.calculator import CalculatorTool
from agent_framework.core.base_llm import LLMConfig

# 配置 LLM
llm = LiteLLMProvider(LLMConfig(
    model="deepseek-chat",
    api_key="sk-your-api-key",
    api_base="https://api.deepseek.com/v1",
))

# 注册工具
registry = ToolRegistry()
registry.register(CalculatorTool())

# 创建 Agent
agent = ReActAgent(llm=llm, tool_registry=registry)

# 运行
result = agent.run("计算 25 + 36 * 2")
print(result.answer)  # 输出: 97
```

### Multi-Agent 团队

```python
from agent_framework.agent.multi_agent import MultiAgentTeam
from agent_framework.agent.react_agent import ReActAgent

# 创建团队
team = MultiAgentTeam()

# 添加 Agent
team.add_agent("researcher", agent1, role="研究员", backstory="擅长信息搜集和分析")
team.add_agent("writer", agent2, role="撰写者", backstory="擅长内容创作和编辑")
team.add_agent("reviewer", agent3, role="审核者", backstory="擅长质量把控")

# 顺序讨论
result = team.sequential_discussion("写一篇关于 AI Agent 的文章")
print(result["final_output"])
```

### MTC Agent（意图澄清）

```python
from agent_framework.agent.mtc_agent import MTCAgent

agent = MTCAgent(llm=llm)

# 模糊需求会触发意图澄清
clarification = agent.clarify_intent("帮我写个文档")

if clarification["needs_clarification"]:
    print("需要澄清的问题:")
    for q in clarification["questions"]:
        print(f"  - {q['question']}")
        if q.get("options"):
            print(f"    选项: {q['options']}")

# 收集回答
agent.collect_clarification_answers({
    "output_format": "Markdown",
    "detail_level": "标准详细",
})

# 执行任务
result = agent.run("帮我写个文档")
```

### RAG 检索

```python
from agent_framework.rag.pipeline import RAGPipeline

# 创建 RAG 流水线
rag = RAGPipeline(
    embedding_model="text-embedding-ada-002",
    vector_db_path="./data/chroma",
)

# 加载文档
rag.load_documents("./documents/")

# 检索
results = rag.retrieve("什么是 Agent?", top_k=5)
for doc in results:
    print(doc.content)
```

### Agent 网关 WebSocket

```javascript
// 前端 WebSocket 连接
const ws = new WebSocket("ws://localhost:18789/ws");

// 初始化
ws.send(JSON.stringify({
  user_id: "user123",
  session_key: "session-001"
}));

// 发送消息
ws.send(JSON.stringify({
  type: "message",
  body: "帮我计算 25 + 36 * 2"
}));

// 接收响应
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "thinking":
      console.log("思考中:", data.message);
      break;
    case "acting":
      console.log("执行工具:", data.message);
      break;
    case "observation":
      console.log("工具结果:", data.result);
      break;
    case "final":
      console.log("最终答案:", data.content);
      break;
  }
};
```

---

## 配置说明

### Agent 框架配置 (config.yaml)

```yaml
# LLM 配置
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: null  # 从环境变量读取
  temperature: 0.7
  max_tokens: 4096
  timeout: 30.0

# 记忆配置
memory:
  window_size: 10
  vector_db_type: chromadb
  vector_db_path: ./data/chroma

# 网关配置
gateway:
  host: 0.0.0.0
  port: 18789
  session_timeout: 3600
  max_sessions: 1000

# 日志配置
logging:
  level: INFO
  format: colored
```

### DeepSeek 优化配置

```python
from agent_framework.deepseek_optimization.llm import DeepSeekProvider, DeepSeekConfig

config = DeepSeekConfig(
    model="deepseek-chat",  # 或 "deepseek-pro", "deepseek-reasoner"
    api_key="sk-your-api-key",
    temperature=0.7,
    max_tokens=8192,
    streaming=True,
)

provider = DeepSeekProvider(config)

# 获取使用统计（包含 KV Cache 命中率）
stats = provider.get_usage_stats()
print(f"缓存命中率: {stats['cache_hit_rate']:.2%}")
print(f"节省费用: ${stats['cost_saved']:.4f}")
```

---

## API 端点

### 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/conversations` | GET | 获取对话列表 |
| `/api/conversations/{id}/messages` | GET | 获取消息历史 |
| `/api/groups` | GET | 获取群组列表 |
| `/api/groups/{id}/messages` | GET | 获取群组消息 |
| `/api/agent/sessions` | POST | 创建 Agent 会话 |
| `/api/agent/sessions/{id}/run` | POST | 运行 Agent |
| `/api/v1/mcp-marketplace/servers` | GET | 获取 MCP 服务器列表 |
| `/api/v1/mcp-marketplace/servers` | POST | 注册 MCP 服务器 |
| `/api/v1/mcp-marketplace/servers/{id}/action` | POST | 启动/停止服务器 |
| `/api/v1/mcp-marketplace/servers/{id}/tools` | GET | 获取服务器工具 |
| `/api/v1/mcp-marketplace/servers/{id}/tools/call` | POST | 调用工具 |

### Agent 网关 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/status` | GET | 网关状态 |
| `/stats` | GET | 统计信息 |
| `/ws` | WebSocket | 实时对话 |

---

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装所有依赖 |
| `make dev` | 启动后端 + 前端 |
| `make dev-backend` | 启动后端服务 |
| `make dev-frontend` | 启动前端服务 |
| `make test` | 运行全部测试 |
| `make test-backend` | 后端测试 |
| `make test-frontend` | 前端测试 |
| `make test-agent` | Agent 框架测试 |
| `make lint` | 代码检查 |
| `make db-init` | 初始化数据库 |
| `make clean` | 清理构建产物 |
| `make help` | 显示帮助 |

---

## 架构图

```mermaid
graph TB
    subgraph Frontend["前端层"]
        FE[Next.js 16]
        WS[WebSocket Client]
        UI[shadcn/ui]
    end

    subgraph Backend["后端层"]
        API[FastAPI]
        AUTH[JWT Auth]
        WM[WebSocket Manager]
        DB[(PostgreSQL)]
        REDIS[(Redis)]
    end

    subgraph AgentFramework["Agent 框架"]
        GW[Agent Gateway]
        BUS[Agent Bus]
        
        subgraph Agents["Agent 实现"]
            REACT[ReAct Agent]
            MULTI[Multi-Agent]
            MTC[MTC Agent]
        end
        
        subgraph Core["核心组件"]
            LLM[LiteLLM]
            MEM[Memory]
            RAG[RAG Pipeline]
            TOOLS[Tool Registry]
        end
        
        subgraph DeepSeek["DeepSeek 优化"]
            CACHE[Semantic Cache]
            COMPRESS[Context Compressor]
            RANKER[Message Ranker]
        end
        
        subgraph MCP["MCP 市场"]
            MCPREG[MCP Registry]
            MCPCLIENT[MCP Client]
        end
    end

    FE -->|HTTP| API
    FE -->|WS| WM
    API --> AUTH
    API --> DB
    API --> REDIS
    API --> GW
    WM --> GW
    GW --> BUS
    BUS --> REACT
    BUS --> MULTI
    BUS --> MTC
    REACT --> LLM
    REACT --> TOOLS
    MULTI --> LLM
    MTC --> LLM
    LLM --> CACHE
    LLM --> COMPRESS
    TOOLS --> MCPREG
    MCPREG --> MCPCLIENT
```

---

## 路线图

### v0.1.0 (当前)

- [x] 实时聊天应用基础功能
- [x] ReAct Agent 实现
- [x] Multi-Agent 团队协作
- [x] RAG 检索流水线
- [x] Agent 网关服务
- [x] DeepSeek 优化模块
- [x] MCP 市场基础 API

### v0.2.0 (计划中)

- [ ] 前端 Office 编辑器（Word/Excel/PPT）
- [ ] 本地优先文件存储（IndexedDB）
- [ ] Office 文件格式转换
- [ ] Agent 对话历史持久化
- [ ] 用户工作区隔离

### v0.3.0 (计划中)

- [ ] Agent 技能市场
- [ ] 可视化工作流编排
- [ ] Agent 性能监控面板
- [ ] 多语言支持

### v1.0.0 (远期)

- [ ] 生产级部署指南
- [ ] Kubernetes 部署方案
- [ ] 完整安全审计修复
- [ ] 性能基准测试

---

## 文档

| 文档 | 说明 |
|------|------|
| [轻量级Agent框架架构设计](docs/轻量级Agent框架架构设计.md) | Agent 框架设计文档 |
| [生产级Agent网关架构设计](docs/生产级Agent网关架构设计.md) | 网关架构设计 |
| [Agent 网关快速开始](agent-framework/GATEWAY_README.md) | 网关使用指南 |
| [MCP 市场安装指南](MCP_MARKETPLACE_SETUP_GUIDE.md) | MCP 配置教程 |
| [安全审计报告](SECURITY_AUDIT_REPORT.md) | 安全漏洞分析 |
| [Bug 追踪系统](bugs/README.md) | Bug 列表 |
| [发布说明](RELEASE_NOTE_v0.1.0.md) | v0.1.0 发布说明 |

---

## 安全

请参阅 [安全审计报告](SECURITY_AUDIT_REPORT.md) 了解已知漏洞和修复建议。

**重要提醒：**
- 生产环境必须更换 `SECRET_KEY`
- 数据库密码不要使用默认值
- API Key 不要提交到代码仓库

---

## 贡献

欢迎贡献代码、报告 Bug 或提出功能建议。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

[MIT License](LICENSE)

---

<div align="center">

**GitHub**: [https://github.com/xiaodu-duhongrui/AloneChat-workspace.git](https://github.com/xiaodu-duhongrui/AloneChat-workspace.git)

Made with ❤️ by AloneChat Team

</div>
