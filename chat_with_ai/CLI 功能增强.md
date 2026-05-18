# CLI 功能增强

> **Workspace:** e:\AloneChat-workspace-master

---

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## Assistant
Error: 

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## Assistant
Error: 

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## Assistant
Error: 

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## Assistant
Error: 

## User
cli加强功能 	 版本 	 说明 
 通配符权限规则 	 2.1.0 	 使用 * 如 Bash(npm *)、Bash(git * main) 
 权限规则中支持输出重定向 	 1.0.123 	 Bash(python:*) 匹配 python script.py > out 
 沙箱模式正式发布 	 2.0.24 	 Linux 和 macOS 上 BashTool 沙箱 
 受管设置支持 macOS plist/Windows 注册表 	 2.1.51 	 企业策略可通过系统配置下发 
 企业托管设置 	 2.0.68 	 
 OAuth 令牌存储在 macOS Keychain 	 0.2.30 	 更安全的凭据存储

## Assistant
我来分析这个CLI增强需求表，先了解项目结构和agent-framework现有实现。

Now let me search for specific implementations in parallel.

## User
继续

## Assistant
Now let me dig deeper into the CLI commands and agent implementations:

Let me explore some more key modules:

## 项目整体布局报告

### 1. 顶级目录结构

项目根目录位于 `E:\AloneChat-workspace-master`，包含以下主要模块：

| 目录/文件 | 说明 |
|----------|------|
| `agent-framework/` | AI Agent 核心框架 (Python包，v0.3.0) |
| `alonechat-cli/` | 命令行工具 (Python包，v0.2.0) |
| `alonechat-desktop/` | 桌面应用 (Tauri + Next.js) |
| `docs/` | 文档目录（架构设计、技术报告、发布说明、安全审计等） |
| `bugs/` | Bug追踪 |
| `.trae/` | 工作区配置/规范/计划文档 |
| `Makefile` | 构建脚本 |
| `README.md` / `README_CN.md` | 项目说明 |

---

### 2. agent-framework 详细结构

