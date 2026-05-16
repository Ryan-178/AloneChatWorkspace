# Verification Checklist

## 项目初始化 (Task 1)
- [ ] `agent-framework/` 目录结构完整（agent_framework/、tests/、examples/）
- [ ] `pyproject.toml` 配置正确，依赖项完整
- [ ] `agent_framework/__init__.py` 正确导出所有公共接口
- [ ] `CHANGELOG.md` 文件存在且格式正确
- [ ] `.env.example` 包含所有必需的环境变量模板

## 核心接口与模型 (Task 2)
- [ ] `BaseLLM` 抽象类定义了 `chat()` 和 `chat_stream()` 方法签名
- [ ] `BaseTool` 抽象类包含 `name`、`description`、`parameters`、`execute()` 字段/方法
- [ ] `BaseMemory` 抽象类定义了 `add()`、`query()`、`clear()` 方法签名
- [ ] `BaseAgent` 抽象类定义了 `perceive()`、`plan()`、`act()`、`reflect()` 生命周期方法
- [ ] `Orchestrator` 定义了 `run()`、`run_multi()`、`run_workflow()` 方法
- [ ] `AgentMessage` Pydantic 模型包含 id、from、to、content、type、timestamp 字段
- [ ] `AgentConfig` Pydantic 模型支持从环境变量、YAML 文件、字典三种方式加载

## LLM 调用层 (Task 3)
- [ ] `LiteLLMProvider.chat()` 正确调用 LiteLLM 并返回 `Message` 对象
- [ ] `LiteLLMProvider.chat_stream()` 返回异步生成器，逐 chunk 输出流式响应
- [ ] Token 计数自动记录 prompt_tokens、completion_tokens、total_tokens
- [ ] 成本估算基于当前模型定价

## 工具系统 (Task 4)
- [ ] `ToolRegistry.register()` 注册工具并校验名称唯一性
- [ ] `ToolRegistry.list_tools()` 返回所有注册工具的名称和描述
- [ ] `ToolRegistry.get_tool(name)` 返回工具的 JSON Schema 定义
- [ ] `ToolRegistry.execute_tool(name, params)` 校验参数并执行工具
- [ ] 参数校验失败时返回明确的 ValidationError
- [ ] 工具执行日志记录完整（输入、输出、耗时、状态）
- [ ] 内置基础工具（calculator、web_search、current_time）可用

## Agent 核心引擎 (Task 5)
- [ ] `ReActAgent.run()` 执行完整的 think → act → observe 循环
- [ ] 达到 `max_iterations`（默认 10）时终止并返回 `stopped_by_max_iterations: true`
- [ ] `ReActAgent.run_stream()` 通过回调机制实时输出 think/act/observe 中间状态
- [ ] 每个中间状态事件包含 type、content、timestamp
- [ ] `AgentResult` 包含最终回答、执行轨迹、Token 统计

## 记忆系统 (Task 6)
- [ ] `ConversationMemory.add()` 正确追加消息记录
- [ ] `ConversationMemory` 按窗口大小截断，保留最近 N 轮对话
- [ ] `ConversationMemory.summarize()` 压缩历史为摘要
- [ ] `VectorMemory.add()` 调用 Embedding 模型生成向量并存入 ChromaDB
- [ ] `VectorMemory.query(text, k)` 返回语义相似 Top-K 结果，含 content、score、metadata
- [ ] 记忆融合时按 当前对话 > 短期记忆 > 长期记忆 排序

## RAG 模块 (Task 7)
- [ ] 文档加载器支持 TXT、PDF、Markdown、HTML 格式
- [ ] 文档分块器使用 RecursiveCharacterTextSplitter（chunk_size=1000，chunk_overlap=200）
- [ ] Embedding 模型可切换（默认 text-embedding-ada-002）
- [ ] `RAGPipeline.ingest()` 完整执行加载→分块→Embedding→存储流程
- [ ] `RAGPipeline.retrieve(query, k)` 返回 Top-K 结果，含 content、score、source

## 任务编排引擎 (Task 8)
- [ ] `SequentialFlow` 按顺序执行任务，前序输出作为后序输入
- [ ] 顺序执行中任一任务失败则中止流程
- [ ] `ParallelFlow` 使用 `asyncio.gather()` 并行执行，返回合并结果
- [ ] `DAGFlow` 根据依赖关系自动解析执行顺序
- [ ] DAGFlow 支持条件分支
- [ ] DAGFlow 返回完整执行轨迹（节点ID、状态、输入、输出、耗时）

## 多 Agent 协作 (Task 9)
- [ ] `AgentBus.send(from, to, message)` 正确传递消息
- [ ] `AgentBus.broadcast(from, message)` 广播给所有 Agent
- [ ] 每个 Agent 配置 role 和 backstory，自动注入 system prompt
- [ ] 顺序协商模式按指定顺序依次执行各 Agent
- [ ] 投票聚合模式收集所有 Agent 输出后汇总

## 可观测性 (Task 10)
- [ ] 结构化日志包含 timestamp、level、module、message、context
- [ ] 执行追踪器记录所有 LLM 调用的请求/响应/Token 数
- [ ] 执行追踪器记录所有工具调用的输入/输出/耗时
- [ ] 执行追踪器记录 ReAct 循环的完整步骤
- [ ] 总耗时和总 Token 消耗正确统计

## 安全性 (Task 11)
- [ ] 工具沙箱设置超时限制（默认 30 秒）
- [ ] 速率限制器按 RPM/TPM 配置排队或拒绝请求
- [ ] 速率限制错误返回 RateLimitError，含 retry_after_seconds
- [ ] 配置管理支持环境变量加载（敏感信息不硬编码）

## 测试覆盖 (Task 12)
- [ ] 核心模块测试覆盖率 > 80%
- [ ] 所有测试用例通过
- [ ] 测试使用 mock/隔离方案，不依赖外部 LLM 或数据库服务

## 示例与文档 (Task 13)
- [ ] `examples/basic_agent.py` 可运行并输出预期结果
- [ ] `examples/tool_usage.py` 可运行并输出预期结果
- [ ] `examples/rag_pipeline.py` 可运行并输出预期结果
- [ ] `examples/multi_agent.py` 可运行并输出预期结果
- [ ] `examples/orchestration.py` 可运行并输出预期结果
- [ ] 不包含任何模拟数据、假字段、假示例、假枚举
