# TRAE SOLO MTC/CODE 模式完整实现 Spec

## Why
实现 TRAE SOLO 的 MTC (More Than Coding) 和 CODE 双模式系统，为不同类型的用户提供专门优化的 AI 工作模式。MTC 模式面向非开发用户，支持文档处理、数据分析、信息调研等通用办公任务；CODE 模式面向开发者，提供代码生成、调试、重构等专业开发能力。两种模式运行在隔离的沙箱环境中，确保安全性和稳定性。

## What Changes
- 在 `agent_framework/core/types.py` 中添加 AgentMode 枚举（MTC, CODE）和模式相关类型定义
- 在 `agent_framework/config.py` 中添加 ModeSettings 配置类
- 创建 `agent_framework/agent/mtc_agent.py` - MTC 模式 Agent 实现
- 创建 `agent_framework/agent/code_agent.py` - CODE 模式 Agent 实现
- 创建 `agent_framework/agent/mtc_prompts.py` - MTC 模式专用提示词
- 创建 `agent_framework/agent/code_prompts.py` - CODE 模式专用提示词
- 创建 `agent_framework/tools/mtc/` 目录 - MTC 专用工具集（文档、数据、调研、文件）
- 创建 `agent_framework/tools/code/` 目录 - CODE 专用工具集（代码生成、调试、重构）
- 增强 `agent_framework/sandbox/subprocess_sandbox.py` - 项目文件夹隔离和权限控制
- 创建 `agent_framework/agent/task_planner.py` - 任务规划器
- 创建 `agent_framework/agent/intent_clarifier.py` - 意图澄清系统
- 创建 `agent_framework/core/task.py` - Task 数据模型
- 创建 `agent_framework/skills/` 目录 - Skills 体系（文档生成、数据分析、网络调研、PPT 生成、报告生成）
- 创建 `agent_framework/tools/skills_registry.py` - Skills 注册系统
- 创建 `agent_framework/tools/skills_marketplace.py` - Skills 市场接口
- 修改 `agent_framework/gateway/router.py` - 添加模式路由逻辑
- 修改 `agent_framework/gateway/types.py` - 添加任务面板相关类型
- 创建 `agent_framework/gateway/api.py` - REST API（模式切换、任务管理、Skills 管理）
- 创建 `agent_framework/gateway/websocket.py` - WebSocket 流式输出
- 创建完整的测试套件 `tests/test_mtc_mode.py` 和 `tests/test_code_mode.py`

## Impact
- Affected specs: 依赖 `agent-framework-core`（Agent 框架核心）
- Affected code: `agent-framework/agent_framework/`（核心框架代码）
- **新增功能**：双模式系统、Skills 体系、意图澄清、任务规划、沙箱增强
- **向后兼容**：现有 Agent 框架核心功能保持不变，MTC/CODE 模式作为扩展

## ADDED Requirements

### Requirement: 模式管理系统
系统 SHALL 提供双模式（MTC 和 CODE）管理能力，支持模式定义、配置和切换。

#### Scenario: 模式枚举定义
- **WHEN** 系统初始化
- **THEN** AgentMode 枚举包含 MTC 和 CODE 两个值
- **AND** 每个模式有对应的 ModeConfig 配置类
- **AND** ModeConfig 包含 allowed_tools、sandbox_config、system_prompt 等字段

#### Scenario: 模式配置加载
- **WHEN** 应用程序启动
- **THEN** 从配置文件或环境变量加载模式配置
- **AND** 每个模式有独立的工具白名单和沙箱配置
- **AND** MTC 模式限制为安全工具，CODE 模式允许开发工具

#### Scenario: 模式切换
- **WHEN** 用户请求切换模式（从 MTC 到 CODE 或反之）
- **THEN** 系统验证切换权限
- **AND** 创建新模式的 Agent 实例
- **AND** 保留当前会话上下文
- **AND** 返回模式切换成功响应

### Requirement: MTC 模式 Agent
系统 SHALL 提供 MTC (More Than Coding) 模式 Agent，面向非开发用户。

#### Scenario: MTC Agent 初始化
- **WHEN** 创建 MTC 模式 Agent
- **THEN** Agent 使用 MTC 专用 system prompt（强调文档处理、数据分析、信息调研能力）
- **AND** Agent 加载 MTC 专用工具集（文档、数据、调研、文件操作）
- **AND** Agent 配置沙箱环境，限制在项目文件夹内操作
- **AND** Agent 启用意图澄清机制

#### Scenario: MTC 意图澄清
- **WHEN** MTC Agent 接收到模糊或复杂的用户请求
- **THEN** Agent 分析请求意图
- **AND** 如果需要澄清，生成追问表单（最多 3 个问题）
- **AND** 收集用户回答后整合为完整需求
- **AND** 基于澄清后的需求执行任务

#### Scenario: MTC 任务规划
- **WHEN** MTC Agent 接收到复杂任务
- **THEN** Agent 将任务分解为子任务列表
- **AND** 识别子任务间的依赖关系
- **AND** 按依赖顺序执行子任务
- **AND** 实时更新任务进度到任务面板

