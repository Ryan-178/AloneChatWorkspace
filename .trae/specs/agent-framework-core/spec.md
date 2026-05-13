# ChatAgent Phase 2: Agent 框架核心 Spec

## Why
构建 ChatAgent 项目的第二阶段：一个自研的轻量级 Python Agent 框架，提供 LLM 调用、工具系统、记忆系统、RAG 检索和多 Agent 编排等核心能力，为后续与聊天软件融合提供智能决策层。

## What Changes
- 创建 `agent-framework/` Python 包目录结构
- 实现核心接口定义（BaseAgent, BaseTool, BaseMemory, BaseLLM, Orchestrator）
- 实现 LLM 调用层（LiteLLM 集成，多模型适配）
- 实现工具系统（注册、发现、执行机制）
- 实现 Agent 核心引擎（ReAct 循环：思考-行动-观察）
- 实现记忆系统（短期会话记忆 + 长期向量记忆）
- 实现 RAG 模块（文档加载、分块、Embedding、检索）
- 实现任务编排引擎（顺序/并行/DAG 工作流）
- 实现多 Agent 协作（Agent 间消息传递、角色分配）
- 实现可观测性（Logging、Tracing、Token 计数）
- 实现安全性（工具沙箱、速率限制、内容过滤）
- 单元测试覆盖核心模块 > 80%

## Impact
- Affected specs: 依赖 Phase 1 `chat-app-foundation`（聊天软件基础）
- Affected code: `agent-framework/`（全新 Python 包）
- **注**：Phase 1（chat-app）尚未实现。Phase 2 是独立的 Python 包，可独立开发和测试。两阶段在 Phase 3 融合。

## ADDED Requirements

### Requirement: 框架架构设计
系统 SHALL 定义 Agent 框架的核心抽象接口，作为所有扩展模块的基础。

#### Scenario: 核心接口定义
- **WHEN** 开发者导入 agent-framework 包
- **THEN** 以下核心抽象类可用：
  - `BaseAgent`: Agent 执行器基类，含 `perceive()` → `plan()` → `act()` → `reflect()` 生命周期
  - `BaseTool`: 工具基类，含 `name`、`description`、`parameters`（JSON Schema）、`execute()` 方法
  - `BaseMemory`: 记忆存储基类，含 `add()`、`query()`、`clear()` 方法
  - `BaseLLM`: LLM 调用基类，含 `chat()`、`chat_stream()` 方法
  - `Orchestrator`: 编排引擎基类，含 `run()`、`run_multi()`、`run_workflow()` 方法

#### Scenario: 类型安全
- **WHEN** 定义 Agent、Tool、Memory 等实体的数据结构
- **THEN** 使用 Pydantic 模型进行类型验证和序列化

### Requirement: LLM 调用层
系统 SHALL 提供统一的 LLM 调用接口，支持多种模型提供商。

#### Scenario: LiteLLM 集成
- **WHEN** 应用程序调用 LLM
- **THEN** 通过 LiteLLM SDK 统一适配 OpenAI、Anthropic、Google Gemini、Azure OpenAI 等模型
- **AND** 模型配置通过 `config` 字典管理（model_name、api_key、temperature、max_tokens 等）

#### Scenario: 流式对话
- **WHEN** 调用 `chat_stream()`
- **THEN** 返回异步生成器（AsyncGenerator），逐 chunk 输出 LLM 的流式响应
- **AND** 每个 chunk 包含 `content`、`finish_reason`、`usage`（可选）字段

#### Scenario: Token 计数与成本追踪
- **WHEN** 每次 LLM 调用完成
- **THEN** 自动记录 `prompt_tokens`、`completion_tokens`、`total_tokens` 和估算成本

### Requirement: 工具系统
系统 SHALL 提供标准化的工具注册、发现和执行机制。

#### Scenario: 工具注册
- **WHEN** 开发者定义一个工具类（继承 BaseTool）
- **THEN** 通过 `ToolRegistry.register()` 将工具注册到全局注册表
- **AND** 注册时校验工具名称唯一性

#### Scenario: 工具发现
- **WHEN** Agent 需要选择工具
- **THEN** 通过 `ToolRegistry.list_tools()` 获取所有已注册工具的名称和描述
- **AND** 通过 `ToolRegistry.get_tool(name)` 获取特定工具的 JSON Schema 定义

#### Scenario: 工具执行
- **WHEN** Agent 调用 `ToolRegistry.execute_tool(name, params)`
- **THEN** 系统校验参数（JSON Schema），执行工具逻辑，返回执行结果
- **AND** 记录工具调用日志（输入、输出、耗时、成功/失败状态）

