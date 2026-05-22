# CLI 功能增强列表

> **Workspace:** e:\AloneChat-workspace-master

---

## User
cli加强：功能 	 版本 	 说明 
 Bash 命令历史自动补全 	 2.1.14 	 在 ! 模式下键入部分命令按 Tab 补全 
 后台 Bash 任务自动后台化 	 2.0.19 	 长时间运行的命令自动后台，可自定义超时 
 后台任务 Ctrl+B 	 2.1.0 	 统一将前台任务后台化 
 任务管理系统（依赖追踪） 	 2.1.16 	 新任务管理，包括依赖追踪 
 LSP 工具 	 2.0.74 	 跳转到定义、查找引用、悬停文档 
 外部编辑器编辑提示词 	 2.0.10 	 按 Ctrl+G 在系统编辑器中编辑 
 后台智能体支持 	 2.0.60 	 代理在用户工作时于后台运行 
 待办事项列表 	 0.2.93 	 Claude 使用 Todo 列表保持组织

## Assistant
Let me first explore the project context to understand what we're working with.

好的，我将全面探索项目结构。让我并行执行多个搜索任务。

现在让我深入探索关键文件和目录内容。

让我继续深入探索关键模块。

让我继续探索更多关键模块。

让我继续查看配置文件和一些更深层的模块。

让我再看看几个关键的agent实现和gateway代码。

让我再检查一下几个剩余的重要文件。

现在我已经收集了足够的信息。以下是完整的项目结构总结：

---

## 项目结构综合分析报告

### 一、顶层目录结构

```
e:\AloneChat-workspace-master/
├── agent-framework/          # 核心Agent框架 (v0.3.0)
├── alonechat-cli/            # CLI命令行工具 (v0.2.0)
├── alonechat-desktop/        # 桌面应用 (Next.js + Tauri)
├── .trae/                    # Trae配置和规则
├── bugs/                     # Bug和安全漏洞记录
├── docs/                     # 文档（研究、技术报告、演示文稿、发布说明）
├── ChatAgent.code-workspace  # VS Code工作区文件
├── Makefile                  # 构建脚本
├── README.md / README_CN.md  # 项目说明
├── generate_docs.py          # 文档生成脚本
└── LICENSE                   # MIT许可
```

**技术栈总结：**
- `agent-framework`: Python >= 3.11, FastAPI, LiteLLM, Pydantic, ChromaDB, PyYAML
- `alonechat-cli`: Python >= 3.10, Click, Rich, httpx, Pydantic, PyYAML
- `alonechat-desktop`: Next.js + Tauri, TypeScript (但规则禁止使用NPM)
- 所有数据存储使用 **YAML** 文件，禁止硬编码

---

### 二、agent-framework 核心框架 (v0.3.0)

