# AloneChat Workspace Code Wiki

> 本文档详细描述 AloneChat Workspace 项目的架构、模块职责、核心类和函数、依赖关系及运行方式。

## 目录

- [项目概述](#项目概述)
- [项目结构](#项目结构)
- [核心架构](#核心架构)
- [agent-framework 核心模块](#agent-framework-核心模块)
  - [core 核心抽象层](#core-核心抽象层)
  - [agent Agent 实现层](#agent-agent-实现层)
  - [gateway 网关层](#gateway-网关层)
  - [llm LLM 提供商](#llm-llm-提供商)
  - [memory 记忆系统](#memory-记忆系统)
  - [rag RAG 检索系统](#rag-rag-检索系统)
  - [tools 工具系统](#tools-工具系统)
  - [services 服务层](#services-服务层)
  - [orchestration 编排系统](#orchestration-编排系统)
  - [deepseek_optimization DeepSeek 优化](#deepseek_optimization-deepseek-优化)
  - [observability 可观测性](#observability-可观测性)
  - [security 安全模块](#security-安全模块)
  - [configs 配置](#configs-配置)
- [user-client 前端模块](#user-client-前端模块)
- [依赖关系](#依赖关系)
- [运行方式](#运行方式)
- [API 接口](#api-接口)

---

## 项目概述

**AloneChat Workspace** 是一个集成了实时聊天应用与生产级 AI Agent 框架的全栈协作平台，提供以下核心能力：

| 能力 | 说明 |
|------|------|
| 实时聊天 | WebSocket 即时通讯，支持私聊、群组、消息历史、文件共享 |
| Agent 网关 | 生产级 Agent 运行时，支持 ReAct 推理、工具调用、会话管理 |
| 多 Agent 编排 | Multi-Agent 团队协作，支持顺序讨论、广播、DAG 工作流 |
| RAG 检索 | ChromaDB 向量存储，支持文档加载、分块、嵌入、检索 |
| MCP 市场 | Model Context Protocol 服务器管理，动态扩展 Agent 能力 |
| DeepSeek 优化 | 百万级上下文优化：语义缓存、消息压缩、重要性排序 |
| 意图澄清 | MTC 模式：自动识别模糊需求，生成追问表单，任务分解 |

---

## 项目结构

```
AloneChat-workspace/
├── agent-framework/                 # AI Agent 框架 (Python)
│   ├── agent_framework/             # 核心包
│   │   ├── core/                    # 核心抽象层
│   │   ├── agent/                   # Agent 实现层
│   │   ├── gateway/                 # 网关层
│   │   ├── llm/                    # LLM 提供商
│   │   ├── memory/                  # 记忆系统
│   │   ├── rag/                     # RAG 检索系统
│   │   ├── tools/                   # 工具系统
│   │   ├── services/                # 服务层
│   │   ├── orchestration/           # 编排系统
│   │   ├── deepseek_optimization/   # DeepSeek 优化
│   │   ├── observability/           # 可观测性
│   │   ├── security/                # 安全模块
│   │   ├── sandbox/                 # 沙箱执行
│   │   ├── channels/                # 通道
│   │   └── configs/                 # 配置
│   ├── examples/                    # 使用示例
│   ├── tests/                       # 测试用例
│   ├── gateway_main.py              # 网关启动脚本
│   ├── config.yaml                  # 配置文件
│   └── pyproject.toml              # 项目配置
│
├── user-client/                     # 前端应用 (Next.js)
│   ├── src/
│   │   ├── app/                     # 页面路由
│   │   ├── components/              # React 组件
│   │   ├── hooks/                   # 自定义 Hooks
│   │   ├── stores/                  # 状态管理 (Zustand)
│   │   └── types/                   # TypeScript 类型
│   └── package.json
│
├── docs/                            # 文档
├── bugs/                            # Bug 追踪
└── README.md                        # 项目说明
```

---

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│   │  Next.js    │  │ WebSocket   │  │   shadcn/ui     │     │
│   │  16         │  │   Client    │  │   组件库         │     │
│   └─────────────┘  └─────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        后端层                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│   │  FastAPI    │  │   JWT Auth  │  │   WebSocket     │     │
│   │  Web框架    │  │   认证      │  │   Manager       │     │
│   └─────────────┘  └─────────────┘  └─────────────────┘     │
│                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│   │ PostgreSQL  │  │    Redis    │  │  Agent Gateway  │     │
│   │   数据库    │  │   缓存      │  │    18789        │     │
│   └─────────────┘  └─────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Framework                          │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                    Agent Bus                        │    │
│   │              (消息总线, Agent 通信)                  │    │
│   └─────────────────────────────────────────────────────┘    │
│                              │
│   ┌──────────────┬──────────────┬────────────────────────┐ │
│   │ ReAct Agent  │ Multi-Agent  │     MTC Agent          │ │
│   │ (推理+工具)   │  (团队协作)   │   (意图澄清+任务规划)    │ │
│   └──────────────┴──────────────┴────────────────────────┘ │
│                              │
│   ┌──────────────┬──────────────┬────────────────────────┐ │
│   │ LiteLLM      │ Tool Registry│    RAG Pipeline       │ │
│   │ (多模型网关)  │ (工具注册)    │   (向量检索)           │ │
│   └──────────────┴──────────────┴────────────────────────┘ │
│                              │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              DeepSeek Optimization                   │  │
│   │  ┌──────────┬───────────┬──────────┬────────────┐  │  │
│   │  │ Semantic │  Context   │ Message  │  MCP      │  │  │
│   │  │  Cache   │ Compressor │  Ranker  │ Marketplace│ │  │
│   │  └──────────┴───────────┴──────────┴────────────┘  │  │
│   └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## agent-framework 核心模块

### core 核心抽象层

核心抽象层定义了 Agent 框架的基础接口和类型。

#### 文件结构

```
agent_framework/core/
├── __init__.py           # 模块导出
├── base_agent.py         # Agent 基类
├── base_llm.py            # LLM 基类
├── base_tool.py           # Tool 基类
├── base_memory.py         # Memory 基类
├── orchestrator.py        # 编排器基类
├── agent_bus.py           # Agent 消息总线
├── task.py                # 任务定义
├── types.py               # 类型定义
└── config.py              # 配置管理
```

#### 核心类和函数

##### BaseAgent (base_agent.py)

**职责**: 所有 Agent 的抽象基类，定义 Agent 的核心行为接口。

```python
class BaseAgent(ABC):
    def __init__(
        self,
        llm: BaseLLM,
        memory: Optional[BaseMemory] = None,
        max_iterations: int = 10,
        name: str = "agent",
    )
```

**核心方法**:

| 方法 | 说明 |
|------|------|
| `perceive(task)` | 感知阶段 - 解析输入任务 |
| `plan(context)` | 规划阶段 - 制定执行计划 |
| `act(plan)` | 执行阶段 - 执行计划 |
| `reflect(result)` | 反思阶段 - 评估结果 |
| `run(task)` | 同步运行 Agent |
| `run_stream(task)` | 流式运行 Agent |

**相关类型**:

```python
class AgentEvent(BaseModel):
    type: str              # 事件类型: think, act, observe, final
    content: str           # 事件内容
    timestamp: datetime    # 时间戳
    metadata: Dict[str, Any] # 元数据

class AgentResult(BaseModel):
    answer: str                              # 最终答案
    trajectory: List[Dict[str, Any]]        # 执行轨迹
    usage: UsageInfo                         # Token 使用统计
    stopped_by_max_iterations: bool         # 是否因最大迭代次数停止
    total_time_ms: float                     # 总耗时(毫秒)
```

---

##### BaseLLM (base_llm.py)

**职责**: LLM 提供商的抽象基类，统一 LLM 调用接口。

```python
class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[Message], config: Optional[LLMConfig] = None) -> Message

    @abstractmethod
    async def chat_stream(self, messages: List[Message], config: Optional[LLMConfig] = None) -> AsyncGenerator[Chunk, None]
```

**核心类型**:

```python
class Message(BaseModel):
    role: str                               # 角色: system, user, assistant, tool
    content: str                            # 消息内容
    name: Optional[str]                     # 工具名称(工具消息)
    tool_calls: Optional[List[Dict]]        # 工具调用列表
    tool_call_id: Optional[str]             # 工具调用ID

class LLMConfig(BaseModel):
    model: str = "gpt-4o"                   # 模型名称
    api_key: Optional[str]                  # API 密钥
    api_base: Optional[str]                 # API 基础URL
    temperature: float = 0.7                # 温度参数
    max_tokens: Optional[int] = 4096        # 最大Token数
    top_p: Optional[float] = 1.0            # Top-p采样
    timeout: Optional[int] = 60             # 超时时间(秒)

class UsageInfo(BaseModel):
    prompt_tokens: int                      # 提示Token数
    completion_tokens: int                  # 完成Token数
    total_tokens: int                       # 总Token数
    estimated_cost: float                    # 预估成本
```

---

##### ToolResult / BaseTool (base_tool.py)

**职责**: 定义工具的抽象接口和结果格式。

```python
class ToolResult(BaseModel):
    success: bool                           # 是否成功
    data: Any                               # 结果数据
    error: Optional[str]                    # 错误信息
    execution_time_ms: float                 # 执行时间(毫秒)
    timestamp: datetime                      # 时间戳

class BaseTool(ABC):
    name: str                                # 工具名称
    description: str                          # 工具描述
    parameters: Dict[str, Any]                # 参数模式(JSON Schema)
    
    @abstractmethod
    def execute(self, **kwargs) -> Any
```

---

##### AgentBus (agent_bus.py)

**职责**: Agent 间的消息总线，支持 Agent 间通信和广播。

```python
class AgentBus:
    def __init__(self)
    
    def register(self, agent_id: str, agent: Any) -> None        # 注册Agent
    def unregister(self, agent_id: str) -> None                 # 注销Agent
    
    def send(self, from_agent: str, to_agent: str, content: str, 
             msg_type: MessageType = MessageType.QUESTION, 
             metadata: Optional[Dict] = None) -> AgentMessage    # 发送消息
    
    def broadcast(self, from_agent: str, content: str, 
                  msg_type: MessageType = MessageType.BROADCAST,
                  metadata: Optional[Dict] = None) -> List[AgentMessage]  # 广播
    
    def receive(self, agent_id: str, limit: int = 100) -> List[AgentMessage]  # 接收消息
    def get_conversation(self, agent_a: str, agent_b: str, 
                        limit: int = 100) -> List[AgentMessage]              # 获取对话
```

---

##### Orchestrator (orchestrator.py)

**职责**: 工作流编排器基类，定义编排接口。

```python
class Orchestrator(ABC):
    @abstractmethod
    def run(self, agent: Any, task: str) -> Any                  # 运行单个Agent
    
    @abstractmethod
    def run_multi(self, agents: List[Any], task: str) -> List[Any]  # 运行多个Agent
    
    @abstractmethod
    def run_workflow(self, graph: WorkflowGraph, 
                     initial_input: Any) -> Dict[str, Any]        # 运行工作流

class WorkflowNode(BaseModel):
    id: str                                  # 节点ID
    agent: Optional[Any]                     # Agent实例或任务函数
    dependencies: List[str]                  # 依赖节点ID列表
    condition: Optional[str]                 # 分支条件表达式
    input_transform: Optional[str]           # 输入转换表达式

class WorkflowGraph(BaseModel):
    nodes: List[WorkflowNode]                 # 节点列表
    edges: List[tuple]                       # 边列表
```

---

### agent Agent 实现层

Agent 实现层包含具体的 Agent 类型实现。

#### 文件结构

```
agent_framework/agent/
├── __init__.py
├── react_agent.py          # ReAct Agent 实现
├── multi_agent.py          # Multi-Agent 团队
├── mtc_agent.py            # MTC Agent (意图澄清)
├── intent_clarifier.py     # 意图澄清器
├── task_planner.py         # 任务规划器
├── code_agent.py           # Code Agent
├── code_prompts.py         # Code 模式提示词
├── mtc_prompts.py          # MTC 模式提示词
└── multi_agent.py         # 多Agent协作
```

#### 核心类和函数

##### ReActAgent (react_agent.py)

**职责**: 基于 ReAct (Reasoning + Acting) 模式的 Agent 实现，结合推理和工具执行。

```python
class ReActAgent(BaseAgent):
    def __init__(
        self,
        llm,                                    # LLM 提供商
        tool_registry: Optional[ToolRegistry],  # 工具注册表
        memory=None,                            # 记忆系统
        max_iterations: int = 10,              # 最大迭代次数
        name: str = "react_agent",              # Agent 名称
        system_prompt: Optional[str] = None,    # 系统提示词
    )
```

**核心方法**:

| 方法 | 说明 |
|------|------|
| `run(task)` | 同步执行任务 |
| `run_stream(task)` | 流式执行任务 |
| `add_callback(callback)` | 添加事件回调 |

**执行流程**:

1. 构建包含系统提示词的消息列表
2. 循环迭代 (最多 max_iterations 次):
   - 调用 LLM 生成响应
   - 解析响应，提取 Thought/Action/Final Answer
   - 如果是 Final Answer，返回结果
   - 如果是 Action，执行工具并添加 Observation
3. 返回最终结果或最后一步的思考

**解析响应格式**:

```
Thought: <推理过程>
Action: tool_name({"param": "value"})
```

或

```
Thought: <推理过程>
Final Answer: <最终答案>
```

---

##### MultiAgentTeam (multi_agent.py)

**职责**: 多 Agent 团队协作，支持顺序讨论、广播、投票聚合等协作模式。

```python
class MultiAgentTeam:
    def __init__(self, bus: Optional[AgentBus] = None)
    
    def add_agent(self, agent_id: str, agent: BaseAgent, 
                  role: str = "", backstory: str = "") -> None  # 添加Agent
    
    def remove_agent(self, agent_id: str) -> None                # 移除Agent
    
    def send(self, from_agent: str, to_agent: str, 
             content: str, msg_type: MessageType = MessageType.QUESTION) -> AgentMessage
    
    def broadcast(self, from_agent: str, content: str, 
                  msg_type: MessageType = MessageType.BROADCAST) -> List[AgentMessage]
    
    def sequential_discussion(self, task: str, 
                              agent_order: Optional[List[str]] = None) -> Dict[str, Any]
    
    def vote_aggregation(self, task: str, 
                        agents: Optional[List[str]] = None) -> Dict[str, Any]
```

**协作模式**:

1. **顺序讨论 (sequential_discussion)**: Agent 按顺序执行，每个 Agent 的输出作为下一个 Agent 的输入
2. **投票聚合 (vote_aggregation)**: 所有 Agent 并行处理同一任务，汇总结果

---

##### MTCAgent (mtc_agent.py)

**职责**: MTC (More Than Coding) 模式 Agent，面向非开发用户的通用办公任务 Agent，具备意图澄清和任务规划能力。

```python
class MTCAgent(ReActAgent):
    def __init__(
        self,
        llm,
        tool_registry: Optional[ToolRegistry] = None,
        memory=None,
        max_iterations: int = 10,
        name: str = "mtc_agent",
        system_prompt: Optional[str] = None,
        config=None,
    )
```

**核心方法**:

| 方法 | 说明 |
|------|------|
| `clarify_intent(task)` | 意图澄清，返回需要澄清的问题 |
| `collect_clarification_answers(answers)` | 收集用户澄清回答 |
| `plan_task(task)` | 任务规划，分解复杂任务 |
| `get_task_progress()` | 获取任务进度 |
| `run(task)` | 执行任务 |

**意图澄清流程**:

1. 分析任务是否需要澄清 (基于关键词和长度)
2. 生成追问表单 (最多3个问题):
   - 输出格式选择
   - 详细程度选择
   - 目标读者(可选)
3. 整合用户回答为完整需求

**任务规划流程**:

1. 估算任务复杂度
2. 根据任务类型分解子任务:
   - 文档类: 分析需求 → 收集信息 → 生成大纲 → 填充内容 → 格式化输出
   - 数据类: 加载数据 → 数据清洗 → 统计分析 → 生成图表 → 输出报告
   - 调研类: 提取关键词 → 执行搜索 → 筛选整理 → 生成报告
3. 构建 DAG 图
4. 按拓扑排序执行

---

##### IntentClarifier (intent_clarifier.py)

**职责**: 意图澄清系统，用于澄清模糊的用户需求。

```python
class IntentClarifier:
    def __init__(self, llm, max_questions: int = 3)
    
    def should_clarify(self, task: str) -> bool    # 判断是否需要澄清
    def analyze(self, task: str) -> Dict[str, Any]  # 分析任务
    def generate_questions(self, task: str) -> List[Dict[str, Any]]  # 生成问题
    def collect_answers(self, answers: Dict[str, Any]) -> None  # 收集回答
    def integrate(self, original_task: str) -> str  # 整合为完整需求
    def reset(self) -> None                          # 重置状态
```

---

##### TaskPlanner (task_planner.py)

**职责**: 任务规划器，将复杂任务分解为可执行的子任务 DAG。

```python
class TaskPlanner:
    def __init__(self, llm)
    
    def decompose(self, task: str) -> List[Task]           # 任务分解
    def identify_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]
    def build_dag(self, tasks: List[Task]) -> Dict[str, Any]  # 构建DAG
    def get_execution_order(self, tasks: List[Task]) -> List[List[Task]]  # 拓扑排序
    def estimate_complexity(self, task: str) -> str         # 复杂度估算
```

---

### gateway 网关层

网关层提供 Agent 的 HTTP/WebSocket 访问接口。

#### 文件结构

```
agent_framework/gateway/
├── __init__.py
├── core.py            # 网关核心
├── session.py         # 会话管理
├── router.py          # 消息路由
├── types.py           # 类型定义
├── tools.py           # 工具执行器
├── auth.py            # 认证
├── api.py             # REST API
├── websocket.py       # WebSocket 处理
├── user_api.py        # 用户 API
├── agent.py           # Agent API
└── types.py           # 类型定义
```

#### 核心类和函数

##### GatewayCore (core.py)

**职责**: 网关核心，处理 WebSocket 连接和消息路由。

```python
class GatewayCore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 18789,
        auth_secret: Optional[str] = None,
        max_request_size: int = 1024 * 1024,  # 1MB
    )
```

**核心方法**:

| 方法 | 说明 |
|------|------|
| `start()` | 启动网关服务器 |
| `register_handler(msg_type, handler)` | 注册消息处理器 |
| `handle_request(request)` | 处理 HTTP 请求 |

**消息类型**:

| 类型 | 说明 |
|------|------|
| `connect` | 连接认证 |
| `message` | 普通消息 |
| `tool_call` | 工具调用 |
| `heartbeat` | 心跳检测 |

**WebSocket 响应类型**:

| 类型 | 说明 |
|------|------|
| `connected` | 连接成功 |
| `thinking` | 思考中 |
| `acting` | 执行工具 |
| `observation` | 工具结果 |
| `final` | 最终答案 |
| `error` | 错误 |

---

##### SessionManager (session.py)

**职责**: 会话管理器，实现会话车道隔离，避免任务冲突。

```python
class SessionManager:
    def __init__(self, timeout_seconds: int = 3600)
    
    def create_session(self, user_id: str, channel: str = "chat_app", 
                       agent_config: Optional[Dict] = None) -> Session
    
    def get_session(self, session_id: str) -> Optional[Session]
    
    def get_or_create_session(self, session_key: str, user_id: str, 
                              channel: str = "chat_app") -> Session
    
    def update_session_state(self, session_id: str, state: SessionState) -> bool
    
    def acquire_session_lane(self, session_id: str) -> bool   # 获取会话车道
    def release_session_lane(self, session_id: str)           # 释放会话车道
    
    def list_active_sessions(self) -> List[Session]
    def cleanup_expired_sessions(self) -> int
    def delete_session(self, session_id: str) -> bool
    def get_stats(self) -> Dict
```

**会话状态**:

```python
class SessionState(str, Enum):
    IDLE = "idle"              # 空闲
    RUNNING = "running"        # 运行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败
```

---

### llm LLM 提供商

#### LiteLLMProvider (litellm_provider.py)

**职责**: 基于 LiteLLM 的统一 LLM 网关，支持 OpenAI、DeepSeek、Anthropic 等多种模型。

```python
class LiteLLMProvider(BaseLLM):
    def __init__(self, config: Optional[LLMConfig] = None)
    
    def chat(self, messages: List[Message], 
             config: Optional[LLMConfig] = None) -> Message
    
    async def chat_stream(self, messages: List[Message], 
                          config: Optional[LLMConfig] = None) -> AsyncGenerator[Chunk, None]
```

---

### memory 记忆系统

#### 文件结构

```
agent_framework/memory/
├── __init__.py
├── conversation_memory.py   # 对话记忆
└── vector_memory.py         # 向量记忆
```

#### ConversationMemory (conversation_memory.py)

**职责**: 基于滑动窗口的对话记忆管理。

```python
class ConversationMemory(BaseMemory):
    def __init__(self, window_size: int = 10)
    
    def add(self, role: str, content: str) -> None
    def get_messages(self) -> List[Message]
    def clear(self) -> None
```

#### VectorMemory (vector_memory.py)

**职责**: 基于向量数据库的记忆存储和检索。

```python
class VectorMemory(BaseMemory):
    def __init__(
        self,
        collection_name: str = "memory",
        persist_path: str = "./data/chroma",
        embedding_model: str = "text-embedding-ada-002",
    )
    
    def add(self, content: str, metadata: Optional[Dict] = None) -> str
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]
    def get_relevant(self, query: str, threshold: float = 0.7) -> List[Dict]
```

---

### rag RAG 检索系统

#### 文件结构

```
agent_framework/rag/
├── __init__.py
├── loader.py         # 文档加载
├── splitter.py       # 文本分块
├── embedding.py      # 向量嵌入
├── retriever.py      # 检索器
└── pipeline.py       # RAG 流水线
```

#### RAGPipeline (pipeline.py)

**职责**: 完整的 RAG 流水线，支持文档加载、分块、嵌入、检索。

```python
class RAGPipeline:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = "text-embedding-ada-002",
        embedding_api_key: Optional[str] = None,
        collection_name: str = "rag_docs",
        persist_path: str = "./chroma_db",
    )
    
    def ingest(self, path: str) -> int        # 导入文档
    def ingest_text(self, text: str, source: str = "inline") -> int  # 导入文本
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]  # 检索
```

#### 加载器 (loader.py)

```python
def load_document(path: str) -> Document
```

支持格式: PDF, DOCX, TXT, Markdown, HTML 等。

#### 分割器 (splitter.py)

```python
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200)
    def split_document(self, document: Document) -> List[DocumentChunk]
```

#### 嵌入 (embedding.py)

```python
class EmbeddingProvider:
    def __init__(self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None)
    def embed(self, texts: List[str]) -> List[List[float]]
```

#### 检索器 (retriever.py)

```python
class Retriever:
    def __init__(self, collection, embedding_provider)
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]
```

---

### tools 工具系统

#### 文件结构

```
agent_framework/tools/
├── __init__.py
├── registry.py              # 工具注册表
├── builtin/                  # 内置工具
│   ├── __init__.py
│   ├── calculator.py         # 计算器
│   ├── current_time.py       # 当前时间
│   └── web_search.py         # 网络搜索
├── code/                     # 代码工具
│   ├── __init__.py
│   └── code_tools.py         # 代码执行
└── mtc/                      # MTC 专用工具
    ├── __init__.py
    └── document_tools.py     # 文档工具
```

#### ToolRegistry (registry.py)

**职责**: 工具注册表，管理所有可用工具。

```python
class ToolRegistry:
    def __init__(self)
    
    def register(self, tool: BaseTool) -> None          # 注册工具
    def unregister(self, name: str) -> None             # 注销工具
    def list_tools(self) -> List[Dict[str, str]]        # 列出工具
    def get_tool(self, name: str) -> Optional[ToolDef]  # 获取工具定义
    def execute_tool(self, name: str, 
                     params: Dict[str, Any]) -> ToolResult  # 执行工具
```

#### 内置工具

##### CalculatorTool (builtin/calculator.py)

```python
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行数学计算"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        },
        "required": ["expression"]
    }
    
    def execute(self, expression: str) -> str
```

##### CurrentTimeTool (builtin/current_time.py)

```python
class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "获取当前时间"
    parameters = {"type": "object", "properties": {}}
    
    def execute(self) -> str
```

##### WebSearchTool (builtin/web_search.py)

```python
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "执行网络搜索"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索查询"}
        },
        "required": ["query"]
    }
    
    def execute(self, query: str) -> str
```

---

### services 服务层

#### 文件结构

```
agent_framework/services/
├── __init__.py
├── file_processors/          # 文件处理器
│   ├── __init__.py
│   ├── registry.py           # 处理器注册表
│   ├── base_processor.py      # 基类
│   ├── document_processor.py  # 文档处理器
│   ├── spreadsheet_processor.py  # 电子表格处理器
│   ├── presentation_processor.py  # 演示文稿处理器
│   ├── code_processor.py      # 代码处理器
│   ├── image_processor.py     # 图片处理器
│   └── text_processor.py      # 文本处理器
├── file_generators/          # 文件生成器
│   ├── __init__.py
│   ├── generator_service.py   # 生成服务
│   └── prompts.py             # 提示词
├── task_planner/              # 任务规划
│   ├── __init__.py
│   ├── planner.py            # 规划器
│   └── prompts.py            # 提示词
└── skills/                    # 技能
    ├── __init__.py
    ├── registry.py           # 技能注册表
    └── executor.py           # 技能执行器
```

#### FileProcessorRegistry (file_processors/registry.py)

**职责**: 统一管理和调度各种文件处理器。

```python
class FileProcessorRegistry:
    def __init__(self)
    
    def register(self, processor: BaseFileProcessor) -> None      # 注册处理器
    def get_processor(self, extension: str) -> Optional[BaseFileProcessor]  # 获取处理器
    def get_processor_for_file(self, file_path: Path) -> Optional[BaseFileProcessor]
    def list_supported_extensions(self) -> list[str]
    def list_processors(self) -> list[str]
```

#### BaseFileProcessor (file_processors/base_processor.py)

**职责**: 文件处理器的抽象基类。

```python
class BaseFileProcessor(ABC):
    @abstractmethod
    def get_supported_extensions(self) -> List[str]
    
    @abstractmethod
    def process(self, file_path: Path) -> Dict[str, Any]
    
    def extract_text(self, file_path: Path) -> str
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]
```

---

### orchestration 编排系统

#### 文件结构

```
agent_framework/orchestration/
├── __init__.py
├── sequential.py     # 顺序执行
├── parallel.py       # 并行执行
└── dag.py            # DAG 工作流
```

#### DAGOrchestrator (dag.py)

**职责**: DAG 工作流编排器，执行有向无环图工作流。

```python
class DAGOrchestrator(Orchestrator):
    def __init__(self)
    
    def add_node(self, node_id: str, task: Callable, 
                 name: Optional[str] = None) -> 'DAGOrchestrator'
    
    def add_edge(self, from_node: str, to_node: str, 
                 condition: Optional[str] = None) -> 'DAGOrchestrator'
    
    def set_timeout(self, seconds: float) -> 'DAGOrchestrator'
    def validate(self) -> bool                              # 验证DAG有效性
    
    def run_workflow(self) -> DAGWorkflowResult             # 同步运行
    async def run_workflow_async(self) -> DAGWorkflowResult # 异步运行
    
    def run_workflow_from_graph(self, graph: WorkflowGraph, 
                                initial_input: Any) -> Dict[str, Any]
```

**执行结果**:

```python
@dataclass
class DAGWorkflowResult:
    success: bool                              # 是否成功
    outputs: Dict[str, Any]                     # 各节点输出
    results: List[NodeExecutionResult]          # 执行结果列表
    total_duration_ms: float                    # 总耗时
    failed_nodes: List[str]                     # 失败节点
    skipped_nodes: List[str]                    # 跳过节点

@dataclass
class NodeExecutionResult:
    node_id: str
    node_name: str
    status: NodeStatus
    input: Any
    output: Any
    error: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]
    duration_ms: float
    dependencies: List[str]
```

---

### deepseek_optimization DeepSeek 优化

#### 文件结构

```
agent_framework/deepseek_optimization/
├── __init__.py
├── llm/                          # DeepSeek 提供商
│   ├── __init__.py
│   ├── deepseek_provider.py      # DeepSeek V4 Provider
│   ├── model_config.py           # 模型配置
│   └── temperature_controller.py # 温度控制器
├── cache/                         # 缓存系统
│   ├── __init__.py
│   ├── cache_engine.py           # 缓存引擎
│   ├── cache_stats.py            # 缓存统计
│   ├── deepseek_cache.py         # DeepSeek 缓存
│   ├── semantic_cache.py         # 语义缓存
│   └── vector_cache.py           # 向量缓存
├── context/                       # 上下文管理
│   ├── __init__.py
│   ├── mega_context_manager.py   # 百万上下文管理
│   ├── message_ranker.py         # 消息排序
│   ├── context_compressor.py     # 上下文压缩
│   ├── compression_strategy.py   # 压缩策略
│   ├── context_cache.py          # 上下文缓存
│   ├── context_config.py         # 上下文配置
│   ├── context_monitor.py        # 上下文监控
│   ├── context_snapshot.py       # 上下文快照
│   ├── feedback_generator.py     # 反馈生成器
│   ├── semantic_retriever.py     # 语义检索
│   ├── session_manager.py        # 会话管理
│   ├── storage_engine.py         # 存储引擎
│   ├── token_estimator.py        # Token 估算
│   └── window_manager.py         # 窗口管理
├── mcp_marketplace/              # MCP 市场
│   ├── __init__.py
│   ├── client.py                # MCP 客户端
│   ├── loader.py                # MCP 加载器
│   ├── registry.py              # MCP 注册表
│   └── types.py                 # MCP 类型
├── security/                    # 安全模块
│   ├── __init__.py
│   ├── audit_logger.py          # 审计日志
│   ├── data_protection.py       # 数据保护
│   ├── encryption.py            # 加密
│   └── license_manager.py       # 许可证管理
└── swe/                         # 软件工程 Agent
    ├── __init__.py
    └── swe_engine.py            # SWE 引擎
```

#### DeepSeekProvider (llm/deepseek_provider.py)

**职责**: DeepSeek V4 专属 Provider，极致优化，支持 KV Cache 和动态温度调整。

```python
class DeepSeekProvider(BaseLLM):
    def __init__(
        self,
        config: Optional[DeepSeekConfig] = None,
        temperature_controller: Optional[TemperatureController] = None,
        enable_dynamic_temperature: bool = True,
    )
    
    def chat(self, messages: List[Message], 
             config: Optional[DeepSeekConfig] = None) -> Message
    
    async def chat_async(self, messages: List[Message], 
                         config: Optional[DeepSeekConfig] = None) -> Message
    
    async def chat_stream(self, messages: List[Message], 
                          config: Optional[DeepSeekConfig] = None) -> AsyncGenerator[Chunk, None]
    
    def get_usage_stats(self) -> Dict[str, Any]
    def reset_usage(self) -> None
    def set_task_type(self, task_type: TaskType) -> float
    def get_dynamic_temperature(self, context: Optional[str] = None, 
                                feedback: Optional[FeedbackSignal] = None) -> float
    def update_feedback(self, feedback: FeedbackSignal) -> None
```

**KV Cache 支持**:

DeepSeek V4 支持 KV Cache，可显著降低重复输入的成本：

```python
@dataclass
class DeepSeekUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    requests_count: int
    
    # KV Cache 字段
    prompt_cache_hit_tokens: int       # 缓存命中Token数
    prompt_cache_miss_tokens: int      # 缓存未命中Token数
    total_cache_hits: int              # 缓存命中次数
    
    def get_stats(self) -> Dict[str, Any]
```

**定价** (DeepSeek 官方):

| 类型 | 价格 |
|------|------|
| 缓存命中 | 0.1 元/百万 tokens |
| 缓存未命中 | 1 元/百万 tokens |

#### MegaContextManager (context/mega_context_manager.py)

**职责**: 100万上下文智能管理器，协调活跃上下文窗口与本地存储。

```python
class MegaContextManager:
    def __init__(
        self,
        storage_root: Optional[Path] = None,
        max_context_tokens: int = 1000000,
        target_active_tokens: int = 800000,
        token_estimation_mode: EstimationMode = EstimationMode.AUTO,
        session_id: Optional[str] = None,
    )
    
    def set_session_id(self, session_id: str) -> None
    
    def add_message(self, message: Dict[str, Any]) -> ManagedMessage
    def add_messages(self, messages: List[Dict[str, Any]]) -> List[ManagedMessage]
    
    def get_active_context(self, current_usage_tokens: int = 0) -> Tuple[List[Dict], List[ManagedMessage]]
    def get_token_usage(self) -> Dict[str, Any]
    def check_token_budget(self, new_message: Optional[Dict] = None) -> Dict[str, Any]
    
    def optimize_context(self) -> Dict[str, Any]
    def get_stats(self) -> ContextStats
    def get_storage_stats(self)
    def get_archived_files(self)
    def search_archive(self, keyword: str, limit: int = 50) -> List[StoredMessage]
```

**消息重要性分类**:

```python
class ImportanceCategory(str, Enum):
    CRITICAL = "critical"    # 关键信息
    IMPORTANT = "important"  # 重要信息
    NORMAL = "normal"        # 普通信息
    LOW = "low"              # 低价值
    TRIVIAL = "trivial"      # 琐碎信息
```

#### MCPServerRegistry (mcp_marketplace/registry.py)

**职责**: MCP 服务器注册表，管理 Model Context Protocol 服务器。

```python
class MCPServerRegistry:
    def __init__(self)
    
    def register_server(self, name: str, config: MCPServerConfig,
                       description: str = "", version: str = "1.0.0",
                       server_id: Optional[str] = None) -> MCPServer
    
    def get_server(self, server_id: str) -> Optional[MCPServer]
    def get_all_servers(self) -> List[MCPServer]
    
    def update_server(self, server_id: str, name: Optional[str] = None,
                      description: Optional[str] = None,
                      version: Optional[str] = None,
                      config: Optional[MCPServerConfig] = None) -> Optional[MCPServer]
    
    def update_server_status(self, server_id: str, status: ServerStatus,
                             error_message: Optional[str] = None) -> Optional[MCPServer]
    
    def update_server_tools(self, server_id: str, 
                            tools: List) -> Optional[MCPServer]
    
    def unregister_server(self, server_id: str) -> bool
    def get_servers_by_status(self, status: ServerStatus) -> List[MCPServer]
```

---

### observability 可观测性

#### 文件结构

```
agent_framework/observability/
├── __init__.py
├── logger.py      # 日志
├── metrics.py     # 指标
└── tracer.py       # 追踪
```

---

### security 安全模块

#### 文件结构

```
agent_framework/security/
├── __init__.py
└── rate_limiter.py  # 限流
```

---

### configs 配置

#### 文件结构

```
agent_framework/configs/
├── __init__.py
├── models.yaml           # 模型配置
├── prompts.yaml          # 提示词配置
├── skills.yaml           # 技能配置
├── sandbox.yaml          # 沙箱配置
└── intent_clarification.yaml  # 意图澄清配置
```

---

## user-client 前端模块

### 项目结构

```
user-client/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # 认证路由
│   │   │   ├── login/         # 登录页
│   │   │   ├── register/       # 注册页
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/       # 仪表盘路由
│   │   │   ├── chat/          # 聊天页
│   │   │   ├── agent/         # Agent 页
│   │   │   ├── tasks/         # 任务页
│   │   │   ├── skills/        # 技能页
│   │   │   ├── workspace/     # 工作区页
│   │   │   ├── settings/      # 设置页
│   │   │   └── layout.tsx
│   │   ├── layout.tsx         # 根布局
│   │   ├── page.tsx           # 首页
│   │   └── globals.css        # 全局样式
│   │
│   ├── components/            # React 组件
│   │   ├── ui/               # shadcn/ui 组件
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ... (更多组件)
│   │   ├── common/            # 通用组件
│   │   │   ├── logo.tsx
│   │   │   ├── loading.tsx
│   │   │   └── empty-state.tsx
│   │   └── layout/            # 布局组件
│   │       ├── header.tsx
│   │       ├── sidebar.tsx
│   │       ├── mobile-nav.tsx
│   │       └── command-palette.tsx
│   │
│   ├── hooks/                 # 自定义 Hooks
│   │   ├── use-agent-session.ts   # Agent 会话
│   │   └── use-websocket.ts      # WebSocket
│   │
│   ├── stores/                 # Zustand 状态管理
│   │   ├── auth-store.ts       # 认证状态
│   │   ├── chat-store.ts       # 聊天状态
│   │   ├── agent-store.ts       # Agent 状态
│   │   └── ui-store.ts          # UI 状态
│   │
│   └── types/                  # TypeScript 类型
│       ├── agent.ts
│       ├── api.ts
│       ├── auth.ts
│       ├── chat.ts
│       ├── skill.ts
│       └── task.ts
│
├── package.json
├── tsconfig.json
├── next.config.ts
├── tailwind.config.ts
└── components.json             # shadcn/ui 配置
```

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 16 | React 全栈框架 |
| React | 19 | UI 库 |
| Tailwind CSS | 4 | 原子化 CSS |
| shadcn/ui | 4.7 | 组件库 |
| Radix UI | - | 无头组件 |
| Zustand | 5 | 状态管理 |
| Dexie | 4 | IndexedDB 封装 |

### 核心组件

#### Hooks

##### use-agent-session (hooks/use-agent-session.ts)

```typescript
interface UseAgentSession {
  sessionId: string | null;
  isConnected: boolean;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  
  connect(userId: string, sessionKey?: string): Promise<void>;
  disconnect(): void;
  sendMessage(content: string): Promise<void>;
  clearMessages(): void;
}
```

##### use-websocket (hooks/use-websocket.ts)

```typescript
interface UseWebSocket {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  
  connect(url: string): void;
  disconnect(): void;
  send(message: unknown): void;
}
```

#### Stores

##### auth-store (stores/auth-store.ts)

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  
  login(email: string, password: string): Promise<void>;
  register(email: string, password: string, name: string): Promise<void>;
  logout(): void;
}
```

##### chat-store (stores/chat-store.ts)

```typescript
interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  
  createConversation(title?: string): Promise<Conversation>;
  selectConversation(id: string): void;
  deleteConversation(id: string): Promise<void>;
}
```

##### agent-store (stores/agent-store.ts)

```typescript
interface AgentState {
  sessions: AgentSession[];
  activeSessionId: string | null;
  
  createSession(config?: AgentConfig): Promise<AgentSession>;
  selectSession(id: string): void;
  deleteSession(id: string): Promise<void>;
}
```

---

## 依赖关系

### Python 依赖 (agent-framework)

```toml
# 核心依赖
litellm>=1.40.0           # 多模型 LLM 网关
pydantic>=2.5.0           # 数据验证
pydantic-settings>=2.1.0  # 配置管理
chromadb>=0.4.22          # 向量数据库
openai>=1.6.0             # OpenAI 客户端
tiktoken>=0.5.0           # Token 估算
pyyaml>=6.0               # YAML 配置
python-dotenv>=1.0.0      # 环境变量

# Web 框架
fastapi>=0.109.0          # Web 框架
uvicorn>=0.27.0           # ASGI 服务器
websockets>=12.0          # WebSocket
PyJWT>=2.8.0              # JWT 认证

# 文档处理
unstructured>=0.12.0      # 通用文档解析
pdfminer.six>=20221105    # PDF 解析
markdown>=3.5.0           # Markdown 处理
beautifulsoup4>=4.12.0    # HTML 解析
pdfplumber>=0.9.0         # PDF 表格提取
python-docx>=0.8.11       # Word 处理
openpyxl>=3.1.2           # Excel 处理
python-pptx>=0.6.21       # PPT 处理
pandas>=2.0.0             # 数据处理
tabulate>=0.9.0           # 表格格式化

# 其他
tenacity>=8.2.0           # 重试机制
networkx>=3.2.0           # DAG 编排
aiofiles>=23.2.0          # 异步文件操作
httpx>=0.25.0             # HTTP 客户端
Pillow>=10.0.0            # 图片处理
```

### Node.js 依赖 (user-client)

```json
{
  "dependencies": {
    "@radix-ui/react-*": "各版本",     // Radix UI 组件
    "@tanstack/react-query": "^5.100.10", // 数据获取
    "next": "16.2.6",                  // React 框架
    "react": "19.2.4",                 // UI 库
    "react-dom": "19.2.4",             // React DOM
    "shadcn": "^4.7.0",                // UI 组件库
    "zustand": "^5.0.13",              // 状态管理
    "dexie": "^4.4.2",                 // IndexedDB
    "lucide-react": "^1.16.0",         // 图标
    "sonner": "^2.0.7",                // 通知
    "class-variance-authority": "^0.7.1", // 类名变体
    "clsx": "^2.1.1",                  // 条件类名
    "tailwind-merge": "^3.6.0",         // Tailwind 合并
    "cmdk": "^1.1.1"                   // 命令面板
  }
}
```

---

## 运行方式

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (可选)
- Redis 7+ (可选)

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/xiaodu-duhongrui/AloneChat-workspace.git
cd AloneChat-workspace

# 安装 Python 依赖
pip install -e agent-framework

# 安装前端依赖
cd user-client
pnpm install
```

### 配置环境变量

```bash
# agent-framework/.env
DEEPSEEK_API_KEY=sk-your-api-key
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
```

### 启动服务

```bash
# 启动 Agent 网关 (默认端口 18789)
cd agent-framework
python gateway_main.py

# 或指定参数
python gateway_main.py --host 127.0.0.1 --port 18789 --auth-secret your-secret

# 启动前端开发服务器
cd user-client
pnpm dev
```

### 使用 Docker (可选)

```bash
# 使用 Makefile
make install    # 安装依赖
make dev        # 启动开发服务
make test       # 运行测试
```

---

## API 接口

### Agent 网关 WebSocket

**连接地址**: `ws://localhost:18789/ws`

**初始化消息**:

```json
{
  "type": "connect",
  "token": "your-jwt-token",
  "session_key": "session-001"
}
```

**发送消息**:

```json
{
  "type": "message",
  "body": "帮我计算 25 + 36 * 2"
}
```

**接收响应**:

| 事件类型 | 说明 |
|------|------|
| `connected` | 连接成功 |
| `thinking` | 思考中 |
| `acting` | 执行工具 |
| `observation` | 工具结果 |
| `final` | 最终答案 |
| `error` | 错误 |

### REST API

#### 健康检查

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/status` | GET | 网关状态 |
| `/stats` | GET | 统计信息 |

---

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

[MIT License](LICENSE)