### Requirement: Agent 核心引擎
系统 SHALL 实现 ReAct（Reasoning + Acting）循环，使 Agent 能够自主思考、选择行动并观察结果。

#### Scenario: ReAct 循环
- **WHEN** Agent 收到一个用户任务
- **THEN** Agent 执行以下循环：
  1. **Think（思考）**：分析当前状态和可用工具，决定下一步行动
  2. **Act（行动）**：执行选定的工具调用或生成最终回答
  3. **Observe（观察）**：接收工具执行结果，更新上下文
- **AND** 循环持续直到 Agent 决定生成最终回答或达到最大迭代次数

#### Scenario: 最大迭代限制
- **WHEN** Agent 循环次数超过 `max_iterations`（默认 10）
- **THEN** Agent 终止循环并返回当前最佳结果，附带 `stopped_by_max_iterations: true` 标记

#### Scenario: 流式思考过程
- **WHEN** Agent 在 ReAct 循环中
- **THEN** 通过回调机制实时输出思考、行动和观察的中间状态
- **AND** 每个中间状态包含 `type`（think/act/observe）、`content`、`timestamp`

### Requirement: 记忆系统
系统 SHALL 提供短期和长期两种记忆存储机制。

#### Scenario: 短期记忆（会话记忆）
- **WHEN** Agent 在一个对话会话中接收新消息
- **THEN** 系统将消息（用户输入 + Agent 响应）追加到 `ConversationMemory`
- **AND** 支持按窗口大小截断（sliding window），保留最近的 N 轮对话
- **AND** 支持 `summarize()` 方法，将超出窗口的历史对话压缩为摘要

#### Scenario: 长期记忆（向量记忆）
- **WHEN** 开发者配置了向量数据库
- **THEN** `VectorMemory` 通过 Embedding 模型将文本转为向量并存入向量数据库
- **AND** `query()` 方法接收文本查询，返回语义相似度最高的 Top-K 条记忆记录
- **AND** 支持 `add()` 方法添加新记忆，每条记录含 `id`、`content`、`metadata`（timestamp、source 等）、`embedding`

#### Scenario: 记忆融合
- **WHEN** Agent 需要检索记忆
- **THEN** 系统合并短期记忆（最近 N 轮对话）和长期记忆（语义检索 Top-K 结果）
- **AND** 在 LLM 上下文中按相关性排序：当前对话 > 短期记忆 > 长期记忆

### Requirement: RAG 模块
系统 SHALL 提供检索增强生成（RAG）能力，使 Agent 能够基于外部文档回答问题。

#### Scenario: 文档加载
- **WHEN** 用户提供文档文件（支持 TXT、PDF、Markdown、HTML 格式）
- **THEN** 系统自动识别文件类型，使用相应加载器读取文档内容
- **AND** 返回文档原始文本

#### Scenario: 文档分块
- **WHEN** 文档加载完成
- **THEN** 系统将文档按配置参数分块：
  - `chunk_size`：每块最大字符数（默认 1000）
  - `chunk_overlap`：块间重叠字符数（默认 200）
- **AND** 使用 RecursiveCharacterTextSplitter 算法，优先在段落/句子边界分割

#### Scenario: Embedding 与检索
- **WHEN** 文档分块完成
- **THEN** 系统调用 Embedding 模型（默认 text-embedding-ada-002，支持替换为开源模型）生成向量
- **AND** 将向量和文本存入向量数据库
- **WHEN** 用户提问
- **THEN** 系统将问题 Embedding 化，在向量数据库中检索 Top-K 最相关文档块
- **AND** 返回检索结果列表，含 `content`、`score`、`source` 字段

### Requirement: 任务编排引擎
系统 SHALL 提供灵活的任务编排能力，支持顺序、并行和 DAG 工作流模式。

#### Scenario: 顺序执行
- **WHEN** 任务列表配置为 `SequentialFlow`
- **THEN** 系统按顺序依次执行每个任务，前一个任务的输出作为后一个任务的输入
- **AND** 任一任务失败则中止整个流程

#### Scenario: 并行执行
- **WHEN** 任务列表配置为 `ParallelFlow`
- **THEN** 系统使用 `asyncio.gather()` 并行执行所有任务
- **AND** 等待所有任务完成后合并结果返回

#### Scenario: DAG 工作流
- **WHEN** 工作流定义为 DAG（有向无环图）
- **THEN** 系统根据依赖关系自动解析执行顺序
- **AND** 支持条件分支（根据前序节点输出决定后续执行路径）
- **AND** 执行完成后返回完整执行轨迹（节点ID、状态、输入、输出、耗时）

