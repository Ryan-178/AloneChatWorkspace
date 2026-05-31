# Agent-Framework 全量迁移至 AloneWork-CLI 重构计划

## 一、项目现状分析

### 1.1 依赖关系

```
alonework-cli ──依赖──→ agent-framework (单向依赖)
agent-framework ──不依赖──→ alonework-cli
```

**alonework-cli 中有 17 个文件引用了 agent_framework**，主要集中在：
- `cli.py` - CLI 增强功能
- `tools/executor.py` - 工具执行器
- `commands/agent.py` - Agent 命令
- `commands/codex.py` - Codex 集成
- `commands/test.py` - 测试生成
- `commands/team_mode.py` - 团队模式
- `modes/manager.py` - 模式管理
- `session/manager.py` - 会话管理
- `mcp/cli.py` - MCP 配置
- `lsp/integration.py` - LSP 集成

### 1.2 模块映射关系

| agent-framework 模块 | 功能描述 | 迁移目标位置 |
|---------------------|----------|-------------|
| `agent_framework/core/` | 核心框架（BaseTool, BaseAgent, QueryEngine, Store, AppState） | `alonechat/core/` |
| `agent_framework/agent/` | Agent 实现（ReactAgent, WorkerAgent, LeaderAgent） | `alonechat/agents/` |
| `agent_framework/tools/` | 工具系统（BashTool, FileReadTool, SkillsRegistry） | `alonechat/tools/` |
| `agent_framework/config.py` | 配置管理 | `alonechat/config/` |
| `agent_framework/llm/` | LLM 提供者 | `alonechat/llm/` |
| `agent_framework/orchestration/` | 编排引擎 | `alonechat/orchestration/` |
| `agent_framework/services/` | 服务层 | `alonechat/services/` |
| `agent_framework/storage/` | 存储层 | `alonechat/storage/` |
| `agent_framework/memory/` | 记忆系统 | `alonechat/memory/` |
| `agent_framework/security/` | 安全模块 | `alonechat/security/` |
| `agent_framework/permissions/` | 权限管理 | `alonechat/permissions/` |
| `agent_framework/sandbox/` | 沙箱环境 | `alonechat/sandbox/` |
| `agent_framework/code/` | 代码引擎 | `alonechat/code/` |
| `agent_framework/deepseek_optimization/` | DeepSeek 优化 | `alonechat/deepseek/` |
| `agent_framework/rag/` | RAG 管道 | `alonechat/rag/` |
| `agent_framework/lsp/` | LSP 集成 | `alonechat/lsp/` |
| `agent_framework/gateway/` | API 网关 | `alonechat/gateway/` |
| `agent_framework/credentials/` | 凭证管理 | `alonechat/credentials/` |
| `agent_framework/enterprise/` | 企业管理 | `alonechat/enterprise/` |
| `agent_framework/cli_enhancements/` | CLI 增强 | `alonechat/cli_enhancements/` |
| `agent_framework/locale/` | 国际化 | `alonechat/locale/` |
| `agent_framework/observability/` | 可观测性 | `alonechat/observability/` |
| `agent_framework/channels/` | 通道系统 | `alonechat/channels/` |
| `agent_framework/queue/` | 任务队列 | `alonechat/queue/` |
| `agent_framework/snapshot/` | 快照引擎 | `alonechat/snapshot/` |
| `agent_framework/rlm/` | RLM 调度 | `alonechat/rlm/` |
| `agent_framework/execution/` | 执行引擎 | `alonechat/execution/` |
| `agent_framework/context/` | 上下文管理 | `alonechat/context/` |
| `agent_framework/framework_agent/` | 框架代理 | `alonechat/framework_agent/` |
| `agent_framework/planning/` | 规划系统 | `alonechat/planning/` |

### 1.3 alonework-cli 已有模块

