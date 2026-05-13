# ChatAgent Phase 1: 聊天软件基础 Spec

## Why
构建 ChatAgent 项目的第一阶段：一个基于 Python FastAPI 后端 + Next.js 前端的实时聊天软件，为后续 Agent 框架集成提供通信基础设施。

## What Changes
- 初始化项目结构（chat-app/backend、chat-app/frontend）
- 实现用户系统：注册、登录、JWT 认证
- 实现 WebSocket 实时消息通信（一对一消息、在线状态）
- 实现 PostgreSQL 消息持久化存储
- 实现群组功能：群聊创建、成员管理
- 实现 Next.js 前端：布局、用户界面
- 实现聊天 UI：消息列表、消息输入框
- 端到端联调：完整聊天流程

## Impact
- Affected specs: 无（首次创建）
- Affected code: chat-app/backend/（FastAPI）、chat-app/frontend/（Next.js）
- 依赖：PostgreSQL、Redis

## ADDED Requirements

### Requirement: 项目初始化与数据库模型
系统 SHALL 初始化 FastAPI 后端项目和 Next.js 前端项目，并定义核心数据库模型。

#### Scenario: 项目结构就绪
- **WHEN** 开发者执行项目初始化
- **THEN** 生成 chat-app/backend/ 的 FastAPI 项目骨架（含 requirements.txt、main.py、数据库配置、Alembic 迁移）
- **AND** 生成 chat-app/frontend/ 的 Next.js 项目骨架（含 Tailwind CSS、Shadcn/ui 配置）
- **AND** 定义 User、Conversation、Message、Group 等数据库模型

### Requirement: 用户系统
系统 SHALL 提供用户注册、登录和 JWT 认证功能。

#### Scenario: 用户注册成功
- **WHEN** 用户提供有效的 email、password、display_name
- **THEN** 系统创建用户记录，密码经 bcrypt 哈希存储，返回 HTTP 201 及用户信息（不含密码）

#### Scenario: 用户注册 - 邮箱重复
- **WHEN** 用户使用已注册的 email 注册
- **THEN** 系统返回 HTTP 409 Conflict，错误信息包含 "Email already registered"

#### Scenario: 用户登录成功
- **WHEN** 用户提供正确的 email 和 password
- **THEN** 系统返回 HTTP 200，包含 access_token（JWT）和 token_type

#### Scenario: 用户登录 - 密码错误
- **WHEN** 用户提供错误的 password
- **THEN** 系统返回 HTTP 401 Unauthorized，错误信息包含 "Incorrect email or password"

#### Scenario: 受保护接口访问
- **WHEN** 请求未携带有效 JWT token
- **THEN** 系统返回 HTTP 401 Unauthorized

### Requirement: WebSocket 实时通信
系统 SHALL 通过 WebSocket 实现用户间的实时消息收发，并维护在线状态。

#### Scenario: 一对一消息发送
- **WHEN** 用户 A 通过 WebSocket 向用户 B 发送消息
- **THEN** 消息通过 Redis Pub/Sub 广播至用户 B 的 WebSocket 连接
- **AND** 消息异步持久化至 PostgreSQL

#### Scenario: 在线状态通知
- **WHEN** 用户上线（建立 WebSocket 连接）
- **THEN** 系统通过 Redis Pub/Sub 广播该用户在线状态变更
- **WHEN** 用户离线（断开 WebSocket 连接）
- **THEN** 系统广播该用户离线状态变更

#### Scenario: 离线消息拉取
- **WHEN** 用户上线后请求历史消息
- **THEN** 系统通过 REST API 返回该用户离线期间未收到的消息

### Requirement: 消息持久化
系统 SHALL 将聊天消息持久化存储至 PostgreSQL。

#### Scenario: 消息存储与查询
- **WHEN** 用户发送一条聊天消息
- **THEN** 系统将消息（含发送者ID、接收者ID/群组ID、内容、时间戳、消息类型）存入 messages 表
- **AND** 支持按对话/群组分页查询历史消息

