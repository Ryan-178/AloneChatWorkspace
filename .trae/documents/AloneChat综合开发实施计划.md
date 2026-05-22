# AloneChat 综合开发实施计划

> 创建日期：2026-05-21
> 整合来源：DeepSeek-TUI对比分析 + Mavis架构启示
> 目标：全面提升AloneChat的核心能力和架构水平
> 覆盖范围：alonework-cli + agent-framework + alonechat-desktop

***

## 一、开发背景与目标

### 1.1 三层架构说明

```
┌─────────────────────────────────────────────────────────────────┐
│                    alonechat-desktop                            │
│              (Next.js + React + Tauri 桌面应用)                  │
│   职责：用户界面、状态可视化、交互体验                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    alonework-cli                                │
│              (Python CLI + Rich终端界面)                         │
│   职责：命令行接口、会话管理、工具执行、LSP集成                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agent-framework                              │
│              (Python核心框架)                                    │
│   职责：Agent核心、工具注册、多Agent协作、Gateway API              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.12 双源分析整合

本计划整合了两份关键研究文档的洞察：

| 来源                   | 核心价值   | 关键启示                                        |
| -------------------- | ------ | ------------------------------------------- |
| **DeepSeek-TUI对比分析** | 功能差距识别 | 交互模式、工具系统、会话管理、LSP集成等具体功能差距                 |
| **Mavis架构分析**        | 架构范式升级 | Leader/Worker/Verifier角色体系、状态机Runtime、对抗式验证 |

### 1.23 总体目标

```
短期（6周）: 补齐核心功能差距，对齐DeepSeek-TUI体验
中期（4周）: 实现架构升级，引入Mavis角色体系
长期（5周）: 产品化落地，形成差异化竞争力
```

***

## 二、开发阶段规划

### Phase 1: 核心功能对齐（第1-6周）

**目标**：补齐最影响核心体验的功能差距

#### Week 1-2: 交互模式管理与工具系统

##### 1.1 交互模式管理系统

**当前状态**：无模式切换
**目标状态**：Plan/Agent/YOLO三种模式

**实施步骤**：

1. **定义交互模式枚举**

   * 文件：`alonework-cli/src/alonechat/modes/__init__.py`（新建）

   * 内容：

     ```python
     class InteractionMode(Enum):
         PLAN = "plan"      # 只读探索，无工具执行
         AGENT = "agent"    # 默认交互，工具执行需审批
         YOLO = "yolo"      # 自动批准，信任工作区
     ```

2. **实现模式管理器**

   * 文件：`alonework-cli/src/alonechat/modes/manager.py`（新建）

   * 职责：

     * 模式切换逻辑

     * 模式权限控制

     * 工具执行审批流程

     * 快捷键绑定

3. **集成到CLI**

   * 修改：`alonework-cli/src/alonechat/cli.py`

   * 新增选项：`--mode plan|agent|yolo`

   * 新增slash命令：`/mode plan|agent|yolo`

4. **实现模式UI反馈**

   * 修改：`alonework-cli/src/alonechat/commands/chat.py`

   * 在状态栏显示当前模式

   * 模式切换时的视觉反馈

##### 1.2 CLI层工具系统扩展

**当前状态**：CLI层工具少，主要依赖Agent Framework
**目标状态**：20+核心工具覆盖shell/file/git/web

**实施步骤**：

1. **创建CLI工具模块**

   * 目录：`alonework-cli/src/alonechat/tools/`（新建）

   * 复用Agent Framework的ToolRegistry和BaseTool

2. **实现核心工具**

   | 工具             | 文件                | 职责                  | 优先级 |
   | -------------- | ----------------- | ------------------- | --- |
   | ShellTool      | `shell.py`        | 安全的shell命令执行        | P0  |
   | FileReadTool   | `file_read.py`    | 文件读取                | P0  |
   | FileWriteTool  | `file_write.py`   | 文件写入                | P0  |
   | FileEditTool   | `file_edit.py`    | 文件编辑（SearchReplace） | P0  |
   | GitStatusTool  | `git_status.py`   | git状态查看             | P1  |
   | GitDiffTool    | `git_diff.py`     | git差异查看             | P1  |
   | WebSearchTool  | 复用agent-framework | 网页搜索                | P1  |
   | ApplyPatchTool | `apply_patch.py`  | 补丁应用                | P2  |

3. **工具审批流程**

   * 文件：`alonework-cli/src/alonechat/tools/approval.py`（新建）

   * 集成现有PermissionManager

   * 支持YOLO模式自动批准

4. **工具注册和发现**

   * 修改：`alonework-cli/src/alonechat/tools/__init__.py`

   * 自动注册所有工具

   * 与Agent Framework ToolRegistry集成

#### Week 3-4: 会话管理升级与LSP集成

##### 1.3 会话管理SQLite迁移

**当前状态**：JSON文件存储
**目标状态**：SQLite持久化 + 完整CRUD + 恢复

**实施步骤**：

1. **设计SQLite Schema**

   * 文件：`alonework-cli/src/alonechat/session/db_schema.py`（新建）

   * 表设计：

     ```sql
     CREATE TABLE sessions (
         id TEXT PRIMARY KEY,
         display_name TEXT,
         created_at TEXT,
         updated_at TEXT,
         parent_id TEXT,
         branch_point INTEGER,
         metadata TEXT,  -- JSON
         agent_config TEXT  -- JSON
     );

     CREATE TABLE messages (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         session_id TEXT,
         role TEXT,
         content TEXT,
         timestamp TEXT,
         FOREIGN KEY (session_id) REFERENCES sessions(id)
     );

     CREATE TABLE session_metadata (
         session_id TEXT,
         key TEXT,
         value TEXT,
         PRIMARY KEY (session_id, key)
     );
     ```

2. **实现SQLite存储后端**

   * 文件：`alonework-cli/src/alonechat/session/db_storage.py`（新建）

   * 使用aiosqlite实现异步操作

   * 支持迁移和版本管理

3. **实现数据迁移**

   * 文件：`alonework-cli/src/alonechat/session/migration.py`（新建）

   * 从JSON迁移到SQLite

   * 保留JSON作为备份

4. **增强会话管理器**

   * 修改：`alonework-cli/src/alonechat/session/manager.py`

   * 新增方法：

     * `search_sessions(query)` - 搜索会话

     * `archive_session(session_id)` - 归档会话

     * `get_session_stats()` - 会话统计

##### 1.4 LSP诊断集成

**当前状态**：无
**目标状态**：编辑后即时诊断反馈

**实施步骤**：

1. **创建LSP模块**

   * 目录：`alonework-cli/src/alonechat/lsp/`（新建）

2. **实现LSP客户端基类**

   * 文件：`alonework-cli/src/alonechat/lsp/client.py`（新建）

   * 基于asyncio的LSP 3.16协议实现

3. **实现语言服务器适配器**

   * Python: pyright/pylsp

   * TypeScript: typescript-language-server

   * Go: gopls

   * Rust: rust-analyzer

4. **集成诊断反馈**

   * 文件：`alonework-cli/src/alonechat/lsp/diagnostics.py`（新建）

   * 文件编辑后自动触发诊断

   * 内联错误/警告显示

   * 诊断结果注入模型上下文

#### Week 5-6: CLI命令增强与成本追踪

##### 1.5 新增顶级CLI命令

**当前状态**：6个顶级命令
**目标状态**：20+顶级命令

**新增命令列表**：

| 命令         | 文件                       | 说明     |
| ---------- | ------------------------ | ------ |
| `models`   | `commands/models.py`     | 列出可用模型 |
| `sessions` | `commands/sessions.py`   | 会话管理   |
| `resume`   | 集成到main                  | 恢复会话   |
| `fork`     | 集成到main                  | 会话分叉   |
| `doctor`   | `commands/doctor.py`     | 系统诊断   |
| `review`   | `commands/review.py`     | 代码审查   |
| `setup`    | `commands/setup.py`      | 引导配置   |
| `features` | `commands/features.py`   | 功能标志查询 |
| `config`   | `commands/config_cmd.py` | 配置管理   |
| `update`   | `commands/update.py`     | 自动更新   |

##### 1.6 成本追踪增强

**当前状态**：基础追踪
**目标状态**：按轮次/会话/缓存明细全维度

**实施步骤**：

1. **创建成本追踪模块**

   * 文件：`alonework-cli/src/alonechat/cost/tracker.py`（新建）

2. **实现多维度统计**

   * 按轮次统计

   * 按会话统计

   * 缓存命中/未命中明细

   * 实时成本估算

3. **新增slash命令**

   * `/cost` - 显示成本报告

   * `/usage` - 显示使用统计

***

#### Week 1-2: 交互模式管理与工具系统

##### 1.1 交互模式管理系统

**当前状态**：无模式切换
**目标状态**：Plan/Agent/YOLO三种模式

**【agent-framework层】**：

1. **定义交互模式枚举和配置**

   * 文件：`agent-framework/agent_framework/core/types.py`（修改）

   * 新增：

     ```python
     class InteractionMode(str, Enum):
         PLAN = "plan"      # 只读探索，无工具执行
         AGENT = "agent"    # 默认交互，工具执行需审批
         YOLO = "yolo"      # 自动批准，信任工作区

     class ModeConfig(BaseModel):
         mode: InteractionMode = InteractionMode.AGENT
         auto_approve_tools: bool = False
         require_confirmation: List[str] = ["shell", "file_write", "file_delete"]
         max_auto_approve_cost: float = 1.0  # 最大自动批准成本
     ```

2. **实现模式管理器基类**

   * 文件：`agent-framework/agent_framework/core/mode_manager.py`（新建）

   * 职责：

     * 模式切换逻辑

     * 工具执行权限检查

     * 审批流程接口

   * 接口定义：

     ```python
     class ModeManager:
         def get_mode() -> InteractionMode
         def set_mode(mode: InteractionMode) -> None
         def check_tool_permission(tool_name: str, params: dict) -> bool
         async def request_approval(tool_name: str, params: dict) -> bool
     ```

3. **配置文件**

   * 文件：`agent-framework/agent_framework/configs/mode_config.yaml`（新建）

   * 内容：

     ```yaml
     modes:
       plan:
         auto_approve_tools: false
         allowed_tools: ["read", "search", "list"]
         description: "只读探索模式，无工具执行"
       agent:
         auto_approve_tools: false
         require_confirmation: ["shell", "file_write", "file_delete"]
         description: "默认交互模式，工具执行需审批"
       yolo:
         auto_approve_tools: true
         max_auto_approve_cost: 10.0
         description: "自动批准模式，信任工作区"
     ```

**【alonework-cli层】**：

1. **实现CLI模式管理器**

   * 文件：`alonework-cli/src/alonechat/modes/manager.py`（新建）

   * 继承agent-framework的ModeManager

   * 实现Rich终端审批界面：

     ```python
     class CliModeManager(ModeManager):
         async def request_approval(self, tool_name: str, params: dict) -> bool:
             # 使用Rich Prompt确认
             return Confirm.ask(f"允许执行 {tool_name}?")
     ```

2. **集成到CLI主入口**

   * 文件：`alonework-cli/src/alonechat/cli.py`（修改）

   * 新增选项：`--mode plan|agent|yolo`

   * 新增slash命令：`/mode plan|agent|yolo`

3. **实现模式UI反馈**

   * 文件：`alonework-cli/src/alonechat/commands/chat.py`（修改）

   * 在状态栏显示当前模式（带颜色）

   * 模式切换时的视觉反馈

**【alonechat-desktop层】**：

1. **模式切换组件**

   * 文件：`alonechat-desktop/src/components/agent/mode-switch.tsx`（修改）

   * 新增Plan模式选项

   * 模式切换动画效果

2. **模式状态显示**

   * 文件：`alonechat-desktop/src/stores/agent-store.ts`（修改）

   * 新增mode状态字段

   * 与Gateway API同步

### Phase 2: 架构升级 - Mavis角色体系（第7-10周）

**目标**：引入Leader/Worker/Verifier角色体系，构建状态机Runtime

#### Week 7-8: 角色体系建设

##### 2.1 定义角色体系

**实施步骤**：

1. **扩展AgentRole枚举**

   * 文件：`agent-framework/agent_framework/core/types.py`

   * 新增：

     ```python
     class AgentRole(str, Enum):
         LEADER = "leader"      # 统筹、规划、调度、聚合
         WORKER = "worker"      # 执行、具体任务
         VERIFIER = "verifier"  # 验收、质量门禁
     ```

2. **创建LeaderAgent基类**

   * 文件：`agent-framework/agent_framework/agent/leader_agent.py`（新建）

   * 职责：

     * 任务理解和规划

     * 子任务拆分（复用TaskPlanner）

     * Worker调度和监控

     * 结果聚合和最终交付

   * 参考：现有MTCAgent的意图澄清和任务规划能力

3. **创建WorkerAgent基类**

   * 文件：`agent-framework/agent_framework/agent/worker_agent.py`（新建）

   * 职责：

     * 专注执行具体子任务

     * 配备独立工具集

     * 独立上下文容器

     * 标准化输出协议

   * 参考：现有ReActAgent的执行能力

4. **创建VerifierAgent基类**

   * 文件：`agent-framework/agent_framework/agent/verifier_agent.py`（新建）

   * 职责：

     * 独立审查Worker输出

     * 质量评分和门禁

     * 打回策略

     * 最大对抗轮数控制

   * 关键：与Worker形成目标函数相反的对抗关系

##### 2.2 扩展MultiAgentTeam

**实施步骤**：

1. **支持角色化注册**

   * 修改：`agent-framework/agent_framework/agent/multi_agent.py`

   * 新增方法：

     * `register_leader(agent)` - 注册Leader

     * `register_worker(agent, capabilities)` - 注册Worker

     * `register_verifier(agent)` - 注册Verifier

2. **实现角色间通信路由**

   * Leader → Worker: 任务分发

   * Worker → Verifier: 成果提交

   * Verifier → Leader: 验收结果

   * Verifier → Worker: 打回修正

#### Week 9-10: Team Engine状态机Runtime

##### 2.3 构建Team Engine

**实施步骤**：

1. **定义Agent生命周期状态**

   * 文件：`agent-framework/agent_framework/orchestration/team_engine.py`（新建）

   * 状态：

     ```python
     class AgentState(str, Enum):
         PENDING = "pending"      # 等待执行
         PRODUCING = "producing"  # 执行中
         VERIFYING = "verifying"  # 验证中
         DONE = "done"           # 完成
         RETRY = "retry"         # 重试
         FAILED = "failed"       # 失败
     ```

2. **实现状态机核心**

   * 状态转换逻辑

   * 事件驱动

   * 超时控制

   * 确定性调度

3. **实现对抗验证循环**

   ```
   Worker交付 → Verifier审查 → 通过/打回 → 重试/继续
   ```

   * 参数：max\_retry\_count, quality\_threshold

   * 防止无限循环

4. **实现局部重试**

   * 只重试失败的Worker

   * 不影响已成功的Worker

   * 失败恢复机制

##### 2.4 上下文隔离机制

**实施步骤**：

1. **创建上下文隔离模块**

   * 文件：`agent-framework/agent_framework/core/context_isolation.py`（新建）

2. **实现结构化摘要生成器**

   * 将完整上下文压缩为结构化摘要

   * 包含关键信息和文件路径引用

3. **实现按需读取协议**

   * Agent只持有职责相关上下文

   * 需要时通过文件路径读取完整内容

4. **集成AgentBus**

   * 修改：`agent-framework/agent_framework/core/agent_bus.py`

   * 支持结构化摘要通信

***

##### 1.2 工具系统扩展

**当前状态**：CLI层工具少，主要依赖Agent Framework
**目标状态**：20+核心工具覆盖shell/file/git/web

**【agent-framework层】**：

1. **扩展工具注册表**

   * 文件：`agent-framework/agent_framework/tools/registry.py`（修改）

   * 新增功能：

     * 工具分类（shell/file/git/web/code）

     * 工具权限级别

     * 工具成本估算

2. **实现核心工具基类增强**

   * 文件：`agent-framework/agent_framework/core/base_tool.py`（修改）

   * 新增字段：

     ```python
     class BaseTool(ABC):
         name: str = ""
         description: str = ""
         parameters: Dict[str, Any] = {}
         category: str = "general"  # 新增：工具分类
         permission_level: str = "read"  # 新增：权限级别
         estimated_cost: float = 0.0  # 新增：预估成本
     ```

3. **实现Shell工具**

   * 文件：`agent-framework/agent_framework/tools/builtin/shell.py`（新建）

   * 功能：

     * 安全的shell命令执行

     * 命令白名单/黑名单

     * 超时控制

     * 输出捕获

4. **实现文件工具集**

   * 目录：`agent-framework/agent_framework/tools/builtin/file/`（新建）

   * 文件：

     * `read.py` - 文件读取

     * `write.py` - 文件写入

     * `edit.py` - 文件编辑（SearchReplace）

     * `delete.py` - 文件删除

     * `search.py` - 文件搜索（ripgrep）

5. **实现Git工具集**

   * 目录：`agent-framework/agent_framework/tools/builtin/git/`（新建）

   * 文件：

     * `status.py` - git状态

     * `diff.py` - git差异

     * `commit.py` - git提交

     * `branch.py` - 分支操作

6. **工具配置**

   * 文件：`agent-framework/agent_framework/configs/tools.yaml`（新建）

   * 内容：

     ```yaml
     tools:
       shell:
         enabled: true
         timeout: 30
         whitelist: ["ls", "cat", "grep", "find"]
         blacklist: ["rm -rf", "sudo"]
       file:
         enabled: true
         max_file_size: 10MB
         allowed_extensions: [".py", ".js", ".ts", ".md", ".yaml"]
       git:
         enabled: true
         auto_commit: false
     ```

**【alonework-cli层】**：

1. **CLI工具执行器**

   * 文件：`alonework-cli/src/alonechat/tools/executor.py`（新建）

   * 职责：

     * 工具调用路由

     * 审批流程集成

     * 结果格式化

2. **工具输出渲染**

   * 文件：`alonework-cli/src/alonechat/tools/renderer.py`（新建）

   * 使用Rich美化工具输出

   * 文件路径超链接

   * 错误高亮

3. **集成到聊天循环**

   * 文件：`alonework-cli/src/alonechat/commands/chat.py`（修改）

   * 工具调用显示

   * 审批确认界面

**【alonechat-desktop层】**：

1. **工具调用卡片组件**

   * 文件：`alonechat-desktop/src/components/agent/tool-call-card.tsx`（修改）

   * 显示工具名称、参数、结果

   * 审批按钮（批准/拒绝）

2. **工具面板**

   * 文件：`alonechat-desktop/src/components/agent/tools-panel.tsx`（新建）

   * 显示可用工具列表

   * 工具启用/禁用开关

### Phase 3: 高级特性与产品化（第11-15周）

**目标**：补齐高级功能，落地产品场景

#### Week 11-12: 工作区快照与RLM

##### 3.1 工作区快照/回滚

**实施步骤**：

1. **创建快照引擎**

   * 文件：`alonework-cli/src/alonechat/snapshot/engine.py`（新建）

   * 使用side-git机制（不影响项目.git）

2. **实现快照操作**

   * `snapshot_create()` - 创建快照

   * `snapshot_list()` - 列出快照

   * `snapshot_restore(id)` - 恢复快照

   * `snapshot_cleanup()` - 清理过期快照

3. **集成到聊天**

   * `/snapshot` - 创建快照

   * `/restore [id]` - 恢复快照

   * `/snapshots` - 列出快照

##### 3.2 RLM (低成本子任务调度)

**实施步骤**：

1. **创建RLM模块**

   * 文件：`agent-framework/agent_framework/rlm/dispatcher.py`（新建）

2. **实现并行子任务调度**

   * 使用flash模型处理低成本子任务

   * 并行执行和结果聚合

   * 批量分析和推理

3. **集成到Team Engine**

   * Leader可委托子任务给RLM

   * 降低总体Token成本

#### Week 13-14: 持久化任务队列与多语言

##### 3.3 持久化任务队列

**实施步骤**：

1. **创建任务队列模块**

   * 文件：`alonework-cli/src/alonechat/queue/task_queue.py`（新建）

2. **实现SQLite任务表**

   * 支持cron表达式

   * 重启后恢复

   * 进度通知

3. **实现任务调度器**

   * 后台任务执行

   * 任务状态管理

   * 失败重试

##### 3.4 多语言UI支持

**实施步骤**：

1. **抽取UI字符串**

   * 目录：`alonework-cli/src/alonechat/locale/`（新建）

   * 支持：en, ja, zh-Hans, pt-BR

2. **实现国际化**

   * 文件：`alonework-cli/src/alonechat/locale/i18n.py`（新建）

   * 自动检测系统语言

   * `/locale [lang]` 切换命令

#### Week 15: 产品化集成

##### 3.5 桌面端集成

1. **Team状态可视化**

   * 修改：`alonechat-desktop/src/components/agent/`

   * 显示Leader/Worker/Verifier状态

   * 实时进度反馈

2. **成本仪表板**

   * 新增：成本统计可视化

   * Token使用趋势图

##### 3.6 CLI集成

1. **Team模式支持**

   * `alonechat team` - 启动Team模式

   * 显示多Agent协作状态

2. **可交互过程**

   * 用户可随时查看进度

   * 支持中途干预

***

#### Week 3-4: 会话管理升级与LSP集成

##### 1.3 会话管理SQLite迁移

**当前状态**：JSON文件存储
**目标状态**：SQLite持久化 + 完整CRUD + 恢复

**【agent-framework层】**：

1. **定义会话存储接口**

   * 文件：`agent-framework/agent_framework/core/base_storage.py`（新建）

   * 抽象接口：

     ```python
     class BaseSessionStorage(ABC):
         @abstractmethod
         async def save(self, session: Session) -> None: ...
         @abstractmethod
         async def load(self, session_id: str) -> Optional[Session]: ...
         @abstractmethod
         async def delete(self, session_id: str) -> bool: ...
         @abstractmethod
         async def list(self, limit: int) -> List[Session]: ...
         @abstractmethod
         async def search(self, query: str) -> List[Session]: ...
     ```

2. **实现SQLite存储后端**

   * 文件：`agent-framework/agent_framework/storage/sqlite_storage.py`（新建）

   * 使用aiosqlite实现异步操作

   * Schema：

     ```sql
     CREATE TABLE sessions (
         id TEXT PRIMARY KEY,
         display_name TEXT,
         created_at TEXT,
         updated_at TEXT,
         parent_id TEXT,
         branch_point INTEGER,
         mode TEXT DEFAULT 'agent',
         metadata TEXT,
         agent_config TEXT
     );

     CREATE TABLE messages (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         session_id TEXT,
         role TEXT,
         content TEXT,
         timestamp TEXT,
         tool_calls TEXT,
         FOREIGN KEY (session_id) REFERENCES sessions(id)
     );

     CREATE INDEX idx_sessions_updated ON sessions(updated_at);
     CREATE INDEX idx_messages_session ON messages(session_id);
     ```

3. **数据迁移工具**

   * 文件：`agent-framework/agent_framework/storage/migration.py`（新建）

   * JSON → SQLite迁移

   * 版本管理

4. **存储配置**

   * 文件：`agent-framework/agent_framework/configs/storage.yaml`（新建）

   * 内容：

     ```yaml
     storage:
       type: sqlite
       path: ~/.alonechat/data/sessions.db
       backup:
         enabled: true
         interval: 3600
         max_backups: 10
       migration:
         from_json: true
         keep_json_backup: true
     ```

**【alonework-cli层】**：

1. **CLI会话管理器**

   * 文件：`alonework-cli/src/alonechat/session/manager.py`（修改）

   * 使用agent-framework的SQLite存储

   * 新增方法：

     * `search_sessions(query)` - 搜索会话

     * `archive_session(session_id)` - 归档会话

     * `get_session_stats()` - 会话统计

2. **会话列表命令**

   * 文件：`alonework-cli/src/alonechat/commands/sessions.py`（新建）

   * `alonechat sessions list` - 列出会话

   * `alonechat sessions search <query>` - 搜索会话

   * `alonechat sessions delete <id>` - 删除会话

3. **会话UI增强**

   * 文件：`alonework-cli/src/alonechat/commands/chat.py`（修改）

   * 会话信息显示

   * 会话切换提示

**【alonechat-desktop层】**：

1. **会话列表组件**

   * 文件：`alonechat-desktop/src/components/agent/session-list.tsx`（修改）

   * 从Gateway API获取会话列表

   * 搜索功能

   * 会话删除/归档

2. **会话详情面板**

   * 文件：`alonechat-desktop/src/components/agent/session-detail.tsx`（新建）

   * 显示会话统计

   * 消息时间线

## 三、技术决策

### 3.1 存储升级

| 决策点  | 选择                    | 理由             |
| ---- | --------------------- | -------------- |
| 会话存储 | SQLite (aiosqlite)    | 零依赖，性能好，支持复杂查询 |
| 任务队列 | SQLite                | 简单可靠，无需外部依赖    |
| 配置格式 | YAML(保留) + TOML(用户配置) | 现有规范延续         |

### 3.2 LSP集成

| 语言         | 服务器                        | 安装方式                                      |
| ---------- | -------------------------- | ----------------------------------------- |
| Python     | pyright                    | npm install -g pyright                    |
| TypeScript | typescript-language-server | npm install -g typescript-language-server |
| Go         | gopls                      | go install golang.org/x/tools/gopls       |
| Rust       | rust-analyzer              | rustup component add rust-analyzer        |

### 3.3 架构原则

1. **保持agent-framework核心地位** - 新功能优先在framework层实现
2. **避免过度工程化** - 从最简单方案开始，按需演进
3. **复用现有能力** - TaskPlanner、ReActAgent、AgentBus等
4. **中英双语注释** - 保持代码可读性
5. **禁止硬编码** - 全部配置使用YAML

***

##### 1.4 LSP诊断集成

**当前状态**：无
**目标状态**：编辑后即时诊断反馈

**【agent-framework层】**：

1. **LSP客户端基类**

   * 文件：`agent-framework/agent_framework/lsp/client.py`（新建）

   * 实现LSP 3.16协议

   * 异步通信

   * 生命周期管理

2. **LSP服务器管理器**

   * 文件：`agent-framework/agent_framework/lsp/manager.py`（新建）

   * 管理多个语言服务器

   * 自动启动/关闭

   * 配置：

     ```python
     class LSPManager:
         servers: Dict[str, LSPClient]  # language -> client
         async def get_client(language: str) -> LSPClient
         async def diagnose(file_path: str) -> List[Diagnostic]
     ```

3. **语言服务器适配器**

   * 目录：`agent-framework/agent_framework/lsp/servers/`（新建）

   * `python.py` - pyright/pylsp

   * `typescript.py` - typescript-language-server

   * `go.py` - gopls

   * `rust.py` - rust-analyzer

4. **诊断结果类型**

   * 文件：`agent-framework/agent_framework/lsp/types.py`（新建）

   * Diagnostic, Position, Range等类型定义

5. **LSP配置**

   * 文件：`agent-framework/agent_framework/configs/lsp.yaml`（新建）

   * 内容：

     ```yaml
     lsp:
       enabled: true
       servers:
         python:
           command: "pyright-langserver"
           args: ["--stdio"]
         typescript:
           command: "typescript-language-server"
           args: ["--stdio"]
         go:
           command: "gopls"
         rust:
           command: "rust-analyzer"
       diagnostics:
         debounce_ms: 500
         max_diagnostics: 100
     ```

**【alonework-cli层】**：

1. **CLI LSP集成**

   * 文件：`alonework-cli/src/alonechat/lsp/integration.py`（新建）

   * 文件编辑后触发诊断

   * 诊断结果格式化

2. **诊断显示**

   * 文件：`alonework-cli/src/alonechat/lsp/display.py`（新建）

   * 使用Rich显示错误/警告

   * 内联诊断信息

3. **诊断注入上下文**

   * 文件：`alonework-cli/src/alonechat/commands/chat.py`（修改）

   * 将诊断结果注入模型上下文

   * 自动修复建议

**【alonechat-desktop层】**：

1. **诊断面板**

   * 文件：`alonechat-desktop/src/components/agent/diagnostics-panel.tsx`（新建）

   * 显示问题列表

   * 按严重程度分类

2. **诊断指示器**

   * 文件：`alonechat-desktop/src/components/agent/diagnostic-indicator.tsx`（新建）

   * 状态栏显示诊断数量

   * 点击跳转到问题

## 四、风险评估

| 风险           | 影响 | 缓解策略                |
| ------------ | -- | ------------------- |
| SQLite迁移数据丢失 | 高  | 保留JSON备份，实现双向同步     |
| LSP服务器不可用    | 中  | 优雅降级，显示警告而非错误       |
| 对抗验证无限循环     | 中  | 设置最大轮数上限，Leader最终裁量 |
| Token成本翻倍    | 中  | 简单任务不用Team，默认单Agent |
| 状态机复杂度       | 中  | 完善的轨迹日志和可观测性        |

***

#### Week 5-6: CLI命令增强与成本追踪

##### 1.5 新增顶级CLI命令

**当前状态**：6个顶级命令
**目标状态**：20+顶级命令

**【alonework-cli层】**：

新增命令列表：

| 命令         | 文件                       | 说明     |
| ---------- | ------------------------ | ------ |
| `models`   | `commands/models.py`     | 列出可用模型 |
| `sessions` | `commands/sessions.py`   | 会话管理   |
| `doctor`   | `commands/doctor.py`     | 系统诊断   |
| `review`   | `commands/review.py`     | 代码审查   |
| `setup`    | `commands/setup.py`      | 引导配置   |
| `features` | `commands/features.py`   | 功能标志查询 |
| `config`   | `commands/config_cmd.py` | 配置管理   |
| `update`   | `commands/update.py`     | 自动更新   |

**【agent-framework层】**：

1. **命令共享逻辑**

   * 文件：`agent-framework/agent_framework/commands/base.py`（新建）

   * 提供命令基类和共享工具

2. **模型管理**

   * 文件：`agent-framework/agent_framework/llm/model_registry.py`（新建）

   * 模型列表、能力查询

**【alonechat-desktop层】**：

1. **设置页面增强**

   * 文件：`alonechat-desktop/src/app/(main)/settings/page.tsx`（修改）

   * 模型选择

   * 功能开关

## 五、验收标准

### Phase 1 验收

* [ ] 三种交互模式可切换，权限控制正确

* [ ] 20+工具可用，审批流程正常

* [ ] SQLite会话存储正常，迁移无数据丢失

* [ ] LSP诊断在编辑后触发，错误显示正确

* [ ] 新增CLI命令全部可用

* [ ] 成本追踪显示完整明细

### Phase 2 验收

* [ ] Leader/Worker/Verifier角色可注册

* [ ] Team Engine状态转换正确

* [ ] 对抗验证循环可收敛

* [ ] 局部重试不影响其他Worker

* [ ] 上下文隔离有效，Token节省明显

### Phase 3 验收

* [ ] 工作区快照可创建和恢复

* [ ] RLM并行调度正常

* [ ] 任务队列重启后恢复

* [ ] 多语言切换正常

* [ ] 桌面端Team状态可视化

***

##### 1.6 成本追踪增强

**当前状态**：基础追踪
**目标状态**：按轮次/会话/缓存明细全维度

**【agent-framework层】**：

1. **成本追踪模块**

   * 文件：`agent-framework/agent_framework/cost/tracker.py`（新建）

   * 功能：

     * 按轮次统计

     * 按会话统计

     * 缓存命中/未命中明细

     * 实时成本估算

2. **成本数据模型**

   * 文件：`agent-framework/agent_framework/cost/types.py`（新建）

   * CostRecord, SessionCost, CacheStats等

3. **成本存储**

   * 文件：`agent-framework/agent_framework/cost/storage.py`（新建）

   * SQLite存储成本记录

4. **成本配置**

   * 文件：`agent-framework/agent_framework/configs/cost.yaml`（新建）

   * 内容：

     ```yaml
     cost:
       tracking_enabled: true
       rates:
         deepseek-v4:
           input: 0.001  # $/1M tokens
           output: 0.002
           cache_hit: 0.0001
       alerts:
         session_threshold: 1.0
         daily_threshold: 10.0
     ```

**【alonework-cli层】**：

1. **成本显示**

   * 文件：`alonework-cli/src/alonechat/cost/display.py`（新建）

   * 使用Rich表格显示成本

   * 实时成本更新

2. **成本slash命令**

   * 文件：`alonework-cli/src/alonechat/slash/commands/cost.py`（修改）

   * `/cost` - 显示当前会话成本

   * `/cost session` - 会话成本明细

   * `/cost daily` - 每日成本统计

**【alonechat-desktop层】**：

1. **成本仪表板**

   * 文件：`alonechat-desktop/src/components/agent/cost-dashboard.tsx`（新建）

   * 成本趋势图

   * Token使用分布

2. **成本指示器**

   * 文件：`alonechat-desktop/src/components/agent/cost-indicator.tsx`（新建）

   * 状态栏显示当前成本

   * 超阈值警告

## 六、执行顺序

```
Week 1-2:  交互模式 + 工具系统
Week 3-4:  会话SQLite + LSP集成
Week 5-6:  CLI命令 + 成本追踪
Week 7-8:  角色体系 + MultiAgentTeam扩展
Week 9-10: Team Engine + 上下文隔离
Week 11-12: 快照系统 + RLM
Week 13-14: 任务队列 + 多语言
Week 15:   产品化集成
```

***

### Phase 2: 架构升级 - Mavis角色体系（第7-10周）

**目标**：引入Leader/Worker/Verifier角色体系，构建状态机Runtime

***

#### Week 7-8: 角色体系建设

##### 2.1 定义角色体系

**【agent-framework层】**：

1. **扩展AgentRole枚举**

   * 文件：`agent-framework/agent_framework/core/types.py`（修改）

   * 新增：

     ```python
     class AgentRole(str, Enum):
         LEADER = "leader"      # 统筹、规划、调度、聚合
         WORKER = "worker"      # 执行、具体任务
         VERIFIER = "verifier"  # 验收、质量门禁

     class RoleConfig(BaseModel):
         role: AgentRole
         capabilities: List[str]
         tools: List[str]
         max_retries: int = 3
         timeout: int = 300
     ```

2. **创建LeaderAgent基类**

   * 文件：`agent-framework/agent_framework/agent/leader_agent.py`（新建）

   * 职责：

     * 任务理解和规划

     * 子任务拆分（复用TaskPlanner）

     * Worker调度和监控

     * 结果聚合和最终交付

   * 参考：现有MTCAgent的意图澄清和任务规划能力

3. **创建WorkerAgent基类**

   * 文件：`agent-framework/agent_framework/agent/worker_agent.py`（新建）

   * 职责：

     * 专注执行具体子任务

     * 配备独立工具集

     * 独立上下文容器

     * 标准化输出协议

   * 参考：现有ReActAgent的执行能力

4. **创建VerifierAgent基类**

   * 文件：`agent-framework/agent_framework/agent/verifier_agent.py`（新建）

   * 职责：

     * 独立审查Worker输出

     * 质量评分和门禁

     * 打回策略

     * 最大对抗轮数控制

   * 关键：与Worker形成目标函数相反的对抗关系

5. **角色配置**

   * 文件：`agent-framework/agent_framework/configs/roles.yaml`（新建）

   * 内容：

     ```yaml
     roles:
       leader:
         model: "deepseek-v4"
         system_prompt_template: "leader_prompt.yaml"
         capabilities: ["plan", "dispatch", "aggregate"]
       worker:
         model: "deepseek-v4-flash"
         system_prompt_template: "worker_prompt.yaml"
         capabilities: ["execute", "report"]
       verifier:
         model: "deepseek-v4"
         system_prompt_template: "verifier_prompt.yaml"
         capabilities: ["verify", "reject"]
     ```

**【alonework-cli层】**：

1. **CLI Team模式**

   * 文件：`alonework-cli/src/alonechat/commands/team.py`（新建）

   * `alonechat team` - 启动Team模式

   * 显示多Agent协作状态

2. **Team状态显示**

   * 文件：`alonework-cli/src/alonechat/team/display.py`（新建）

   * 使用Rich显示Leader/Worker/Verifier状态

   * 实时进度更新

**【alonechat-desktop层】**：

1. **Team可视化组件**

   * 文件：`alonechat-desktop/src/components/agent/team-view.tsx`（新建）

   * 显示Team结构

   * Agent状态卡片

   * 通信流程图

2. **Team状态Store**

   * 文件：`alonechat-desktop/src/stores/team-store.ts`（新建）

   * 管理Team状态

   * 与Gateway同步

***

##### 2.2 扩展MultiAgentTeam

**【agent-framework层】**：

1. **支持角色化注册**

   * 文件：`agent-framework/agent_framework/agent/multi_agent.py`（修改）

   * 新增方法：

     * `register_leader(agent)` - 注册Leader

     * `register_worker(agent, capabilities)` - 注册Worker

     * `register_verifier(agent)` - 注册Verifier

2. **实现角色间通信路由**

   * 文件：`agent-framework/agent_framework/core/role_router.py`（新建）

   * 通信模式：

     * Leader → Worker: 任务分发

     * Worker → Verifier: 成果提交

     * Verifier → Leader: 验收结果

     * Verifier → Worker: 打回修正

***

#### Week 9-10: Team Engine状态机Runtime

##### 2.3 构建Team Engine

**【agent-framework层】**：

1. **定义Agent生命周期状态**

   * 文件：`agent-framework/agent_framework/orchestration/team_engine.py`（新建）

   * 状态：

     ```python
     class AgentState(str, Enum):
         PENDING = "pending"      # 等待执行
         PRODUCING = "producing"  # 执行中
         VERIFYING = "verifying"  # 验证中
         DONE = "done"           # 完成
         RETRY = "retry"         # 重试
         FAILED = "failed"       # 失败

     class TeamState(BaseModel):
         leader_state: AgentState
         workers: Dict[str, AgentState]
         verifiers: Dict[str, AgentState]
         current_phase: str  # "planning" | "executing" | "verifying" | "done"
     ```

2. **实现状态机核心**

   * 状态转换逻辑

   * 事件驱动

   * 超时控制

   * 确定性调度

3. **实现对抗验证循环**

   ```
   Worker交付 → Verifier审查 → 通过/打回 → 重试/继续
   ```

   * 参数：max\_retry\_count, quality\_threshold

   * 防止无限循环

4. **实现局部重试**

   * 只重试失败的Worker

   * 不影响已成功的Worker

   * 失败恢复机制

5. **Team Engine配置**

   * 文件：`agent-framework/agent_framework/configs/team_engine.yaml`（新建）

   * 内容：

     ```yaml
     team_engine:
       max_retries: 3
       verification_threshold: 0.8
       timeout:
         worker: 300
         verifier: 60
       parallel_workers: 4
     ```

**【alonework-cli层】**：

1. **Team Engine CLI集成**

   * 文件：`alonework-cli/src/alonechat/team/engine_cli.py`（新建）

   * Team启动/停止

   * 状态查询

**【alonechat-desktop层】**：

1. **Team Engine可视化**

   * 文件：`alonechat-desktop/src/components/agent/team-engine-view.tsx`（新建）

   * 状态机流程图

   * 实时状态转换动画

***

##### 2.4 上下文隔离机制

**【agent-framework层】**：

1. **创建上下文隔离模块**

   * 文件：`agent-framework/agent_framework/core/context_isolation.py`（新建）

2. **实现结构化摘要生成器**

   * 将完整上下文压缩为结构化摘要

   * 包含关键信息和文件路径引用

3. **实现按需读取协议**

   * Agent只持有职责相关上下文

   * 需要时通过文件路径读取完整内容

4. **集成AgentBus**

   * 文件：`agent-framework/agent_framework/core/agent_bus.py`（修改）

   * 支持结构化摘要通信

***

### Phase 3: 高级特性与产品化（第11-15周）

**目标**：补齐高级功能，落地产品场景

***

#### Week 11-12: 工作区快照与RLM

##### 3.1 工作区快照/回滚

**【agent-framework层】**：

1. **快照引擎**

   * 文件：`agent-framework/agent_framework/snapshot/engine.py`（新建）

   * 使用side-git机制（不影响项目.git）

   * 功能：

     * `create_snapshot()` - 创建快照

     * `list_snapshots()` - 列出快照

     * `restore_snapshot(id)` - 恢复快照

     * `cleanup_snapshots()` - 清理过期快照

2. **快照存储**

   * 文件：`agent-framework/agent_framework/snapshot/storage.py`（新建）

   * SQLite存储快照元数据

**【alonework-cli层】**：

1. **快照slash命令**

   * 文件：`alonework-cli/src/alonechat/slash/commands/snapshot.py`（新建）

   * `/snapshot` - 创建快照

   * `/restore [id]` - 恢复快照

   * `/snapshots` - 列出快照

**【alonechat-desktop层】**：

1. **快照面板**

   * 文件：`alonechat-desktop/src/components/agent/snapshot-panel.tsx`（新建）

   * 快照列表

   * 恢复操作

***

##### 3.2 RLM (低成本子任务调度)

**【agent-framework层】**：

1. **RLM调度器**

   * 文件：`agent-framework/agent_framework/rlm/dispatcher.py`（新建）

   * 功能：

     * 使用flash模型处理低成本子任务

     * 并行执行和结果聚合

     * 批量分析和推理

2. **RLM配置**

   * 文件：`agent-framework/agent_framework/configs/rlm.yaml`（新建）

   * 内容：

     ```yaml
     rlm:
       model: "deepseek-v4-flash"
       max_parallel: 8
       timeout: 60
       cost_threshold: 0.1
     ```

***

#### Week 13-14: 持久化任务队列与多语言

##### 3.3 持久化任务队列

**【agent-framework层】**：

1. **任务队列模块**

   * 文件：`agent-framework/agent_framework/queue/task_queue.py`（新建）

   * 功能：

     * SQLite任务表

     * 支持cron表达式

     * 重启后恢复

     * 进度通知

2. **任务调度器**

   * 文件：`agent-framework/agent_framework/queue/scheduler.py`（新建）

   * 后台任务执行

   * 任务状态管理

**【alonework-cli层】**：

1. **任务队列命令**

   * 文件：`alonework-cli/src/alonechat/commands/tasks.py`（新建）

   * `alonechat tasks list` - 列出任务

   * `alonechat tasks cancel <id>` - 取消任务

**【alonechat-desktop层】**：

1. **任务面板**

   * 文件：`alonechat-desktop/src/app/(main)/tasks/page.tsx`（修改）

   * 任务列表

   * 进度显示

***

##### 3.4 多语言UI支持

**【agent-framework层】**：

1. **国际化模块**

   * 文件：`agent-framework/agent_framework/i18n/__init__.py`（新建）

   * 语言资源加载

   * 翻译函数

**【alonework-cli层】**：

1. **CLI国际化**

   * 目录：`alonework-cli/src/alonechat/locale/`（新建）

   * 支持：en, ja, zh-Hans, pt-BR

   * 自动检测系统语言

2. **语言切换命令**

   * `/locale [lang]` - 切换语言

**【alonechat-desktop层】**：

1. **桌面端国际化**

   * 目录：`alonechat-desktop/src/locale/`（新建）

   * next-intl集成

   * 语言切换UI

***

#### Week 15: 产品化集成

##### 3.5 Gateway API扩展

**【agent-framework层】**：

1. **Team API**

   * 文件：`agent-framework/agent_framework/gateway/team_api.py`（新建）

   * 端点：

     * `POST /team/create` - 创建Team

     * `GET /team/{id}/status` - 获取状态

     * `POST /team/{id}/abort` - 中止Team

2. **成本API**

   * 文件：`agent-framework/agent_framework/gateway/cost_api.py`（新建）

   * 端点：

     * `GET /cost/session` - 会话成本

     * `GET /cost/daily` - 每日成本

**【alonechat-desktop层】**：

1. **完整集成**

   * Team状态可视化

   * 成本仪表板

   * 诊断面板

   * 快照管理

***

## 三、技术决策

### 3.1 存储升级

| 决策点  | 选择                    | 理由             |
| ---- | --------------------- | -------------- |
| 会话存储 | SQLite (aiosqlite)    | 零依赖，性能好，支持复杂查询 |
| 任务队列 | SQLite                | 简单可靠，无需外部依赖    |
| 快照存储 | side-git + SQLite元数据  | 复用git能力，元数据持久化 |
| 配置格式 | YAML(保留) + TOML(用户配置) | 现有规范延续         |

### 3.2 LSP集成

| 语言         | 服务器                        | 安装方式                                      |
| ---------- | -------------------------- | ----------------------------------------- |
| Python     | pyright                    | npm install -g pyright                    |
| TypeScript | typescript-language-server | npm install -g typescript-language-server |
| Go         | gopls                      | go install golang.org/x/tools/gopls       |
| Rust       | rust-analyzer              | rustup component add rust-analyzer        |

### 3.3 架构原则

1. **保持agent-framework核心地位** - 新功能优先在framework层实现
2. **三层协同** - 每个功能在三层都有对应实现
3. **复用现有能力** - TaskPlanner、ReActAgent、AgentBus等
4. **中英双语注释** - 保持代码可读性
5. **禁止硬编码** - 全部配置使用YAML

***

## 四、风险评估

| 风险           | 影响 | 缓解策略                |
| ------------ | -- | ------------------- |
| SQLite迁移数据丢失 | 高  | 保留JSON备份，实现双向同步     |
| LSP服务器不可用    | 中  | 优雅降级，显示警告而非错误       |
| 对抗验证无限循环     | 中  | 设置最大轮数上限，Leader最终裁量 |
| Token成本翻倍    | 中  | 简单任务不用Team，默认单Agent |
| 状态机复杂度       | 中  | 完善的轨迹日志和可观测性        |
| 三层同步复杂度      | 中  | 明确API契约，使用类型检查      |

***

## 五、验收标准

### Phase 1 验收

* [ ] 三种交互模式可切换，权限控制正确

* [ ] 20+工具可用，审批流程正常

* [ ] SQLite会话存储正常，迁移无数据丢失

* [ ] LSP诊断在编辑后触发，错误显示正确

* [ ] 新增CLI命令全部可用

* [ ] 成本追踪显示完整明细

* [ ] 桌面端模式切换、工具面板、会话列表正常

### Phase 2 验收

* [ ] Leader/Worker/Verifier角色可注册

* [ ] Team Engine状态转换正确

* [ ] 对抗验证循环可收敛

* [ ] 局部重试不影响其他Worker

* [ ] 上下文隔离有效，Token节省明显

* [ ] 桌面端Team可视化正常

### Phase 3 验收

* [ ] 工作区快照可创建和恢复

* [ ] RLM并行调度正常

* [ ] 任务队列重启后恢复

* [ ] 多语言切换正常

* [ ] 桌面端完整集成正常

***

## 六、执行顺序

```
Week 1-2:  交互模式 + 工具系统 (三层同步)
Week 3-4:  会话SQLite + LSP集成 (三层同步)
Week 5-6:  CLI命令 + 成本追踪 (三层同步)
Week 7-8:  角色体系 + MultiAgentTeam扩展 (三层同步)
Week 9-10: Team Engine + 上下文隔离 (三层同步)
Week 11-12: 快照系统 + RLM (三层同步)
Week 13-14: 任务队列 + 多语言 (三层同步)
Week 15:   产品化集成 + Gateway API扩展
```

***

## 七、下一步行动

1. **立即开始**：Phase 1.1 交互模式管理系统

2. **立即开始**：Phase 1.1 交互模式管理系统

   * agent-framework: 定义类型和配置

   * alonework-cli: 实现CLI模式管理器

   * alonechat-desktop: 实现模式切换组件

3. **并行准备**：SQLite Schema设计和LSP调研

4. **持续集成**：每个功能完成后编写测试