| 模块 | 功能 | 是否与 agent-framework 重叠 |
|------|------|---------------------------|
| `alonechat/agents/` | Agent 管理 | 部分重叠 |
| `alonechat/tools/` | 工具系统 | 部分重叠 |
| `alonechat/commands/` | 命令系统 | 部分重叠 |
| `alonechat/config/` | 配置管理 | 部分重叠 |
| `alonechat/session/` | 会话管理 | 部分重叠 |
| `alonechat/mcp/` | MCP 配置 | 部分重叠 |
| `alonechat/lsp/` | LSP 集成 | 部分重叠 |
| `alonechat/orchestration/` | 工作流编排 | 部分重叠 |
| `alonechat/permissions/` | 权限管理 | 部分重叠 |
| `alonechat/deepseek/` | DeepSeek 优化 | 部分重叠 |
| `alonechat/data/` | 数据收集 | 无重叠 |
| `alonechat/code/` | 代码生成 | 部分重叠 |
| `alonechat/git/` | Git 操作 | 无重叠 |
| `alonechat/chinese/` | 中文 NLP | 无重叠 |
| `alonechat/environment/` | 环境管理 | 无重叠 |
| `alonechat/models/` | 模型路由 | 无重叠 |
| `alonechat/modes/` | 交互模式 | 部分重叠 |
| `alonechat/cost/` | 成本显示 | 无重叠 |
| `alonechat/slash/` | 斜杠命令 | 无重叠 |
| `alonechat/tui/` | 终端 UI | 无重叠 |
| `alonechat/utils/` | 工具函数 | 无重叠 |

---

## 二、迁移策略

### 2.1 核心原则

1. **保留 alonework-cli 作为主项目**
2. **agent-framework 代码作为子模块合并**
3. **解决重叠模块，保留更完整的实现**
4. **统一导入路径为 `alonechat.*`**
5. **更新 pyproject.toml 依赖**

### 2.2 重叠模块处理策略

| 重叠模块 | agent-framework 实现 | alonework-cli 实现 | 处理策略 |
|---------|---------------------|-------------------|---------|
| `core/base_tool.py` | 完整的 BaseTool + ToolDef + ToolResult | 简单的 ToolExecutor | **保留 agent-framework 版本**，重命名为 `alonechat/tools/base.py` |
| `core/query_engine.py` | 完整的 QueryEngine | 无直接实现 | **保留 agent-framework 版本** |
| `core/store.py` | 发布-订阅 Store | 无直接实现 | **保留 agent-framework 版本** |
| `core/app_state.py` | AppState 管理 | `framework_config.py` 中的 AppState | **合并两者**，保留更完整的版本 |
| `core/mode_manager.py` | ModeManager | `modes/manager.py` | **保留 alonework-cli 版本**，补充 agent-framework 的功能 |
| `tools/` | BashTool, FileReadTool 等 | ToolExecutor, ToolRenderer | **合并两者**，保留 agent-framework 的工具实现 |
| `agents/` | 多种 Agent 实现 | AgentManager, AgentDefinition | **合并两者** |
| `llm/` | LiteLLMProvider, ModelRegistry | 无直接实现 | **保留 agent-framework 版本** |
| `orchestration/` | DAG, Parallel, Sequential, TeamEngine | 工作流编排 | **合并两者** |
| `storage/` | SQLiteSessionStorage | 无直接实现 | **保留 agent-framework 版本** |
| `config/` | Pydantic 配置 | YAML 配置 | **合并两者** |

---

## 三、详细迁移步骤

### 阶段 1：准备工作（预迁移）

#### 步骤 1.1：创建目标目录结构