位置：`E:\AloneChat-workspace-master\agent-framework\agent_framework\`

这是一个**生产级 Agent 网关**系统，版本 v0.3.0，依赖 LiteLLM、FastAPI、ChromaDB、NetworkX 等关键库。

#### 2.1 核心抽象层 (`core/`)

| 文件 | 功能 |
|------|------|
| [base_llm.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_llm.py) | LLM 抽象基类，定义 `chat()` 和 `chat_stream()` 接口，以及 `Message`、`LLMConfig`、`UsageInfo` 模型 |
| [base_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_agent.py) | Agent 抽象基类，定义感知(perceive)、规划(plan)、行动(act)、反思(reflect)四阶段接口 |
| [base_tool.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_tool.py) | 工具抽象基类，定义 `execute()` 接口，以及 `ToolDef`、`ToolResult`、`ToolParameter` 模型 |
| [base_memory.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_memory.py) | 记忆抽象基类，定义 `add()`、`query()`、`clear()` 接口 |
| [types.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) | 核心类型定义：`AgentState`、`MessageRole`、`AgentMode`(MTC/CODE)、`TaskStatus`、`TaskPriority`、`FilePermission`、`ExecutionEnvironment` |
| [task.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/task.py) | 任务模型：`Task`(含依赖关系)、`Artifact`(产物)、`Reference`(引用) |
| [orchestrator.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/orchestrator.py) | 编排器抽象基类，支持 `run`、`run_multi`、`run_workflow`(DAG) |
| [agent_bus.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/core/agent_bus.py) | Agent 消息总线，支持 `send`、`broadcast`、`receive`、`get_conversation` |

#### 2.2 Agent 实现层 (`agent/`)

| 文件 | 功能 |
|------|------|
| [react_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/react_agent.py) | **ReAct Agent**：核心实现，支持 Thought-Action-Observation 循环，工具调用和流式执行 |
| [mtc_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/mtc_agent.py) | **MTC Agent** (More Than Coding)：面向非开发用户，含意图澄清(`IntentClarifier`)、任务规划(`TaskPlanner`)、任务分解 |
| [code_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/code_agent.py) | **Code Agent**：面向开发者用户 |
| [multi_agent.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/multi_agent.py) | **MultiAgent Team**：多Agent团队协作，支持 `sequential_discussion`(顺序讨论)、`vote_aggregation`(投票聚合) |
| [intent_clarifier.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/intent_clarifier.py) | 独立意图澄清器 |
| [task_planner.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/agent/task_planner.py) | 独立任务规划器 |

#### 2.3 网关层 (`gateway/`)

| 文件 | 功能 |
|------|------|
| [core.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/core.py) | **GatewayCore**：WebSocket 服务器，处理连接、认证(JWT)、消息路由、工具调用、心跳 |
| [api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/api.py) | **FastAPI REST API**：模式切换(MTC/CODE)、任务管理、Skills管理、Artifact管理、统计 |
| [router.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/router.py) | 消息路由器，支持按用户/会话/主题/Agent路由 |
| [session.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/session.py) | 会话管理器 |
| [auth.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/auth.py) | 认证模块 |
| [tools.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/tools.py) | 工具执行器 |
| [mcp_api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/mcp_api.py) | MCP 服务器管理 API |
| [user_api.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/user_api.py) | 用户 API |
| [websocket.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/websocket.py) | WebSocket 管理 |

启动方式：`gateway_main.py`，默认绑定 `127.0.0.1:18789`。

#### 2.4 其他重要模块

| 模块 | 功能 |
|------|------|
| `llm/` | LiteLLM 提供者封装 |
| `memory/` | 对话记忆 + 向量记忆(ChromaDB) |
| `rag/` | RAG流水线：文档加载、分块、嵌入、检索、代码索引 |
| `tools/` | 工具系统：注册中心、内置工具(计算器/搜索/时间)、Skills管理CLI、Skills市场、skills.sh客户端 |
| `sandbox/` | 子进程沙箱、增强沙箱 |
| `orchestration/` | 编排系统：顺序流、并行流、DAG工作流 |
| `observability/` | 日志、指标、追踪 |
| `services/` | 文件处理(Word/Excel/PPT/PDF/图片OCR)、文件生成、任务规划、测试生成、错误修复 |
| `deepseek_optimization/` | DeepSeek 优化：语义缓存、向量缓存、上下文压缩、消息排名、百万级上下文管理、SWE引擎、许可证管理、数据保护 |
| `channels/` | 通道适配器，支持聊天应用集成 |
| `security/` | 速率限制器 |
| `configs/` | YAML 配置文件：`models.yaml`(模型配置)、`prompts.yaml`、`skills.yaml`、`sandbox.yaml`、`intent_clarification.yaml` |

---

### 3. CLI 相关代码详细结构

CLI 工具位于 `E:\AloneChat-workspace-master\alonechat-cli`，版本 v0.2.0，使用 Click + Rich 构建。

#### 3.1 CLI 入口

[cli.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/cli.py) 是主入口，注册了以下命令：

```python
# 命令注册
main.add_command(init.init_command, name="init")       # 初始化配置
main.add_command(chat.chat_command, name="chat")       # 交互式对话
main.add_command(generate.generate_command, name="generate")  # 代码生成
main.add_command(test.test_command, name="test")       # 自动测试
main.add_command(commit.commit_command, name="commit")  # 智能提交
main.add_command(mcp_command, name="mcp")              # MCP管理
main.add_command(agent_commands, name="agent")         # Agent高级功能
```

支持的全局选项：
- `-p/--print`：打印模式（非交互）
- `-C/--continue`：继续最近会话
- `-r/--resume`：恢复指定会话
- `--name`：设置会话名称
- `--model`：指定模型
- `--auto-compact`：自动压缩对话

#### 3.2 命令模块 (`commands/`)

| 文件 | 功能 |
|------|------|
| [init.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/init.py) | 初始化配置，创建 `.alonechatrc` 和加密存储 API Key |
| [chat.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/chat.py) | 交互式对话，支持多轮对话、Slash命令、上下文缓存、使用量显示 |
| [generate.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/generate.py) | 代码生成：函数、类、模块、项目脚手架 |
| [test.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/test.py) | 自动测试：调用 agent-framework 的 TestGenerator |
| [commit.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/commit.py) | 智能提交：Git变更分析、AI增强提交消息、交互式提交 |
| [agent.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/commands/agent.py) | **关键集成点**：调用 agent-framework 的高级功能，包括任务规划(task)、文件处理(process)、错误修复(fix)、技能管理(skill)、RAG检索(rag)、文件生成(generate)、数据分析(analyze) |

#### 3.3 Slash 命令系统 (`slash/`)

CLI 在交互式对话中支持丰富的 Slash 命令：

| 命令 | 功能 |
|------|------|
| `/help` | 帮助信息 |
| `/clear` | 清除对话历史 |
| `/compact` | 压缩对话上下文 |
| `/config` | 打开配置界面 |
| `/model` | 切换模型 |
| `/agents` | 管理子代理 |
| `/mcp` | 管理MCP服务器 |
| `/permissions` | 管理权限 |
| `/init` | 初始化项目 |
| `/review` | 请求代码审查 |
| `/rewind` | 回退对话 |
| `/fork` | 分叉当前会话 |
| `/branch` | 管理会话分支 |
| `/status` | 显示当前状态 |
| `/usage` | 显示使用限制 |
| `/cost` | 显示token使用统计 |
| `/doctor` | 检查安装健康状态 |
| `/vim` | Vim模式 |

#### 3.4 其他 CLI 模块

| 模块 | 功能 |
|------|------|
| `config/` | 配置管理，支持 `.alonechatrc` 和加密 API Key 存储 |
| `configs/` | YAML 配置：`deepseek_config.yaml`、`code_config.yaml`、`chinese_config.yaml`、`git_config.yaml`、`utils_config.yaml` |
| `session/` | 会话管理：创建、恢复、消息存储(mananger + storage) |
| `models/` | 模型路由，集成 DeepSeek V4 Flash |
| `deepseek/` | DeepSeek 专用：上下文管理、加密、提示工程 |
| `mcp/` | MCP CLI 和配置 |
| `git/` | Git集成：GitManager(状态/分析/提交)、SmartCommit(AI增强) |
| `code/` | 代码生成器 |
| `chinese/` | 中文优化：NLP、代码风格 |
| `utils/` | 工具函数：交互式、日志、进度条 |

---

### 4. 关键架构关系

**CLI 与 agent-framework 的关系**：

CLI 有两种使用模式：
1. **独立模式**：直接使用 DeepSeek 模型进行交互，不依赖 agent-framework
2. **集成模式**：通过 `alonechat agent` 命令和 `alonechat test` 命令，调用 agent-framework 的 TaskPlanner、FileProcessors、ErrorFixer、SkillsRegistry、RAGPipeline、TestGenerator、FileGeneratorService 等模块

**agent-framework 的入口**：
- 网关服务：`gateway_main.py`（启动 WebSocket + FastAPI 服务器）
- 代码库入口：`agent_framework.__init__` 导出核心组件（BaseLLM、BaseAgent、BaseTool、BaseMemory、Orchestrator、AgentBus、AgentConfig）
- Skills CLI：`pyproject.toml` 中注册的 `skills` 命令入口

**数据存储方式**（遵循项目规则）：
- 所有配置数据使用 YAML 存储：`config.yaml`(框架)、`models.yaml`(模型)、`skills.yaml`(技能)、`intent_clarification.yaml`(意图澄清) 等
- 禁止硬编码

好的，让我先深入了解现有代码中与这些功能相关的部分。

我来系统地搜索 agent-framework 中所有与权限相关的代码。首先并行执行搜索和文件读取操作。

现在读取所有关键文件：

让我继续读取配置初始化文件和工具目录中的相关文件：

现在让我检查网关的用户API和Agent基类中是否有权限相关的逻辑：

现在我已经完成了全面的搜索和分析。以下是所有搜索结果的详细报告。

---

## 配置管理与凭据存储实现分析报告

### 一、agent-framework 配置管理

#### 1. 主配置管理模块 -- [config.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/config.py)

**核心类：**

- **`AgentConfig`** (`BaseSettings`): 主配置类，通过 `pydantic_settings` 支持从 `.env` 文件读取环境变量。
  - 子配置：`LLMSettings`、`MemorySettings`、`GatewaySettings`、`LoggingSettings`、`MetricsSettings`、`TracingSettings`、`ModeSettings`（含 `MTCSettings` 和 `CODESettings`）
  - 支持从 YAML (`from_yaml`)、JSON (`from_json`)、字典 (`from_dict`) 加载
  - 支持导出为 YAML/JSON/字典

- **`ConfigManager`**: 单例模式配置管理器，支持：
  - 配置热加载（通过 `watchfiles`）
  - 配置变更回调通知
  - 深度更新配置
  - 文件变更监控

```python
# 关键设计：api_key 存储在 LLMSettings 中，默认从环境变量读取
class LLMSettings(BaseModel):
    api_key: Optional[str] = Field(default=None, description="API密钥")