### Requirement: 多 Agent 协作
系统 SHALL 支持多个 Agent 之间的消息传递和角色分配。

#### Scenario: Agent 间消息传递
- **WHEN** Agent A 需要向 Agent B 发送消息
- **THEN** 通过 `AgentBus.send(from_agent, to_agent, message)` 传递消息
- **AND** Agent B 通过 `AgentBus.receive()` 接收消息
- **AND** 消息包含 `id`、`from`、`to`、`content`、`type`（question/answer/result/error）、`timestamp`

#### Scenario: 角色分配
- **WHEN** 创建多 Agent 团队
- **THEN** 每个 Agent 配置 `role`（角色描述）和 `backstory`（背景设定）
- **AND** Agent 的 system prompt 自动包含角色描述，指导其行为

#### Scenario: 多 Agent 协商
- **WHEN** 多个 Agent 协作解决一个任务
- **THEN** Orchestrator 协调各 Agent 按配置的协作模式（顺序/投票/辩论）工作
- **AND** 收集各 Agent 的中间产出，汇总为最终结果

### Requirement: 可观测性
系统 SHALL 提供完善的日志和追踪能力。

#### Scenario: 结构化日志
- **WHEN** Agent 框架运行
- **THEN** 使用 Python logging 模块输出结构化日志，每条日志包含 `timestamp`、`level`、`module`、`message`、`context`（含 session_id、agent_id 等）
- **AND** 日志级别支持 DEBUG、INFO、WARNING、ERROR、CRITICAL

#### Scenario: 执行追踪
- **WHEN** 一个 Agent 任务执行完成
- **THEN** 系统返回完整的执行轨迹（Trace），包含：
  - 所有 LLM 调用的请求/响应/Token 数
  - 所有工具调用的输入/输出/耗时
  - 整个 ReAct 循环的步骤列表
  - 总耗时和总 Token 消耗

### Requirement: 安全性与配置
系统 SHALL 提供安全执行环境和灵活的配置管理。

#### Scenario: 工具沙箱
- **WHEN** Agent 调用高危工具（如执行系统命令、文件读写）
- **THEN** 系统在沙箱环境中执行（subprocess 隔离）
- **AND** 设置超时限制（默认 30 秒）、内存限制、禁止的网络访问策略

#### Scenario: 速率限制
- **WHEN** Agent 频繁调用 LLM 或工具
- **THEN** 系统按配置的速率限制（RPM/TPM）排队或拒绝请求
- **AND** 返回 RateLimitError，含 `retry_after_seconds` 字段

#### Scenario: 配置管理
- **WHEN** 初始化 Agent 框架
- **THEN** 通过 `AgentConfig` Pydantic 模型管理所有配置项，支持从环境变量、YAML 文件或字典加载
- **AND** 关键配置项：LLM 提供商/模型、向量数据库类型/连接、记忆窗口大小、RAG 参数

## API 接口设计（Python API）

### 核心类 API

| 类 | 方法 | 描述 |
|----|------|------|
| `BaseLLM` | `chat(messages, config) -> Message` | 同步对话 |
| `BaseLLM` | `chat_stream(messages, config) -> AsyncGenerator[Chunk]` | 流式对话 |
| `BaseTool` | `execute(params) -> Any` | 执行工具 |
| `ToolRegistry` | `register(tool_cls)` | 注册工具 |
| `ToolRegistry` | `list_tools() -> List[ToolDef]` | 列出工具 |
| `ToolRegistry` | `execute_tool(name, params) -> Any` | 执行工具 |
| `BaseAgent` | `run(task) -> AgentResult` | 运行 Agent |
| `BaseAgent` | `run_stream(task) -> AsyncGenerator[AgentEvent]` | 流式运行 |
| `ConversationMemory` | `add(message)` / `query()` / `summarize()` | 短期记忆 |
| `VectorMemory` | `add(entry)` / `query(text, k)` / `clear()` | 长期记忆 |
| `RAGPipeline` | `ingest(document)` / `retrieve(query, k)` | RAG 管道 |
| `Orchestrator` | `run(agent, task)` / `run_multi(agents, task)` / `run_workflow(graph)` | 编排引擎 |
| `AgentBus` | `send(from, to, msg)` / `broadcast(from, msg)` | Agent 消息总线 |
| `AgentConfig` | `from_env()` / `from_yaml(path)` / `from_dict(d)` | 配置加载 |
