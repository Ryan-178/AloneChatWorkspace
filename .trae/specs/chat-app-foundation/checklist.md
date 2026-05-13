# Verification Checklist

## 项目初始化 (Task 1)
- [ ] chat-app/backend/ 目录存在，含 main.py、config.py、requirements.txt
- [ ] chat-app/frontend/ 目录存在，含 package.json（Next.js + Tailwind CSS + Shadcn/ui）
- [ ] 数据库模型定义完整（User、Message、Conversation、Group、GroupMember）
- [ ] Alembic 初始化并可成功执行迁移
- [ ] PostgreSQL 连接配置正确
- [ ] CHANGELOG.md 文件存在且格式正确

## 用户系统 (Task 2)
- [ ] POST /api/auth/register 返回 201 且密码经 bcrypt 哈希
- [ ] 重复 email 注册返回 409
- [ ] POST /api/auth/login 返回 JWT access_token
- [ ] 错误密码登录返回 401
- [ ] GET /api/users/me 正确返回当前用户信息（需 JWT）
- [ ] 无 JWT 访问受保护接口返回 401

## WebSocket 实时通信 (Task 3)
- [ ] WebSocket 连接可以通过 JWT token 认证
- [ ] 无效 token 的 WebSocket 连接被拒绝
- [ ] Redis Pub/Sub 消息发送与接收正常
- [ ] 用户上线时广播在线状态
- [ ] 用户离线时广播离线状态
- [ ] WebSocket 心跳检测正常（ping/pong）

## 消息系统 (Task 4)
- [ ] 一对一消息通过 WebSocket 实时送达
- [ ] 消息异步持久化至 PostgreSQL
- [ ] GET /api/conversations/{id}/messages 分页查询正确
- [ ] 分页响应格式符合统一规范（items、total、page、page_size、pages）
- [ ] GET /api/conversations 返回当前用户会话列表

## 群组功能 (Task 5)
- [ ] POST /api/groups 创建群组并返回群组信息
- [ ] 群主可以添加/移除群成员
- [ ] 非群主操作返回 403
- [ ] 群消息通过 WebSocket 广播至所有在线群成员
- [ ] GET /api/groups/{id}/messages 分页查询正确

## 前端界面 (Task 6)
- [ ] 登录/注册页面可正常使用
- [ ] JWT token 正确存储并在请求中携带
- [ ] WebSocket 客户端能正确连接和重连
- [ ] 会话列表展示正确
- [ ] 消息列表区分发送者（左右对齐）
- [ ] 新消息自动滚动至底部
- [ ] 消息输入框 Enter 键发送

## 兼容性与质量 (Task 7)
- [ ] 所有 API 错误响应格式统一（error、message、details）
- [ ] HTTP 状态码使用正确
- [ ] 响应式布局在 320px、768px、1024px、1440px 正常
- [ ] 无控制台错误（前端）
- [ ] 无未捕获异常（后端）
- [ ] 不包含任何模拟数据、假字段、假枚举

## UI/UX 质量
- [ ] 不使用 emoji 作为 UI 图标（使用 SVG 图标如 Lucide）
- [ ] 所有可点击元素有 cursor-pointer
- [ ] 悬停状态有视觉反馈
- [ ] 过渡动画流畅（150-300ms）
- [ ] 亮色模式下文字对比度 ≥ 4.5:1
- [ ] 暗色模式支持
- [ ] 焦点状态对键盘导航可见