```
alonework-cli/src/alonechat/
├── core/                    # 新增：核心框架
│   ├── __init__.py
│   ├── base_agent.py       # 从 agent-framework 迁移
│   ├── base_llm.py         # 从 agent-framework 迁移
│   ├── base_memory.py      # 从 agent-framework 迁移
│   ├── base_tool.py        # 从 agent-framework 迁移
│   ├── query_engine.py     # 从 agent-framework 迁移
│   ├── store.py            # 从 agent-framework 迁移
│   ├── app_state.py        # 从 agent-framework 迁移
│   ├── orchestrator.py     # 从 agent-framework 迁移
│   ├── agent_bus.py        # 从 agent-framework 迁移
│   ├── command.py          # 从 agent-framework 迁移
│   ├── command_registry.py # 从 agent-framework 迁移
│   ├── types.py            # 从 agent-framework 迁移
│   ├── task.py             # 从 agent-framework 迁移
│   ├── tool.py             # 从 agent-framework 迁移
│   ├── tool_builder.py     # 从 agent-framework 迁移
│   ├── error_handling.py   # 从 agent-framework 迁移
│   ├── cache.py            # 从 agent-framework 迁移
│   ├── context_isolation.py # 从 agent-framework 迁移
│   ├── dual_mode_manager.py # 从 agent-framework 迁移
│   ├── mode_manager.py     # 从 agent-framework 迁移
│   └── role_router.py      # 从 agent-framework 迁移
├── llm/                    # 新增：LLM 提供者
│   ├── __init__.py
│   ├── litellm_provider.py # 从 agent-framework 迁移
│   └── model_registry.py   # 从 agent-framework 迁移
├── storage/                # 新增：存储层
│   ├── __init__.py
│   ├── base_storage.py     # 从 agent-framework 迁移
│   ├── sqlite_storage.py   # 从 agent-framework 迁移
│   ├── database_manager.py # 从 agent-framework 迁移
│   └── migration.py        # 从 agent-framework 迁移
├── memory/                 # 新增：记忆系统
│   ├── __init__.py
│   ├── conversation_memory.py # 从 agent-framework 迁移
│   └── vector_memory.py    # 从 agent-framework 迁移
├── rag/                    # 新增：RAG 管道
│   ├── __init__.py
│   ├── code_indexer.py     # 从 agent-framework 迁移
│   ├── embedding.py        # 从 agent-framework 迁移
│   ├── loader.py           # 从 agent-framework 迁移
│   ├── local_embedding.py  # 从 agent-framework 迁移
│   ├── pipeline.py         # 从 agent-framework 迁移
│   ├── retriever.py        # 从 agent-framework 迁移
│   └── splitter.py         # 从 agent-framework 迁移
├── gateway/                # 新增：API 网关
│   ├── __init__.py
│   ├── api.py              # 从 agent-framework 迁移
│   ├── auth.py             # 从 agent-framework 迁移
│   ├── core.py             # 从 agent-framework 迁移
│   ├── router.py           # 从 agent-framework 迁移
│   ├── session.py          # 从 agent-framework 迁移
│   ├── tools.py            # 从 agent-framework 迁移
│   ├── types.py            # 从 agent-framework 迁移
│   ├── websocket.py        # 从 agent-framework 迁移
│   └── mcp_api.py          # 从 agent-framework 迁移
├── credentials/            # 新增：凭证管理
│   ├── __init__.py
│   ├── credential_store.py # 从 agent-framework 迁移
│   └── oauth_token_store.py # 从 agent-framework 迁移
├── enterprise/             # 新增：企业管理
│   ├── __init__.py
│   ├── enterprise_manager.py # 从 agent-framework 迁移
│   └── managed_settings.py # 从 agent-framework 迁移
├── cli_enhancements/       # 新增：CLI 增强
│   ├── __init__.py
│   ├── manager.py          # 从 agent-framework 迁移
│   ├── claude_md_loader.py # 从 agent-framework 迁移
│   ├── rules_loader.py     # 从 agent-framework 迁移
│   ├── skills_discovery.py # 从 agent-framework 迁移
│   ├── worktree_manager.py # 从 agent-framework 迁移
│   └── additional_dir_loader.py # 从 agent-framework 迁移
├── locale/                 # 新增：国际化
│   ├── __init__.py
│   └── i18n.py             # 从 agent-framework 迁移
├── observability/          # 新增：可观测性
│   ├── __init__.py
│   ├── logger.py           # 从 agent-framework 迁移
│   ├── metrics.py          # 从 agent-framework 迁移
│   └── tracer.py           # 从 agent-framework 迁移
├── channels/               # 新增：通道系统
│   ├── __init__.py
│   ├── base.py             # 从 agent-framework 迁移
│   └── chat_app.py         # 从 agent-framework 迁移
├── queue/                  # 新增：任务队列
│   ├── __init__.py
│   └── task_queue.py       # 从 agent-framework 迁移
├── snapshot/               # 新增：快照引擎
│   ├── __init__.py
│   └── engine.py           # 从 agent-framework 迁移
├── rlm/                    # 新增：RLM 调度
│   ├── __init__.py
│   └── dispatcher.py       # 从 agent-framework 迁移
├── execution/              # 新增：执行引擎
│   └── __init__.py
├── context/                # 已有，补充内容
│   └── __init__.py
├── framework_agent/        # 已有，补充内容
│   └── task_planner.py     # 从 agent-framework 迁移
├── planning/               # 新增：规划系统
│   └── __init__.py
├── sandbox/                # 新增：沙箱环境
│   ├── __init__.py
│   ├── enhanced_sandbox.py # 从 agent-framework 迁移
│   └── subprocess_sandbox.py # 从 agent-framework 迁移
├── security/               # 新增：安全模块
│   ├── __init__.py
│   ├── config.py           # 从 agent-framework 迁移
│   ├── input_validation.py # 从 agent-framework 迁移
│   ├── path_validator.py   # 从 agent-framework 迁移
│   ├── rate_limiter.py     # 从 agent-framework 迁移
│   └── scanner.py          # 从 agent-framework 迁移
└── services/               # 新增：服务层
    ├── __init__.py
    ├── api_client.py       # 从 agent-framework 迁移
    ├── error_fixer/        # 从 agent-framework 迁移
    ├── file_generators/    # 从 agent-framework 迁移
    ├── file_processors/    # 从 agent-framework 迁移
    ├── skills/             # 从 agent-framework 迁移
    ├── task_manager/       # 从 agent-framework 迁移
    ├── task_planner/       # 从 agent-framework 迁移
    └── test_generator/     # 从 agent-framework 迁移
```

