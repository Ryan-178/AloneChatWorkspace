# CLI 功能增强

> **Workspace:** e:\AloneChat-workspace-master

---

## User
cli加强：功能 	 版本 	 说明 
 --worktree 标志 	 2.1.49 	 在隔离的 Git 工作树中启动 Claude 
 工作树稀疏检出 	 2.1.76 	 worktree.sparsePaths 仅检出需要的目录 
 从 --add-dir 加载技能/插件 	 2.1.45 	 支持从附加目录读取 enabledPlugins 等 
 支持从 --add-dir 加载 CLAUDE.md 	 2.1.20 	 需要 CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 
 嵌套技能自动发现 	 2.1.6 	 从嵌套的 .claude/skills 目录中自动发现技能 
 .claude/rules/ 支持 	 2.0.64 	 存放条件性加载的规则文件 
 CLAUDE.md 支持导入其他文件 	 0.2.107 	 使用 @path/to/file.md 导入

## Assistant
以下是 `E:\AloneChat-workspace-master` 项目的全面代码库结构总结。

---

## 项目概览

**AloneChat Workspace** 是一个集成了实时聊天应用与生产级 AI Agent 框架的全栈协作平台。项目 MIT 许可，GitHub 地址为 `https://github.com/Ryan-178/AloneChatWorkspace`。

---

## 顶级目录结构

| 目录/文件 | 用途 |
|---|---|
| `agent-framework/` | Python AI Agent 核心框架（v0.3.0） |
| `alonechat-cli/` | Python CLI 工具（v0.2.0），CLI 用户交互层 |
| `alonechat-desktop/` | Tauri + Next.js 桌面应用 |
| `chat-app/` | 实时聊天应用（FastAPI 后端 + Next.js 前端）-- 注意：从 README 可知存在，但实际磁盘上未出现 |
| `docs/` | 文档：指南、技术报告、版本发布说明、安全审计、市场调研 |
| `bugs/` | Bug 跟踪和安全漏洞报告 |
| `.trae/` | Trae IDE 配置：`rules/`（工作区规则）、`documents/`（实施计划）、`specs/`（功能规格说明） |
| `Makefile` | 构建脚本（`make install`、`make dev`、`make test` 等） |
| `README.md` / `README_CN.md` | 项目说明（中英文） |
| `LICENSE` | MIT 许可证 |

---

## 1. agent-framework/ -- AI Agent 核心框架

**版本**: v0.3.0 | **语言**: Python >= 3.11 | **构建系统**: setuptools

这是整个项目的核心库。CLI 和其他组件均在其基础上构建，绝不在已有实现的情况下重复造轮子。

### 架构分层

