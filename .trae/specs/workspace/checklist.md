# Checklist

## Phase 1: VS Code Workspace 配置

- [x] ChatAgent.code-workspace 文件已创建，包含三个 folder 配置
- [x] launch.json 包含 Backend Dev、Frontend Dev、Python Tests、Attach to Backend、Full Stack Dev 配置
- [x] tasks.json 包含 Install All Dependencies、Backend Dev、Frontend Dev 任务
- [x] 推荐扩展列表完整（Python、Pylance、ESLint、Prettier、Docker、GitLens 等）
- [x] Makefile 已创建，包含 install、dev、test、lint、clean、db-init、help 目标
- [x] .gitignore 已更新，覆盖 Python、Node、IDE、环境文件、系统文件、日志和数据库文件
- [x] README.md 已创建，包含项目简介、目录结构、环境要求、快速开始、Makefile 速查表、架构图和许可证

## Phase 2: 聊天+Agent 融合工作区

- [x] agent_service.py 已创建，包含 get_or_create_agent_session 和 run_agent_task 函数
- [x] agent_service.py 已集成 LiteLLMProvider、ReActAgent、ToolRegistry
- [x] 工具 web_search、calculator、current_time 已注册
- [x] models.py 已新增 AgentSession 和 AgentMessage 模型
- [x] schemas.py 已新增 AgentSessionCreate、AgentSessionResponse、AgentMessageResponse、AgentRunRequest、AgentRunResponse、AgentSessionsListResponse
- [x] routers/agent.py 已创建，包含 POST /api/agent/sessions、GET /api/agent/sessions、GET /api/agent/sessions/{session_id}、DELETE /api/agent/sessions/{session_id}、POST /api/agent/sessions/{session_id}/run
- [x] main.py 已注册 agent router
- [x] websocket_manager.py 已支持检测 /agent 前缀消息
- [x] websocket_manager.py 已支持 agent_response 消息类型推送
- [x] agent-panel.tsx 已创建，包含会话列表和 AgentChat 嵌入
- [x] agent-chat.tsx 已创建，包含消息列表、输入框、加载状态
- [x] chat-layout.tsx 已新增 "Agent" 标签
- [x] api.ts 已新增 Agent API 方法
- [x] chat-area.tsx 已支持 @Agent 唤起浮层
- [x] chat-area.tsx 已支持 @Agent 高亮标记
- [x] websocket_manager.py 已支持 agent 类型消息处理
- [x] multi_agent_service.py 已创建，集成 MultiAgentTeam 和 AgentBus
- [x] websocket_manager.py 已支持 /multi-agent 和 @all-agents 指令
- [x] agent_service.py 已新增 run_agent_task_stream 异步生成器
- [x] websocket_manager.py 已支持逐事件推送流式消息
- [x] agent-chat.tsx 已支持流式渲染 Agent 响应
- [x] agent_service.py 已保存用户消息和 Agent 响应到 AgentMessage 表
- [x] agent_service.py 已加载最近 20 条历史消息作为 LLM 上下文

## Phase 3: 团队协作工作区（多租户）

- [x] models.py 已新增 Workspace 和 WorkspaceMember 模型
- [x] models.py 已修改 Conversation 和 Group 模型，新增 workspace_id 外键
- [x] schemas.py 已新增 WorkspaceCreate、WorkspaceResponse、WorkspaceMemberResponse、WorkspaceUpdate、WorkspaceInviteRequest、WorkspaceListResponse
- [x] routers/workspaces.py 已创建，包含工作区 CRUD 端点
- [x] routers/workspaces.py 已包含成员管理端点（邀请、移除、修改角色、列表）
- [x] routers/workspaces.py 已实现 owner/admin/member 权限控制
- [x] main.py 已注册 workspaces router
- [x] workspace-switcher.tsx 已创建，支持下拉选择和创建工作区
- [x] api.ts 已新增 Workspace API 方法
- [x] chat-layout.tsx 已嵌入 WorkspaceSwitcher
- [x] chat-layout.tsx 已支持工作区切换后刷新会话/群组列表
- [x] main.py 中的 conversations/groups 查询已增加 workspace_id 过滤
- [x] 未指定 workspace_id 时兼容旧数据
- [x] workspace-settings.tsx 已创建，包含基本信息和成员管理 Tab
- [x] workspace-settings.tsx 已支持邀请、移除、修改角色、离开工作区功能