#### 步骤 1.2：创建模块索引文件

为每个新模块创建 `__init__.py`，导出公共 API。

---

### 阶段 2：核心模块迁移

#### 步骤 2.1：迁移 `core/` 模块

**源文件**：`agent-framework/agent_framework/core/`
**目标位置**：`alonework-cli/src/alonechat/core/`

需要迁移的文件：
- `base_agent.py` - Agent 基类
- `base_llm.py` - LLM 基类
- `base_memory.py` - 记忆基类
- `base_tool.py` - 工具基类
- `query_engine.py` - 查询引擎
- `store.py` - 状态存储
- `app_state.py` - 应用状态
- `orchestrator.py` - 编排器
- `agent_bus.py` - Agent 通信总线
- `command.py` - 命令定义
- `command_registry.py` - 命令注册
- `types.py` - 类型定义
- `task.py` - 任务定义
- `tool.py` - 工具定义
- `tool_builder.py` - 工具构建器
- `error_handling.py` - 错误处理
- `cache.py` - 缓存系统
- `context_isolation.py` - 上下文隔离
- `dual_mode_manager.py` - 双模式管理
- `mode_manager.py` - 模式管理
- `role_router.py` - 角色路由

**导入路径变更**：
```python
# 旧路径
from agent_framework.core.base_tool import BaseTool
# 新路径
from alonechat.core.base_tool import BaseTool
```

#### 步骤 2.2：迁移 `tools/` 模块

**源文件**：`agent-framework/agent_framework/tools/`
**目标位置**：`alonework-cli/src/alonechat/tools/`

需要迁移的文件：
- `builtin/` - 内置工具（shell, file, git）
- `code/` - 代码工具
- `mtc/` - 文档工具
- `bash_tool.py` - Bash 工具
- `file_read_tool.py` - 文件读取工具
- `file_write_tool.py` - 文件写入工具
- `glob_tool.py` - Glob 搜索工具
- `grep_tool.py` - Grep 搜索工具
- `registry.py` - 工具注册
- `skills_cli.py` - 技能 CLI
- `skills_hot_reload.py` - 技能热重载
- `skills_marketplace.py` - 技能市场
- `skills_registry.py` - 技能注册
- `skills_sh_client.py` - 技能客户端

**处理策略**：
- 保留 alonework-cli 的 `executor.py` 和 `renderer.py`
- 将 agent-framework 的工具实现合并到 `builtin/` 子目录
- 更新 `__init__.py` 导出所有工具

#### 步骤 2.3：迁移 `agent/` 模块

**源文件**：`agent-framework/agent_framework/agent/`
**目标位置**：`alonework-cli/src/alonechat/agents/`

需要迁移的文件：
- `code_agent.py` - 代码 Agent
- `code_prompts.py` - 代码提示
- `intent_clarifier.py` - 意图澄清
- `leader_agent.py` - 领导 Agent
- `mode_manager.py` - 模式管理
- `mode_router.py` - 模式路由
- `mtc_agent.py` - MTC Agent
- `mtc_prompts.py` - MTC 提示
- `multi_agent.py` - 多 Agent
- `react_agent.py` - ReAct Agent
- `task_planner.py` - 任务规划
- `verifier_agent.py` - 验证 Agent
- `worker_agent.py` - 工作 Agent

**处理策略**：
- 保留 alonework-cli 的 `manager.py`, `definition.py`, `executor.py`
- 将 agent-framework 的 Agent 实现合并到 `workers/` 子目录
- 更新 `__init__.py` 导出所有 Agent