```
agent-framework/
├── agent_framework/
│   ├── core/                 # 核心抽象层（基类、类型）
│   │   ├── base_llm.py       # LLM 抽象
│   │   ├── base_agent.py     # Agent 抽象
│   │   ├── base_tool.py      # 工具抽象
│   │   ├── base_memory.py    # 记忆抽象
│   │   ├── orchestrator.py   # 编排器 + 工作流图
│   │   ├── agent_bus.py      # Agent 消息总线
│   │   ├── task.py           # 任务模型
│   │   └── types.py          # 通用类型
│   ├── agent/                # Agent 实现（4种类型）
│   │   ├── react_agent.py    # ReAct 模式 Agent
│   │   ├── multi_agent.py    # 多 Agent 团队（顺序/投票）
│   │   ├── mtc_agent.py      # MTC Agent（面向非开发用户）
│   │   ├── code_agent.py     # Code Agent（面向开发用户）
│   │   ├── intent_clarifier.py  # 意图澄清
│   │   └── task_planner.py   # 任务规划器
│   ├── gateway/              # Agent 网关层（FastAPI）
│   │   ├── agent.py          # 网关 Agent 核心
│   │   ├── api.py            # REST API
│   │   ├── websocket.py      # WebSocket 端点
│   │   ├── router.py         # 路由
│   │   ├── session.py        # 会话管理
│   │   ├── auth.py           # 认证
│   │   ├── tools.py          # 工具执行器
│   │   ├── mcp_api.py        # MCP API
│   │   ├── user_api.py       # 用户 API
│   │   └── types.py          # 网关类型
│   ├── llm/                  # LLM 提供商
│   │   ├── litellm_provider.py   # LiteLLM 统一接口
│   │   └── __init__.py
│   ├── memory/               # 记忆系统
│   │   ├── conversation_memory.py  # 对话记忆
│   │   └── vector_memory.py        # 向量记忆
│   ├── rag/                  # RAG 检索系统
│   │   ├── pipeline.py       # RAG 流水线
│   │   ├── embedding.py      # 嵌入
│   │   ├── retriever.py      # 检索器
│   │   ├── splitter.py       # 分块器
│   │   ├── loader.py         # 加载器
│   │   ├── code_indexer.py   # 代码索引器
│   │   └── local_embedding.py # 本地嵌入
│   ├── tools/                # 工具系统
│   │   ├── registry.py       # 工具注册中心
│   │   ├── builtin/          # 内置工具（计算器、时间、网页搜索）
│   │   ├── code/             # 代码工具（code_tools.py）
│   │   ├── mtc/              # MTC 工具（document_tools.py）
│   │   ├── skills_cli.py         # Skills CLI 入口
│   │   ├── skills_registry.py    # Skills 注册中心
│   │   ├── skills_marketplace.py # Skills 市场
│   │   └── skills_sh_client.py   # skills.sh 客户端
│   ├── services/             # 服务层
│   │   ├── task_planner/     # 任务规划服务
│   │   ├── test_generator/   # 测试生成服务
│   │   ├── error_fixer/      # 错误修复服务
│   │   ├── file_generators/  # 文件生成服务
│   │   ├── file_processors/  # 文件处理服务（文档、代码、图片、演示文稿、电子表格）
│   │   └── skills/           # Skills 执行服务
│   ├── orchestration/        # 编排系统
│   │   ├── sequential.py     # 顺序编排
│   │   ├── parallel.py       # 并行编排
│   │   └── dag.py            # DAG 工作流编排
│   ├── deepseek_optimization/ # DeepSeek 百万级上下文优化
│   │   ├── cache/            # 语义缓存、向量缓存
│   │   ├── context/          # 上下文压缩、窗口管理、消息排序
│   │   ├── llm/              # DeepSeek LLM 提供商
│   │   ├── mcp_marketplace/  # MCP 市场（客户端、配置、加载器、管理器、注册中心、适配器）
│   │   ├── security/         # 审计日志、数据保护、加密、许可证管理
│   │   └── swe/              # SWE 引擎
│   ├── sandbox/              # 沙箱执行
│   │   ├── subprocess_sandbox.py
│   │   └── enhanced_sandbox.py
│   ├── security/             # 安全模块（限流器）
│   ├── observability/        # 可观测性（日志、指标、追踪）
│   ├── channels/             # 通道（base.py、chat_app.py）
│   └── configs/              # YAML 配置
│       ├── models.yaml
│       ├── prompts.yaml
│       ├── skills.yaml
│       ├── sandbox.yaml
│       └── intent_clarification.yaml
├── config.yaml               # 框架级配置（LLM、记忆、网关、日志、MCP）
├── gateway_main.py           # 网关启动入口
├── pyproject.toml
└── tests/                    # 12 个测试文件
```

### 关键依赖
- `litellm` -- 统一 LLM 接口
- `chromadb` -- 向量数据库
- `fastapi` + `uvicorn` + `websockets` -- 网关
- `unstructured` / `pdfminer` / `python-docx` / `openpyxl` / `python-pptx` -- 文档处理
- `networkx` -- DAG 工作流编排

---

## 2. alonechat-cli/ -- CLI 工具

**版本**: v0.2.0 | **语言**: Python >= 3.10 | **框架**: Click + Rich

这是面向用户的命令行界面层。它作为轻量级封装，将核心功能委托给 `agent-framework`。

### CLI 命令结构

```
alonechat                          # 主入口（Click group）
├── init                           # 初始化配置
├── chat                           # 交互式对话
├── generate                       # 代码生成
├── test                           # 自动测试
├── commit                         # 智能 Git 提交
├── mcp                            # MCP 服务器管理
└── agent                          # Agent 功能（集成 agent-framework）
    ├── task                       # 任务规划与执行
    ├── multi                      # 多 Agent 协作
    ├── process                    # 文件处理
    ├── fix                        # 错误修复
    ├── generate                   # 文件生成
    ├── docs                       # 文档生成
    └── rag                        # RAG 检索命令
```

### 源代码结构

