# CLI功能增强与优化

> **Workspace:** e:\AloneChat-workspace-master

---

## User
cli加强：自动记忆（Auto Memory） 	 2.1.59 	 Claude 自动保存有用上下文，通过 /memory 管理 
 记忆最后修改时间戳 	 2.1.75 	 帮助判断记忆新鲜度 
 自动记忆自定义目录 	 2.1.74 	 autoMemoryDirectory 设置 
 会话自动命名 	 2.1.77 	 接受计划时根据内容自动命名 
 会话质量调查 	 2.1.76 	 企业可配置采样率 feedbackSurveyRate 
 后台智能体保留部分结果 	 2.1.76 	 终止后台智能体时保留其部分结果

## Assistant
Let me first explore the project context to understand the current architecture.

I'll explore the codebase comprehensively by running multiple searches in parallel.

Now let me dive deeper into the key files to understand the CLI architecture and agent-framework structure.

Let me now read additional key files to complete the picture.

Let me check a few more key files to complete the analysis.

Now I have a comprehensive view of the entire codebase. Here is the detailed summary.

---

## Comprehensive Project Structure Analysis

### 1. Overall Project Structure

The workspace is at `E:\AloneChat-workspace-master` and contains **three main sub-projects** plus supporting directories:

```
E:\AloneChat-workspace-master/
├── .trae/                          # Trae (IDE) configuration
│   ├── documents/                  # 21 planning/spec documents
│   ├── rules/acw.md                # Project rules
│   └── specs/                      # Formal specifications (agent-framework-core, chat-app, mtc, workspace)
├── agent-framework/                # Core agent framework (Python library)
├── alonechat-cli/                  # CLI application (Python package)
├── alonechat-desktop/              # Desktop app (Next.js + Tauri)
├── bugs/                           # Bug tracking
├── docs/                           # Guides, releases, research, security, tech reports
├── .gitignore
├── ChatAgent.code-workspace        # VS Code workspace file
├── LICENSE
├── Makefile
├── README.md / README_CN.md
└── generate_docs.py
```

---

### 2. Project Rules (.trae/rules/acw.md)

