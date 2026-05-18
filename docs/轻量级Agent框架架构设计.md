# 轻量级Agent框架架构设计

## 设计原则

基于B/C/D三端框架调研，本框架遵循以下设计原则：

1. **轻量级起步**: 核心简单，通过组合实现复杂能力，避免过度抽象
2. **聊天原生**: 与聊天应用深度融合，消息即任务、会话即记忆
3. **渐进式演进**: 从简单ReAct开始，逐步增加复杂度
4. **无第三方Agent框架依赖**: 只使用LiteLLM等基础工具库
5. **状态管理清晰**: 简单明确的状态机制，不需要一开始就用图

## 核心架构

### 整体分层结构

```
┌─────────────────────────────────────────────────────┐
│                   应用层 (Application)                │
│  ┌───────────────────────────────────────────────┐  │
│  │  聊天集成 (Chat Integration)                   │  │
│  │  - 消息→任务转换                              │  │
│  │  - 流式UI响应                                 │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  编排层 (Orchestration)              │
│  ┌───────────────────────────────────────────────┐  │
│  │  AgentOrchestrator                            │  │
│  │  - 单Agent执行                                │  │
│  │  - 多Agent协作                                │  │
│  │  - 状态管理                                   │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   核心层 (Core)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Agent     │  │    Tool      │  │  Memory   │ │
│  │  (智能体)   │  │   (工具)     │  │  (记忆)   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
│  ┌───────────────────────────────────────────────┐  │
│  │               LLM Provider                    │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 核心抽象设计

### 1. Agent抽象

```python
class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"
    ERROR = "error"

class BaseAgent:
    """基础Agent类"""
    def __init__(self, name, llm, tools=None, memory=None):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self.state = AgentState.IDLE
        self.max_iterations = 10
    
    async def run(self, task: str) -> AgentResult:
        """执行任务的主循环（ReAct模式）"""
        pass
    
    async def run_stream(self, task: str):
        """流式执行任务"""
        pass
```

### 2. Tool抽象

```python
class Tool:
    """工具类 - 简化设计，函数注册模式"""
    def __init__(self, name, description, func, params_schema=None):
        self.name = name
        self.description = description
        self.func = func
        self.params_schema = params_schema or {}
    
    async def execute(self, **kwargs):
        """执行工具"""
        pass
    
    def to_openai_format(self):
        """转换为OpenAI工具格式"""
        pass
```

### 3. Memory抽象

```python
class ConversationMemory:
    """会话记忆 - 简单实现"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        pass
    
    def get_history(self, limit=None):
        pass

class VectorMemory:
    """向量记忆 - 可选组件"""
    pass
```

### 4. LLM Provider抽象

```python
class LLMProvider:
    """LLM提供者 - 封装LiteLLM"""
    def __init__(self, config):
        self.config = config
    
    async def chat(self, messages, stream=False):
        pass
```

## 执行流程

### ReAct循环流程

```
用户输入
   │
   ▼
┌─────────┐
│ 思考    │ → 决定下一步行动
└────┬────┘
     │
     ├─ 需要工具? ──是──► ┌─────────┐
     │                     │ 执行工具│
     │                     └────┬────┘
     │                          │
     │                          ▼
     │                     ┌─────────┐
     │                     │ 观察结果│
     │                     └────┬────┘
     │                          │
     │                          └───┐
     │                              │
     │                              ▼
     │                    回到思考步骤
     │
     └─ 否 ──► ┌─────────┐
               │ 给出答案│
               └────┬────┘
                    │
                    ▼
               任务完成
```

## 与聊天应用集成

### 消息协议扩展

```python
class AgentMessage:
    role: str  # user/assistant/tool
    content: str
    agent_state: Optional[AgentState]
    tool_calls: Optional[List]
    thought: Optional[str]  # Agent思考过程
```

### 会话绑定

每个聊天会话绑定一个Agent实例，会话历史自动成为Agent的记忆。

## 演进路线

### Phase 1: 最小可用版本 (MVP)
- [x] 基础LLM封装 (LiteLLM)
- [x] 简单Tool系统
- [x] 基础ReAct Agent
- [x] 流式响应
- [x] 会话记忆

### Phase 2: 多Agent协作
- [ ] Agent Bus消息总线
- [ ] 简单多Agent编排
- [ ] 角色定义

### Phase 3: 企业特性
- [ ] 状态持久化
- [ ] 人在回路
- [ ] 可观测性增强

## 文件结构

```
agent_framework/
├── __init__.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── agent.py          # Agent抽象与实现
│   ├── tool.py           # Tool抽象与实现
│   ├── memory.py         # Memory抽象与实现
│   ├── llm.py            # LLM封装
│   └── types.py          # 数据类型定义
├── tools/
│   ├── __init__.py
│   ├── builtin/          # 内置工具
│   └── registry.py       # 工具注册
├── orchestration/
│   ├── __init__.py
│   └── orchestrator.py   # 编排器
└── utils/
    ├── __init__.py
    └── logger.py
```
