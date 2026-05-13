# ChatAgent Workspace 整体规划

> **目标：** 在已完成的 chat-app（Phase 1）和 agent-framework（Phase 2）基础上，打造统一的开发工作区、聊天+Agent 融合工作区、以及团队协作工作区三大体系。

**架构：** 三层递进策略——先建立统一的开发环境配置，再实现 Agent 框架与聊天应用的深度集成（Phase 3 融合），最后引入组织级多租户工作区管理。

**技术栈：** VS Code multi-root workspace + FastAPI + Next.js + WebSocket + Redis Pub/Sub + PostgreSQL + LiteLLM + ChromaDB + SQLAlchemy

---

## 一、VS Code Workspace 配置

**目标：** 创建一个 multi-root workspace，将 `chat-app`（frontend + backend）和 `agent-framework` 整合到统一的开发环境中。

**架构：** 通过单一 `.code-workspace` 文件聚合三个子项目，配置共享的调试启动项、任务、代码检查规则和推荐的 VS Code 扩展。

---

### Task 1.1: 创建 Workspace 配置文件

**文件：** 创建 `e:\alonechat-all\ChatAgent.code-workspace`

**内容描述：**
- 配置三个 folder：chat-app-backend（指向 `chat-app/backend`）、chat-app-frontend（指向 `chat-app/frontend`）、agent-framework（指向 `agent-framework`）
- 设置编辑器全局规则：formatOnSave、Python 类型检查、TS/JSX 格式化器
- 配置五个 launch configuration：
  - Backend Dev Server（Python FastAPI uvicorn）
  - Frontend Dev Server（npm run dev）
  - Python Tests（pytest）
  - Attach to Backend（debugpy attach）
  - Full Stack Dev（compound，同时启动 backend + frontend）
- 配置 tasks.json 中的三个任务：Install All Dependencies（并行安装）、Backend Dev、Frontend Dev
- 列出推荐的 VS Code 扩展（Python、Pylance、ESLint、Prettier、Docker、GitLens 等 12 个）

---

### Task 1.2: 创建 Makefile

**文件：** 创建 `e:\alonechat-all\Makefile`

**内容描述：**
- `install`：并行执行 pip install + npm install
- `dev`：同时启动 backend uvicorn + frontend Next.js dev
- `test`：同时运行 pytest + npm test
- `lint`：同时运行 ruff check + npm run lint
- `clean`：清理 `__pycache__`、`.next`、`node_modules`、`venv`
- `db-init`：初始化 PostgreSQL 数据库
- `help`：列出所有可用命令

---

### Task 1.3: 更新根目录 .gitignore

**文件：** 更新 `e:\alonechat-all\.gitignore`

**内容描述：**
- Python 忽略：`__pycache__/`, `*.pyc`, `venv/`, `.pytest_cache/`, `.ruff_cache/`
- Node 忽略：`node_modules/`, `.next/`, `dist/`
- IDE 忽略：`.vscode/`, `*.swp`
- 环境文件：`.env`, `.env.local`, `*.env`
- 系统文件：`Thumbs.db`, `.DS_Store`
- 日志文件：`*.log`
- 数据库文件：`*.sqlite3`

---

### Task 1.4: 创建 Workspace README

**文件：** 创建 `e:\alonechat-all\README.md`

**内容描述：**
- 项目简介：ChatAgent 是一个集成了实时聊天和 AI Agent 的协作平台
- 目录结构说明（chat-app/backend、chat-app/frontend、agent-framework 三个子项目）
- 环境要求：Python 3.11+、Node.js 18+、PostgreSQL 16+、Redis 7+
- 快速开始步骤（克隆 → 创建虚拟环境 → 安装依赖 → 配置环境变量 → 初始化数据库 → 启动开发服务器）
- Makefile 命令速查表
- 项目架构图（Mermaid）
- 许可证信息

---

## 二、聊天+Agent 融合工作区（Phase 3）

**目标：** 打通 chat-app 和 agent-framework，让用户能在聊天界面中直接调用 AI Agent，支持单 Agent 对话、多 Agent 协作、流式响应和历史会话管理。

**架构：** 在 chat-app backend 中新增 `agent_service.py` 作为桥梁层，通过 LiteLLM provider 调用大模型，通过 ReAct agent 执行推理，通过 WebSocket 扩展协议推送 Agent 响应。前端新增 Agent 专属 UI 组件，并在聊天输入框中支持 `@Agent` 触发。

---

### Task 2.1: 创建 Agent 服务层

**文件：** 新建 `e:\alonechat-all\chat-app\backend\agent_service.py`

