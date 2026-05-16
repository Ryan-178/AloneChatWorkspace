# AloneChat Workspace

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production-Grade AI Agent Collaboration Platform**

Real-time Chat × Intelligent Agent × RAG Retrieval × Multi-Agent Orchestration

[Quick Start](#quick-start) · [Documentation](#documentation) · [Examples](#usage-examples) · [Roadmap](#roadmap) · [中文文档](README_CN.md)

</div>

---

## Introduction

**AloneChat Workspace** is a full-stack collaboration platform integrating real-time chat application with a production-grade AI Agent framework.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Real-time Chat** | WebSocket-based instant messaging with private chat, groups, history, file sharing |
| **Agent Gateway** | Production-grade Agent runtime with ReAct reasoning, tool calling, session management |
| **Multi-Agent Orchestration** | Multi-Agent team collaboration with sequential discussion, broadcast, DAG workflow |
| **RAG Retrieval** | ChromaDB vector storage with document loading, chunking, embedding, retrieval |
| **MCP Marketplace** | Model Context Protocol server management for dynamic Agent capability extension |
| **DeepSeek Optimization** | Million-token context optimization: semantic cache, message compression, importance ranking |
| **Intent Clarification** | MTC Mode: automatic vague requirement detection, question form generation, task decomposition |
| **Multi-format File Processing** | Support for PDF, Word, Excel, PPT, Code files with OCR image recognition |
| **i18n Support** | Bilingual support (English/Chinese) with next-intl |

---

## Project Structure

```
AloneChat-workspace/
├── chat-app/                     # Real-time Chat Application
│   ├── backend/                  # FastAPI Backend
│   │   ├── main.py               # Application Entry
│   │   ├── auth.py               # JWT Authentication
│   │   ├── models.py             # Data Models
│   │   ├── websocket_manager.py  # WebSocket Management
│   │   ├── routers/              # API Routes
│   │   ├── services/             # Business Services
│   │   └── tests/                # Test Cases
│   └── frontend/                 # Next.js Frontend
│       ├── src/app/              # Page Routes
│       ├── src/components/       # React Components
│       └── package.json
│
├── agent-framework/              # AI Agent Framework
│   ├── agent_framework/          # Core Package
│   │   ├── core/                 # Core Abstractions
│   │   ├── agent/                # Agent Implementations
│   │   │   ├── react_agent.py    # ReAct Agent
│   │   │   ├── multi_agent.py    # Multi-Agent Team
│   │   │   ├── mtc_agent.py      # MTC Agent
│   │   │   └── intent_clarifier.py
│   │   ├── gateway/              # Agent Gateway
│   │   ├── llm/                  # LLM Providers
│   │   ├── memory/               # Memory System
│   │   ├── rag/                  # RAG Pipeline
│   │   ├── tools/                # Tool System
│   │   ├── deepseek_optimization/ # DeepSeek Optimization
│   │   ├── orchestration/        # Orchestration
│   │   ├── observability/        # Observability
│   │   └── sandbox/              # Sandbox Execution
│   ├── examples/                 # Usage Examples
│   └── tests/                    # Test Cases
│
├── docs/                         # Documentation
├── bugs/                         # Bug Tracking
└── Makefile                      # Build Script
```

---

## Tech Stack

### Backend

| Tech | Version | Purpose |
|------|---------|---------|
| FastAPI | 0.109+ | High-performance async web framework |
| SQLAlchemy | 2.0 | ORM and database interaction |
| Alembic | 1.13 | Database migrations |
| PostgreSQL | 16+ | Relational database |
| Redis | 7+ | Cache and message queue |
| WebSockets | 12.0 | Real-time bidirectional communication |

### Frontend

| Tech | Version | Purpose |
|------|---------|---------|
| Next.js | 16 | React full-stack framework |
| React | 19 | UI library |
| Tailwind CSS | 4 | Atomic CSS |
| shadcn/ui | - | Component library |
| next-intl | 3.21+ | Internationalization |

### Agent Framework

| Tech | Version | Purpose |
|------|---------|---------|
| LiteLLM | 1.40+ | Multi-model LLM unified gateway |
| ChromaDB | 0.4+ | Vector database |
| NetworkX | 3.2+ | DAG workflow orchestration |
| PaddleOCR | 2.7+ | OCR image recognition |

---

## Quick Start

### Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+

### 1. Clone Repository

```bash
git clone https://github.com/xiaodu-duhongrui/AloneChat-workspace.git
cd AloneChat-workspace
```

### 2. Install Dependencies

```bash
make install
```

### 3. Configure Environment

```bash
cp chat-app/backend/.env.example chat-app/backend/.env
cp agent-framework/.env.example agent-framework/.env
```

Edit `.env` files:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatapp
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production

LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=sk-your-api-key
LLM_API_BASE=https://api.deepseek.com/v1
```

### 4. Initialize Database

```bash
make db-init
```

### 5. Start Services

```bash
make dev              # Start backend + frontend
make dev-backend      # http://localhost:8000
make dev-frontend     # http://localhost:3000

cd agent-framework && python gateway_main.py  # http://localhost:18789
```

---

## Usage Examples

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
result = agent.run("Calculate 25 + 36 * 2")
print(result.answer)
```

### Multi-Agent Team

```python
from agent_framework.agent.multi_agent import MultiAgentTeam

team = MultiAgentTeam()
team.add_agent("researcher", agent1, role="Researcher")
team.add_agent("writer", agent2, role="Writer")
team.add_agent("reviewer", agent3, role="Reviewer")

result = team.sequential_discussion("Write an article about AI Agents")
print(result["final_output"])
```

### MTC Agent (Intent Clarification)

```python
from agent_framework.agent.mtc_agent import MTCAgent

agent = MTCAgent(llm=llm)
clarification = agent.clarify_intent("Help me write a document")

if clarification["needs_clarification"]:
    for q in clarification["questions"]:
        print(f"Q: {q['question']}")
        if q.get("options"):
            print(f"Options: {q['options']}")

agent.collect_clarification_answers({
    "output_format": "Markdown",
    "detail_level": "Standard",
})

result = agent.run("Help me write a document")
```

### Multi-format File Processing

```python
from agent_framework.services.file_processors import get_processor

# Parse PDF
processor = get_processor('.pdf')
text = await processor.to_text('document.pdf')

# Parse Excel
processor = get_processor('.xlsx')
text = await processor.to_text('data.xlsx')

# OCR Image
processor = get_processor('.png')
text = await processor.to_text('screenshot.png')
```

### Agent Gateway WebSocket

```javascript
const ws = new WebSocket("ws://localhost:18789/ws");

ws.send(JSON.stringify({ user_id: "user123", session_key: "session-001" }));

ws.send(JSON.stringify({ type: "message", body: "Calculate 25 + 36 * 2" }));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case "thinking": console.log("Thinking:", data.message); break;
    case "acting": console.log("Executing:", data.message); break;
    case "final": console.log("Answer:", data.content); break;
  }
};
```

---

## API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/conversations` | GET | Get conversation list |
| `/api/agent/sessions` | POST | Create Agent session |
| `/api/v1/mcp-marketplace/servers` | GET | List MCP servers |
| `/api/v1/mcp-marketplace/servers/{id}/tools/call` | POST | Call MCP tool |
| `/api/v1/files/parse` | POST | Parse file to text |
| `/api/v1/files/generate/{type}` | POST | Generate file |
| `/api/v1/tasks/decompose` | POST | Decompose task |
| `/api/v1/skills` | GET | List skills |

### Agent Gateway API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | Gateway status |
| `/ws` | WebSocket | Real-time conversation |

---

## Roadmap

### v0.1.1 (Current)

- [x] Real-time chat application
- [x] ReAct Agent implementation
- [x] Multi-Agent team collaboration
- [x] RAG retrieval pipeline
- [x] Agent Gateway service
- [x] DeepSeek optimization module
- [x] MCP Marketplace API
- [x] MTC Mode (Intent Clarification)
- [x] Multi-format file processing (PDF/Word/Excel/PPT/Code)
- [x] OCR image recognition
- [x] Skills registration system
- [x] Task decomposition and execution
- [x] i18n support (English/Chinese)

### v0.2.0 (Planned)

- [ ] Frontend Office editors (Word/Excel/PPT)
- [ ] Local-first file storage (IndexedDB)
- [ ] Office file format conversion
- [ ] Agent conversation history persistence
- [ ] User workspace isolation

### v1.0.0 (Future)

- [ ] Production deployment guide
- [ ] Kubernetes deployment
- [ ] Complete security audit fixes
- [ ] Performance benchmarks

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Design](docs/轻量级Agent框架架构设计.md) | Agent framework design |
| [Gateway Design](docs/生产级Agent网关架构设计.md) | Gateway architecture |
| [Gateway Quick Start](agent-framework/GATEWAY_README.md) | Gateway usage guide |
| [MCP Setup Guide](MCP_MARKETPLACE_SETUP_GUIDE.md) | MCP configuration |
| [Security Audit](SECURITY_AUDIT_REPORT.md) | Security vulnerabilities |
| [Bug Tracking](bugs/README.md) | Bug list |
| [中文文档](README_CN.md) | Chinese documentation |

---

## Security

See [Security Audit Report](SECURITY_AUDIT_REPORT.md) for known vulnerabilities and fixes.

**Important:**
- Change `SECRET_KEY` in production
- Don't use default database passwords
- Never commit API keys to repository

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Create Pull Request

---

## License

[MIT License](LICENSE)

---

<div align="center">

**GitHub**: [https://github.com/xiaodu-duhongrui/AloneChat-workspace.git](https://github.com/xiaodu-duhongrui/AloneChat-workspace.git)

Made with ❤️ by AloneChat Team

</div>