位于 [agent-framework](file:///e:/AloneChat-workspace-master/agent-framework)，是整个项目的核心基础库。

#### 2.1 核心架构 - [core/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/)

| 文件 | 职责 |
|------|------|
| [base_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_agent.py) | Agent抽象基类，定义 perceive/plan/act/reflect 生命周期，支持同步和流式执行 |
| [base_llm.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_llm.py) | LLM抽象基类，定义 chat/chat_stream/embedding 接口 |
| [base_tool.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_tool.py) | 工具抽象基类，定义 execute/get_definition 接口 |
| [base_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_memory.py) | 记忆模块抽象基类 |
| [types.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) | **核心类型定义**：AgentState, Message, ToolCall, ToolResult, AgentMode(MTC/CODE), TaskStatus, TaskPriority, FilePermission, ExecutionEnvironment |
| [task.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/task.py) | **任务模型**：Task(含id/description/status/dependencies/priority/metadata), Artifact, Reference |
| [orchestrator.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/orchestrator.py) | **编排器抽象**：run/run_multi/run_workflow，支持WorkflowGraph |
| [agent_bus.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/agent_bus.py) | **Agent消息总线**：支持register/send/broadcast/receive，多Agent通信 |

#### 2.2 Agent实现 - [agent/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/)

| 文件 | 职责 |
|------|------|
| [react_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/react_agent.py) | **ReAct Agent**：Thought-Action-Observation循环，支持工具调用、回调系统 |
| [code_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/code_agent.py) | **CODE模式Agent**：面向开发者，支持代码搜索(SearchSubAgent)、生成、调试、重构 |
| [mtc_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/mtc_agent.py) | **MTC模式Agent**：面向非开发用户，多格式文件处理 |
| [task_planner.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/task_planner.py) | 任务规划器，任务拆解和执行 |
| [multi_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/multi_agent.py) | 多Agent协调 |
| [intent_clarifier.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/intent_clarifier.py) | 意图澄清 |

#### 2.3 沙箱系统 - [sandbox/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/)

| 文件 | 职责 |
|------|------|
| [subprocess_sandbox.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/subprocess_sandbox.py) | **子进程沙箱**：白/黑名单命令验证，资源限制(CPU/内存/输出)，`execute()`和`execute_python()` |
| [enhanced_sandbox.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/enhanced_sandbox.py) | **增强沙箱**：从YAML配置加载命令白名单，支持MTC/CODE双模式，路径验证，文件读写权限控制，执行历史记录 |

**关键能力**：
- 命令白名单/黑名单验证
- 危险参数检查 (`-c`, `--eval` 等)
- 资源限制（CPU时间、内存、输出大小）
- 路径遍历防护 (`validate_path`)
- 文件权限检查 (READ/WRITE/EXECUTE)
- 执行超时控制

#### 2.4 工具系统 - [tools/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/)

| 模块 | 内容 |
|------|------|
| [builtin/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/builtin/) | 内置工具：`calculator`, `current_time`, `web_search` |
| [code/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/code/) | 代码工具：`code_generator`, `code_executor` |
| [mtc/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/mtc/) | MTC工具：`document_tools` |
| [registry.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/registry.py) | 工具注册表 |
| [skills_registry.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_registry.py) | Skills注册表（内置Skill: DocumentGeneration, DataAnalysis, WebResearch, PPTGeneration, ReportGeneration） |
| [skills_cli.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_cli.py) | Skills CLI入口 |
| [skills_marketplace.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_marketplace.py) | Skills市场 |

#### 2.5 服务层 - [services/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/)

| 模块 | 内容 |
|------|------|
| [error_fixer/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/error_fixer/) | 错误修复服务 |
| [file_generators/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/file_generators/) | 文件生成服务 (PPT/Excel/Word/Code) |
| [file_processors/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/file_processors/) | 文件处理器 (code/document/image/presentation/spreadsheet/text) |
| [skills/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/skills/) | Skill执行器和注册表 |
| [task_planner/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/task_planner/) | 任务规划服务 |
| [test_generator/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/test_generator/) | 测试生成服务 |

#### 2.6 其他模块

| 模块 | 内容 |
|------|------|
| [gateway/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/) | **WebSocket网关**：GatewayCore, MessageRouter, ToolExecutor, Auth, Session管理, MCP API (端口18789) |
| [llm/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/llm/) | LLM实现 (LiteLLMProvider) |
| [memory/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/memory/) | 记忆管理 (conversation_memory, vector_memory) |
| [rag/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/rag/) | RAG检索 (code_indexer, embedding, retriever, pipeline) |
| [observability/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/observability/) | 可观测性 (logger, metrics, tracer) |
| [orchestration/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/orchestration/) | 工作流编排 (DAG, parallel, sequential) |
| [deepseek_optimization/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/) | DeepSeek优化 (缓存、上下文压缩、MCP市场、安全) |
| [configs/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/) | **YAML配置文件**：prompts.yaml, models.yaml, sandbox.yaml, skills.yaml, intent_clarification.yaml |
| [config.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/config.py) | 配置管理：AgentConfig（Pydantic BaseSettings），支持YAML/JSON加载、热加载(watchfiles) |

#### 2.7 YAML配置结构

- **sandbox.yaml**: MTC/CODE双模式命令白名单、禁止命令、危险参数、环境变量、权限
- **skills.yaml**: 5个内置Skill配置（document_generation, data_analysis, web_research, ppt_generation, report_generation）
- **prompts.yaml**: 所有系统提示词和模板
- **models.yaml**: DeepSeek/OpenAI模型配置
- **intent_clarification.yaml**: 意图澄清规则和模板

---

### 三、alonechat-cli 命令行工具 (v0.2.0)

位于 [alonechat-cli](file:///e:/AloneChat-workspace-master/alonechat-cli)，是用户直接使用的CLI工具。

#### 3.1 CLI入口 - [cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/cli.py)

基于 **Click** 框架，入口命令：`alonechat`

```
alonechat [OPTIONS] [QUERY] COMMAND [ARGS]...
```

**全局选项：**
- `-p/--print`: 打印模式（非交互）
- `-C/--continue`: 继续最近会话
- `-r/--resume`: 恢复指定会话
- `--output-format`: text/json/stream-json
- `-m/--model`: 指定模型
- `--name`: 设置会话显示名称
- `--agent`: 覆盖代理设置
- `--auto-compact`: 自动压缩对话

**子命令：**

| 命令 | 文件 | 功能 |
|------|------|------|
| `init` | [commands/init.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/init.py) | 初始化项目配置 |
| `chat` | [commands/chat.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/chat.py) | 启动交互式对话（DeepSeek V4 Flash） |
| `generate` | [commands/generate.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/generate.py) | 代码生成 |
| `test` | [commands/test.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/test.py) | 自动测试 |
| `commit` | [commands/commit.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/commit.py) | 智能提交 |
| `mcp` | [mcp/cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/mcp/cli.py) | MCP服务器管理 |
| `agent` | [commands/agent.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/agent.py) | **集成agent-framework的命令** |

#### 3.2 agent命令（直接调用agent-framework）

[commands/agent.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/agent.py) 是CLI与agent-framework的**桥接层**，包含：

| 子命令 | 功能 | 调用的agent-framework模块 |
|--------|------|--------------------------|
| `agent task` | 任务规划执行 | `services.task_planner.TaskPlanner` |
| `agent process` | 文件处理 | `services.file_processors.get_processor` |
| `agent fix` | 错误修复 | `services.error_fixer.ErrorFixer` |
| `agent skill` | Skills管理 | `tools.skills_registry.SkillsRegistry` |
| `agent rag` | RAG检索 | `rag.RAGPipeline` |
| `agent generate` | 文件生成(ppt/excel/report/doc) | `services.file_generators.FileGeneratorService` |
| `agent analyze` | 数据分析 | `services.file_generators.FileGeneratorService` |

#### 3.3 Slash命令系统

[slash/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/) 提供了完整的斜杠命令框架：

| 组件 | 文件 | 功能 |
|------|------|------|
| 注册表 | [registry.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/registry.py) | SlashCommand注册、查找、补全、分类 |
| 解析器 | [parser.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/parser.py) | 命令解析 |
| 执行器 | [executor.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/executor.py) | 命令分发执行，注册19个内置命令 |
| 自定义加载 | [custom_loader.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/custom_loader.py) | 自定义命令加载 |

**内置Slash命令（19个）：**
- **general**: `help`
- **session**: `clear`, `compact`, `fork`, `rewind`, `branch`
- **settings**: `config`, `model`, `permissions`
- **info**: `cost`, `status`, `usage`
- **agents**: `agents`
- **actions**: `review`
- **integrations**: `mcp`
- **project**: `init`
- **debug**: `doctor`
- **editor**: `vim`
- 以及 `clear`, `agent`, `permissions` 等

#### 3.4 权限系统 - [permissions/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/)

| 文件 | 功能 |
|------|------|
| [rules.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/rules.py) | 权限规则定义：PermissionMode(ACCEPT/PLAN/REVIEW/DEFAULT)，工具描述(Read/Write/Edit/Delete/Bash等) |
| [manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/manager.py) | 权限管理器：加载/保存权限配置，检查工具是否允许，通配符匹配 |

**默认允许的工具：** Read, Glob, Grep, LS
**默认禁止的工具：** 无

#### 3.5 其他模块

| 模块 | 内容 |
|------|------|
| [config/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/config/) | 配置管理器 |
| [configs/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/) | YAML配置文件：code_config.yaml, deepseek_config.yaml, git_config.yaml, chinese_config.yaml, utils_config.yaml |
| [models/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/models/) | 模型路由和响应 |
| [session/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/) | 会话管理(manager, storage) |
| [context/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/context/) | 上下文管理 |
| [git/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/git/) | Git操作 (git_manager, smart_commit) |
| [deepseek/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/deepseek/) | DeepSeek集成 (context_manager, encryption, prompt_engineer) |
| [mcp/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/mcp/) | MCP协议支持 (cli, config) |
| [utils/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/utils/) | 工具函数 (interactive, logger, progress) |
| [chinese/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/chinese/) | 中文NLP (code_style, nlp) |

---

### 四、项目规则 (.trae/rules/acw.md)

规则文件 [acw.md](file:///e:/AloneChat-workspace-master/.trae/rules/acw.md) 定义了以下强制规则：

1. **禁止使用NPM** - 所有项目不得依赖npm
2. **禁止硬编码** - 全部数据使用YAML存储
3. **全部注释使用中英双语**
4. **代码复用原则** - 如果agent-framework已实现的功能，直接套用，不再重复实现；未实现的在agent-framework中实现

---

### 五、关于任务管理、Shell命令处理和后台任务的总结

#### 现有任务管理
- **agent-framework**: [task.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/task.py) 定义了Task模型（含id/status/priority/dependencies/created_at等），[task_planner.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/task_planner.py) 和 [services/task_planner/](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/task_planner/) 提供任务拆解和执行能力
- **CLI**: [commands/agent.py - `task`子命令](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/agent.py#L44-L128) 封装了TaskPlanner的调用

#### 现有Shell命令处理
- **agent-framework/sandbox/**: 两个沙箱实现提供命令执行能力，通过白名单验证和路径保护确保安全
- **CLI**: 目前CLI层级没有直接的shell命令执行功能，所有命令执行都通过agent-framework的沙箱

#### 后台任务
- 目前项目中**没有**独立的后台任务管理模块。`gateway/core.py` 运行WebSocket服务器（`asyncio.Future()`永久运行），但这不是通用后台任务系统
- `orchestrator.py` 定义了编排器抽象（run/run_multi/run_workflow），但偏重Agent执行流而非独立后台任务
- 配置热加载使用了 `watchfiles` 的 `awatch` 来实现文件监控

---

### 六、关键架构关系图

```
alonechat CLI (click + rich)
    │
    ├── commands/ (init, chat, generate, test, commit)
    │   └── chat ─── run_chat_loop() ─── ModelRouter (DeepSeek)
    │   └── agent ─── 桥接层，调用 agent-framework 的功能
    │
    ├── slash/ (19个内置slash命令)
    ├── permissions/ (工具权限管理)
    └── session/ (会话管理)
    
agent-framework (核心框架)
    │
    ├── core/ (base_agent, base_llm, base_tool, types, task, orchestrator)
    ├── agent/ (react_agent, code_agent, mtc_agent, multi_agent)
    ├── sandbox/ (subprocess_sandbox + enhanced_sandbox)
    ├── tools/ (builtin, code, mtc, registry, skills_registry)
    ├── services/ (task_planner, error_fixer, file_generators, file_processors, skills)
    ├── gateway/ (WebSocket网关，端口18789)
    ├── rag/ (RAG检索)
    ├── memory/ (对话/向量记忆)
    ├── llm/ (LiteLLMProvider)
    ├── configs/ (所有YAML配置)
    └── config.py (Pydantic配置管理，支持热加载)
```

我已经深入了解了项目结构。项目主要由两部分组成：

1. **agent-framework** (v0.3.0) - 核心 Python Agent 框架，提供 Task 模型、沙箱执行、工具系统等
2. **alonechat-cli** (v0.2.0) - 基于 Click 的 CLI 工具，通过 `agent` 命令桥接 agent-framework

现在我需要先了解您的具体需求。让我问第一个问题：

好的，全部实现！在深入设计之前，让我先仔细查看现有代码中与这些功能相关的部分，特别是交互循环、任务管理等方面。

Let me check a few more key files to understand the existing capabilities better.

现在我对项目有了全面了解。让我开始问一些关键问题来明确需求。

好的，全部推进！现在让我提出架构方案。

根据对项目的深入分析，我将这8个功能分为 **4个功能组**，并提出 **3种架构方案**：

---

## 功能分组

| 分组 | 功能 | 说明 |
|------|------|------|
| **A. 输入体验升级** | ①历史补全 ⑥外部编辑器 ③Ctrl+B快捷键 | 依赖 prompt_toolkit 替换 Rich.Prompt |
| **B. 后台执行系统** | ②自动后台化 ③Ctrl+B后台 ⑦后台智能体 | 新建后台任务管理器 |
| **C. 任务管理系统** | ④依赖追踪 ⑧待办列表 | 增强 agent-framework 的 Task 模型 |
| **D. LSP工具** | ⑤跳转定义/查找引用/悬停 | 新建 LSP 客户端模块 |

---

## 方案一：单体增强（简单直接）

将所有功能直接嵌入现有的 `chat.py` 和 `commands/agent.py`，使用条件分支控制功能开关。

- **优点**：改动最小，快速实现
- **缺点**：`chat.py` 将膨胀到 500+ 行，难以维护；功能耦合严重

## 方案二：模块化 + 服务层（推荐 ✅）

创建独立的功能模块，通过清晰的接口与 chat 循环交互：

```
alonechat-cli/src/alonechat/
├── enhanced_input/       # Group A: prompt_toolkit 输入系统
│   ├── input_handler.py  # 键盘事件管理 (Ctrl+B/G/Tab)
│   ├── history.py        # Bash历史补全
│   └── external_editor.py# 外部编辑器集成
├── background/           # Group B: 后台执行系统
│   ├── manager.py        # 后台任务管理器
│   └── agent_runner.py   # 后台智能体运行器
├── task_manager/         # Group C: 任务管理 (包装agent-framework)
│   ├── manager.py        # 任务依赖追踪
│   └── todo.py           # 待办事项列表
├── lsp/                  # Group D: LSP工具
│   └── client.py         # LSP客户端 (跳转/引用/悬停)
└── commands/
    └── chat.py           # 改造为使用 enhanced_input
```

- **优点**：符合项目现有模块化风格；各功能可独立测试；容易维护
- **缺点**：初期需要搭建更多文件

## 方案三：插件式架构

将每个功能设计为可插拔的插件，通过事件系统与核心交互循环通信。

- **优点**：最灵活，可动态加载/卸载功能
- **缺点**：过度设计，8个功能不需要这种复杂度；增加不必要的抽象层

---

**我推荐方案二**，原因：
1. 与项目现有架构风格一致（看 `slash/`, `permissions/`, `session/` 等模块都是独立目录）
2. `agent-framework` 已经提供了 Task 模型和 Sandbox 执行能力，直接增强包装即可
3. 功能之间有清晰的边界，便于逐步实现和测试

您觉得方案二可以吗？或者有其他想法？

## User
方案二

## Assistant
好的！方案二得到确认，现在我来逐部分呈现详细设计。先从**最核心的部分**开始。

好，现在我有了全面的了解。让我正式提出分区设计。

---

## 整体架构设计

### 核心原则

根据项目规则，先判断哪些实现属于 **agent-framework 层**（核心能力），哪些属于 **alonechat-cli 层**（CLI 交互呈现）：

| 层级 | 存放内容 |
|------|---------|
| **agent-framework** | 后台任务调度引擎、任务依赖追踪引擎、LSP客户端核心 |
| **alonechat-cli** | prompt_toolkit 输入系统、历史管理、Todo列表UI、快捷键绑定、外部编辑器集成 |

---

### 第一部分：输入系统改造 (Group A)

**现状问题**：`chat.py` 使用 Rich 的 `Prompt.ask()`，无法捕获键盘事件。

**设计**：用 prompt_toolkit 替换 Rich.Prompt，创建 `EnhancedInputSession`：

```
alonechat-cli/src/alonechat/
├── input/                        # ← 新建目录
│   ├── __init__.py
│   ├── session.py               # EnhancedInputSession - 统一的输入会话
│   │   - 包装 prompt_toolkit.PromptSession
│   │   - 注册全局快捷键 (Ctrl+B, Ctrl+G, Tab补全)
│   │   - 支持 ! 模式历史搜索
│   ├── key_bindings.py           # 键盘绑定定义
│   │   - handle_ctrl_b() → 后台化当前任务
│   │   - handle_ctrl_g() → 打开外部编辑器
│   │   - handle_tab() → Slash命令补全 / !历史补全
│   │   - handle_bang() → 检测 ! 前缀切换到历史搜索模式
│   ├── history.py                # Bash命令历史管理
│   │   - YAML文件存储 (~/.alonechat/history.yaml)
│   │   - 历史搜索/过滤/补全
│   │   - 会话间共享
│   └── external_editor.py        # 外部编辑器集成
│       - 检测 $EDITOR / $VISUAL
│       - Windows: notepad / 用户配置编辑器
│       - 临时文件创建/编辑/读取
```

**chat.py 改造**：
- `run_chat_loop()` 中的 `Prompt.ask()` → 替换为 `EnhancedInputSession.prompt()`
- 保留所有现有逻辑（slash命令处理、消息循环等）

**数据流**：
```
用户输入
  → EnhancedInputSession.prompt()
    → key_bindings.py 处理快捷键
    → /命令 → process_slash_command() [保持现有逻辑]
    → !历史 → history.py 搜索 + Tab 补全
    → Ctrl+G → external_editor.py 打开编辑器
    → Ctrl+B → background/manager.py 后台化
  → 常规输入 → [现有消息处理逻辑]
```

这部分设计是否合理？如果没问题，我继续讲 Group B（后台执行系统）。

## User
合计，继续执行

## User
合计，继续执行

## Assistant
好的，继续设计 **Group B：后台执行系统**。

---

### 第二部分：后台执行系统 (Group B)

**功能目标**：
- ② 长时间命令自动后台化
- ③ Ctrl+B 手动将前台任务后台化
- ⑦ 后台智能体支持（用户工作时后台运行 Agent）

**设计原则**：核心调度引擎放 **agent-framework**，CLI 层只做交互触发和状态展示。

```
agent-framework/agent_framework/
├── background/                   # ← 新建目录
│   ├── __init__.py
│   ├── scheduler.py              # 后台任务调度器（核心引擎）
│   │   - 任务队列 (asyncio.Queue)
│   │   - 工作线程池 (asyncio.TaskGroup)
│   │   - 任务状态追踪
│   │   - 超时检测与自动后台化
│   ├── task_wrapper.py           # 后台任务包装器
│   │   - 包装 Agent 执行 / Shell 命令 / 任意协程
│   │   - 进度回调 / 状态变更通知
│   ├── agent_runner.py           # 后台智能体运行器
│   │   - 独立的 Agent 实例管理
│   │   - 与主会话隔离的上下文
│   │   - 结果收集与通知
│   └── types.py                  # 类型定义
│       - BackgroundTaskStatus (pending/running/completed/failed)
│       - BackgroundTask (id, status, started_at, completed_at, result)
│       - TaskResult (stdout, stderr, artifacts, summary)

alonechat-cli/src/alonechat/
├── background/                   # ← 新建目录
│   ├── __init__.py
│   ├── manager.py                # CLI层后台任务管理器
│   │   - 封装 agent-framework.background.scheduler
│   │   - 任务列表展示
│   │   - 任务状态轮询
│   ├── display.py                # 后台任务状态展示
│   │   - Rich Live 实时状态面板
│   │   - 任务进度条
│   └── config.yaml               # 后台任务配置
│       - auto_background_timeout: 30  # 超过30秒自动后台化
│       - max_concurrent_tasks: 5
│       - notification: true
```

**核心类设计**：

```python
# agent-framework/agent_framework/background/scheduler.py

class BackgroundScheduler:
    """
    后台任务调度器 / Background Task Scheduler
    单例模式，全局唯一实例
    """
    _instance: Optional["BackgroundScheduler"] = None
    
    def __init__(self, max_concurrent: int = 5):
        self._queue: asyncio.Queue[BackgroundTask] = asyncio.Queue()
        self._tasks: Dict[str, BackgroundTask] = {}
        self._workers: List[asyncio.Task] = []
        self._max_concurrent = max_concurrent
        self._running = False
    
    @classmethod
    def get_instance(cls) -> "BackgroundScheduler":
        """获取单例实例 / Get singleton instance"""
        ...
    
    async def start(self) -> None:
        """启动调度器 / Start scheduler"""
        ...
    
    async def submit(
        self,
        coro: Coroutine,
        name: str,
        timeout: Optional[int] = None,
        on_complete: Optional[Callable] = None,
    ) -> str:
        """提交后台任务 / Submit background task"""
        ...
    
    async def submit_agent(
        self,
        agent: "BaseAgent",
        query: str,
        on_complete: Optional[Callable] = None,
    ) -> str:
        """提交后台智能体任务 / Submit background agent task"""
        ...
    
    def get_status(self, task_id: str) -> Optional[BackgroundTaskStatus]:
        """获取任务状态 / Get task status"""
        ...
    
    def list_tasks(self) -> List[BackgroundTask]:
        """列出所有任务 / List all tasks"""
        ...
    
    async def cancel(self, task_id: str) -> bool:
        """取消任务 / Cancel task"""
        ...
```

**自动后台化逻辑**：

```python
# alonechat-cli/src/alonechat/background/manager.py

class BackgroundManager:
    """
    CLI层后台任务管理 / CLI Background Task Manager
    """
    
    AUTO_BACKGROUND_TIMEOUT = 30  # 默认30秒
    
    async def execute_with_auto_background(
        self,
        coro: Coroutine,
        name: str,
        timeout_threshold: int = AUTO_BACKGROUND_TIMEOUT,
    ) -> Tuple[bool, Any]:
        """


## User
不是设计，是开发

## Assistant
明白！用户希望直接进入开发阶段。让我快速完成设计文档，然后立即开始实现。

好的，直接开始开发！我将按照方案二的架构实现这8个功能。

首先，让我添加必要的依赖并创建模块结构：

现在开始实现！首先添加依赖并创建模块结构：

现在创建核心模块。首先创建 **input/** 模块（输入系统）：

现在创建 **background/** 模块（后台执行系统）：

现在增强 **agent-framework** 的任务管理（依赖追踪）。先查看现有结构：

现在在 **agent-framework** 中创建增强的任务管理模块（依赖追踪）：

现在创建 **lsp/** 模块（LSP工具）：

现在创建 **todo/** 模块（待办事项列表）：

现在更新 **chat.py** 集成新的输入系统：

现在创建配置文件：

## 实现完成！

我已经完成了全部 8 个 CLI 增强功能的实现。以下是创建的文件和功能总结：

---

### 📁 新增文件结构

```
alonechat-cli/src/alonechat/
├── input/                          # Group A: 输入系统
│   ├── __init__.py
│   ├── session.py                  # EnhancedInputSession (prompt_toolkit)
│   ├── history.py                  # 命令历史管理 (YAML存储)
│   ├── key_bindings.py             # 快捷键绑定 (Ctrl+B, Ctrl+G)
│   └── external_editor.py          # 外部编辑器集成
│
├── background/                     # Group B: 后台执行系统
│   ├── __init__.py
│   ├── manager.py                  # BackgroundManager (后台任务管理器)
│   ├── task.py                     # BackgroundTask 模型
│   └── agent_runner.py             # BackgroundAgentRunner (后台智能体)
│
├── todo/                           # Group C: 待办事项
│   ├── __init__.py
│   ├── item.py                     # TodoItem 模型
│   └── manager.py                  # TodoManager (YAML存储)
│
├── lsp/                            # Group D: LSP工具
│   ├── __init__.py
│   ├── client.py                   # LSPClient (语言服务器客户端)
│   └── features.py                 # 跳转定义/查找引用/悬停文档
│
└── configs/
    └── cli_enhanced.yaml           # 功能配置文件

agent-framework/agent_framework/services/
└── task_manager/                   # Group C: 任务管理 (依赖追踪)
    └── __init__.py                 # TaskManager, TaskDependencyGraph
```

---

### ✅ 实现的功能对照

| 功能 | 版本 | 实现位置 |
|------|------|---------|
| **① Bash 命令历史自动补全** | 2.1.14 | [input/history.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/input/history.py) - `!` 模式 + Tab 补全 |
| **② 后台 Bash 任务自动后台化** | 2.0.19 | [background/manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/background/manager.py) - 超时自动后台 |
| **③ 后台任务 Ctrl+B** | 2.1.0 | [input/key_bindings.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/input/key_bindings.py) - 快捷键后台化 |
| **④ 任务管理系统（依赖追踪）** | 2.1.16 | [agent-framework/services/task_manager](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/services/task_manager/__init__.py) - DAG依赖图 |
| **⑤ LSP 工具** | 2.0.74 | [lsp/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/lsp) - 跳转定义/查找引用/悬停 |
| **⑥ 外部编辑器编辑提示词** | 2.0.10 | [input/external_editor.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/input/external_editor.py) - Ctrl+G |
| **⑦ 后台智能体支持** | 2.0.60 | [background/agent_runner.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/background/agent_runner.py) |
| **⑧ 待办事项列表** | 0.2.93 | [todo/](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/todo) - TodoManager |

---

### 🔧 关键改动

1. **pyproject.toml** - 添加了 `prompt_toolkit>=3.0.0` 依赖
2. **chat.py** - 集成了 `EnhancedInputSession`，支持快捷键和后台任务
3. **agent-framework/services/__init__.py** - 导出了新的 `TaskManager`

---

### 📝 使用方式

```bash
# 安装依赖
pip install prompt_toolkit

# 启动交互模式
alonechat chat

# 快捷键:
# - Ctrl+B: 将当前输入后台化
# - Ctrl+G: 打开外部编辑器编辑输入
# - !<command>: 搜索历史命令 (Tab 补全)
# - !!: 执行上一条命令
```

所有数据均使用 **YAML 文件** 持久化存储，符合项目规则！

## User
把你做的更改写到这个文件里面 `e:\AloneChat-workspace-master\docs\releases\RELEASE_NOTE_v0.2.1.md`

## Assistant
已更新发布说明文件！新增内容包括：

### 📝 新增的 8 个功能文档

1. **⌨️ Bash 命令历史自动补全** (v2.1.14) - `!` 模式 + Tab 补全
2. **🔄 后台 Bash 任务自动后台化** (v2.0.19) - 超时自动后台
3. **⏯️ 后台任务 Ctrl+B** (v2.1.0) - 快捷键后台化
4. **📋 任务管理系统（依赖追踪）** (v2.1.16) - DAG 依赖图
5. **🔍 LSP 工具** (v2.0.74) - 跳转定义/查找引用/悬停
6. **📝 外部编辑器编辑提示词** (v2.0.10) - Ctrl+G
7. **🤖 后台智能体支持** (v2.0.60) - 后台 Agent 运行
8. **✅ 待办事项列表** (v0.2.93) - TodoManager

### 📋 新增章节

- **快捷键表格** - 列出 Ctrl+B、Ctrl+G、Tab、! 等快捷键
- **功能对标表** - 新增 8 项功能的状态追踪
- **文件变更列表** - 详细列出所有新增和修改的文件

文档已保存到 [RELEASE_NOTE_v0.2.1.md](file:///e:/AloneChat-workspace-master/docs/releases/RELEASE_NOTE_v0.2.1.md)。