**File:** [acw.md](file:///e:/AloneChat-workspace-master/.trae/rules/acw.md)

Key rules:
- **NPM is banned** -- no npm usage allowed
- **No hardcoding** -- all data must use YAML storage
- **Chinese-English bilingual comments** required throughout
- **Reuse agent-framework** -- if something is already implemented in `agent-framework`, do not re-implement it in other projects; if a feature is missing, implement it in `agent-framework` first

---

### 3. agent-framework Structure

**Path:** `E:\AloneChat-workspace-master\agent-framework`
**Package:** `agent-framework` v0.3.0 -- described as "Production-Grade Agent Gateway (like OpenClaw) for LLM-powered applications"
**Entry point:** `agent_framework/__init__.py` exposes core abstractions (BaseLLM, BaseTool, BaseMemory, BaseAgent, Orchestrator, AgentBus, etc.)

#### Core Layer (`agent_framework/core/`)
| File | Description |
|------|-------------|
| [base_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_agent.py) | Abstract BaseAgent with perceive/plan/act/reflect lifecycle, AgentEvent, AgentResult |
| [base_llm.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_llm.py) | Abstract BaseLLM, Message, Chunk, LLMConfig |
| [base_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_memory.py) | Abstract BaseMemory, MemoryEntry (Pydantic model) |
| [base_tool.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_tool.py) | Abstract BaseTool, ToolDef, ToolResult |
| [types.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) | Core types: AgentState, MessageRole, Message, ToolCall, AgentMode, ModeConfig, FilePermission, TaskStatus, TaskPriority |
| [orchestrator.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/orchestrator.py) | Abstract Orchestrator with run/run_multi/run_workflow, WorkflowNode, WorkflowGraph |
| [agent_bus.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/agent_bus.py) | AgentMessage, AgentBus (message passing between agents) |
| [task.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/task.py) | Task model |

#### Gateway Layer (`agent_framework/gateway/`)
| File | Description |
|------|-------------|
| [core.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/core.py) | GatewayCore -- WebSocket server, message routing, tool execution, authentication |
| [types.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/types.py) | MsgContext (unified message format), Session, SessionState, GatewayConfig, GatewayStatus |
| [session.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/session.py) | Gateway-level SessionManager with session lanes, user sessions, cleanup |
| [router.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/router.py) | MessageRouter |
| [tools.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/tools.py) | ToolExecutor |
| [agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/agent.py) | ReActAgent |
| [api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/api.py) | REST API endpoints |
| [auth.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/auth.py) | Authentication |
| [mcp_api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/mcp_api.py) | MCP API |
| [user_api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/user_api.py) | User API |
| [websocket.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/websocket.py) | WebSocket handler |

#### Agent Implementations (`agent_framework/agent/`)
| File | Description |
|------|-------------|
| [react_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/react_agent.py) | ReAct agent implementation |
| [code_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/code_agent.py) | Code mode agent |
| [code_prompts.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/code_prompts.py) | Code mode prompts |
| [mtc_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/mtc_agent.py) | MTC (More Than Coding) mode agent |
| [mtc_prompts.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/mtc_prompts.py) | MTC mode prompts |
| [multi_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/multi_agent.py) | Multi-agent orchestration |
| [task_planner.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/task_planner.py) | Task planner agent |
| [intent_clarifier.py](file

## User
所有功能全部实现

## Assistant
好的，我来先了解项目结构，然后逐步设计并实现所有功能。

让我先探索项目上下文，了解 CLI 和 agent-framework 的结构。

---

# AloneChat 项目结构综合分析报告

## 一、项目整体结构（顶层目录与文件）

项目根目录 `E:\AloneChat-workspace-master` 包含三大核心组件：

| 目录/文件 | 说明 |
|-----------|------|
| `agent-framework/` | Agent 核心框架（Python 包，v0.3.0） |
| `alonechat-cli/` | CLI 命令行工具（Python 包，v0.2.0） |
| `alonechat-desktop/` | 桌面端应用（Next.js + Tauri v0.1.0） |
| `docs/` | 项目文档（技术报告、发布说明、安全审计等） |
| `.trae/` | Trae 配置（规格文档、实现计划、workspace 规则） |
| `bugs/` | Bug 与安全漏洞记录 |
| `.gitignore` | Git 忽略规则 |
| `README.md` / `README_CN.md` | 项目说明 |
| `Makefile` | 构建自动化 |
| `ChatAgent.code-workspace` | VS Code 工作区配置 |
| `LICENSE` | MIT 许可证 |
| `generate_docs.py` | 文档生成脚本 |

**工作空间规则**（来自 [acw.md](file:///e:/AloneChat-workspace-master/.trae/rules/acw.md)）：
- 禁止使用 NPM
- 全部数据使用 YAML 存储，禁止硬编码
- 全部注释使用中英双语
- 已由 agent-framework 实现的功能直接套用，不再重复实现；未实现的功能在 agent-framework 中实现

---

## 二、CLI 架构 -- 命令组织结构

CLI 代码位于 [alonechat-cli/src/alonechat/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/)，基于 **Click** 框架构建。

### 2.1 主入口

[cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/cli.py#L116-L269) 定义了 `@click.group(invoke_without_command=True)` 的 `main` 函数，注册了 6 个顶级子命令：

```python
main.add_command(init.init_command, name="init")       # 初始化
main.add_command(chat.chat_command, name="chat")         # 交互对话
main.add_command(generate.generate_command, name="generate")  # 代码生成
main.add_command(test.test_command, name="test")         # 自动测试
main.add_command(commit.commit_command, name="commit")   # 智能提交
main.add_command(mcp_command, name="mcp")                # MCP 管理
main.add_command(agent_commands, name="agent")           # Agent 管理
```

### 2.2 CLI 选项（全局支持）

| 选项 | 说明 |
|------|------|
| `--name` | 设置会话显示名称 |
| `--agent` | 覆盖代理设置（格式：key=value,key=value） |
| `--print/-p` | 非交互打印模式 |
| `--continue/-C` | 继续最近的会话 |
| `--resume/-r` | 恢复指定会话 |
| `--auto-compact` | 启用自动对话压缩 |
| `--output-format` | 输出格式（text/json/stream-json） |
| `--model/-m` | 指定模型 |
| `--system-prompt` | 替换系统提示词 |
| `--append-system-prompt` | 追加系统提示词 |

### 2.3 Slash 命令系统

位于 [alonechat-cli/src/alonechat/slash/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/)，包括：
- **解析器** [parser.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/parser.py)
- **注册器** [registry.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/registry.py)
- **执行器** [executor.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/executor.py)
- **17 个内置命令** 位于 [slash/commands/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/)：
  `agents`, `clear`, `compact`, `config`, `context`, `cost`, `doctor`, `fork`, `help`, `init`, `mcp`, `model`, `permissions`, `review`, `rewind`, `stats`, `status`, `usage`, `vim`

### 2.4 配置管理

[configs/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/) 使用 **ConfigLoader** 单例模式加载 YAML：
- [config_loader.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/config_loader.py) -- 通过 `config.get("key.subkey")` 点分法访问
- 包含 5 个 YAML 配置文件：`utils_config.yaml`, `chinese_config.yaml`, `code_config.yaml`, `deepseek_config.yaml`, `git_config.yaml`

---

## 三、Agent-Framework 模块结构

框架代码位于 [agent-framework/agent_framework/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/)，包含 15 个核心模块：

| 模块目录 | 说明 |
|----------|------|
| **core/** | 核心抽象：`BaseAgent`, `BaseLLM`, `BaseMemory`, `BaseTool`, `AgentBus`, `Orchestrator`, `Task`, `Types` |
| **agent/** | Agent 实现：`CodeAgent`, `MTCAgent`, `ReActAgent`, `MultiAgentTeam`, `TaskPlanner`, `IntentClarifier` |
| **memory/** | 内存实现：`ConversationMemory`（窗口式）, `VectorMemory`（ChromaDB 向量） |
| **llm/** | LLM 供应商：`LiteLLMProvider`（统一接口） |
| **rag/** | RAG 管线：`CodeIndexer`, `Embedding`, `Retriever`, `Splitter`, `Pipeline` |
| **tools/** | 工具系统：内置工具（calculator, time, web_search）+ 代码工具 + MTC 文档工具 + Skills 注册 |
| **sandbox/** | 沙箱执行：`SubprocessSandbox`, `EnhancedSandbox` |
| **security/** | 安全：`RateLimiter` |
| **services/** | 服务层：`ErrorFixer`, `FileGenerators`, `FileProcessors`, `Skills Executor`, `TaskPlanner`, `TestGenerator` |
| **orchestration/** | 编排：`DAG`, `Parallel`, `Sequential` |
| **observability/** | 可观测性：`Logger`, `Metrics`, `Tracer` |
| **channels/** | 渠道：`BaseChannel`, `ChatAppChannel` |
| **gateway/** | 网关：`Router`, `Session Manager`, `Auth`, `API`, `WebSocket`, `MCP API`, `User API` |
| **deepseek_optimization/** | DeepSeek 优化：上下文管理、缓存、MCP 市场、安全、SWE 引擎 |
| **cli_enhancements/** | CLI 增强：`ClaudeMdLoader`, `RulesLoader`, `SkillsDiscovery`, `WorktreeManager`, `AdditionalDirLoader` |
| **configs/** | YAML 配置：`models.yaml`, `prompts.yaml`, `skills.yaml`, `sandbox.yaml`, `intent_clarification.yaml`, `cli_enhancements.yaml` |

---

## 四、YAML 配置存储模式

项目全面使用 YAML 替代硬编码，服务端配置和业务数据均通过 YAML 存储。

### 4.1 框架级配置

[agent-framework/config.yaml](file:///e:/AloneChat-workspace-master/agent-framework/config.yaml) 是主配置文件，包含：
```yaml
llm:
  provider: openai
  model: gpt-4o
memory:
  window_size: 10
  vector_db_type: chromadb
gateway:
  host: 0.0.0.0
  port: 8787
mcp:
  enabled: true
  servers: [...]
```

### 4.2 模块级 YAML 配置

框架模块配置位于 [agent_framework/configs/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/)：
- [models.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/models.yaml) -- 模型定义（DeepSeek V4 Flash/Pro/Reasoner, OpenAI GPT-4o/Turbo, Embedding）
- [prompts.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/prompts.yaml) -- 系统提示词模板（Code/MTC 模式、意图澄清、任务规划、多格式输出指南）
- [skills.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/skills.yaml) -- 内置技能定义（文档生成、数据分析、网络调研、PPT 生成、报告生成）
- [sandbox.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/sandbox.yaml) -- 沙箱资源限制和权限控制
- [intent_clarification.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/intent_clarification.yaml) -- 意图澄清规则和问题模板
- [cli_enhancements.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/cli_enhancements.yaml) -- CLI 增强配置

### 4.3 CLI 级 YAML 配置

CLI 配置文件在 [alonechat-cli/src/alonechat/configs/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/)：
- [chinese_config.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/chinese_config.yaml) -- 中文 NLP、代码风格、提示词模板
- [code_config.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/code_config.yaml) -- 多语言代码配置
- [deepseek_config.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/deepseek_config.yaml) -- DeepSeek API 配置
- [git_config.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/git_config.yaml) -- Git 提交规范
- [utils_config.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/utils_config.yaml) -- 进度消息、日志、命令定义、UI 样式

### 4.4 会话数据存储

**注意：** 会话数据（messages/display_name 等）目前使用 **JSON** 文件存储（`~/.alonechat/sessions/{id}.json`），并未使用 YAML。这是当前架构中不一致的地方。

---

## 五、现有 Memory / 会话命名 / 反馈功能

### 5.1 Memory 系统

存在**三层**记忆系统：

**（1）Core 层抽象** -- [base_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_memory.py)：
```python
class BaseMemory(ABC):
    def add(self, entry: MemoryEntry) -> None
    def query(self, text: str, k: int = 5) -> List[MemoryEntry]
    def clear(self) -> None
```

**（2）ConversationMemory** -- [conversation_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/memory/conversation_memory.py)：
- 基于窗口大小（默认 10）的循环内存
- `add_message()` / `get_messages()` / `summarize(llm)` 方法
- 先进先出截断

**（3）VectorMemory** -- [vector_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/memory/vector_memory.py)：
- 基于 ChromaDB 持久化向量存储
- 支持 OpenAI Embedding API
- 语义相似度查询

### 5.2 会话管理（三个独立实现）

**（A）CLI 会话系统** -- [session/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/)：
- [storage.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/storage.py) -- `Session` 数据类（`display_name`, `parent_id` 用于分叉, `compressed`, `agent_config`），通过 `~/.alonechat/sessions/{id}.json` JSON 文件持久化
- [manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/manager.py) -- `SessionManager` 提供：`create_session(display_name)`, `fork_session()`, `set_display_name()`, `set_agent_config()`, `continue_session()`, `resume_session()`, `add_message()`, `list_sessions()`, `delete_session()`

**（B）Gateway 会话系统** -- [gateway/session.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/session.py)：
- 内存中的会话管理（非持久化）
- 会话车道（`acquire_session_lane` / `release_session_lane`）
- 超时清理和过期驱逐

**（C）DeepSeek Context 会话系统** -- [deepseek_optimization/context/session_manager.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/context/session_manager.py)：
- 基于文件的持久化存储（`metadata.json` + `messages.jsonl`）
- `SessionMetadata` 包含 `title`, `tags`, `user_id`
- 搜索、列表、预览、清理过期会话

### 5.3 反馈系统

**ContextFeedbackGenerator** -- [feedback_generator.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/context/feedback_generator.py)：
- `generate_feedback()` -- 生成上下文状态反馈（消息总数、活跃数、归档数、主题索引）
- `generate_detailed_report()` -- 生成详细报告（重要性分布、归档文件列表）
- `_generate_insertion_marker()` -- 生成插入到对话中的标记文本

此反馈系统专注于**上下文管理反馈**，而非用户交互反馈或会话质量反馈。

### 5.4 自动命名

当前没有独立的**自动命名**功能。会话的默认命名规则为：
- **CLI 会话**：`display_name` 为 None 时，使用 `session.id[:8]`（前 8 位 UUID）
- **Gateway 会话**：无默认命名
- **DeepSeek Context 会话**：`title = f"Session {now.strftime('%Y-%m-%d %H:%M')}"`

即目前**没有基于 LLM 的自动会话命名**功能，需要人工通过 `--name` 参数或 `/fork --name` slash 命令设置名称。

---

## 六、技术栈

### Agent-Framework (v0.3.0)

核心依赖见 [pyproject.toml](file:///e:/AloneChat-workspace-master/agent-framework/pyproject.toml)：
- **LLM 交互**：`litellm>=1.40.0`, `openai>=1.6.0`
- **数据结构**：`pydantic>=2.5.0`, `pydantic-settings>=2.1.0`
- **向量存储**：`chromadb>=0.4.22`
- **Token 管理**：`tiktoken>=0.5.0`
- **配置**：`pyyaml>=6.0`
- **网关**：`fastapi>=0.109.0`, `uvicorn>=0.27.0`, `websockets>=12.0`
- **文档处理**：`pdfplumber`, `python-docx`, `openpyxl`, `python-pptx`, `pandas`
- **HTTP 客户端**：`httpx>=0.25.0`

### AloneChat-CLI (v0.2.0)

依赖见 [pyproject.toml](file:///e:/AloneChat-workspace-master/alonechat-cli/pyproject.toml)：
- **CLI 框架**：`click>=8.1.0`
- **终端渲染**：`rich>=13.0.0`
- **加密**：`cryptography>=41.0.0`
- **配置**：`PyYAML>=6.0`, `tomli>=2.0.0`
- 可选：`agent-framework` 作为本地包依赖

### AloneChat-Desktop (v0.1.0)

依赖见 [package.json](file:///e:/AloneChat-workspace-master/alonechat-desktop/package.json)：
- **前端框架**：Next.js 16.2.6 + React 19.2.4
- **UI 组件**：Radix UI（Accordion, Avatar, Dialog, Dropdown, Tabs, Tooltip 等）
- **样式**：Tailwind CSS 4
- **桌面框架**：Tauri 2.11（Rust 后端）
- **构建工具**：TypeScript 5, ESLint 9
- **包管理**：pnpm

---

## 关键发现总结

1. **三个会话系统并行存在**：CLI Session、Gateway Session、DeepSeek Context Session，各有不同的持久化和功能，存在功能重叠
2. **数据存储不一致**：YAML 用于配置，JSON 用于会话数据持久化，未统一
3. **无自动命名功能**：会话命名依赖手动输入，尚无 LLM 自动命名机制
4. **反馈系统局限于上下文管理**：`ContextFeedbackGenerator` 只处理上下文状态反馈，缺少用户对 AI 回复的评分/反馈机制
5. **Memory 系统已有基础抽象**：`BaseMemory` + `ConversationMemory` + `VectorMemory` 架构清晰，可直接复用扩展
6. **CLI 与框架之间的集成**：alonechat-cli 通过 optional dependency 引用 agent-framework，但实际并未深度集成使用

非常好的分析！让我再看一些关键文件的具体实现，以便设计出可靠的方案。

让我继续查看一些关键文件来完善设计。

我已经深入了解了项目架构。现在让我向您展示完整的设计方案。

---

## CLI 加强功能设计方案

基于项目现有架构分析，以下是 6 个功能的设计方案：

### 1. 自动记忆（Auto Memory）`/memory` 管理
- **位置**: 在 `agent-framework/memory/` 中新建 `auto_memory.py`
- **核心**: 继承 `BaseMemory`，新增 `AutoMemory` 类，自动保存交互中的有用上下文
- **存储**: YAML 格式（遵循项目规范）
- **CLI**: 新增 `/memory` slash 命令（list / view / delete / search / clear）
- **数据流**: Chat 循环中自动截取关键信息 → 语义筛选 → 写入 YAML 文件

### 2. 记忆最后修改时间戳
- **位置**: 在 `agent-framework/core/base_memory.py` 的 `MemoryEntry` 中已有 `timestamp` 字段
- **增强**: 新增 `last_modified` 字段 + `freshness_score()` 方法计算新鲜度（0.0~1.0）

### 3. 自动记忆自定义目录 `autoMemoryDirectory`
- **位置**: 在 `agent-framework/configs/cli_enhancements.yaml` 中新增 `auto_memory` 配置节
- **支持**: 用户可通过 `/config` slash 命令或 `--auto-memory-dir` CLI 选项设置

### 4. 会话自动命名
- **位置**: 在 `agent-framework/services/` 中新建 `session_namer.py`
- **核心**: 调用 LLM 根据会话的第一条用户消息或计划内容自动生成简短名称
- **集成**: 在 `SessionManager.create_session()` 中扩展，支持延迟命名

### 5. 会话质量调查
- **位置**: 在 `agent-framework/services/` 中新建 `feedback_survey.py`
- **核心**: 可配置采样率 `feedbackSurveyRate`（0.0~1.0），随机抽检用户满意度
- **存储**: YAML 格式保留调查结果

### 6. 后台智能体保留部分结果
- **位置**: 在 `agent-framework/services/` 中新建 `background_agent_manager.py`
- **核心**: 当终止后台智能体时，将已有结果保存到 `AutoMemory`

---

请问这个方案是否符合您的预期？有没有需要调整的地方？如果没问题，我将开始编写详细的设计文档并推进实现。

## User
`e:\AloneChat-workspace-master\docs\releases\RELEASE_NOTE_v0.2.0.md` 把你写的相关更改写到这个文件里面

## Assistant
好的，我来把刚才设计的 6 个 CLI 加强功能写入发布说明文件。

## User
`e:\AloneChat-workspace-master\docs\releases\RELEASE_NOTE_v0.2.0.md` 把你写的相关更改写到这个文件里面