#### Scenario: MTC 输出格式
- **WHEN** MTC Agent 完成任务
- **THEN** 输出支持多种格式（Markdown、PDF、PPT、Excel、Word）
- **AND** 输出包含结构化的产出物列表
- **AND** 输出包含引用来源和参考链接

### Requirement: CODE 模式 Agent
系统 SHALL 提供 CODE 模式 Agent，面向开发者用户。

#### Scenario: CODE Agent 初始化
- **WHEN** 创建 CODE 模式 Agent
- **THEN** Agent 使用 CODE 专用 system prompt（强调代码生成、调试、重构能力）
- **AND** Agent 加载 CODE 专用工具集（代码生成、调试、重构、测试）
- **AND** Agent 配置沙箱环境，允许代码执行和文件修改
- **AND** Agent 启用代码上下文理解

#### Scenario: CODE 代码生成
- **WHEN** CODE Agent 接收到代码生成请求
- **THEN** Agent 分析需求并生成符合最佳实践的代码
- **AND** 代码包含完整的注释和文档
- **AND** 代码通过静态检查（lint、type check）
- **AND** 提供代码使用示例

#### Scenario: CODE 调试支持
- **WHEN** CODE Agent 接收到调试请求
- **THEN** Agent 分析错误信息和代码上下文
- **AND** 识别问题根因
- **AND** 提供修复建议和修复代码
- **AND** 解释修复原理

#### Scenario: CODE 重构能力
- **WHEN** CODE Agent 接收到重构请求
- **THEN** Agent 分析代码结构
- **AND** 提供重构方案（保持行为不变）
- **AND** 生成重构后的代码
- **AND** 提供重构前后对比

### Requirement: 沙箱环境增强
系统 SHALL 提供增强的沙箱环境，支持项目文件夹隔离和权限控制。

#### Scenario: 项目文件夹隔离
- **WHEN** Agent 在沙箱中执行操作
- **THEN** 操作限制在配置的项目文件夹内
- **AND** 禁止访问项目文件夹外的路径
- **AND** 文件路径经过安全验证（防止路径遍历攻击）

#### Scenario: 文件权限控制
- **WHEN** Agent 执行文件操作
- **THEN** 根据 FilePermission 枚举验证权限（READ、WRITE、EXECUTE）
- **AND** MTC 模式默认只允许 READ 和受限 WRITE
- **AND** CODE 模式允许 READ、WRITE 和受限 EXECUTE

#### Scenario: 命令白名单
- **WHEN** Agent 执行系统命令
- **THEN** 命令必须在配置的白名单内
- **AND** MTC 模式白名单：文档处理、数据分析相关命令
- **AND** CODE 模式白名单：开发工具相关命令（git、npm、pip 等）
- **AND** 禁止执行的命令返回 PermissionError

#### Scenario: 沙箱超时和资源限制
- **WHEN** 沙箱执行操作
- **THEN** 设置执行超时（默认 30 秒）
- **AND** 设置内存限制（默认 512MB）
- **AND** 超时或超限自动终止并返回错误

### Requirement: MTC Skills 体系
系统 SHALL 提供 Skills 体系，封装常用工作流为可复用的技能。

#### Scenario: Skills 注册
- **WHEN** 系统启动或用户安装新 Skill
- **THEN** Skill 注册到 SkillsRegistry
- **AND** 注册信息包含 name、description、version、author、dependencies
- **AND** 验证 Skill 的依赖是否满足

#### Scenario: 内置 MTC Skills
- **WHEN** MTC 模式初始化
- **THEN** 以下内置 Skills 可用：
  - `document_generation`: 文档生成（支持多种格式）
  - `data_analysis`: 数据分析（统计、可视化）
  - `web_research`: 网络调研（搜索、摘要）
  - `ppt_generation`: PPT 生成
  - `report_generation`: 报告生成
- **AND** 每个 Skill 包含 workflow、tools、templates

#### Scenario: Skills 执行
- **WHEN** 用户调用 Skill
- **THEN** 加载 Skill 的 workflow 定义
- **AND** 按工作流步骤执行
- **AND** 实时输出执行进度
- **AND** 返回最终产出物

#### Scenario: Skills 市场
- **WHEN** 用户访问 Skills 市场
- **THEN** 列出所有可用 Skills（内置 + 已安装）
- **AND** 支持搜索、过滤、排序
- **AND** 支持查看 Skill 详情和评价
- **AND** 支持安装/卸载 Skills

### Requirement: 任务管理系统
系统 SHALL 提供任务管理能力，支持任务规划、进度追踪和产出物管理。

#### Scenario: 任务分解
- **WHEN** Agent 接收到复杂任务
- **THEN** TaskPlanner 将任务分解为子任务列表
- **AND** 每个子任务包含 id、description、status、dependencies
- **AND** 识别任务间的依赖关系（DAG 结构）

#### Scenario: 任务执行与进度追踪
- **WHEN** 执行任务列表
- **THEN** 按依赖顺序执行子任务
- **AND** 实时更新子任务状态（pending、in_progress、completed、failed）
- **AND** 通过 WebSocket 推送进度更新
- **AND** 记录每个子任务的开始时间、结束时间、耗时

