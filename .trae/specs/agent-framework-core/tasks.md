# Tasks

- [ ] Task 1: 项目初始化与包结构
  - [ ] 创建 `agent-framework/` 目录结构：`agent_framework/`、`tests/`、`examples/`
  - [ ] 创建 `pyproject.toml`（Python 包配置，含依赖：litellm、pydantic、chromadb、openai 等）
  - [ ] 创建 `agent_framework/__init__.py`（统一导出接口）
  - [ ] 创建 `CHANGELOG.md` 初始化条目
  - [ ] 创建 `.env.example` 环境变量模板

- [ ] Task 2: 核心接口定义与 Pydantic 模型
  - [ ] 定义 `agent_framework/core/base_llm.py` — `BaseLLM` 抽象类和 `Message`、`Chunk`、`LLMConfig` 模型
  - [ ] 定义 `agent_framework/core/base_tool.py` — `BaseTool` 抽象类和 `ToolDef`、`ToolResult` 模型
  - [ ] 定义 `agent_framework/core/base_memory.py` — `BaseMemory` 抽象类和 `MemoryEntry` 模型
  - [ ] 定义 `agent_framework/core/base_agent.py` — `BaseAgent` 抽象类，定义 `perceive()` → `plan()` → `act()` → `reflect()` 生命周期
  - [ ] 定义 `agent_framework/core/orchestrator.py` — `Orchestrator` 基类和 `WorkflowGraph` 模型
  - [ ] 定义 `agent_framework/core/agent_bus.py` — `AgentMessage` 模型和消息传递接口
  - [ ] 定义 `agent_framework/config.py` — `AgentConfig` Pydantic 模型（支持 env、yaml、dict 加载）

- [ ] Task 3: LLM 调用层实现
  - [ ] 实现 `agent_framework/llm/litellm_provider.py` — `LiteLLMProvider(BaseLLM)`：封装 LiteLLM SDK
  - [ ] 实现 `chat()` 方法：同步对话，返回 `Message` 对象
  - [ ] 实现 `chat_stream()` 方法：异步生成器，逐 chunk 输出流式响应
  - [ ] 实现 Token 计数与成本追踪：自动记录每次调用的 token 使用量和估算成本
  - [ ] 实现 `agent_framework/llm/__init__.py` 统一导出

- [ ] Task 4: 工具系统实现
  - [ ] 实现 `agent_framework/tools/registry.py` — `ToolRegistry`：全局工具注册表（register、list_tools、get_tool、execute_tool）
  - [ ] 实现参数校验（JSON Schema 验证）
  - [ ] 实现执行日志记录（输入、输出、耗时、状态）
  - [ ] 内置基础工具：`agent_framework/tools/builtin/`（calculator、web_search、current_time 等）
  - [ ] 实现 `agent_framework/tools/__init__.py` 统一导出

- [ ] Task 5: Agent 核心引擎实现（ReAct 循环）
  - [ ] 实现 `agent_framework/agent/react_agent.py` — `ReActAgent(BaseAgent)`：
    - `run(task)`：完整的 think → act → observe 循环
    - `run_stream(task)`：流式输出中间思考过程
    - 最大迭代限制（默认 10）
    - 回调机制（`AgentCallback` 接口，输出中间状态事件）
  - [ ] 实现思考过程解析器：从 LLM 响应中提取"思考"、"行动"、"观察"结构
  - [ ] 实现结果格式化：`AgentResult` 包含最终回答、执行轨迹、Token 统计

- [ ] Task 6: 记忆系统实现
  - [ ] 实现 `agent_framework/memory/conversation_memory.py` — `ConversationMemory(BaseMemory)`：
    - sliding window 截断（保留最近 N 轮）
    - `summarize()` 方法压缩历史
  - [ ] 实现 `agent_framework/memory/vector_memory.py` — `VectorMemory(BaseMemory)`：
    - Embedding 模型调用
    - 向量数据库集成（默认 ChromaDB）
    - `add(entry)` 和 `query(text, k)` 方法
  - [ ] 实现记忆融合逻辑：短期 + 长期合并，按相关性排序

- [ ] Task 7: RAG 模块实现
  - [ ] 实现 `agent_framework/rag/loader.py` — 文档加载器（支持 TXT、PDF、Markdown、HTML）
  - [ ] 实现 `agent_framework/rag/splitter.py` — 文档分块器（RecursiveCharacterTextSplitter，chunk_size=1000，chunk_overlap=200）
  - [ ] 实现 `agent_framework/rag/embedding.py` — Embedding 模型封装（支持 OpenAI / 开源模型切换）
  - [ ] 实现 `agent_framework/rag/pipeline.py` — `RAGPipeline`：整合 loading → splitting → embedding → retrieval
  - [ ] 实现 `agent_framework/rag/retriever.py` — 检索器：Top-K 语义检索

