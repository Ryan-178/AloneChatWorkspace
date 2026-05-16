# Tasks

## Phase 1: VS Code Workspace 配置

- [x] Task 1.1: 创建 Workspace 配置文件
  - [x] 创建 `e:\alonechat-all\ChatAgent.code-workspace`，配置三个 folder、编辑器规则、launch configurations、tasks 和推荐扩展
- [x] Task 1.2: 创建 Makefile
  - [x] 创建 `e:\alonechat-all\Makefile`，包含 install、dev、test、lint、clean、db-init、help 目标
- [x] Task 1.3: 更新根目录 .gitignore
  - [x] 更新 `e:\alonechat-all\.gitignore`，覆盖 Python、Node、IDE、环境文件、系统文件、日志和数据库文件
- [x] Task 1.4: 创建 Workspace README
  - [x] 创建 `e:\alonechat-all\README.md`，包含项目简介、目录结构、环境要求、快速开始、Makefile 速查表、架构图和许可证

## Phase 2: 聊天+Agent 融合工作区

- [x] Task 2.1: 创建 Agent 服务层
  - [x] 新建 `e:\alonechat-all\chat-app\backend\agent_service.py`
  - [x] 实现 `get_or_create_agent_session(user_id, conversation_id)`
  - [x] 实现 `run_agent_task(session_id, user_message)`，集成 LiteLLMProvider、ReActAgent、ToolRegistry
  - [x] 注册工具：web_search、calculator、current_time
- [x] Task 2.2: 创建 Agent 会话数据库模型
  - [x] 更新 `e:\alonechat-all\chat-app\backend\models.py`，新增 AgentSession 和 AgentMessage 模型
  - [x] 更新 `e:\alonechat-all\chat-app\backend\schemas.py`，新增 Agent 相关 Pydantic Schema
- [x] Task 2.3: 创建 Agent 对话 REST API
  - [x] 新建 `e:\alonechat-all\chat-app\backend\routers\agent.py`，实现 CRUD 和 run 端点
  - [x] 更新 `e:\alonechat-all\chat-app\backend\main.py`，注册 agent router
- [x] Task 2.4: 扩展 WebSocket 协议支持 Agent
  - [x] 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`，检测 `/agent` 前缀消息并调用 agent_service
- [x] Task 2.5: 创建 Agent 前端 UI
  - [x] 新建 `e:\alonechat-all\chat-app\frontend\src\components\agent-panel.tsx`
  - [x] 新建 `e:\alonechat-all\chat-app\frontend\src\components\agent-chat.tsx`
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-layout.tsx`，新增 "Agent" 标签
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\lib\api.ts`，新增 Agent API 方法
- [x] Task 2.6: 支持 @Agent 唤起
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-area.tsx`，监听 `@` 并触发 Agent 选择浮层
  - [x] 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`，处理 agent 类型消息
- [x] Task 2.7: 多 Agent 团队协作
  - [x] 新建 `e:\alonechat-all\chat-app\backend\multi_agent_service.py`，集成 MultiAgentTeam 和 AgentBus
  - [x] 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`，检测 `/multi-agent` 或 `@all-agents` 指令
- [x] Task 2.8: 流式响应支持
  - [x] 更新 `e:\alonechat-all\chat-app\backend\agent_service.py`，新增 `run_agent_task_stream` 异步生成器
  - [x] 更新 `e:\alonechat-all\chat-app\backend\websocket_manager.py`，逐事件推送流式消息
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\components\agent-chat.tsx`，流式渲染 Agent 响应
- [x] Task 2.9: Agent 会话历史持久化
  - [x] 更新 `e:\alonechat-all\chat-app\backend\agent_service.py`，保存消息到 AgentMessage 表，加载最近 20 条历史

## Phase 3: 团队协作工作区（多租户）

- [x] Task 3.1: 工作区数据库模型
  - [x] 更新 `e:\alonechat-all\chat-app\backend\models.py`，新增 Workspace、WorkspaceMember 模型，修改 Conversation 和 Group
  - [x] 更新 `e:\alonechat-all\chat-app\backend\schemas.py`，新增 Workspace 相关 Pydantic Schema
- [x] Task 3.2: 工作区 REST API
  - [x] 新建 `e:\alonechat-all\chat-app\backend\routers\workspaces.py`，实现工作区 CRUD 和成员管理端点
  - [x] 更新 `e:\alonechat-all\chat-app\backend\main.py`，注册 workspaces router
- [x] Task 3.3: 工作区切换器前端
  - [x] 新建 `e:\alonechat-all\chat-app\frontend\src\components\workspace-switcher.tsx`
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\lib\api.ts`，新增 Workspace API 方法
  - [x] 更新 `e:\alonechat-all\chat-app\frontend\src\components\chat-layout.tsx`，嵌入 WorkspaceSwitcher
- [x] Task 3.4: 资源隔离查询改造
  - [x] 更新 `e:\alonechat-all\chat-app\backend\main.py` 中的 conversations/groups 查询，增加 workspace_id 过滤
- [x] Task 3.5: 成员管理界面
  - [x] 新建 `e:\alonechat-all\chat-app\frontend\src\components\workspace-settings.tsx`

# Task Dependencies

- Task 2.2 依赖 Task 2.1
- Task 2.3 依赖 Task 2.2
- Task 2.4 依赖 Task 2.1
- Task 2.5 依赖 Task 2.1、Task 2.3
- Task 2.6 依赖 Task 2.4、Task 2.5
- Task 2.7 依赖 Task 2.1
- Task 2.8 依赖 Task 2.4
- Task 2.9 依赖 Task 2.2
- Task 3.2 依赖 Task 3.1
- Task 3.3 依赖 Task 3.2
- Task 3.4 依赖 Task 3.1
- Task 3.5 依赖 Task 3.2