#### Scenario: 消息分页查询
- **WHEN** 客户端请求 /api/conversations/{id}/messages?page=1&page_size=20
- **THEN** 系统返回按时间倒序排列的消息列表，含分页元数据（total、page、page_size、pages）

### Requirement: 群组功能
系统 SHALL 支持群聊的创建、成员管理和群消息收发。

#### Scenario: 创建群聊
- **WHEN** 用户创建一个群组（提供 name、可选 member_ids 列表）
- **THEN** 系统创建群组记录，创建者自动成为群主，成员关系存入 group_members 表

#### Scenario: 群成员管理
- **WHEN** 群主添加/移除成员
- **THEN** 系统更新 group_members 表
- **WHEN** 非群主尝试管理成员
- **THEN** 系统返回 HTTP 403 Forbidden

#### Scenario: 群消息发送
- **WHEN** 群成员发送群消息
- **THEN** 系统通过 Redis Pub/Sub 广播至所有在线群成员
- **AND** 消息异步持久化

### Requirement: 聊天前端界面
系统 SHALL 提供基于 Next.js + Tailwind CSS + Shadcn/ui 的聊天界面。

#### Scenario: 聊天界面布局
- **WHEN** 用户登录后进入聊天界面
- **THEN** 系统展示左侧会话列表 + 右侧聊天区域的经典布局
- **AND** 支持响应式布局（移动端全屏显示聊天区域）

#### Scenario: 消息列表展示
- **WHEN** 用户选中一个会话
- **THEN** 系统展示按时间排列的消息列表，区分发送者（左右对齐、不同颜色）
- **AND** 新消息到来时自动滚动至底部

#### Scenario: 消息输入与发送
- **WHEN** 用户在输入框输入消息并点击发送（或按 Enter）
- **THEN** 系统通过 WebSocket 发送消息，输入框清空
- **AND** 消息立即显示在消息列表中（乐观更新）

### Requirement: REST API 设计规范
系统 SHALL 遵循 RESTful API 设计原则，提供统一的接口规范。

#### Scenario: 资源型 URL 设计
- **WHEN** 系统定义 API 端点
- **THEN** 使用复数名词命名资源（如 /api/users、/api/conversations、/api/groups）
- **AND** HTTP 方法与操作语义一致（GET=查询、POST=创建、PUT=全量更新、PATCH=部分更新、DELETE=删除）

#### Scenario: 统一错误响应格式
- **WHEN** API 发生错误
- **THEN** 系统返回统一格式的错误响应：
```json
{
  "error": "ErrorCode",
  "message": "Human readable message",
  "details": {}
}
```
- **AND** HTTP 状态码正确反映错误类型（400/401/403/404/409/422/500）

#### Scenario: 统一分页响应格式
- **WHEN** 接口返回列表数据
- **THEN** 系统使用统一分页响应：
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

## API 端点设计

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/users/me | 获取当前用户信息 |
| PATCH | /api/users/me | 更新当前用户信息 |
| GET | /api/users | 获取用户列表（搜索） |
| GET | /api/users/{id} | 获取指定用户信息 |
| GET | /api/conversations | 获取当前用户的会话列表 |
| POST | /api/conversations | 创建一对一对话 |
| GET | /api/conversations/{id} | 获取会话详情 |
| GET | /api/conversations/{id}/messages | 获取会话历史消息（分页） |
| POST | /api/groups | 创建群组 |
| GET | /api/groups | 获取用户所在的群组列表 |
| GET | /api/groups/{id} | 获取群组详情 |
| PATCH | /api/groups/{id} | 更新群组信息 |
| POST | /api/groups/{id}/members | 添加群成员 |
| DELETE | /api/groups/{id}/members/{user_id} | 移除群成员 |
| GET | /api/groups/{id}/messages | 获取群组历史消息（分页） |
| WS | /ws/{token} | WebSocket 实时通信端点 |