- [ ] Task 8: 任务编排引擎实现
  - [ ] 实现 `agent_framework/orchestration/sequential.py` — `SequentialFlow`：顺序执行，前序输出作为后序输入
  - [ ] 实现 `agent_framework/orchestration/parallel.py` — `ParallelFlow`：`asyncio.gather()` 并行执行
  - [ ] 实现 `agent_framework/orchestration/dag.py` — `DAGFlow`：有向无环图工作流，含依赖解析和条件分支

- [ ] Task 9: 多 Agent 协作实现
  - [ ] 实现 `agent_framework/agent/multi_agent.py` — `MultiAgentTeam`：角色分配、Agent 团队管理
  - [ ] 实现 `agent_framework/core/agent_bus.py` — `AgentBus`：Agent 间消息传递（send、broadcast、receive）
  - [ ] 实现协作模式：顺序协商、投票聚合、辩论模式

- [ ] Task 10: 可观测性实现
  - [ ] 实现 `agent_framework/observability/logger.py` — 结构化日志（timestamp、level、module、message、context）
  - [ ] 实现 `agent_framework/observability/tracer.py` — 执行追踪器：记录 LLM 调用、工具调用、ReAct 步骤
  - [ ] 实现 Token 计数器：跟踪每次 Agent 运行的总 token 消耗和成本

- [ ] Task 11: 安全性与配置实现
  - [ ] 实现 `agent_framework/sandbox/subprocess_sandbox.py` — 工具沙箱（超时 30s、资源限制）
  - [ ] 实现 `agent_framework/security/rate_limiter.py` — 速率限制器（RPM/TPM 配置）
  - [ ] 实现 `agent_framework/config.py` — 配置管理完善（环境变量、YAML 文件、字典三种加载方式）

- [ ] Task 12: 单元测试覆盖
  - [ ] `tests/test_core.py` — 核心接口与 Pydantic 模型测试
  - [ ] `tests/test_llm.py` — LLM 调用层测试（mock LiteLLM）
  - [ ] `tests/test_tools.py` — 工具系统测试（注册、发现、执行、参数校验）
  - [ ] `tests/test_agent.py` — ReAct Agent 测试（循环控制、流式输出、回调）
  - [ ] `tests/test_memory.py` — 记忆系统测试（短期窗口截断、向量检索、记忆融合）
  - [ ] `tests/test_rag.py` — RAG 模块测试（文档加载、分块、检索）
  - [ ] `tests/test_orchestration.py` — 编排引擎测试（顺序、并行、DAG）
  - [ ] `tests/test_multi_agent.py` — 多 Agent 协作测试（消息传递、角色分配）
  - [ ] `tests/test_sandbox.py` — 沙箱安全测试

- [ ] Task 13: 使用示例与文档
  - [ ] `examples/basic_agent.py` — 基础 Agent 使用示例
  - [ ] `examples/tool_usage.py` — 工具注册与调用示例
  - [ ] `examples/rag_pipeline.py` — RAG 管道使用示例
  - [ ] `examples/multi_agent.py` — 多 Agent 协作示例
  - [ ] `examples/orchestration.py` — 任务编排示例
  - [ ] 确保所有示例可执行并输出预期结果

# Task Dependencies
- Task 2（核心接口）依赖 Task 1（项目结构）
- Task 3（LLM 层）、Task 4（工具系统）、Task 6（记忆系统）依赖 Task 2（需要核心接口定义）
- Task 5（Agent 引擎）依赖 Task 3 和 Task 4（需要 LLM 和工具系统）
- Task 7（RAG）依赖 Task 6（需要记忆系统中的向量存储）
- Task 8（编排引擎）依赖 Task 5（需要 Agent 执行器）
- Task 9（多 Agent 协作）依赖 Task 5 和 Task 8（需要 Agent 引擎和编排）
- Task 10（可观测性）可与 Task 3-9 并行开发，但最终需要集成验证
- Task 11（安全性）可与 Task 3-9 并行开发
- Task 12（测试）依赖 Task 2-11（需要实现完后测试）
- Task 13（示例）依赖 Task 2-11