**实现内容：**
- `get_or_create_agent_session(user_id, conversation_id)`：获取或创建 Agent 会话，返回 session_id
- `run_agent_task(session_id, user_message)`：执行 Agent 任务
  - 加载会话历史 + 新建 Chroma 集合用于 RAG
  - 构建 LLM 消息列表（system prompt + 历史 + 当前消息）
  - 实例化 LiteLLMProvider + ReActAgent + ToolRegistry
  - 运行 agent.run() 获取最终响应
  - 将用户消息和 Agent 响应保存到数据库
  - 返回 Agent 响应文本
- 工具注册：`web_search`（通过 WebSearch）、`calculator`（简单算术）、`current_time`（获取当前时间）

**依赖：** agent-framework 的 `LiteLLMProvider`、`ReActAgent`、`ToolRegistry`、`ChromaMemory`

---

### Task 2.2: 创建 Agent 会话数据库模型

**文件：** 更新 `e:\alonechat-all\chat-app\backend\models.py`

**新增模型：**
- `AgentSession`：id（UUID PK）、user_id（FK→users）、conversation_id（FK→conversations，nullable）、title、status（active/archived）、created_at、updated_at
- `AgentMessage`：id（UUID PK）、session_id（FK→agent_sessions）、role（user/agent）、content、tool_calls（JSON，nullable）、tool_results（JSON，nullable）、metadata（JSON，nullable）、created_at

**文件：** 更新 `e:\alonechat-all\chat-app\backend\schemas.py`

**新增 Schema：**
- `AgentSessionCreate`、`AgentSessionResponse`（含消息列表）
- `AgentMessageResponse`
- `AgentRunRequest`（session_id + message）、`AgentRunResponse`
- `AgentSessionsListResponse`

---

### Task 2.3: 创建 Agent 对话 REST API

**文件：** 新建 `e:\alonechat-all\chat-app\backend\routers\agent.py`

**端点：**
- `POST /api/agent/sessions`：创建新会话（body: conversation_id + title）
- `GET /api/agent/sessions`：获取当前用户的会话列表
- `GET /api/agent/sessions/{session_id}`：获取会话详情（含消息历史）
- `DELETE /api/agent/sessions/{session_id}`：删除会话
- `POST /api/agent/sessions/{session_id}/run`：向 Agent 发送消息并获取响应

**文件：** 更新 `e:\alonechat-all\chat-app\backend\main.py`
- 注册 `routers/agent.py` 的 router

---

### Task 2.4: 扩展 WebSocket 协议支持 Agent

**文件：** 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`

**改动：**
- 在消息分发循环中，检测以 `/agent` 开头的消息
- 调用 `agent_service.run_agent_task()` 执行 Agent
- 通过 `agent_response` 消息类型推送结果到前端（payload 结构：sender_id = `__agent__`、content、session_id、conversation_id）

---

### Task 2.5: 创建 Agent 前端 UI

**文件：** 新建 `e:\alonechat-all\chat-app\frontend\src\components\agent-panel.tsx`
**文件：** 新建 `e:\alonechat-all\chat-app\frontend\src\components\agent-chat.tsx`

**组件设计：**
- `AgentPanel`：Agent 主面板
  - 左侧会话列表（显示所有 Agent 会话，支持新建/切换/删除）
  - 右侧为主体区域（嵌入 `AgentChat`）
  - 响应式布局（移动端用 Tabs 切换）
- `AgentChat`：单个 Agent 会话的聊天界面
  - 消息列表（用户消息 + Agent 响应，Agent 消息带 Bot 图标 + 特殊样式）
  - 底部输入框 + 发送按钮
  - 加载状态（thinking 动画）
  - 通过 REST API 获取/发送消息

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-layout.tsx`
- 在标签栏中新增 "Agent" 标签
- 选中时渲染 `AgentPanel` 组件

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\lib\api.ts`
- 新增 Agent API 方法：`createAgentSession`、`getAgentSessions`、`getAgentSession`、`deleteAgentSession`、`runAgentTask`

---

### Task 2.6: 支持 @Agent 唤起

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-area.tsx`

**改动：**
- 在聊天输入框中监听 `@` 字符输入，弹出 Agent 选择浮层
- 用户选择 Agent 后，输入框显示 `@Agent ` 高亮标记
- 发送消息时，若包含 `@Agent` 前缀，WebSocket 消息自动转为 agent 类型
- 在消息列表中渲染 Agent 响应用特殊样式（Bot 图标 + 绿色调）