#### Scenario: 产出物管理
- **WHEN** 任务完成
- **THEN** 收集所有产出物（文件、数据、报告等）
- **AND** 产出物包含 name、type、path、size、created_at
- **AND** 支持产出物预览和下载
- **AND** 支持产出物引用和溯源

### Requirement: REST API 接口
系统 SHALL 提供 REST API 接口，支持模式管理、任务管理和 Skills 管理。

#### Scenario: 模式管理 API
- **WHEN** 调用 `/api/mode` 接口
- **THEN** 支持 GET 获取当前模式
- **AND** 支持 POST 切换模式
- **AND** 返回模式配置信息

#### Scenario: 任务管理 API
- **WHEN** 调用 `/api/tasks` 接口
- **THEN** 支持 GET 获取任务列表和状态
- **AND** 支持 POST 创建新任务
- **AND** 支持 GET `/api/tasks/{id}` 获取任务详情
- **AND** 支持 DELETE `/api/tasks/{id}` 取消任务

#### Scenario: Skills 管理 API
- **WHEN** 调用 `/api/skills` 接口
- **THEN** 支持 GET 列出所有 Skills
- **AND** 支持 POST `/api/skills/{name}/execute` 执行 Skill
- **AND** 支持 GET `/api/skills/{name}` 获取 Skill 详情

#### Scenario: 产出物管理 API
- **WHEN** 调用 `/api/artifacts` 接口
- **THEN** 支持 GET 列出产出物
- **AND** 支持 GET `/api/artifacts/{id}` 获取产出物详情
- **AND** 支持 GET `/api/artifacts/{id}/download` 下载产出物

### Requirement: WebSocket 流式输出
系统 SHALL 提供 WebSocket 接口，支持实时流式输出。

#### Scenario: 任务进度推送
- **WHEN** 任务执行中
- **THEN** 通过 WebSocket 推送进度更新事件
- **AND** 事件包含 task_id、status、progress、message
- **AND** 支持订阅特定任务的进度

#### Scenario: Agent 思考过程推送
- **WHEN** Agent 在 ReAct 循环中
- **THEN** 通过 WebSocket 推送思考过程事件
- **AND** 事件包含 type（think/act/observe）、content、timestamp
- **AND** 支持订阅 Agent 的思考流

#### Scenario: 产出物更新推送
- **WHEN** 产出物生成或更新
- **THEN** 通过 WebSocket 推送产出物更新事件
- **AND** 事件包含 artifact_id、action（create/update）、metadata

### Requirement: 测试覆盖
系统 SHALL 提供完整的测试覆盖，确保功能正确性和稳定性。

#### Scenario: MTC 模式测试
- **WHEN** 运行 MTC 模式测试
- **THEN** 测试 MTC Agent 初始化
- **AND** 测试意图澄清功能
- **AND** 测试任务规划功能
- **AND** 测试 MTC 工具调用
- **AND** 测试输出格式生成

#### Scenario: CODE 模式测试
- **WHEN** 运行 CODE 模式测试
- **THEN** 测试 CODE Agent 初始化
- **AND** 测试代码生成功能
- **AND** 测试调试支持功能
- **AND** 测试重构能力
- **AND** 测试 CODE 工具调用

#### Scenario: 沙箱安全测试
- **WHEN** 运行沙箱安全测试
- **THEN** 测试项目文件夹隔离
- **AND** 测试文件权限控制
- **AND** 测试命令白名单
- **AND** 测试超时和资源限制

#### Scenario: API 接口测试
- **WHEN** 运行 API 接口测试
- **THEN** 测试所有 REST API 端点
- **AND** 测试 WebSocket 连接和消息推送
- **AND** 测试错误处理和异常情况

## MODIFIED Requirements

### Requirement: 配置管理扩展
系统 SHALL 扩展现有配置管理，支持模式配置。

#### Scenario: 模式配置集成
- **WHEN** 加载 AgentConfig
- **THEN** 包含 ModeSettings 子配置
- **AND** ModeSettings 定义默认模式、模式切换权限、各模式配置
- **AND** 支持从环境变量、YAML、JSON 加载模式配置

### Requirement: 网关路由扩展
系统 SHALL 扩展现有网关路由，支持模式路由。

#### Scenario: 模式路由逻辑
- **WHEN** 请求到达网关
- **THEN** 根据请求中的 mode 参数或会话状态选择对应 Agent
- **AND** MTC 请求路由到 MTCAgent
- **AND** CODE 请求路由到 CodeAgent
- **AND** 支持动态模式切换

### Requirement: 类型定义扩展
系统 SHALL 扩展现有类型定义，支持模式和任务相关类型。

#### Scenario: 模式相关类型
- **WHEN** 导入 core.types
- **THEN** 包含 AgentMode、ModeConfig、FilePermission、ExecutionEnvironment 枚举
- **AND** 包含 Task、TaskStatus、TaskDependency 模型
- **AND** 包含 Artifact、Reference 模型

## REMOVED Requirements
无移除的需求。所有现有功能保持向后兼容。