---

### 阶段 3：服务层迁移

#### 步骤 3.1：迁移 `llm/` 模块

**源文件**：`agent-framework/agent_framework/llm/`
**目标位置**：`alonework-cli/src/alonechat/llm/`

需要迁移的文件：
- `litellm_provider.py` - LiteLLM 提供者
- `model_registry.py` - 模型注册

#### 步骤 3.2：迁移 `orchestration/` 模块

**源文件**：`agent-framework/agent_framework/orchestration/`
**目标位置**：`alonework-cli/src/alonechat/orchestration/`

需要迁移的文件：
- `dag.py` - DAG 编排
- `parallel.py` - 并行执行
- `sequential.py` - 顺序执行
- `team_engine.py` - 团队引擎

**处理策略**：
- 保留 alonework-cli 的 `executor.py`, `planner.py`, `workflow.py`, `nodes/`
- 将 agent-framework 的编排实现合并
- 更新 `__init__.py` 导出所有编排器

#### 步骤 3.3：迁移 `storage/` 模块

**源文件**：`agent-framework/agent_framework/storage/`
**目标位置**：`alonework-cli/src/alonechat/storage/`

需要迁移的文件：
- `base_storage.py` - 存储基类
- `sqlite_storage.py` - SQLite 存储
- `database_manager.py` - 数据库管理
- `migration.py` - 迁移脚本

#### 步骤 3.4：迁移 `memory/` 模块

**源文件**：`agent-framework/agent_framework/memory/`
**目标位置**：`alonework-cli/src/alonechat/memory/`

需要迁移的文件：
- `conversation_memory.py` - 对话记忆
- `vector_memory.py` - 向量记忆

#### 步骤 3.5：迁移 `rag/` 模块

**源文件**：`agent-framework/agent_framework/rag/`
**目标位置**：`alonework-cli/src/alonechat/rag/`

需要迁移的文件：
- `code_indexer.py` - 代码索引
- `embedding.py` - 嵌入
- `loader.py` - 加载器
- `local_embedding.py` - 本地嵌入
- `pipeline.py` - 管道
- `retriever.py` - 检索器
- `splitter.py` - 分割器

#### 步骤 3.6：迁移 `services/` 模块

**源文件**：`agent-framework/agent_framework/services/`
**目标位置**：`alonework-cli/src/alonechat/services/`

需要迁移的文件：
- `api_client.py` - API 客户端
- `error_fixer/` - 错误修复
- `file_generators/` - 文件生成
- `file_processors/` - 文件处理
- `skills/` - 技能服务
- `task_manager/` - 任务管理
- `task_planner/` - 任务规划
- `test_generator/` - 测试生成

---

### 阶段 4：基础设施迁移

#### 步骤 4.1：迁移 `security/` 模块

**源文件**：`agent-framework/agent_framework/security/`
**目标位置**：`alonework-cli/src/alonechat/security/`

#### 步骤 4.2：迁移 `permissions/` 模块

**源文件**：`agent-framework/agent_framework/permissions/`
**目标位置**：`alonework-cli/src/alonechat/permissions/`

**处理策略**：
- 保留 alonework-cli 的 `manager.py`, `prompts.py`, `rules.py`
- 合并 agent-framework 的 `permission_manager.py`, `permission_rule.py`

#### 步骤 4.3：迁移 `sandbox/` 模块

**源文件**：`agent-framework/agent_framework/sandbox/`
**目标位置**：`alonework-cli/src/alonechat/sandbox/`

#### 步骤 4.4：迁移 `code/` 模块

**源文件**：`agent-framework/agent_framework/code/`
**目标位置**：`alonework-cli/src/alonechat/code/`

**处理策略**：
- 保留 alonework-cli 的 `generator.py`
- 合并 agent-framework 的 `apply_patch.py`, `code_engine.py`, `codex_bridge.py`, `codex_config.py`, `codex_parser.py`, `shell_tool.py`

#### 步骤 4.5：迁移 `deepseek_optimization/` 模块

**源文件**：`agent-framework/agent_framework/deepseek_optimization/`
**目标位置**：`alonework-cli/src/alonechat/deepseek/`