```
alonechat-cli/src/alonechat/
├── cli.py                   # 主入口，Click group 定义
├── commands/                # Click 命令实现
│   ├── init.py              # 初始化
│   ├── chat.py              # 交互式对话
│   ├── generate.py          # 代码生成
│   ├── test.py              # 测试
│   ├── commit.py            # Git 提交
│   └── agent.py             # Agent 命令（集成 agent-framework）
├── slash/                   # Slash 命令系统（/help, /clear 等）
│   ├── registry.py
│   ├── executor.py
│   ├── parser.py
│   └── commands/            # 14 个内置 slash 命令
├── config/                  # 配置管理
├── configs/                 # YAML 配置文件（5个）
│   ├── chinese_config.yaml
│   ├── code_config.yaml
│   ├── deepseek_config.yaml
│   ├── git_config.yaml
│   └── utils_config.yaml
├── session/                 # 会话管理器 + 存储
├── models/                  # 模型路由
├── context/                 # 上下文管理器
├── agents/                  # Agent 定义/执行器/管理器
├── mcp/                     # MCP CLI 交互
├── git/                     # Git 集成（智能提交、分支、回滚）
├── execution/               # 代码执行
├── deepseek/                # DeepSeek 特定功能
├── permissions/             # 权限管理（规则、管理器、提示词）
├── utils/                   # 进度显示、日志、交互式会话
└── code/                    # 代码生成器
```

### CLI 关键特性
- 会话管理（恢复、继续、命名会话）
- 打印模式（`-p`，非交互式查询）
- 输出格式（text / json / stream-json）
- 自动对话压缩（`--auto-compact`）
- 代理配置覆盖（`--agent key=value`）
- 14 个 slash 命令（`/help`、`/clear`、`/compact`、`/model`、`/status` 等）

### 与 agent-framework 的集成（来自 INTEGRATION.md）
- **原则**: CLI 仅负责用户交互，核心功能调用 agent-framework
- **复用率**: CLI 约 500 行封装代码，复用 agent-framework 的 15,000+ 行
- **节省**: 约 70% 的开发时间

---

## 3. alonechat-desktop/ -- 桌面应用

Tauri + Next.js 桌面壳。

```
alonechat-desktop/
├── app/                  # Next.js App Router（layout.tsx、page.tsx）
├── src-tauri/            # Tauri Rust 后端
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs
│   ├── tauri.conf.json
│   └── Cargo.toml
└── package.json          # 仅有的 package.json（Next.js 依赖）
```

---

## 4. 工作区规则（.trae/rules/acw.md）

