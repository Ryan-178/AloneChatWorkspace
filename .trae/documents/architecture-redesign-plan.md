# AloneWork 架构重构计划 / Architecture Redesign Plan

## 参考架构分析 / Reference Architecture Analysis

### claude-code-claude 核心架构模式 / Core Architecture Patterns

1. **状态管理 (State Management)**
   - `createStore<T>` 自定义 Store 模式，不可变状态
   - `AppState` 全局状态容器，包含 MCP、插件、任务、权限等
   - `useSyncExternalStore` React 集成

2. **工具系统 (Tool System)**
   - `Tool<Input, Output, Progress>` 泛型接口
   - `buildTool()` 工厂函数，提供默认值
   - 权限检查 (`checkPermissions`)、输入验证 (`validateInput`)
   - 进度回调 (`ToolCallProgress`)
   - 并发安全 (`isConcurrencySafe`)

3. **查询引擎 (Query Engine)**
   - `AsyncGenerator` 流式查询循环
   - 自动压缩 (auto-compact)、响应式压缩 (reactive compact)
   - 工具执行与结果处理
   - 上下文管理与预算追踪

4. **命令系统 (Command System)**
   - 模块化命令 (`commands/xxx/index.ts`)
   - 懒加载与特性标志 (feature flags)
   - 技能 (Skills) 与插件 (Plugins) 分离

5. **服务层 (Services Layer)**
   - API 客户端 (多提供商支持)
   - MCP 客户端 (认证、工具、资源)
   - LSP 集成
   - 分析与遥测

---

## 重构目标 / Redesign Goals

1. **统一状态管理** - 从分散的 ConfigManager/SessionManager 迁移到统一的 Store 模式
2. **类型化工具系统** - 实现泛型 Tool 接口，支持权限、验证、进度
3. **流式查询引擎** - AsyncGenerator 模式的查询循环
4. **模块化命令** - 懒加载、特性标志、技能系统
5. **服务层抽象** - 统一的 API/MCP/LSP 服务接口

---

## 实施步骤 / Implementation Steps

### Phase 1: 核心状态管理 (Core State Management)

#### 1.1 创建 Store 基础设施
**文件**: `agent-framework/agent_framework/core/store.py`

```python
from typing import TypeVar, Generic, Callable, Set, Optional
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Store(Generic[T]):
    """响应式状态存储 / Reactive state store"""
    _state: T
    _listeners: Set[Callable[[], None]]
    _on_change: Optional[Callable[[T, T], None]]
    
    def get_state(self) -> T:
        return self._state
    
    def set_state(self, updater: Callable[[T], T]) -> None:
        prev = self._state
        next_state = updater(prev)
        if next_state is prev:
            return
        self._state = next_state
        if self._on_change:
            self._on_change(next_state, prev)
        for listener in self._listeners:
            listener()
    
    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        def unsubscribe():
            self._listeners.discard(listener)
        return unsubscribe

def create_store(initial_state: T, on_change: Optional[Callable] = None) -> Store[T]:
    return Store(_state=initial_state, _listeners=set(), _on_change=on_change)
```

#### 1.2 定义 AppState
**文件**: `agent-framework/agent_framework/core/app_state.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class PermissionMode(Enum):
    DEFAULT = "default"
    PLAN = "plan"
    BYPASS = "bypass"
    YOLO = "yolo"

@dataclass
class ToolPermissionContext:
    mode: PermissionMode = PermissionMode.DEFAULT
    always_allow_rules: Dict[str, List[str]] = field(default_factory=dict)
    always_deny_rules: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class MCPState:
    clients: List[Any] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)
    commands: List[Any] = field(default_factory=list)
    resources: Dict[str, List[Any]] = field(default_factory=dict)

@dataclass
class TaskState:
    id: str
    type: str
    status: str  # pending, running, completed, failed, killed
    description: str
    start_time: float
    end_time: Optional[float] = None

@dataclass
class AppState:
    """全局应用状态 / Global application state"""
    verbose: bool = False
    main_loop_model: Optional[str] = None
    tool_permission_context: ToolPermissionContext = field(default_factory=ToolPermissionContext)
    mcp: MCPState = field(default_factory=MCPState)
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    thinking_enabled: bool = True
    effort_value: Optional[str] = None
    # ... 更多状态字段
```

