# Agent框架与聊天软件：B/C/D三端调研 + 生产级Agent网关

## 概述

- **Summary**：深度调研B/C/D三端主流Agent框架，参考OpenClaw（龙虾）架构，从零构建生产级Agent运行时网关系统
- **Purpose**：打造7×24小时稳定运行、支持大规模并发、全渠道接入的Agent网关，像龙虾一样冲量！
- **Target Users**：企业用户、开发者、终端用户

## 目标

1. 完成B/C/D三端框架深度调研分析
2. 设计并实现5层架构的生产级Agent网关
3. 实现Gateway核心、分层记忆、技能系统、多Agent协作
4. 与现有聊天应用深度集成，消息即任务
5. 7×24小时稳定运行，支持大规模并发

## 非目标

- 不做轻量级框架，我们要生产级、可扩展、高性能
- 不依赖任何现有Agent框架（LangChain/CrewAI/AutoGen等）
- 不仅做聊天机器人，要做真正能执行任务的Agent系统

## 背景与上下文

**调研发现**：
- OpenClaw（龙虾）是2026年最成功的Agent框架，34万+ GitHub Stars
- 核心成功要素：Gateway网关架构、分层记忆、本地优先、技能插件化
- 生产级特性从第一天就要考虑，不是事后加

**项目现状**：
- 已有聊天应用基础
- 有初步的agent-framework模块
- 现在要重构升级为生产级Agent网关

## 功能需求

### FR-1: Gateway核心系统
- 常驻WebSocket服务（默认端口: 18789）
- 会话管理与车道隔离
- 配置热加载
- 健康监控与告警

### FR-2: 分层记忆系统
- 瞬时记忆：当前对话上下文
- 短期记忆：最近几小时任务状态
- 长期记忆：向量化历史经验
- 程序性记忆：固化技能流程

### FR-3: Agent执行系统
- ReAct推理循环
- 工具调用与沙箱执行
- 流式输出
- 多Agent协作编排

### FR-4: 技能插件系统
- 热插拔技能注册
- 技能间协作
- 技能市场基础

### FR-5: 全渠道接入
- 聊天应用原生集成
- WebSocket API
- 可扩展通道适配器

## 非功能需求

### NFR-1: 性能
- 支持1000+ 并发会话
- Gateway延迟 < 50ms（不含LLM调用）
- 7×24小时无故障运行

### NFR-2: 可扩展性
- 插件化架构，核心与扩展分离
- 支持分布式部署
- 多租户能力基础

### NFR-3: 可观测性
- 结构化日志（trace_id贯穿）
- 指标采集（QPS、延迟、错误率）
- 链路追踪（OpenTelemetry）

### NFR-4: 安全
- 工具沙箱执行
- RBAC权限控制
- 高危操作二次确认（有界涌现）
- 审计日志

## 约束

- 技术栈：Python 3.11+, FastAPI, Redis, SQLite/PostgreSQL
- 不依赖任何现有Agent框架（LangChain/CrewAI/AutoGen等）
- 只使用LiteLLM等基础工具库
- 与现有聊天应用架构兼容

## 假设

- LiteLLM继续稳定维护
- 现有聊天应用可与Gateway通过WebSocket集成
- Redis和PostgreSQL已有部署基础

## 验收标准

### AC-1: Gateway核心可用
- **Given**：Gateway配置完成
- **When**：启动Gateway服务
- **Then**：WebSocket连接成功，健康检查端点返回200，会话创建成功
- **Verification**：programmatic + human-judgment

### AC-2: 分层记忆工作
- **Given**：有历史对话记录
- **When**：Agent执行新任务
- **Then**：能正确检索瞬时、短期、长期记忆
- **Verification**：programmatic

### AC-3: ReAct Agent正常工作
- **Given**：Agent有工具可用
- **When**：用户发送任务
- **Then**：Agent能完成思考→工具调用→观察→回答循环
- **Verification**：programmatic

### AC-4: 与聊天应用集成
- **Given**：Gateway与聊天应用连接
- **When**：用户在聊天中发消息
- **Then**：消息自动转为Agent任务，结果流式返回
- **Verification**：programmatic + human-judgment

## 开放问题

- [ ] 技能系统的具体格式定义
- [ ] 多Agent协作的具体调度策略
- [ ] 是否需要支持多模型路由策略