该规则文件 [acw.md](file:///e:/AloneChat-workspace-master/.trae/rules/acw.md) 规定了关键约束：

1. **禁止使用 NPM**
2. **禁止硬编码** -- 全部数据使用 YAML 存储
3. **全部注释使用中英双语**
4. **代码复用优先** -- 如果 agent-framework 已实现某功能，必须复用而非重写；若未实现，则在 agent-framework 中实现

---

## 5. 关于 worktree / sparse / rules 实现

- **Git worktree**: 项目中未发现专门的 worktree 实现。仅 [git_manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/git/git_manager.py) 提供基础 Git 操作（创建分支、回滚、智能提交）。
- **Sparse checkout**: 未发现相关实现。
- **Rules 引擎**: [permissions/rules.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/rules.py) 实现了一个工具权限规则系统，定义了默认允许/拒绝的工具列表（Read、Glob、Grep、LS、Write、Edit、Delete、Bash 等）及其中文描述。

---

## 6. 关键 YAML 配置文件

| 文件 | 用途 |
|---|---|
| `agent-framework/config.yaml` | 框架全局配置（LLM、记忆、网关、日志、MCP） |
| `agent-framework/agent_framework/configs/models.yaml` | 模型配置 |
| `agent-framework/agent_framework/configs/prompts.yaml` | 提示词模板 |
| `agent-framework/agent_framework/configs/skills.yaml` | Skills 配置 |
| `agent-framework/agent_framework/configs/sandbox.yaml` | 沙箱配置 |
| `alonechat-cli/src/alonechat/configs/deepseek_config.yaml` | DeepSeek 配置 |
| `alonechat-cli/src/alonechat/configs/git_config.yaml` | Git 配置 |

---

## 总结

AloneChat Workspace 采用**分层架构**：

```
AloneChat Desktop (Tauri + Next.js)
        ↓
AloneChat CLI (Click + Rich)   ← 用户交互层
        ↓
Agent Framework (FastAPI + LiteLLM + ChromaDB)  ← 核心功能层
```

- **CLI 代码**: 集中在 `alonechat-cli/src/alonechat/`，主要文件是 [cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/cli.py)（273 行）及其下的 `commands/`、`slash/commands/`、`permissions/`、`git/` 等子模块。
- **Agent Framework 代码**: 集中在 `agent-framework/agent_framework/`，是核心业务逻辑所在，包含完整的 Agent 类型、服务、工具、RAG、编排、DeepSeek 优化等模块。
- **Worktree/Sparse**: 项目中暂无专门实现。
- **Rules 系统**: 存在基础的 [rules.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/rules.py) 权限规则实现和 [acw.md](file:///e:/AloneChat-workspace-master/.trae/rules/acw.md) 工作区规则约束。

以下是三个系统的详细总结：

---

## 一、Slash 命令系统

**目录**: [alonechat-cli/src/alonechat/slash](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash)

Slash 命令系统由以下核心组件构成：

### 1.1 解析器（Parser）
[parser.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/parser.py) — `SlashCommandParser` 类

- 通过 `PREFIX = "/"` 前缀识别 slash 命令
- `parse(text)` 方法将用户输入解析为 `ParsedCommand` 数据类（包含 `name`, `args`, `raw`, `is_valid`, `error`）
- 支持带引号的参数分割（`_split_args` 处理单引号和双引号）
- 命令名称验证使用正则 `^[a-zA-Z][a-zA-Z0-9_-]*$`
- 提供 `parse_frontmatter(content)` 解析 Markdown 文件的 YAML 前置元数据（支持字符串、列表、布尔、整数类型）
- `substitute_args(template, args)` 支持 `$ARGUMENTS`、`$1`、`$2`... 参数替换（用于自定义命令模板）

### 1.2 注册表（Registry）
[registry.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/registry.py) — `SlashCommandRegistry` 类和 `SlashCommand` 数据类

`SlashCommand` 包含字段：`name`, `description`, `handler`, `aliases`, `usage`, `examples`, `category`

注册表提供：`register()`、`unregister()`、`get()`（支持别名查找）、`has()`、`list_commands()`（按分类筛选）、`list_categories()`、`search()`（按名称/描述模糊搜索）、`get_completions()`（用于自动补全）

### 1.3 执行器（Executor）
[executor.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/executor.py) — `SlashCommandExecutor` 类

- 构造函数接收 `obj`（全局对象字典）和 `session_manager`
- `_register_builtin_commands()` 注册内置命令
- `_register_custom_commands()` 通过 `CustomCommandLoader` 加载自定义命令
- `execute(name, args)` 查找并执行命令，异常时打印错误
- `execute_raw(text)` 先解析再执行
- `get_completions(prefix)` 和 `list_commands(category)` 委托给注册表

### 1.4 自定义命令加载器（Custom Loader）
[custom_loader.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/custom_loader.py) — `CustomCommandLoader` 类和 `CustomCommand` 数据类

- 从两个目录加载 `.md` 文件作为自定义命令：
  - 用户级别：`~/.alonechat/commands`（source="user"）
  - 项目级别：`<cwd>/.alonechat/commands`（source="project"）
- `.md` 文件支持 YAML frontmatter（`description`, `allowed-tools`, `argument-hint`, `model`）
- 子目录组织支持命名空间（如 `namespace:command-name`）
- `execute_custom_command()` 对 prompt 进行参数替换、bash 命令执行（`` !`command` `` 语法）和文件引用处理（`@file-path` 语法）
- `process_bash_commands()` 使用 `subprocess.run` 执行内嵌 shell 命令（30秒超时）
- `process_file_references()` 将 `@path` 引用替换为文件内容

### 1.5 内置命令一览（16 个）

| 命令 | 别名 | 分类 | 功能 |
|------|------|------|------|
| `/clear` | cls | session | 清除当前会话的对话历史 |
| `/compact` | - | session | 压缩对话上下文，保留最近 6 条消息并生成摘要 |
| `/config` | cfg | settings | 查看/设置配置（分层键访问，如 `model.temperature`） |
| `/cost` | - | info | 显示 token 使用统计和估算成本 |
| `/doctor` | - | debug | 检查 Python 版本、配置文件、会话目录、依赖库 |
| `/help` | h, ? | general | 显示命令帮助，支持 `/help <cmd>` 查看详情 |
| `/init` | - | project | 交互式创建 CLAUDE.md 项目文件 |
| `/model` | m | settings | 显示当前模型信息（固定 DeepSeek V4 Flash） |
| `/fork` | - | session | 从当前点或指定索引创建会话分支 |
| `/branch` | - | session | 管理分支（list, new, switch, delete） |
| `/rewind` | rw | session | 回退对话（支持数字参数或交互式选择） |
| `/review` | r | actions | 请求代码审查模式 |
| `/status` | st | info | 显示版本、模型、输出格式、工作目录、会话信息 |
| `/usage` | - | info | 显示使用限制和定价信息 |
| `/agents` | agent | agents | 管理子代理（列出、详情、启用/禁用、运行） |
| `/mcp` | - | integrations | 管理 MCP 服务器（列出、启用/禁用） |
| `/vim` | - | editor | 启用 Vim 模式 |
| `/permissions` | perm | settings | 管理工具权限（allow, deny, mode, reset） |

### 1.6 __init__.py 导出
[slash/__init__.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/__init__.py) 导出三个核心类：`SlashCommandRegistry`, `SlashCommandParser`, `SlashCommandExecutor`

---

## 二、上下文系统（Context System）

**文件**: [context/__init__.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/context/__init__.py)

仅包含一个 `ContextManager` 类，负责对话历史管理和上下文窗口控制。

### 核心功能

- **`__init__(max_tokens=128000)`** — 初始化上下文管理器，默认最大 128,000 tokens
- **`add_message(role, content)`** — 添加消息，自动进行窗口控制：如果新消息会导致超出 `max_tokens`，则从左侧（最早的消息）移除消息直到有足够空间
- **`get_messages()`** — 返回所有消息的列表
- **`clear()`** — 清空所有消息并重置 token 计数
- **`_estimate_tokens(text)`** — 估算 token 数：中文字符按 1.5 字符/token，其他字符按 4 字符/token

使用 `collections.deque` 作为底层数据结构，提供高效的左侧弹出操作。

---

## 三、Agent 管理系统（Agent Management System）

**目录**: [alonechat-cli/src/alonechat/agents](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/agents)

系统由三个核心文件组成：

### 3.1 代理定义（Agent Definition）
[definition.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/agents/definition.py)

**`AgentModel` 枚举** — 支持四种模型：`SONNET`, `OPUS`, `HAIKU`, `DEEPSEEK`

**`AgentDefinition` 数据类** — 定义代理的完整配置：
- `name`：代理名称
- `description`：描述
- `prompt`：系统提示词
- `tools`：允许使用的工具列表（空列表表示全部允许）
- `model`：使用的模型，默认 `DEEPSEEK`
- `enabled`：是否启用，默认 `True`

提供 `to_dict()` / `from_dict()` / `from_json()` 序列化方法

**内置默认代理（4 个）**：

| 名称 | 描述 | 允许的工具 |
|------|------|-----------|
| `code-reviewer` | 代码审查专家 | Read, Grep, Glob, Bash |
| `debugger` | 调试专家 | Read, Grep, Glob, Bash |
| `test-writer` | 测试编写专家 | Read, Write, Edit, Bash |
| `doc-writer` | 文档编写专家 | Read, Write, Edit |

### 3.2 代理管理器（Agent Manager）
[manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/agents/manager.py)

**`AgentManager` 类** — 管理代理的完整生命周期：
- **初始化**：加载内置默认代理（`DEFAULT_AGENTS`），然后从 `~/.alonechat/agents.json` 加载用户自定义代理
- **`register(agent)`** — 注册新代理并持久化到 JSON 文件
- **`unregister(name)`** — 注销代理
- **`get(name)`** — 按名称获取代理
- **`list_agents()`** — 列出所有代理
- **`enable(name)` / `disable(name)`** — 启用/禁用代理
- **`load_from_json(json_str)`** — 从 JSON 字符串批量加载代理（用于 `--agents` CLI 标志）
- **`get_agent_info(name)`** — 获取代理详细信息字典

用户代理持久化在 `~/.alonechat/agents.json`（只保存非默认代理）。

### 3.3 代理执行器（Agent Executor）
[executor.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/agents/executor.py)

**`AgentExecutor` 类** — 执行子代理任务：
- **`execute(agent_name, task, context)`** — 主入口：查找代理、检查启用状态、构建消息并调用模型
- **`_run_agent(agent, task, context)`** — 内部执行：使用 `ModelRouter` 构建 system prompt + user message，通过 `model_router.chat_with_reasoning()` 调用 DeepSeek 模型
- **`list_available_agents()`** — 以 Rich table 格式展示所有代理的名称、描述、模型和状态

### 3.4 与 Slash 命令的集成
在 [commands/agents.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/agents.py) 中，`/agents` 命令与 Agent 系统对接：
- `/agents` — 调用 `AgentExecutor.list_available_agents()` 列出所有代理
- `/agents run <name>` — 调用 `AgentExecutor.execute()` 运行指定代理
- `/agents enable/disable <name>` — 调用 `AgentManager.enable/disable()`
- `/agents <name>` — 显示单个代理的详细信息（模型、工具、状态）

### 3.5 __init__.py 导出
[agents/__init__.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/agents/__init__.py) 导出三个类：`AgentManager`, `AgentDefinition`, `AgentExecutor`

---

## 四、系统间关系总结

**架构层次**：
1. **用户输入** -> `SlashCommandParser` 解析为命令 + 参数
2. **命令路由** -> `SlashCommandExecutor` 从 `SlashCommandRegistry` 查找命令处理器
3. **命令执行** -> 各命令处理器调用下游系统
4. **上下文管理** -> `ContextManager` 在会话层管理消息队列和 token 窗口
5. **Agent 系统** -> `AgentManager` 管理代理定义，`AgentExecutor` 执行代理任务，两者都通过 `/agents` 命令暴露给用户

所有命令处理器遵循统一签名 `(args, obj, session_manager, registry, **kwargs)`，通过共享的 `obj` 字典传递全局状态（如 `config_manager`）。

以下是针对 `E:\AloneChat-workspace-master\agent-framework` 中与所述概念相关的现有实现的全面搜索报告。

---

## 搜索结果总览

**搜索范围**: `agent-framework/` 核心目录 + `alonechat-cli/` 中相关部分
**搜索概念**: git worktree / sparse checkout / 从目录加载规则 / CLAUDE.md 支持 / skill 自动发现 / add-dir 风格目录加载 / 插件加载模式

---

## 一、Git Worktree 与 Sparse Checkout

**未发现任何相关实现。**

在 agent-framework 和整个项目中，没有任何关于 `git worktree` 或 `sparse checkout` 的代码。现有 Git 相关功能仅包括：
- [git_manager.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/git/git_manager.py) - 基础 Git 操作（分支、提交、推送、回滚）
- [code_tools.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/code/code_tools.py#L264-L305) - GitTool（status/log/diff/branch）

两者都不涉及 worktree 或 sparse checkout 操作。

---

## 二、CLAUDE.md 支持

**没有全局/框架级的 CLAUDE.md 加载机制。**

现有相关的唯一实现是 CLI 中的 `/init` 命令：

- [alonechat-cli/src/alonechat/slash/commands/init.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/init.py) - 一个 slash command，功能是**创建** CLAUDE.md 文件（如果不存在），但没有任何读取/解析/加载 CLAUDE.md 内容的框架层逻辑。

agent-framework 内部**完全没有任何**读取 CLAUDE.md 或将其注入到系统提示词/上下文中的代码。

---

## 三、从目录加载规则

**没有通用规则加载机制。**

项目根目录存在 `.trae/rules/acw.md`，但它只是通过 IDE 插件加载的静态文件，agent-framework 并无读取它的逻辑。也没有任何从 `.rules/` 或类似目录动态加载规则文件的机制。

---

## 四、Skill 自动发现 / 从目录加载 / 插件加载模式

这是**实现最丰富的领域**，有以下几种模式：

### 4.1 SkillsConfig - 从 YAML 配置文件加载

- [configs/skills.yaml](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/skills.yaml) - 所有内置 skill 定义的 YAML 配置中心
- [configs/__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/__init__.py#L328-L367) - `SkillsConfig` 类，使用单例模式从 `skills.yaml` 加载配置

```python
class SkillsConfig:
    _instance: Optional["SkillsConfig"] = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_yaml_config("skills.yaml")
        return cls._instance
```

**模式**: 从单个 YAML 文件加载，所有 skill 定义静态列出，**没有目录扫描机制**。

### 4.2 SkillsRegistry + register_builtin_skills - Python 类注册

- [tools/skills_registry.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_registry.py) - 主要注册表，包含：

  - **`register_builtin_skills()`** (第 419-425 行) - 手动注册 5 个内置 skill 类
  - **`load_skill(skill_path)`** (第 130-150 行) - 通过 `importlib` 从指定路径加载单个 skill 模块（要求 `__init__.py` + `get_skill()` 函数）
  - **没有 `load_from_directory()` 方法** - 虽然 [docs/tech-reports](file:///E:/AloneChat-workspace-master/docs/tech-reports/Agent框架技术开发报告.md#L290) 中有架构文档描述了 `load_skills_from_dir`，但**实际代码中不存在**。

### 4.3 SkillRegistry (services/skills/) - 硬编码注册

- [services/skills/registry.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/services/skills/registry.py) - 另一个注册表（与 tools/ 下的不同），所有 skill 通过 `_register_builtin_skills()` 硬编码注册，**没有动态加载**。

### 4.4 SkillsMarketplace - 从远程 Git 安装

- [tools/skills_marketplace.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_marketplace.py) - 市场实现，支持：

  - **`install_from_remote(url)`** (第 231-343 行) - 从 GitHub/skills.sh 下载并安装到 `~/.skills/` 或 `./.skills/`
  - **`list_installed_remote()`** (第 375-397 行) - **扫描目录**：遍历 `~/.skills/` 和 `./.skills/` 查找 SKILL.md 文件
  - 安装后**注册**到 SkillsRegistry（通过 `self.registry.load_skill()`）

### 4.5 SkillsCLI - 目录扫描

- [tools/skills_cli.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_cli.py) - CLI 接口：

  - **`list_skills()`** (第 146-175 行) - 扫描 `./.skills/` 和 `~/.skills/`，对每个子目录检查是否存在 SKILL.md
  - 安装路径模式：`{skills_dir}/{skill_name}/`，文件直接放在 skill 名下

### 4.6 SkillsShClient - Git 仓库内容下载

- [tools/skills_sh_client.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_sh_client.py) - 远程客户端：

  - **`download_skill_content()`** - 通过 GitHub API 列出目录内容，逐个下载文件
  - **`parse()`** - 解析 GitHub URL，支持 `tree/branch/skills/skill-name` 格式
  - 搜索路径模式：始终从仓库中的 `skills/{skill_name}/` 目录下载

---

## 五、add-dir 风格目录加载模式

**部分实现，但不在 agent-framework 内部。**

- [alonechat-cli/src/alonechat/slash/custom_loader.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/custom_loader.py) - **这是最接近 "add-dir" 目录加载模式的实现**：

  ```python
  class CustomCommandLoader:
      PROJECT_DIR = ".alonechat/commands"
      USER_DIR = ".alonechat/commands"
      
      def _load_from_dir(self, directory: Path, source: str) -> list[CustomCommand]:
          """从目录加载命令"""
          if not directory.exists():
              return commands
          for md_file in directory.rglob("*.md"):
              cmd = self._parse_command_file(md_file, source)
              if cmd:
                  commands.append(cmd)
          return commands
  ```

  但这是 `alonechat-cli` 的一部分，**不是 agent-framework**。

---

## 六、MCP Marketplace 插件模式

- [deepseek_optimization/mcp_marketplace/](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/mcp_marketplace/) - 包含：
  - `registry.py` - 通过 `register_server()` 手动注册
  - `loader.py` - 通过 `loader.start_server()` 生命周期管理
  - **没有目录自动发现** - MCP 服务器必须通过 API 手动注册

---

## 七、YAML 配置目录（configs/）

所有 6 个配置文件均位于 [configs/](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/)：

| 文件 | 内容 |
|------|------|
| `skills.yaml` | 5 个内置 skill 定义（document/data/research/ppt/report） |
| `prompts.yaml` | 系统提示词模板 |
| `models.yaml` | LLM 模型配置（DeepSeek/OpenAI/Embedding） |
| `sandbox.yaml` | 沙箱安全配置（MTC/CODE 模式） |
| `intent_clarification.yaml` | 意图澄清配置 |
| `__init__.py` | 配置加载器（YAML→Python 单例） |

配置加载模式为 `load_yaml_config(filename)` 从 `configs/` 目录加载，支持缓存和重新加载。

---

## 总结表

| 概念 | agent-framework 中状态 | 位置/说明 |
|------|----------------------|-----------|
| **git worktree** | 不存在 | 完全缺失 |
| **sparse checkout** | 不存在 | 完全缺失 |
| **CLAUDE.md 读取** | 不存在 | 仅 `alonechat-cli` 中有创建逻辑 |
| **规则目录加载** | 不存在 | 无 `.rules/` 或类似扫描 |
| **skill 自动发现** | 部分存在 | `skills_marketplace.py` 扫描 `~/.skills/` 目录，但核心注册表没有动态加载 |
| **add-dir 加载** | 仅 `alonechat-cli` 中有 | `custom_loader.py` 的 `_load_from_dir()` |
| **YAML 配置驱动** | 已实现 | 所有配置通过 `configs/` YAML 文件加载 |
| **插件目录扫描** | 不存在 | MCP 和 skill 都需手动注册，无自动插件发现 |
| **load_skill 模块加载** | 已实现 | `skills_registry.py` 的 `load_skill()` 使用 `importlib` 从路径加载 |

所有 CLI 增强功能已实现完成。以下是完整的实现总结：

---

## 实现概览

遵循项目规则，所有核心逻辑实现在 **agent-framework** 中，CLI 层负责集成调用。

### 新增文件 (agent-framework)

| 文件 | 说明 |
|---|---|
| [cli_enhancements/__init__.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/__init__.py) | 模块入口，导出所有公共类 |
| [cli_enhancements/manager.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/manager.py) | 统一管理器，串联所有增强功能 |
| [cli_enhancements/worktree_manager.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/worktree_manager.py) | Git 工作树管理 + 稀疏检出 |
| [cli_enhancements/claude_md_loader.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/claude_md_loader.py) | CLAUDE.md 加载器 + @import 支持 |
| [cli_enhancements/rules_loader.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/rules_loader.py) | .claude/rules/ 条件性规则加载 |
| [cli_enhancements/skills_discovery.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/skills_discovery.py) | 嵌套技能自动发现 |
| [cli_enhancements/additional_dir_loader.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/cli_enhancements/additional_dir_loader.py) | --add-dir 附加目录加载器 |
| [configs/cli_enhancements.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/cli_enhancements.yaml) | 全 YAML 配置（遵循无硬编码规则）|

### 修改文件 (alonechat-cli)

| 文件 | 说明 |
|---|---|
| [cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/cli.py) | 添加 `--worktree` 和 `--add-dir` 标志 |

---

## 功能详情

### 1. `--worktree` 标志 (v2.1.49)
- 在隔离的 Git 工作树中启动会话，避免影响主仓库
- 自动生成分支名（`alonechat_worktree_<timestamp>_<session_id>`）
- 支持工作树列表、移除、清理过期工作树
- 创建临时工作树的 fallback 机制

### 2. 工作树稀疏检出 (v2.1.76)
- 创建工作树后自动配置 git sparse-checkout
- 默认仅检出 `src/`, `configs/`, `tests/`, `pyproject.toml` 等必要路径
- 路径列表通过 YAML 配置，可自定义

### 3. `--add-dir` 加载技能/插件 (v2.1.45)
- 支持从附加目录加载 skills、plugins、commands、models 等资源
- 自动检测 enabledPlugins.yaml/yml 配置
- 支持多次使用：`--add-dir /path/a --add-dir /path/b`
- 支持环境变量 `ALONECHAT_ADDITIONAL_DIRECTORIES`

### 4. 支持从 `--add-dir` 加载 CLAUDE.md (v2.1.20)
- 从项目目录和所有附加目录搜索 CLAUDE.md
- 环境变量 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 控制
- 支持 YAML frontmatter 解析

### 5. 嵌套技能自动发现 (v2.1.6)
- 从 `.claude/skills/`, `.skills/`, `~/.claude/skills/` 中自动发现
- 递归扫描嵌套目录（最大深度 3 级）
- 解析 SKILL.md 定义文件，提取名称、描述、版本
- 支持自动注册到技能注册中心

### 6. `.claude/rules/` 条件性规则 (v2.0.64)
- 从 `.claude/rules/` 目录加载规则文件
- 文件名即条件：`always.md`（始终加载）、`python.md`（检测到 Python 时加载）、`react.md`、`docker.md` 等
- 内置 18+ 种项目类型检测（Python、JS、TS、React、Rust、Go、Java 等）
- 通过项目文件扫描自动判断条件

### 7. CLAUDE.md @import (v0.2.107)
- 使用 `@path/to/file.md` 语法导入其他文件
- 支持 `.md`, `.txt`, `.yaml`, `.yml`, `.json`, `.toml` 扩展名
- 递归解析导入链（最大深度 10 层）
- 循环引用检测
- 导入内容自动包裹 HTML 注释标记

### 使用示例

```bash
# 在隔离工作树中启动（自动稀疏检出）
alonechat --worktree /tmp/my-worktree chat

# 加载附加目录（技能/插件/CLAUDE.md）
alonechat --add-dir /path/to/skills --add-dir /path/to/plugins chat

# 组合使用
alonechat --worktree /tmp/wt --add-dir /path/to/extras -v chat

# 打印模式 + 工作树
alonechat --worktree /tmp/wt -p "分析项目结构"
```

## User
`e:\AloneChat-workspace-master\docs\releases\RELEASE_NOTE_v0.2.0.md` 把你写的相关更改写到这个文件里面

## Assistant
现在我来更新发布说明文件，把我刚才实现的 CLI 增强内容加进去。