#### 1.3 迁移 SessionManager 到 Store 模式
**文件**: `alonework-cli/src/alonechat/session/store_session.py`

- 将 SessionManager 重构为基于 Store 的实现
- 保持向后兼容的 API

---

### Phase 2: 类型化工具系统 (Typed Tool System)

#### 2.1 定义 Tool 接口
**文件**: `agent-framework/agent_framework/core/tool.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Any, Optional, Callable, Awaitable
from enum import Enum

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')

class PermissionResult(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"

@dataclass
class ToolResult:
    data: Any
    error: Optional[str] = None
    new_messages: list = field(default_factory=list)

class Tool(ABC, Generic[InputT, OutputT]):
    """工具基类 / Tool base class"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def input_schema(self) -> dict:
        """JSON Schema for input"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: InputT, context: 'ToolUseContext') -> ToolResult:
        pass
    
    def is_enabled(self) -> bool:
        return True
    
    def is_read_only(self, input_data: InputT) -> bool:
        return False
    
    def is_destructive(self, input_data: InputT) -> bool:
        return False
    
    async def validate_input(self, input_data: InputT, context: 'ToolUseContext') -> Optional[str]:
        """返回 None 表示有效，返回字符串表示错误信息"""
        return None
    
    async def check_permissions(self, input_data: InputT, context: 'ToolUseContext') -> PermissionResult:
        return PermissionResult.ALLOW
```

#### 2.2 实现 buildTool 工厂
**文件**: `agent-framework/agent_framework/core/tool_builder.py`

```python
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

@dataclass
class ToolDefaults:
    is_enabled: Callable[[], bool] = lambda: True
    is_read_only: Callable[[Any], bool] = lambda _: False
    is_destructive: Callable[[Any], bool] = lambda _: False

def build_tool(tool_class: type, **overrides) -> type:
    """构建工具类，填充默认值 / Build tool class with defaults"""
    for attr, default_fn in ToolDefaults().__dict__.items():
        if not hasattr(tool_class, attr):
            setattr(tool_class, attr, default_fn)
    return tool_class
```

#### 2.3 迁移现有工具
**目录**: `alonework-cli/src/alonechat/tools/`

- 将现有工具迁移到新的 Tool 接口
- 实现核心工具: BashTool, FileReadTool, FileEditTool, GlobTool, GrepTool

---

### Phase 3: 流式查询引擎 (Streaming Query Engine)

#### 3.1 实现 QueryEngine
**文件**: `agent-framework/agent_framework/core/query_engine.py`

```python
from typing import AsyncGenerator, Any, Optional
from dataclasses import dataclass

@dataclass
class QueryParams:
    messages: list
    system_prompt: str
    tools: list
    model: str
    max_turns: Optional[int] = None

@dataclass
class StreamEvent:
    type: str  # 'assistant', 'tool_use', 'tool_result', 'error', 'system'
    data: Any

class QueryEngine:
    """流式查询引擎 / Streaming query engine"""
    
    async def query(self, params: QueryParams) -> AsyncGenerator[StreamEvent, None]:
        """执行查询循环 / Execute query loop"""
        messages = params.messages.copy()
        turn_count = 0
        
        while True:
            turn_count += 1
            if params.max_turns and turn_count > params.max_turns:
                yield StreamEvent(type='system', data='Max turns reached')
                break
            
            # 调用模型
            response = await self._call_model(messages, params)
            yield StreamEvent(type='assistant', data=response)
            
            # 检查是否有工具调用
            tool_uses = self._extract_tool_uses(response)
            if not tool_uses:
                break
            
            # 执行工具
            for tool_use in tool_uses:
                yield StreamEvent(type='tool_use', data=tool_use)
                result = await self._execute_tool(tool_use, params.tools)
                yield StreamEvent(type='tool_result', data=result)
                messages.append(self._create_tool_result_message(tool_use, result))
    
    async def _call_model(self, messages, params):
        # 调用 LLM API
        pass
    
    def _extract_tool_uses(self, response):
        # 提取工具调用
        pass
    
    async def _execute_tool(self, tool_use, tools):
        # 执行工具
        pass
```