```

**问题：** API Key 存储在内存中明文状态，序列化到 YAML 文件时也是明文。

#### 2. YAML 配置加载 -- [configs/__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/__init__.py)

提供多个单例配置类，均从 YAML 文件加载：

| 类 | 配置文件 | 用途 |
|---|---|---|
| `PromptsConfig` | `prompts.yaml` | 提示词模板 |
| `ModelsConfig` | `models.yaml` | 模型参数和定价 |
| `SandboxConfig` | `sandbox.yaml` | 沙箱权限和命令白名单 |
| `IntentClarificationConfig` | `intent_clarification.yaml` | 意图澄清规则 |
| `SkillsConfig` | `skills.yaml` | 技能定义 |

使用 `load_yaml_config()` 函数实现带缓存的 YAML 加载，支持 `reload_config()` 重新加载。

#### 3. JWT 认证与令牌管理 -- [gateway/auth.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/auth.py)

**核心类：**

- **`UserManager`**: 内存用户管理器
  - `_users`、`_users_by_username`、`_users_by_email` -- 内存字典存储
  - `_refresh_tokens` -- 刷新令牌内存存储

- **JWT 配置：**
  - `JWT_SECRET_KEY` -- 从环境变量或随机生成
  - `JWT_ALGORITHM = "HS256"`
  - `JWT_EXPIRE_MINUTES` -- 默认 1440 分钟（24 小时）
  - `JWT_REFRESH_EXPIRE_DAYS` -- 默认 7 天

- **密码加密：** PBKDF2-HMAC-SHA256，100000 次迭代，16 字节随机盐值
- **Token 格式：** `{user_id, username, exp, iat, jti}`

**问题：** 用户和令牌全部存储在内存中，没有持久化；密钥通过环境变量或随机生成，无安全存储机制。

#### 4. 加密管理 -- [deepseek_optimization/security/encryption.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/security/encryption.py)

**`EncryptionManager`**: 基于 `cryptography.fernet` (AES-256-GCM)

```python
class EncryptionManager:
    DEFAULT_SALT_SIZE = 32
    DEFAULT_ITERATIONS = 480000  # OWASP 推荐
```
- PBKDF2 密钥派生（SHA-256）
- 盐值+密文组合存储（Base64 编码）
- `encrypt(data)` / `decrypt(encrypted_data)` 方法
- 支持密钥生成、安全随机数、哈希

#### 5. 许可证管理 -- [deepseek_optimization/security/license_manager.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/security/license_manager.py)

**`LicenseManager`**: 许可证密钥管理
- 基于 HMAC 的许可证签名验证
- 密钥从环境变量 `LICENSE_SECRET_KEY` 或随机生成
- 内存字典存储许可证信息和用量统计

#### 6. 数据保护 -- [deepseek_optimization/security/data_protection.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/security/data_protection.py)

**`DataProtectionManager`**: PII 检测和遮蔽
- 预定义模式：邮箱、电话、SSN、IP地址、信用卡
- `detect_pii()` / `mask_pii()` / `is_sensitive()` / `sanitize_output()`
- 支持自定义 PII 模式

#### 7. 上下文配置 -- [deepseek_optimization/context/context_config.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/context/context_config.py)

**`ContextConfig`**: 单例模式，管理上下文管理相关的所有配置
- 嵌套 dataclass：`TokenEstimationConfig`、`CompressionConfig`、`StorageConfig`、`CacheConfig`、`SessionConfig`
- 支持从 YAML 和环境变量加载
- 支持配置验证

#### 8. MCP 配置管理 -- [deepseek_optimization/mcp_marketplace/config.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/mcp_marketplace/config.py)

**`MCPConfig`**: MCP 服务器配置管理器
- 支持 YAML 加载和环境变量替换 (`${VAR_NAME}` 模式)
- 服务器定义的 CRUD 操作
- `MCPServerDefinition` 和 `MCPSettings` Pydantic 模型

#### 9. 网关会话管理 -- [gateway/session.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/session.py)

**`SessionManager`**: 内存会话管理器
- 会话车道隔离（避免并发冲突）
- 超时清理过期会话
- 用户与会话的映射关系

#### 10. 速率限制 -- [security/rate_limiter.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/security/rate_limiter.py)

**`RateLimiter`**: RPM/TPM 速率限制
- `RateLimitConfig(rpm=60, tpm=100000)`
- 内存滑动窗口

---

### 二、alonechat-cli 配置管理

#### 1. 配置管理与 API 密钥加密 -- [config/__init__.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/config/__init__.py)

**`ConfigManager`**: 最关键的凭据管理实现

```python
class ConfigManager:
    def _get_encryption_key(self) -> bytes:
        # 使用机器特定信息生成加密密钥
        machine_id = f"{platform.node()}-{user_id}"
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=b"alonechat-salt", iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key
```

- **配置文件：** 当前目录下的 `.alonechatrc`（TOML 格式）或 JSON
- **API 密钥加密存储：** 使用 Fernet (AES-256-GCM) 加密
- **加密密钥派生：** 基于机器名+用户ID + PBKDF2，盐值硬编码为 `b"alonechat-salt"`
- **密钥获取优先级：** 环境变量 > 配置文件中的加密密钥

```python
def get_api_key(self, provider: str) -> str | None:
    env_var = f"{provider.upper()}_API_KEY"
    if env_key := os.getenv(env_var):  # 1. 环境变量
        return env_key
    config = self.load_config()
    # 2. 配置文件中的加密密钥
    if encrypted_key := provider_config.get("api_key"):
        return self.decrypt_api_key(encrypted_key)
