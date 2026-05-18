# AloneWork

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**生产级 AI Agent 协作平台**

实时聊天 × 智能Agent × RAG检索 × 多Agent编排

[快速开始](#快速开始) · [文档](#文档) · [示例](#使用示例) · [路线图](#路线图) · [English](README.md)

</div>

---

## 简介

**AloneWork** 是一个集成了实时聊天应用与生产级 AI Agent 框架的全栈协作平台。

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
| **多格式文件处理** | 支持 PDF、Word、Excel、PPT、代码文件，含 OCR 图片识别 |
| **国际化支持** | 中英双语支持，基于 next-intl |

---

## 项目结构

```
AloneWork-workspace/
├── chat-app/                     # 实时聊天应用
│   ├── backend/                  # FastAPI 后端
│   │   ├── main.py               # 应用入口
│   │   ├── auth.py               # JWT 认证
│   │   ├── models.py             # 数据模型
│   │   ├── websocket_manager.py  # WebSocket 管理
│   │   ├── routers/              # API 路由
│   │   ├── services/             # 业务服务
│   │   └── tests/                # 测试用例
│   └── frontend/                 # Next.js 前端
│       ├── src/app/              # 页面路由
│       ├── src/components/       # React 组件
│       └── package.json
│
├── agent-framework/              # AI Agent 框架
│   ├── agent_framework/          # 核心包
│   │   ├── core/                 # 核心抽象
│   │   ├── agent/                # Agent 实现
│   │   │   ├── react_agent.py    # ReAct Agent
│   │   │   ├── multi_agent.py    # 多 Agent 团队
│   │   │   ├── mtc_agent.py      # MTC Agent
│   │   │   └── intent_clarifier.py
│   │   ├── gateway/              # Agent 网关
│   │   ├── llm/                  # LLM 提供商
│   │   ├── memory/               # 记忆系统
│   │   ├── rag/                  # RAG 流水线
│   │   ├── tools/                # 工具系统
│   │   ├── deepseek_optimization/ # DeepSeek 优化
│   │   ├── orchestration/        # 编排系统
│   │   ├── observability/        # 可观测性
│   │   └── sandbox/              # 沙箱执行
│   ├── examples/                 # 使用示例
│   └── tests/                    # 测试用例
│
├── docs/                         # 文档
├── bugs/                         # Bug 追踪
└── Makefile                      # 构建脚本
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

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16 | React 全栈框架 |
| React | 19 | UI 库 |
| Tailwind CSS | 4 | 原子化 CSS |
| shadcn/ui | - | 组件库 |
| next-intl | 3.21+ | 国际化 |

### Agent 框架

| 技术 | 版本 | 用途 |
|------|------|------|
| LiteLLM | 1.40+ | 多模型 LLM 统一网关 |
| ChromaDB | 0.4+ | 向量数据库 |
| NetworkX | 3.2+ | DAG 工作流编排 |
| PaddleOCR | 2.7+ | OCR 图片识别 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+

### 1. 克隆仓库

```bash
git clone https://github.com/AlonechatWorkspace/AloneWork.git
cd AloneWork
```

### 2. 安装依赖

```bash
make install
```

### 3. 配置环境变量

```bash
cp chat-app/backend/.env.example chat-app/backend/.env
cp agent-framework/.env.example agent-framework/.env
```

编辑 `.env` 文件：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production

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
make dev              # 同时启动后端和前端
make dev-backend      # http://localhost:8000
make dev-frontend     # http://localhost:3000

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

llm = LiteLLMProvider(LLMConfig(
    model="deepseek-chat",
    api_key="sk-your-api-key",
    api_base="https://api.deepseek.com/v1",
))

registry = ToolRegistry()
registry.register(CalculatorTool())

agent = ReActAgent(llm=llm, tool_registry=registry)
result = agent.run("计算 25 + 36 * 2")
print(result.answer)
```

### Multi-Agent 团队

```python
from agent_framework.agent.multi_agent import MultiAgentTeam

team = MultiAgentTeam()
team.add_agent("researcher", agent1, role="研究员")
team.add_agent("writer", agent2, role="撰写者")
team.add_agent("reviewer", agent3, role="审核者")

result = team.sequential_discussion("写一篇关于 AI Agent 的文章")
print(result["final_output"])
```

### MTC Agent（意图澄清）

```python
from agent_framework.agent.mtc_agent import MTCAgent

agent = MTCAgent(llm=llm)
clarification = agent.clarify_intent("帮我写个文档")

if clarification["needs_clarification"]:
    for q in clarification["questions"]:
        print(f"问题: {q['question']}")
        if q.get("options"):
            print(f"选项: {q['options']}")

agent.collect_clarification_answers({
    "output_format": "Markdown",
    "detail_level": "标准详细",
})

result = agent.run("帮我写个文档")
```

### 多格式文件处理

```python
from agent_framework.services.file_processors import get_processor

# 解析 PDF
processor = get_processor('.pdf')
text = await processor.to_text('document.pdf')

# 解析 Excel
processor = get_processor('.xlsx')
text = await processor.to_text('data.xlsx')

# OCR 图片识别
processor = get_processor('.png')
text = await processor.to_text('screenshot.png')
```

### Agent 网关 WebSocket

```javascript
const ws = new WebSocket("ws://localhost:18789/ws");

ws.send(JSON.stringify({ user_id: "user123", session_key: "session-001" }));

ws.send(JSON.stringify({ type: "message", body: "计算 25 + 36 * 2" }));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "thinking": console.log("思考中:", data.message); break;
    case "acting": console.log("执行工具:", data.message); break;
    case "final": console.log("最终答案:", data.content); break;
  }
};
```

---

## API 端点

### 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/conversations` | GET | 获取对话列表 |
| `/api/agent/sessions` | POST | 创建 Agent 会话 |
| `/api/v1/mcp-marketplace/servers` | GET | 获取 MCP 服务器列表 |
| `/api/v1/mcp-marketplace/servers/{id}/tools/call` | POST | 调用 MCP 工具 |
| `/api/v1/files/parse` | POST | 解析文件为文本 |
| `/api/v1/files/generate/{type}` | POST | 生成文件 |
| `/api/v1/tasks/decompose` | POST | 任务分解 |
| `/api/v1/skills` | GET | 获取技能列表 |

### Agent 网关 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/status` | GET | 网关状态 |
| `/ws` | WebSocket | 实时对话 |

---

## 路线图

### v0.1.1 (当前版本)

- [x] 实时聊天应用
- [x] ReAct Agent 实现
- [x] Multi-Agent 团队协作
- [x] RAG 检索流水线
- [x] Agent 网关服务
- [x] DeepSeek 优化模块
- [x] MCP 市场 API
- [x] MTC 模式（意图澄清）
- [x] 多格式文件处理（PDF/Word/Excel/PPT/代码）
- [x] OCR 图片识别
- [x] Skills 注册系统
- [x] 任务分解与执行
- [x] 国际化支持（中英双语）

### v0.2.0 (计划中)

- [ ] 前端 Office 编辑器（Word/Excel/PPT）
- [ ] 本地优先文件存储（IndexedDB）
- [ ] Office 文件格式转换
- [ ] Agent 对话历史持久化
- [ ] 用户工作区隔离

### v1.0.0 (远期)

- [ ] 生产级部署指南
- [ ] Kubernetes 部署方案
- [ ] 完整安全审计修复
- [ ] 性能基准测试

---

## 文档

| 文档 | 说明 |
|------|------|
| [架构设计](docs/轻量级Agent框架架构设计.md) | Agent 框架设计文档 |
| [网关设计](docs/生产级Agent网关架构设计.md) | 网关架构设计 |
| [网关快速开始](agent-framework/GATEWAY_README.md) | 网关使用指南 |
| [MCP 安装指南](MCP_MARKETPLACE_SETUP_GUIDE.md) | MCP 配置教程 |
| [安全审计](SECURITY_AUDIT_REPORT.md) | 安全漏洞分析 |
| [Bug 追踪](bugs/README.md) | Bug 列表 |
| [English](README.md) | 英文文档 |

---

## 安全

请参阅 [安全审计报告](SECURITY_AUDIT_REPORT.md) 了解已知漏洞和修复建议。

**重要提醒：**
- 生产环境必须更换 `SECRET_KEY`
- 数据库密码不要使用默认值
- API Key 不要提交到代码仓库

---

## 贡献

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

**GitHub**: [https://github.com/AloneWorkWorkspace/AloneWork](https://github.com/AloneWorkWorkspace/AloneWork)

Made with ❤️ by AloneWork Team

</div>