#### 3.2 集成自动压缩
**文件**: `agent-framework/agent_framework/core/auto_compact.py`

- 实现 token 计数
- 自动压缩触发逻辑
- 压缩策略（摘要、裁剪）

---

### Phase 4: 模块化命令系统 (Modular Command System)

#### 4.1 定义 Command 接口
**文件**: `agent-framework/agent_framework/core/command.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, Any
from enum import Enum

class CommandType(Enum):
    LOCAL = "local"        # 本地执行
    PROMPT = "prompt"      # 提示命令
    LOCAL_JSX = "local-jsx"  # UI 命令

class Command(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    def command_type(self) -> CommandType:
        return CommandType.LOCAL
    
    @property
    def aliases(self) -> list:
        return []
    
    def is_enabled(self) -> bool:
        return True
    
    @abstractmethod
    async def execute(self, args: str, context: Any) -> Optional[str]:
        pass
```

#### 4.2 实现命令注册表
**文件**: `agent-framework/agent_framework/core/command_registry.py`

```python
from typing import Dict, List, Optional
import importlib
import os

class CommandRegistry:
    """命令注册表 / Command registry with lazy loading"""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._lazy_modules: Dict[str, str] = {}
    
    def register(self, command: Command) -> None:
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command
    
    def register_lazy(self, name: str, module_path: str) -> None:
        self._lazy_modules[name] = module_path
    
    def get(self, name: str) -> Optional[Command]:
        if name in self._commands:
            return self._commands[name]
        
        if name in self._lazy_modules:
            module = importlib.import_module(self._lazy_modules[name])
            command = module.get_command()
            self.register(command)
            return command
        
        return None
    
    def list_commands(self) -> List[Command]:
        # 触发所有懒加载
        for name in list(self._lazy_modules.keys()):
            self.get(name)
        return list(set(self._commands.values()))
```

#### 4.3 迁移现有命令
**目录**: `alonework-cli/src/alonechat/commands/`

- 将 Click 命令迁移到新的 Command 接口
- 实现懒加载机制

---

### Phase 5: 服务层抽象 (Service Layer Abstraction)

#### 5.1 API 客户端抽象
**文件**: `agent-framework/agent_framework/services/api_client.py`

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Optional

class APIClient(ABC):
    """API 客户端基类 / API client base class"""
    
    @abstractmethod
    async def chat(self, messages: list, model: str, **kwargs) -> Any:
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: list, model: str, **kwargs) -> AsyncGenerator[Any, None]:
        pass

class DeepSeekClient(APIClient):
    """DeepSeek API 客户端"""
    pass

class OpenAIClient(APIClient):
    """OpenAI 兼容 API 客户端"""
    pass

class LocalModelClient(APIClient):
    """本地模型客户端"""
    pass
```

#### 5.2 MCP 服务集成
**文件**: `agent-framework/agent_framework/services/mcp_service.py`

- 实现 MCP 客户端
- 工具发现与注册
- 资源管理

#### 5.3 LSP 集成
**文件**: `agent-framework/agent_framework/services/lsp_service.py`

- LSP 客户端管理
- 代码智能功能

---

### Phase 6: 插件与技能系统 (Plugin & Skill System)

#### 6.1 插件系统
**文件**: `agent-framework/agent_framework/plugins/`

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class Plugin(ABC):
    """插件基类 / Plugin base class"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        pass
    
    def initialize(self, context: Any) -> None:
        pass
    
    def get_tools(self) -> List[Any]:
        return []
    
    def get_commands(self) -> List[Any]:
        return []
    
    def cleanup(self) -> None:
        pass
```