**处理策略**：
- 保留 alonework-cli 的 `context_manager.py`, `encryption.py`, `prompt_engineer.py`
- 合并 agent-framework 的 `cache/`, `context/`, `llm/`, `mcp_marketplace/`, `security/`, `swe/`, `optimizer.py`

---

### 阶段 5：辅助模块迁移

#### 步骤 5.1：迁移以下模块

| 源模块 | 目标位置 | 说明 |
|--------|---------|------|
| `gateway/` | `alonechat/gateway/` | API 网关 |
| `credentials/` | `alonechat/credentials/` | 凭证管理 |
| `enterprise/` | `alonechat/enterprise/` | 企业管理 |
| `cli_enhancements/` | `alonechat/cli_enhancements/` | CLI 增强 |
| `locale/` | `alonechat/locale/` | 国际化 |
| `observability/` | `alonechat/observability/` | 可观测性 |
| `channels/` | `alonechat/channels/` | 通道系统 |
| `queue/` | `alonechat/queue/` | 任务队列 |
| `snapshot/` | `alonechat/snapshot/` | 快照引擎 |
| `rlm/` | `alonechat/rlm/` | RLM 调度 |
| `lsp/` | `alonechat/lsp/` | LSP 集成 |

---

### 阶段 6：更新导入路径

#### 步骤 6.1：批量替换导入路径

在 `alonework-cli` 中，将所有 `from agent_framework` 替换为 `from alonechat`。

**需要更新的文件**（17 个）：
1. `src/alonechat/cli.py`
2. `src/alonechat/tools/executor.py`
3. `src/alonechat/commands/agent.py`
4. `src/alonechat/commands/codex.py`
5. `src/alonechat/commands/test.py`
6. `src/alonechat/commands/team_mode.py`
7. `src/alonechat/commands/enhanced_commands.py`
8. `src/alonechat/modes/manager.py`
9. `src/alonechat/modes/__init__.py`
10. `src/alonechat/session/manager.py`
11. `src/alonechat/mcp/cli.py`
12. `src/alonechat/lsp/integration.py`
13. `src/alonechat/slash/commands/skills_cmd.py`
14. `src/alonechat/slash/commands/mode.py`
15. `src/alonechat/slash/commands/mcp.py`
16. `examples/integration_test.py`
17. `INTEGRATION.md`

**替换规则**：
```python
# 旧导入
from agent_framework.core.base_tool import BaseTool
from agent_framework.tools.builtin.shell import ShellTool
from agent_framework.config import config

# 新导入
from alonechat.core.base_tool import BaseTool
from alonechat.tools.builtin.shell import ShellTool
from alonechat.config.framework_config import config
```

#### 步骤 6.2：更新内部导入

在迁移后的 agent-framework 代码中，更新所有内部导入。

---

### 阶段 7：更新配置文件

#### 步骤 7.1：更新 `pyproject.toml`

```toml
[project]
name = "alonework-cli"
version = "0.3.0"  # 版本升级
description = "国产化、终端原生、深度中文优化的AI编程Agent"

dependencies = [
    # 现有依赖
    "click>=8.1.0",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "cryptography>=41.0.0",
    "PyYAML>=6.0",
    "tomli>=2.0.0",
    "tomli-w>=1.0.0",
    "aiosqlite>=0.20.0",
    "prompt_toolkit>=3.0.40",
    # 从 agent-framework 迁移的依赖
    "litellm>=1.40.0",
    "pydantic-settings>=2.1.0",
    "chromadb>=0.4.22",
    "openai>=1.6.0",
    "tiktoken>=0.5.0",
    "aiofiles>=23.2.0",
    "unstructured>=0.12.0",
    "pdfminer.six>=20221105",
    "markdown>=3.5.0",
    "beautifulsoup4>=4.12.0",
    "tenacity>=8.2.0",
    "networkx>=3.2.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "websockets>=12.0",
    "PyJWT>=2.8.0",
    "email-validator>=2.1.0",
    "pdfplumber>=0.9.0",
    "python-docx>=0.8.11",
    "openpyxl>=3.1.2",
    "python-pptx>=0.6.21",
    "pandas>=2.0.0",
    "tabulate>=0.9.0",
    "Pillow>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
local-models = [
    "ollama>=0.1.0",
]
rag = [
    "chromadb>=0.4.0",
    "sentence-transformers>=2.0.0",
]
chinese-nlp = [
    "jieba>=0.42.0",
]
gateway = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "websockets>=12.0",
]
```

