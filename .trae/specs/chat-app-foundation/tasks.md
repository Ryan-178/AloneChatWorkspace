# Tasks

- [ ] Task 1: 项目初始化与数据库模型
  - [ ] 初始化 chat-app/backend FastAPI 项目（main.py、config.py、requirements.txt）
  - [ ] 初始化 chat-app/frontend Next.js 项目（含 Tailwind CSS、Shadcn/ui）
  - [ ] 配置 PostgreSQL 连接与 Alembic 迁移
  - [ ] 定义数据库模型：User、Message、Conversation、Group、GroupMember
  - [ ] 创建初始 Alembic 迁移脚本并执行
  - [ ] 创建 CHANGELOG.md 文件

- [ ] Task 2: 用户系统 - 注册与登录
  - [ ] 实现密码哈希（bcrypt）工具函数
  - [ ] 实现 JWT token 生成与验证中间件
  - [ ] 实现 POST /api/auth/register 端点
  - [ ] 实现 POST /api/auth/login 端点
  - [ ] 实现 GET /api/users/me 与 PATCH /api/users/me 端点
  - [ ] 实现 GET /api/users 用户搜索端点
  - [ ] 实现 GET /api/users/{id} 端点

- [ ] Task 3: WebSocket 实时通信
  - [ ] 配置 Redis 连接
  - [ ] 实现 WebSocket 连接管理器（ConnectionManager）
  - [ ] 实现 WebSocket /ws/{token} 端点（JWT 认证）
  - [ ] 实现 Redis Pub/Sub 消息分发机制
  - [ ] 实现在线状态通知（上线/离线广播）
  - [ ] 实现 WebSocket 心跳检测（ping/pong）

- [ ] Task 4: 消息系统与持久化
  - [ ] 实现消息业务服务（send_message、get_messages）
  - [ ] 实现 GET /api/conversations/{id}/messages 分页查询端点
  - [ ] 实现 GET /api/conversations 会话列表端点
  - [ ] 实现 POST /api/conversations 创建会话端点
  - [ ] 实现 GET /api/conversations/{id} 获取会话详情
  - [ ] WebSocket 消息处理集成（接收→验证→存储→广播）

- [ ] Task 5: 群组功能
  - [ ] 实现群组业务服务（create_group、add_member、remove_member）
  - [ ] 实现 POST /api/groups 创建群组端点
  - [ ] 实现 GET /api/groups 用户群组列表端点
  - [ ] 实现 GET /api/groups/{id} 群组详情端点
  - [ ] 实现 PATCH /api/groups/{id} 更新群组端点
  - [ ] 实现 POST /api/groups/{id}/members 添加成员端点
  - [ ] 实现 DELETE /api/groups/{id}/members/{user_id} 移除成员端点
  - [ ] 实现 GET /api/groups/{id}/messages 群消息分页查询端点
  - [ ] WebSocket 群消息广播逻辑

- [ ] Task 6: Next.js 前端基础与 UI
  - [ ] 实现基础布局组件（AppLayout、Sidebar）
  - [ ] 实现认证页面（登录、注册表单）
  - [ ] 实现 JWT token 管理（存储、刷新、拦截器）
  - [ ] 实现 WebSocket 客户端连接管理
  - [ ] 实现会话列表组件（ConversationList）
  - [ ] 实现消息列表组件（MessageList，含自动滚动）
  - [ ] 实现消息输入组件（MessageInput）
  - [ ] 实现群组管理界面（创建、成员列表）

- [ ] Task 7: 端到端联调与优化
  - [ ] 前后端 WebSocket 联调（消息收发、在线状态）
  - [ ] 前后端 REST API 联调（注册、登录、会话、群组）
  - [ ] 错误处理与边界情况测试
  - [ ] 响应式布局适配（移动端、平板、桌面）
  - [ ] 消息分页加载与上拉加载更多
  - [ ] 性能优化（虚拟滚动、消息去重）

# Task Dependencies
- Task 2 依赖 Task 1（需要数据库模型）
- Task 3 依赖 Task 1（需要项目基础设施）
- Task 4 依赖 Task 2（需要用户认证）和 Task 3（需要 WebSocket 基础设施）
- Task 5 依赖 Task 4（需要基础消息系统）
- Task 6 依赖 Task 2、Task 3、Task 4、Task 5（需要后端 API 就绪）
- Task 7 依赖 Task 6（需要前端 UI 就绪）