#### 6.2 技能系统
**文件**: `agent-framework/agent_framework/skills/`

- 技能发现与加载
- 技能执行框架
- 动态技能注册

---

### Phase 7: CLI 重构 (CLI Refactoring)

#### 7.1 统一入口点
**文件**: `alonework-cli/src/alonechat/main.py`

- 参考 claude-code-claude 的 `cli.tsx` 入口
- 实现快速路径 (fast paths)
- 设置流程 (setup flow)

#### 7.2 TUI 重构
**文件**: `alonework-cli/src/alonechat/tui/`

- 基于新状态管理重构 TUI
- 实现 REPL 模式
- 流式输出支持

---

## 文件结构 / File Structure

```
agent-framework/
├── agent_framework/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── store.py              # 状态管理
│   │   ├── app_state.py          # AppState 定义
│   │   ├── tool.py               # Tool 接口
│   │   ├── tool_builder.py       # buildTool 工厂
│   │   ├── command.py            # Command 接口
│   │   ├── command_registry.py   # 命令注册表
│   │   ├── query_engine.py       # 查询引擎
│   │   ├── auto_compact.py       # 自动压缩
│   │   └── types.py              # 核心类型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_client.py         # API 客户端
│   │   ├── mcp_service.py        # MCP 服务
│   │   └── lsp_service.py        # LSP 服务
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base.py               # 插件基类
│   │   └── manager.py            # 插件管理器
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base.py               # 技能基类
│   │   └── loader.py             # 技能加载器
│   └── tools/
│       ├── __init__.py
│       ├── bash.py               # BashTool
│       ├── file_read.py          # FileReadTool
│       ├── file_edit.py          # FileEditTool
│       ├── glob.py               # GlobTool
│       └── grep.py               # GrepTool

alonework-cli/
├── src/
│   ├── alonechat/
│   │   ├── __init__.py
│   │   ├── main.py               # 新入口点
│   │   ├── cli.py                # CLI 定义 (保留向后兼容)
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   ├── store.py          # 应用状态 Store
│   │   │   └── selectors.py      # 状态选择器
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── chat/
│   │   │   │   ├── __init__.py
│   │   │   │   └── command.py
│   │   │   ├── init/
│   │   │   │   ├── __init__.py
│   │   │   │   └── command.py
│   │   │   └── ...
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── ... (迁移现有工具)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── ...
│   │   └── tui/
│   │       ├── __init__.py
│   │       ├── app.py            # TUI 应用
│   │       └── components/       # UI 组件
```

---

## 迁移策略 / Migration Strategy

### 向后兼容 / Backward Compatibility

1. **保留现有 CLI 接口** - `alonework` 命令保持不变
2. **渐进式迁移** - 新旧系统并行运行
3. **适配器模式** - 为旧代码提供适配器

### 迁移顺序 / Migration Order

1. **Phase 1-2**: 核心基础设施 (Store, Tool)
2. **Phase 3**: 查询引擎
3. **Phase 4-5**: 命令系统和服务层
4. **Phase 6-7**: 插件系统和 CLI 重构

---

## 验证计划 / Verification Plan

1. **单元测试** - 每个新模块配套测试
2. **集成测试** - 端到端测试
3. **性能测试** - 确保不降低性能
4. **用户验收** - 保持现有功能正常

---

## 风险与缓解 / Risks & Mitigations

| 风险 | 缓解措施 |
|------|----------|
| 破坏现有功能 | 渐进式迁移，保持向后兼容 |
| 性能下降 | 性能测试，优化热点代码 |
| 学习曲线 | 提供文档和示例 |
| 依赖冲突 | 使用虚拟环境，明确依赖版本 |

---

## 时间线 / Timeline

- **Week 1-2**: Phase 1 (状态管理)
- **Week 3-4**: Phase 2 (工具系统)
- **Week 5-6**: Phase 3 (查询引擎)
- **Week 7-8**: Phase 4-5 (命令系统、服务层)
- **Week 9-10**: Phase 6-7 (插件系统、CLI 重构)