```

**问题：** 盐值硬编码，降低了基于 PBKDF2 的安全性；加密密钥基于机器信息可预测。

#### 2. YAML 配置加载 -- [configs/config_loader.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/config_loader.py)

**`ConfigLoader`**: 单例 YAML 配置加载器
- 从 `utils_config.yaml` 加载 UI 样式、进度消息、命令配置、历史记录配置、自动补全配置
- 支持点分隔符键访问 (`get("progress.messages")`)
- 提供默认配置回退

#### 3. DeepSeek 加密模块 -- [deepseek/encryption.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/deepseek/encryption.py)

**`CodeEncryptor`**: AES-256-GCM 代码加密

```python
class CodeEncryptor:
    def _get_or_create_master_key(self) -> str:
        key_file = Path.home() / ".alonechat" / ".key"
        if key_file.exists():
            return key_file.read_text().strip()
        # 不存在则基于机器标识生成
        machine_id = self._get_machine_id()
        master_key = hashlib.sha256(machine_id.encode()).hexdigest()
        key_file.write_text(master_key)
        key_file.chmod(0o600)  # 仅所有者可读写
        return master_key
```

- **主密钥存储：** `~/.alonechat/.key` 文件，权限 600
- **密钥派生：** PBKDF2-HMAC-SHA256，100000 次迭代
- **加密结果格式：** `EncryptionResult` dataclass（密文、nonce、盐值、时间戳）
- **`DeepSeekConfigLoader`**: 单例，加载 `deepseek_config.yaml`
- **`SecureUploader`**: 加密后上传代码到 API

#### 4. MCP 配置管理 -- [mcp/config.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/mcp/config.py)

**`MCPConfigManager`**: MCP 服务器配置管理
- 配置文件：`~/.alonechat/mcp.json`
- JSON 格式，符合 MCP 标准
- 支持服务器的添加、删除、启用/禁用

#### 5. 会话存储 -- [session/storage.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/storage.py)

**`SessionStorage`**: 会话持久化存储
- 存储路径：`~/.alonechat/sessions/`
- 每个会话一个 JSON 文件
- 支持会话分叉、显示名称、压缩状态跟踪

**`Session`**: 会话数据类，包含消息列表、元数据、Agent 配置等

#### 6. 会话管理器 -- [session/manager.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/manager.py)

**`SessionManager`**: 会话生命周期管理
- 包装 `SessionStorage`
- 支持创建、分叉、恢复、删除会话
- 自动保存当前会话

#### 7. 权限管理 -- [permissions/manager.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/permissions/manager.py)

**`PermissionManager`**: 工具权限管理
- 配置文件：`~/.alonechat/permissions.json`
- 三种模式：DEFAULT / ACCEPT / PLAN
- 允许/拒绝工具列表
- 支持通配符匹配

#### 8. Slash 命令配置 -- [slash/commands/config.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/config.py)

`/config` 命令，查看当前配置（键值对表格展示），设置配置功能开发中。

#### 9. Slash 命令注册表 -- [slash/registry.py](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/registry.py)

**`SlashCommandRegistry`**: Slash 命令注册中心
- 命令注册、别名管理、分类管理
- 支持搜索

---

### 三、总结与对比

| 功能 | agent-framework | alonechat-cli |
|---|---|---|
| **主配置类** | `AgentConfig` (pydantic BaseSettings) | `ConfigManager` (自定义) |
| **配置文件格式** | YAML / JSON / .env | TOML / JSON / 环境变量 |
| **配置热加载** | 支持 (watchfiles) | 不支持 |
| **API 密钥存储** | 明文，从环境变量或 YAML 读取 | **加密存储** (Fernet) |
| **加密算法** | AES-256-GCM (cryptography) | AES-256-GCM (cryptography) |
| **密钥派生** | PBKDF2-HMAC-SHA256 | PBKDF2-HMAC-SHA256 |
| **密钥存储位置** | 环境变量 / 随机内存 | `~/.alonechat/.key` (chmod 600) |
| **JWT 令牌管理** | 支持，内存存储 | 不支持 |
| **会话存储** | 内存 | `~/.alonechat/sessions/*.json` |
| **MCP 配置** | YAML + 环境变量替换 | `~/.alonechat/mcp.json` |
| **权限管理** | 沙箱配置 (YAML) | `~/.alonechat/permissions.json` |
| **速率限制** | RPM/TPM 限制 | 不支持 |
| **数据保护/PII** | 支持 (正则匹配遮蔽) | 不支持 |

### 四、现有问题

1. **agent-framework 的 `api_key` 未加密存储** -- 在 [config.py:L22](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/config.py#L22) 中 `LLMSettings.api_key` 是明文字段，序列化到 YAML 时也会明文暴露。

2. **alonechat-cli 的盐值硬编码** -- 在 [config/__init__.py:L63](file:///E:/AloneChat-workspace-master/alonechat-cli/src/alonechat/config/__init__.py#L63) 中 `salt=b"alonechat-salt"` 是固定值，降低 PBKDF2 安全性。

3. **加密密钥可预测** -- `config/__init__.py` 中基于机器名生成密钥，同一个机器的所有用户可互解密。

4. **无统一的密钥管理服务** -- 两个项目各自实现了加密，没有共用的密钥管理抽象层。

5. **agent-framework 的令牌存储无持久化** -- `UserManager` 中用户和刷新令牌全部存储在内存字典中，重启后丢失。

让我再检查一下配置文件是否存在权限相关的 YAML 以及 deepseek_optimization/security 目录：

以下是 E:\AloneChat-workspace-master\agent-framework 中与沙箱、子进程、执行环境相关的完整搜索结果和分析。

---

## 一、目录结构

沙箱模块位于 `agent_framework/agent_framework/sandbox/`，包含以下文件：

| 文件 | 说明 |
|------|------|
| [__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/__init__.py) | 模块入口，仅导出 `SubprocessSandbox` |
| [subprocess_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/subprocess_sandbox.py) | 基础子进程沙箱（231行） |
| [enhanced_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/enhanced_sandbox.py) | 增强沙箱（359行） |

相关配置文件：
- [sandbox.yaml](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/sandbox.yaml) -- 沙箱YAML配置（146行）

相关测试文件：
- [tests/test_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/tests/test_sandbox.py) -- 基础沙箱测试
- [tests/test_code_mode.py](file:///E:/AloneChat-workspace-master/agent-framework/tests/test_code_mode.py) -- 增强沙箱测试（TestEnhancedSandbox + TestSandboxSecurity）

相关核心类型：
- [core/types.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) -- 定义了 `ExecutionEnvironment` 和 `FilePermission` 枚举
- [configs/__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/__init__.py) -- 定义了 `SandboxConfig` 配置加载类

---

## 二、现有实现详解

### 2.1 SubprocessSandbox（基础子进程沙箱）

文件：[subprocess_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/subprocess_sandbox.py)

**定位**：第一代基础实现，硬编码命令白名单/黑名单。

**核心设计**：

1. **`SandboxResult` 数据类（第11-17行）**：
   ```python
   @dataclass
   class SandboxResult:
       stdout: str
       stderr: str
       return_code: int
       timed_out: bool = False
   ```

2. **命令白名单/黑名单（第26-51行）**：
   - `ALLOWED_COMMANDS` -- 硬编码的允许命令集合（python, ls, cat, grep 等）
   - `FORBIDDEN_COMMANDS` -- 硬编码的禁止命令集合（rm, sudo, bash, wget, docker 等）
   - 同时还禁止 `python -c`、`python3 -c` 等内联代码执行模式

3. **命令验证 `_validate_command()`（第70-98行）**：
   - 检查命令是否为空
   - 在黑名单中逐个匹配（精确匹配和前缀匹配）
   - 检查是否在白名单中
   - 检查是否包含危险参数（`-c`, `--command`, `-e`, `--eval`, `-exec` 等）

4. **资源限制 `_setup_resource_limits()`（第100-127行）**：
   使用 `resource.setrlimit()` 设置：
   - CPU时间限制（`RLIMIT_CPU`）
   - 内存限制（`RLIMIT_AS`）
   - 输出文件大小限制（`RLIMIT_FSIZE`）
   - 子进程数量限制（`RLIMIT_NPROC`，最多10个）
   - 打开文件数量限制（`RLIMIT_NOFILE`，最多64个）

5. **子进程启动前函数 `_preexec_fn()`（第129-133行）**：
   - 设置资源限制
   - 将工作目录切换为沙箱目录

6. **异步执行 `execute()`（第135-194行）**：
   - 使用 `asyncio.create_subprocess_exec()` 创建子进程
   - 严格限制环境变量（PATH 仅包含 `/usr/bin:/bin`）
   - 设置 `cwd` 为沙箱工作目录
   - 支持超时处理（`asyncio.TimeoutError`），超时时 `proc.kill()`

7. **Python代码安全执行 `execute_python()`（第196-231行）**：
   - 检查危险导入（`os`, `sys`, `subprocess`, `socket` 等30个模块）
   - 将代码写入临时文件后通过 `python3 -u` 执行
   - 执行完毕后清理临时文件

**安全缺陷**（已在 bug 追踪中标注 ACW-0022）：
- `_validate_command()` 的匹配逻辑存在绕过风险
- `python -c` 等禁止模式的黑名单匹配不够严谨
- Linux平台特有的 `resource.setrlimit()` 在Windows上不可用

---

### 2.2 EnhancedSandbox（增强沙箱）

文件：[enhanced_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/enhanced_sandbox.py)

**定位**：第二代实现，从YAML配置文件加载数据替代硬编码，支持MTC/CODE双模式。

**核心设计**：

1. **`SandboxResult` 类（第19-25行）**：
   ```python
   class SandboxResult:
       stdout: str
       stderr: str
       return_code: int
       timed_out: bool = False
       permission_denied: bool = False  # 新增字段
   ```

2. **模式感知的初始化（第48-106行）**：
   - 根据 `AgentMode.MTC` 或 `AgentMode.CODE` 加载不同的配置
   - MTC模式：256MB内存 / 15秒CPU / 30秒wall time，仅read+write权限
   - CODE模式：512MB内存 / 30秒CPU / 60秒wall time，含execute权限
   - 命令白名单从YAML配置自动加载

3. **路径安全验证 `validate_path()`（第114-129行）**：
   - 使用 `Path.resolve()` 解析绝对路径
   - 检查是否包含 `..` 路径遍历攻击
   - 通过 `path.relative_to(project_path)` 验证路径是否在项目文件夹内

4. **文件权限控制（第131-133行）**：
   ```python
   def check_permission(self, permission: FilePermission) -> bool:
       return permission in self.allowed_permissions
   ```

5. **命令验证 `validate_command()`（第139-158行）**：
   - 检查黑名单（禁止命令）
   - 检查白名单（允许命令）
   - 检查危险参数

6. **带超时的执行 `execute_with_timeout()`（第165-239行）**：
   - 与 `SubprocessSandbox.execute()` 类似
   - 但未使用 `resource.setrlimit()`，而是仅依赖 `asyncio.wait_for` 的超时
   - 执行历史记录（`_execution_history`）

7. **文件操作（第241-303行）**：
   - `read_file()` -- 带路径验证和读权限检查的读文件
   - `write_file()` -- 带路径验证和写权限检查的写文件
   - `list_files()` -- 带路径验证的列出目录

8. **沙箱信息 `get_sandbox_info()`（第313-323行）**：
   - 返回沙箱的完整配置信息，便于调试和审计

9. **工厂函数（第326-353行）**：
   - `create_mtc_sandbox()` -- 创建MTC模式沙箱
   - `create_code_sandbox()` -- 创建CODE模式沙箱
   - `reload_sandbox_config()` -- 热重载配置

---

### 2.3 SandboxConfig（配置加载）

文件：[configs/__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/__init__.py) 第198-274行

**设计**：
- 单例模式（`_instance` 类变量）
- 自动从 `sandbox.yaml` 加载配置
- 提供属性访问：`default_config`, `mtc_config`, `code_config`, `forbidden_commands`, `dangerous_flags`, `default_env`
- 提供权限转换方法：`get_mtc_permissions()` / `get_code_permissions()`
- 支持 `reload()` 热重载

---

### 2.4 sandbox.yaml 配置

文件：[sandbox.yaml](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/sandbox.yaml)（146行）

**配置结构**：
- `default` -- 默认限制
- `mtc` -- MTC模式专用配置（命令白名单较严格，仅基础工具命令）
- `code` -- CODE模式专用配置（命令白名单较宽松，含 git/npm/pip/make 等开发工具）
- `forbidden_commands` -- 全局禁止命令（40+条）
- `dangerous_flags` -- 危险参数列表
- `default_env` -- 默认环境变量（PATH, HOME, TMPDIR）

---

### 2.5 核心类型定义

文件：[core/types.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) 第94-113行

```python
class FilePermission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"

class ExecutionEnvironment(str, Enum):
    SANDBOX = "sandbox"
    HOST = "host"
    DOCKER = "docker"
```

`ExecutionEnvironment` 枚举定义了三种执行环境，但目前只有 `SANDBOX` 有实际实现，`HOST` 和 `DOCKER` 尚未实现。

---

### 2.6 测试覆盖

测试文件 | 覆盖范围
---------|----------
[tests/test_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/tests/test_sandbox.py) | `SubprocessSandbox` 的echo、超时、命令白名单、stderr捕获、退出码、网络禁用、执行时间
[tests/test_code_mode.py](file:///E:/AloneChat-workspace-master/agent-framework/tests/test_code_mode.py) (第87-196行) | `EnhancedSandbox` 的双模式创建、路径验证（含路径遍历攻击）、命令验证（白名单/黑名单）、文件读写、权限检查、沙箱信息

---

## 三、整体架构总结

```
sandbox/
  __init__.py          -> 导出 SubprocessSandbox
  subprocess_sandbox.py -> 基础子进程沙箱（硬编码白名单/黑名单 + resource限制）
  enhanced_sandbox.py  -> 增强沙箱（YAML驱动 + 模式感知 + 文件权限 + 路径安全）

configs/
  sandbox.yaml         -> 沙箱全部配置参数
  __init__.py          -> SandboxConfig 单例加载器

core/
  types.py             -> ExecutionEnvironment / FilePermission / AgentMode 枚举

tests/
  test_sandbox.py      -> SubprocessSandbox 测试
  test_code_mode.py    -> EnhancedSandbox + SandboxSecurity 测试
```

**已知问题**：
1. 基础 `SubprocessSandbox` 的 `resource.setrlimit()` 仅支持 Linux/macOS，Windows 不兼容
2. 基础实现中 `FORBIDDEN_COMMANDS` 的黑名单匹配逻辑存在被绕过的风险（bug ACW-0022）
3. 增强沙箱 `EnhancedSandbox` 未使用 `resource.setrlimit()`，资源限制仅依赖 asyncio 超时，安全性较弱
4. `ExecutionEnvironment.DOCKER` 和 `ExecutionEnvironment.HOST` 枚举已定义但无实际实现
5. `__init__.py` 仅导出 `SubprocessSandbox`，未导出 `EnhancedSandbox`

以下是 agent-framework 中与权限相关代码的完整分析报告。

---

## 一、核心类型定义

**文件：** [core/types.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py)

定义了以下权限相关的枚举类型：

1. **`FilePermission`** (第94-102行) -- 文件操作权限枚举，包含三个级别：
   - `READ = "read"` -- 读取权限
   - `WRITE = "write"` -- 写入权限
   - `EXECUTE = "execute"` -- 执行权限

2. **`AgentMode`** (第73-80行) -- Agent 运行模式枚举，包含：
   - `MTC = "mtc"` -- 面向非开发用户
   - `CODE = "code"` -- 面向开发者用户

3. **`ModeConfig`** (第83-91行) -- 模式配置，包含：
   - `allowed_tools: List[str]` -- 该模式允许的工具名称列表
   - `sandbox_config` -- 代码执行的沙箱配置
   - `system_prompt` -- 系统提示词

4. **`ExecutionEnvironment`** (第105-113行) -- 执行环境枚举：
   - `SANDBOX`, `HOST`, `DOCKER`

---

## 二、基础工具类

**文件：** [core/base_tool.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/core/base_tool.py)

基类 `BaseTool` (第30-44行) 本身**不包含任何权限逻辑**。它只定义了工具的基本结构：
- `name`, `description`, `parameters` 属性
- 抽象的 `execute()` 方法
- `get_definition()` 返回 `ToolDef`

工具注册和执行是通过 `ToolRegistry` 类管理的。

---

## 三、工具注册表

**文件：** [tools/registry.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/registry.py)

`ToolRegistry` (第8-122行) 同样**不包含任何权限检查**。它只负责：
- 工具的注册/注销（`register`, `unregister`）
- 工具列表查询（`list_tools`）
- 工具执行（`execute_tool`）-- 仅做参数类型校验，无权限校验
- 执行日志记录

---

## 四、沙箱权限系统（核心权限实现）

### 4.1 SubprocessSandbox（原始/遗留实现）

**文件：** [sandbox/subprocess_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/subprocess_sandbox.py)

这是一个较旧的沙箱实现，包含**硬编码的权限列表**：

- **`ALLOWED_COMMANDS`** (第27-33行) -- 白名单：`python`, `node`, `ls`, `cat`, `grep` 等基础安全命令
- **`FORBIDDEN_COMMANDS`** (第36-51行) -- 黑名单：`rm`, `sudo`, `wget`, `curl`, `bash`, `docker`, `pip` 等危险命令
- **`_validate_command()`** (第70-98行) -- 命令验证方法：
  1. 先检查是否在黑名单中
  2. 再检查是否在白名单中
  3. 最后检查危险参数（`-c`, `--command`, `-e`, `--eval`, `-exec`, `--system` 等）
- **`execute_python()`** (第196-231行) -- 对 Python 代码额外检查危险导入（`os`, `sys`, `subprocess` 等）

资源限制通过 `resource.setrlimit()` 实现（CPU时间、内存、文件大小、子进程数、打开文件数）。

> 注意：此文件中的命令配置是**硬编码**的，并且已经通过 [sandbox.yaml](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/sandbox.yaml) 实现了配置化，由 EnhancedSandbox 替代。

### 4.2 EnhancedSandbox（当前主要实现）

**文件：** [sandbox/enhanced_sandbox.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/enhanced_sandbox.py)

这是当前使用的主要沙箱实现，从 YAML 配置文件加载权限配置：

#### 权限数据来源
- **类级别常量** (第40-46行)：
  - `DEFAULT_ALLOWED_COMMANDS` = 从 `SandboxConfig` 加载 MTC 允许命令
  - `MTC_ALLOWED_COMMANDS` = 从 `SandboxConfig` 加载 MTC 允许命令
  - `CODE_ALLOWED_COMMANDS` = 从 `SandboxConfig` 加载 CODE 允许命令
  - `FORBIDDEN_COMMANDS` = 从 `SandboxConfig` 加载禁止命令

#### 权限检查方法

1. **`validate_path()`** (第114-129行) -- 路径安全检查（防止路径遍历）：
   - 对路径做 `resolve()` 规范化
   - 检查路径是否包含 `..`
   - 通过 `relative_to()` 验证路径是否在项目文件夹内

2. **`check_permission()`** (第131-133行) -- 文件操作权限检查：
   - 检查 `FilePermission` 是否在 `allowed_permissions` 集合中

3. **`set_command_whitelist()`** (第135-137行) -- 设置命令白名单：
   - 允许的命令需要减去禁止的命令集合

4. **`validate_command()`** (第139-158行) -- 命令验证（白名单+黑名单双重校验）：
   - 空命令检查
   - 黑名单检查：检查命令是否在 `FORBIDDEN_COMMANDS` 中
   - 白名单检查：检查命令是否在 `allowed_commands` 中
   - 危险参数检查：检查参数是否在 `dangerous_flags` 中

5. **`execute_with_timeout()`** (第165-239行) -- 带权限验证的执行方法：
   - 执行前调用 `validate_command()` 进行权限检查
   - 权限被拒绝时返回 `SandboxResult(permission_denied=True)`
   - 使用受限的环境变量（仅 `PATH`, `HOME`, `TMPDIR`）

6. **`read_file()` / `write_file()`** (第241-278行) -- 文件读写操作：
   - 先验证路径安全性
   - 再检查文件操作权限

7. **模式工厂函数** (第326-353行)：
   - `create_mtc_sandbox()` -- 创建 MTC 模式沙箱（限制更强）
   - `create_code_sandbox()` -- 创建 CODE 模式沙箱（权限更多）

---

## 五、YAML 配置文件

**文件：** [configs/sandbox.yaml](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/sandbox.yaml)

这是**替代硬编码方案**的权限配置文件，包含以下权限定义：

### 默认配置 (default)
- `max_memory_mb: 512`
- `default_permissions: [read, write]`

### MTC模式权限（面向非开发用户）
- `allowed_permissions: [read, write]` -- 只允许读写
- `allowed_commands` -- 17个基础命令（`python`, `ls`, `cat`, `echo`, `grep` 等）

### CODE模式权限（面向开发者）
- `allowed_permissions: [read, write, execute]` -- 允许读写和执行
- `allowed_commands` -- 30个命令，包含 `node`, `npm`, `git`, `pip`, `make`, `pytest` 等开发工具

### 全局黑名单 (forbidden_commands)
- 共 33 条禁止命令，涵盖：
  - 文件操作：`rm`, `mv`, `chmod`, `chown`
  - 网络：`wget`, `curl`, `ssh`, `scp`
  - Shell：`bash`, `sh`, `zsh` 等
  - 系统：`kill`, `reboot`, `shutdown`, `mount`
  - 包管理：`apt`, `pip`, `npm`, `docker`, `kubectl` 等

### 危险参数 (dangerous_flags)
- `-c`, `--command`, `-e`, `--eval`, `-exec`, `--system`, `--shell`, `--sh`

---

## 六、配置加载器

**文件：** [configs/__init__.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/configs/__init__.py)

`SandboxConfig` 类 (第198-274行) 负责从 `sandbox.yaml` 加载配置并转换为 Python 对象：

- `get_mtc_allowed_commands()` / `get_code_allowed_commands()` -- 获取模式允许命令
- `get_mtc_permissions()` / `get_code_permissions()` -- 获取模式文件权限（将字符串映射为 `FilePermission` 枚举）
- 使用单例模式和缓存机制

---

## 七、主配置中的权限设置

**文件：** [config.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/config.py)

`MTCSettings` (第79-93行) 和 `CODESettings` (第96-109行) 包含沙箱白名单配置：

- **MTC模式**：`allowed_commands: List[str]` 默认为空列表
- **CODE模式**：`allowed_commands: List[str]` 默认为 `["git", "npm", "yarn", "pip", "pip3", "node", "npx", "python", "python3", "make", "docker"]`

---

## 八、计算器工具的白名单验证

**文件：** [tools/builtin/calculator.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/tools/builtin/calculator.py)

`CalculatorTool` (第8-391行) 包含独立的表达式安全性校验：

- `ALLOWED_NAMES` -- math 模块的函数白名单
- `ALLOWED_OPERATORS` -- 允许的运算符
- `_sanitize_expression()` -- 通过正则黑名单模式匹配危险关键字
- 使用 `ast.parse()` + 白名单验证替代 `eval()`

---

## 九、Gateway 层权限

**文件：** [gateway/tools.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/tools.py)

- 包含 `safe_evaluate_math()` 函数，重复了 calculator 的 AST 安全校验逻辑
- 在用户 API [gateway/user_api.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/gateway/user_api.py) 中有基本的会话访问控制（403 权限拒绝）

---

## 十、安全模块

**文件：** [security/rate_limiter.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/security/rate_limiter.py)

- `RateLimiter` -- 请求频率限制器，按 RPM（每分钟请求数）和 TPM（每分钟Token数）限流

**文件：** [deepseek_optimization/security/license_manager.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/security/license_manager.py)

- `LicenseManager` -- 许可证管理器，提供基于 HMAC 签名的授权控制、配额检查和并发限制

---

## 十一、现有权限模型总结

| 维度 | 实现位置 | 机制 |
|---|---|---|
| **命令白名单** | `enhanced_sandbox.py` + `sandbox.yaml` | 允许的命令列表，按模式(MTC/CODE)区分 |
| **命令黑名单** | `enhanced_sandbox.py` + `sandbox.yaml` | 禁止的危险命令列表 |
| **危险参数检查** | `enhanced_sandbox.py` + `sandbox.yaml` | 禁止 `-c`, `--eval` 等危险标志 |
| **文件操作权限** | `enhanced_sandbox.py` + `types.py` `FilePermission` | READ/WRITE/EXECUTE 三级 |
| **路径安全** | `enhanced_sandbox.py::validate_path()` | 防止路径遍历攻击 |
| **资源限制** | `subprocess_sandbox.py` + `sandbox.yaml` | CPU、内存、输出大小限制 |
| **工具级别权限** | 没有统一实现 | `ToolRegistry` 没有任何权限检查 |
| **计算器白名单** | `calculator.py` | AST + 函数白名单 |
| **速率限制** | `security/rate_limiter.py` | RPM/TPM 限流 |
| **许可证/配额** | `deepseek_optimization/security/license_manager.py` | HMAC签名+配额控制 |

### 关键缺失

1. **`ToolRegistry` 没有工具级别的权限检查** -- 任何注册的工具都可以被任意调用，没有白名单/黑名单机制
2. **`BaseTool` 没有权限属性** -- 每个工具无法声明自身需要的权限级别
3. **权限仅在沙箱层级实现** -- 只对命令执行有权限控制，工具层面无控制
4. **无角色/用户权限模型** -- 没有基于用户角色的工具访问控制
5. **`ModeConfig.allowed_tools` 定义但未使用** -- [core/types.py](file:///E:/AloneChat-workspace-master/agent-framework/agent_framework/core/types.py) 第89行的 `allowed_tools` 字段在 `ModeConfig` 中已定义，但在 `ToolRegistry` 中未被使用

让我进一步查看关键代码文件。

现在我已经全面了解了代码库。让我制定实施计划。

好的，开始逐步实现。先从通配符权限规则 + 输出重定向支持开始。

首先创建权限规则系统的核心模块。

现在创建权限规则的 YAML 配置文件和更新配置加载器。

现在增强沙箱模式，修复 `SandboxResult` 为 dataclass、添加跨平台支持和正式发布状态。

现在更新沙箱模块的导出和配置文件。

现在创建企业托管设置模块，支持 macOS plist / Windows 注册表。

更新 `__init__.py` 以导出新模块，并继续实现 OAuth 令牌存储。

现在创建 OAuth 令牌安全存储模块，支持多平台凭据存储。

更新 `__init__.py` 导出凭证模块，然后验证所有代码。

现在验证所有代码的语法正确性。

所有 6 个 CLI 加强功能已在 `agent-framework` 中实现完成。以下是详细的实现总结：

---

## 实现总结

### 1. 通配符权限规则 (v2.1.0)

**文件：** [permission_rule.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/permissions/permission_rule.py)

- 使用 `fnmatch` 实现标准通配符匹配，支持 `Bash(npm *)`、`Bash(git * main)` 等模式
- `PermissionRule` 数据类支持 `tool_pattern` 和 `command_pattern` 的灵活组合
- `PermissionMode` (ACCEPT/PLAN/REVIEW/DEFAULT) 和 `PermissionAction` (ALLOW/DENY/PROMPT) 
- 支持 `*` 全局匹配

### 2. 权限规则中支持输出重定向 (v1.0.123)

**文件：** [permission_rule.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/permissions/permission_rule.py#L26-L31)

- `_strip_redirects()` 函数自动剥离 `>`、`>>`、`<`、`|`、`2>`、`2>&1` 等重定向和管道符号
- `matches_redirect()` 方法：先剥离重定向再匹配，确保 `Bash(python:*)` 匹配 `python script.py > out`
- `:` 前缀模式匹配（如 `python:*` 表示任何 python 开头的命令）

**文件：** [permission_manager.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/permissions/permission_manager.py)
- 中央权限管理器，单例模式，支持从 YAML 配置加载
- `is_allowed()` 支持 `tool_name` + `command` + `raw_command` 三重参数

**文件：** [permissions.yaml](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/configs/permissions.yaml)
- YAML 驱动的规则配置，示例规则：
  ```yaml
  - tool_pattern: "Bash"
    action: "allow"
    command_pattern: "python:*"
  ```

### 3. 沙箱模式正式发布 (v2.0.24)

**文件：** [enhanced_sandbox.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/enhanced_sandbox.py)
- `SandboxResult` 改为标准 `@dataclass`，带默认值
- 添加 Windows 跨平台支持：`creationflags=0x08000000` (CREATE_NO_WINDOW)
- 添加 `allowed_command_patterns` 支持 fnmatch 通配符命令匹配
- `platform` 属性自动检测操作系统

**文件：** [sandbox/__init__.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/sandbox/__init__.py)
- 导出 `EnhancedSandbox`、`SandboxResult`、工厂函数 `create_mtc_sandbox()`、`create_code_sandbox()`

### 4. 受管设置支持 macOS plist/Windows 注册表 (v2.1.51)

**文件：** [managed_settings.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/enterprise/managed_settings.py)
- **macOS**: 从 `/Library/Preferences/com.alonechat.plist` 和 `~/Library/Preferences/` 读取 plist
- **Windows**: 从注册表 `HKLM\Software\com.alonechat` 和 `HKCU\Software\` 读取
- **回退**: YAML/JSON 文件 `/etc/com.alonechat/managed.yaml` 或 `~/.alonechat/managed.json`

### 5. 企业托管设置 (v2.0.68)

**文件：** [enterprise_manager.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/enterprise/enterprise_manager.py)
- `EnterprisePolicy` 数据类：允许/禁止命令列表、工具白名单、权限模式、并发会话数、审计日志、速率限制、允许的模型
- `EnterpriseManager` 单例：强制覆盖本地配置，支持命令/工具/模型白名单校验
- `get_merged_config()` 方法将企业策略合并到本地配置

### 6. OAuth 令牌存储在 macOS Keychain (v0.2.30)

**文件：** [credential_store.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/credentials/credential_store.py)
- **macOS**: 使用 `security` CLI 存储到系统钥匙串 (Keychain)
- **Windows**: 使用 PowerShell `Export-Clixml` 存储到 Credential Manager
- **Linux**: 使用 `secret-tool` 存储到 Secret Service (libsecret)
- **回退**: AES-256-GCM (Fernet) 加密文件存储，PBKDF2 密钥派生（480000 次迭代）

**文件：** [oauth_token_store.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/credentials/oauth_token_store.py)
- `OAuthToken` 数据类：access_token、refresh_token、过期时间、自动过期检查
- `save_token()` / `get_token()` / `delete_token()` / `save_api_key()` / `get_api_key()` 完整 API

### 更新了 `agent_framework/__init__.py`

所有新模块已导出，可通过 `from agent_framework import ...` 直接导入使用。

## User
`e:\AloneChat-workspace-master\docs\releases\RELEASE_NOTE_v0.2.0.md` 把你写的相关更改写到这个文件里面

## Assistant
现在我来更新发布说明文件，将 CLI 加强功能写入。