#### 步骤 7.2：更新 `agent-framework` 的 `pyproject.toml`

将其标记为已弃用，或直接删除。

---

### 阶段 8：测试与验证

#### 步骤 8.1：运行单元测试

```bash
cd alonework-cli
python -m pytest tests/ -v
```

#### 步骤 8.2：运行集成测试

```bash
python -m pytest examples/integration_test.py -v
```

#### 步骤 8.3：验证 CLI 功能

```bash
# 测试基本命令
alonework --version
alonework init
alonework chat
alonework generate
alonework test
alonework commit

# 测试斜杠命令
alonework chat
> /help
> /model
> /compact
> /cost

# 测试 Agent 命令
alonework agent analyze
alonework agent fix
alonework agent generate

# 测试 MCP 命令
alonework mcp list
alonework mcp status

# 测试 Codex 命令
alonework codex status
alonework codex review
```

#### 步骤 8.4：验证依赖导入

```python
# 测试所有导入
from alonechat.core.base_tool import BaseTool
from alonechat.core.base_agent import BaseAgent
from alonechat.core.query_engine import QueryEngine
from alonechat.tools.builtin.shell import ShellTool
from alonechat.llm.litellm_provider import LiteLLMProvider
from alonechat.orchestration.team_engine import TeamEngine
from alonechat.storage.sqlite_storage import SQLiteSessionStorage
```

---

### 阶段 9：清理与收尾

#### 步骤 9.1：删除 `agent-framework` 目录

确认所有功能正常后，删除 `agent-framework` 目录。

#### 步骤 9.2：更新项目文档

- 更新 `README.md`
- 更新 `INTEGRATION.md`
- 更新 `QUICKSTART.md`

#### 步骤 9.3：更新 Git 配置

- 更新 `.gitignore`
- 更新 `pyproject.toml` 中的包路径

#### 步骤 9.4：版本发布

- 更新版本号为 `0.3.0`
- 创建 Git 标签
- 发布新版本

---

## 四、风险与注意事项

### 4.1 潜在风险

1. **循环导入**：合并后可能出现循环导入，需要仔细检查依赖关系
2. **命名冲突**：两个项目可能有同名模块或类，需要重命名
3. **配置不兼容**：两个项目的配置格式可能不同，需要统一
4. **测试覆盖**：迁移后需要确保测试覆盖率

### 4.2 注意事项

1. **保持向后兼容**：尽量保持公共 API 不变
2. **渐进式迁移**：可以分模块逐步迁移，不要一次性全部迁移
3. **版本控制**：每个阶段都应该有 Git 提交，方便回滚
4. **文档同步**：迁移过程中同步更新文档

---

## 五、时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 阶段 1 | 准备工作 | 1-2 小时 |
| 阶段 2 | 核心模块迁移 | 3-4 小时 |
| 阶段 3 | 服务层迁移 | 2-3 小时 |
| 阶段 4 | 基础设施迁移 | 2-3 小时 |
| 阶段 5 | 辅助模块迁移 | 1-2 小时 |
| 阶段 6 | 更新导入路径 | 1-2 小时 |
| 阶段 7 | 更新配置文件 | 1 小时 |
| 阶段 8 | 测试与验证 | 2-3 小时 |
| 阶段 9 | 清理与收尾 | 1 小时 |
| **总计** | | **14-21 小时** |

---

## 六、迁移检查清单

- [ ] 创建目标目录结构
- [ ] 迁移 `core/` 模块
- [ ] 迁移 `tools/` 模块
- [ ] 迁移 `agent/` 模块
- [ ] 迁移 `llm/` 模块
- [ ] 迁移 `orchestration/` 模块
- [ ] 迁移 `storage/` 模块
- [ ] 迁移 `memory/` 模块
- [ ] 迁移 `rag/` 模块
- [ ] 迁移 `services/` 模块
- [ ] 迁移 `security/` 模块
- [ ] 迁移 `permissions/` 模块
- [ ] 迁移 `sandbox/` 模块
- [ ] 迁移 `code/` 模块
- [ ] 迁移 `deepseek_optimization/` 模块
- [ ] 迁移辅助模块（gateway, credentials, enterprise, etc.）
- [ ] 更新导入路径（17 个文件）
- [ ] 更新 `pyproject.toml`
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 验证 CLI 功能
- [ ] 删除 `agent-framework` 目录
- [ ] 更新文档
- [ ] 版本发布