**文件：** 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`
- 在处理 `agent` 类型消息时执行 `run_agent_task`，返回 `agent_response` 类型消息

---

### Task 2.7: 多 Agent 团队协作

**文件：** 新建 `e:\alonechat-all\chat-app\backend\multi_agent_service.py`

**实现内容：**
- `run_multi_agent_team(session_id, user_message, agent_ids)`：
  - 从传入的 agent_ids 列表实例化多个 Agent
  - 使用 agent-framework 的 `MultiAgentTeam` + `AgentBus` 编排协作
  - 协调多个 Agent 依次推理、共享上下文
  - 汇总所有 Agent 的最终响应
  - 返回到 WebSocket 的消息流

**文件：** 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`
- 群组聊天消息检测如果包含 `/multi-agent` 指令或 `@all-agents`，触发多 Agent 协作模式

---

### Task 2.8: 流式响应支持

**文件：** 更新 `e:\alonechat-all\chat-app\backend\agent_service.py`

**改动：**
- 新增 `run_agent_task_stream(session_id, user_message)` 异步生成器
- 事件类型：
  - `thinking`：Agent 开始思考
  - `tool_call`：Agent 调用工具（含工具名和参数）
  - `tool_result`：工具返回结果
  - `final`：最终响应文本

**文件：** 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`
- 通过 WebSocket 逐事件推送流式消息（event 字段区分事件类型）
- 前端根据 event 类型分别渲染（thinking 用动画、tool_call 用卡片、final 用文本）

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\components\agent-chat.tsx`
- 流式渲染：逐步追加 final 文本，tool_call/tool_result 显示为可折叠卡片
- 使用 WebSocket 的流式消息通道接收事件

---

### Task 2.9: Agent 会话历史持久化

**文件：** 更新 `e:\alonechat-all\chat-app\backend\agent_service.py`

**改动：**
- 每次 `run_agent_task` 完成后，将用户消息和 Agent 响应保存到 `AgentMessage` 表
- 会话初始化时从 DB 加载最近 20 条消息作为 LLM 的历史上下文
- 支持用户手动归档/删除 Agent 会话
- 用户消息和 Agent 消息分别存储（role 字段区分）

---

## 三、团队协作工作区（多租户）

**目标：** 引入组织级工作区（Workspace）概念，实现多租户隔离、成员角色管理和跨项目资源绑定。

**架构：** 新增 `workspaces` 和 `workspace_members` 表，在已有的 `Conversation` 和 `Group` 上添加 `workspace_id` 外键。前端新增工作区切换器和成员管理界面。

---

### Task 3.1: 工作区数据库模型

**文件：** 更新 `e:\alonechat-all\chat-app\backend\models.py`

**新增模型：**
- `Workspace`：id（UUID PK）、name、description、owner_id（FK→users）、created_at、updated_at
- `WorkspaceMember`：id（UUID PK）、workspace_id（FK→workspaces）、user_id（FK→users）、role（enum: owner/admin/member）、invited_by（FK→users，nullable）、created_at

**修改模型：**
- `Conversation`：新增 `workspace_id`（FK→workspaces，nullable）
- `Group`：新增 `workspace_id`（FK→workspaces，nullable）

**文件：** 更新 `e:\alonechat-all\chat-app\backend\schemas.py`

**新增 Schema：**
- `WorkspaceCreate`、`WorkspaceResponse`（含成员列表）
- `WorkspaceMemberResponse`
- `WorkspaceUpdate`（name/description）
- `WorkspaceInviteRequest`（email + role）
- `WorkspaceListResponse`

---

### Task 3.2: 工作区 REST API

**文件：** 新建 `e:\alonechat-all\chat-app\backend\routers\workspaces.py`

**端点：**
- `POST /api/workspaces`：创建工作区（当前用户自动成为 owner）
- `GET /api/workspaces`：获取当前用户所属工作区列表
- `GET /api/workspaces/{workspace_id}`：获取工作区详情
- `PUT /api/workspaces/{workspace_id}`：更新工作区信息（owner/admin 权限）
- `DELETE /api/workspaces/{workspace_id}`：删除工作区（仅 owner）

**成员管理端点：**
- `POST /api/workspaces/{workspace_id}/members`：邀请成员（body: email + role）
- `DELETE /api/workspaces/{workspace_id}/members/{user_id}`：移除成员
- `PUT /api/workspaces/{workspace_id}/members/{user_id}`：修改成员角色
- `GET /api/workspaces/{workspace_id}/members`：获取成员列表

**权限逻辑：**
- owner：完全控制（删除工作区、修改所有角色、移除成员）
- admin：管理成员（邀请/移除普通 member、修改 member 角色）、更新工作区信息
- member：查看工作区信息、查看成员列表

**文件：** 更新 `e:\alonechat-all\chat-app\backend\main.py`
- 注册 `routers/workspaces.py` 的 router

---

### Task 3.3: 工作区切换器前端

**文件：** 新建 `e:\alonechat-all\chat-app\frontend\src\components\workspace-switcher.tsx`

**组件设计：**
- 顶部下拉选择器，显示当前工作区名称
- 下拉列表列出用户所有工作区（带 icon）
- 底部 "创建工作区" 按钮 → 弹出 Modal（输入 name + description）
- 选中工作区后全局切换，更新 localStorage 中的 currentWorkspaceId

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\lib\api.ts`
- 新增 API 方法：`getWorkspaces`、`createWorkspace`、`getWorkspace`、`updateWorkspace`、`deleteWorkspace`
- 新增成员管理 API：`inviteMember`、`removeMember`、`updateMemberRole`、`getMembers`

**文件：** 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-layout.tsx`
- 顶部导航栏左侧嵌入 `WorkspaceSwitcher` 组件
- 当前工作区切换后，自动刷新会话/群组列表（带上 workspace_id 参数）

---

### Task 3.4: 资源隔离查询改造

**文件：** 更新 `e:\alonechat-all\chat-app\backend\routers\conversations.py`（或对应路由文件）

**改动：**
- 列表查询接口增加可选的 `workspace_id` 查询参数
- 创建会话/群组时，如果请求中携带了 `workspace_id`，则写入该字段
- 查询时按 `workspace_id` 过滤（前端从 WorkspaceSwitcher 获取当前工作区 ID）
- 未指定 workspace_id 时兼容旧数据（返回所有或仅返回 workspace_id IS NULL 的记录）

---

### Task 3.5: 成员管理界面

**文件：** 新建 `e:\alonechat-all\chat-app\frontend\src\components\workspace-settings.tsx`

**组件设计：**
- 可切换的 Modal/Drawer，入口在 WorkspaceSwitcher dropdown 中的 "工作区设置"
- Tab 1 - 基本信息：显示/编辑工作区名称和描述
- Tab 2 - 成员管理：
  - 成员列表（头像 + 显示名 + 邮箱 + 角色 badge）
  - owner 显示皇冠 icon，admin 显示盾牌 icon，member 显示用户 icon
  - 邀请成员：输入邮箱 + 选择角色 → 发送邀请
  - 移除成员：hover 时显示删除按钮（仅 owner/admin 可操作）
  - 修改角色：下拉选择器（仅 owner/admin 可操作）
  - 离开工作区按钮（普通成员）

---

## 执行计划总览

| 阶段 | 任务 | 预计工作量 | 依赖 |
|------|------|-----------|------|
| **一、开发环境** | Task 1.1-1.4 Workspace 配置 | ~30分钟 | 无 |
| **二、融合集成** | Task 2.1 Agent 服务层 | ~1小时 | Phase 2 完成 |
| | Task 2.2 Agent 会话模型 | ~30分钟 | Task 2.1 |
| | Task 2.3 Agent REST API | ~30分钟 | Task 2.2 |
| | Task 2.4 WebSocket 协议扩展 | ~30分钟 | Task 2.1 |
| | Task 2.5 Agent UI 组件 | ~1.5小时 | Task 2.1-2.3 |
| | Task 2.6 @Agent 调用 | ~1小时 | Task 2.4, 2.5 |
| | Task 2.7 多 Agent 协作 | ~1小时 | Task 2.1 |
| | Task 2.8 流式响应 | ~1小时 | Task 2.4 |
| | Task 2.9 历史持久化 | ~30分钟 | Task 2.2 |
| **三、团队协作** | Task 3.1 工作区 DB 模型 | ~30分钟 | 无 |
| | Task 3.2 工作区 REST API | ~1小时 | Task 3.1 |
| | Task 3.3 工作区切换器 UI | ~1小时 | Task 3.2 |
| | Task 3.4 资源隔离查询改造 | ~30分钟 | Task 3.1 |
| | Task 3.5 成员管理 UI | ~1小时 | Task 3.2 |
| **总计** | **18 个任务** | **~13 小时** | — |

> **建议执行顺序：** 按阶段顺序执行（一 → 二 → 三），阶段内任务按编号顺序执行。每个任务完成后运行对应的测试确保质量。

---

*文档版本：v1.1*
*最后更新：2026-05-10*
