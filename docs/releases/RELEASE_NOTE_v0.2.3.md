# AloneChat Workspace v0.2.3

> **为了行动而思考，三种模式掌控。**

***

## 发布语

v0.2.2 搭建了骨架，v0.2.3 注入了灵魂，赋予了掌控。

这个版本我们做了两件大事：**让 AI 从"思考答案"进化到"为了行动而思考"** + **交互模式系统与工具完备**。

**环境原生的智能体系统**：我们不再让模型孤立地完成推理链然后吐出答案。我们构建了一个完整的行动环境——Agent 在其中行动、接收反馈、修正计划、继续推进。训练的对象不再是"模型本身"，而是"模型+环境"的系统。这是研究方向的根基性变化。

**三种交互模式**：Plan（只读探索🔍）、Agent（交互审批🤖）、YOLO（自动批准🚀）。不再一刀切地执行所有操作，而是根据场景选择合适的模式。Plan 模式下只允许读取和搜索，安全探索代码库；Agent 模式下危险操作需要确认，平衡效率与安全；YOLO 模式下全速前进，适合信任的工作区。

**10+ 核心工具**：Shell（白名单/黑名单安全执行）、File（读/写/编辑/删除/搜索）、Git（状态/差异/提交/分支）。每个工具都有分类、权限级别、预估成本。工具执行需要审批，YOLO 模式自动批准。

**Supervisor-Worker 多智能体协作**：一个 Supervisor 协调多个 Worker Agent（代码、数据、研究、测试），任务分解、动态分配、结果汇总。复杂任务不再依赖单点推理，而是分布式协作完成。

**数据收集与训练数据输出**：我们不做在线训练，我们收集。每一次用户与 Agent 的交互都被完整记录为轨迹，经过多维度质量评估（完成度、效率、奖励、错误率），输出为结构化的 JSONL 训练数据。这些数据可以用于后续的模型微调，但选择权在用户手中。

**工作流编排引擎**：顺序、并行、条件、循环——四种节点类型构成完整的工作流图。代码审查、数据处理管道、研究分析，都可以被定义为可复用的工作流模板。

**CLI 命令增强**：`alonechat data` 管理交互数据，`alonechat workflow` 编排工作流，`alonechat env` 管理行动环境，`alonechat --mode` 切换交互模式。命令行不再是简单的对话入口，而是整个智能体系统的操控面板。

**单一模型，深度优化**：依然只使用 DeepSeek V4 Flash。但现在的它不再是一个孤立的推理引擎，而是一个生活在环境中的行动者。reasoning_effort=high 的思考模式与行动-反馈闭环结合，让每一次思考都指向具体的行动。

依然不完美，但比 0.2.2 行动了一点，掌控了一点。这就是"为了行动而思考"与"模式掌控"的意义。

***

## 新增功能

### 交互模式系统

| 模式 | 图标 | 说明 | 适用场景 |
|------|------|------|---------|
| PLAN | 🔍 | 只读探索 | 代码分析、理解代码库 |
| AGENT | 🤖 | 交互审批 | 日常开发、平衡安全与效率 |
| YOLO | 🚀 | 自动批准 | 信任环境、快速迭代 |

### 工具系统

| 工具 | 分类 | 权限 | 说明 |
|------|------|------|------|
| `shell` | shell | execute | 安全Shell执行（白名单/黑名单） |
| `file_read` | file | read | 文件读取（支持编码/行范围） |
| `file_write` | file | write | 文件写入（自动创建目录） |
| `file_edit` | file | write | SearchReplace编辑 |
| `file_delete` | file | dangerous | 文件删除（需确认） |
| `file_search` | file | read | ripgrep/grep搜索 |
| `git_status` | git | read | Git状态 |
| `git_diff` | git | read | Git差异 |
| `git_commit` | git | write | Git提交 |
| `git_branch` | git | write | 分支操作 |

***

## 快速开始

```bash
# 进入CLI目录
cd alonechat-cli

# 安装依赖
pip install -e .
pip install -e ../agent-framework

# 初始化（只需配置API key）
alonechat init

# 启动对话（默认Agent模式）
alonechat chat

# 指定交互模式
alonechat chat --mode plan    # 只读探索
alonechat chat --mode agent   # 交互审批
alonechat chat --mode yolo    # 自动批准

# 在对话中切换模式
/mode plan   # 切换到Plan模式
/mode agent  # 切换到Agent模式
/mode yolo   # 切换到YOLO模式
/mode cycle  # 循环切换

# 收集交互数据
alonechat data collect

# 导出训练数据
alonechat data export --format jsonl

# 评估数据质量
alonechat data quality --threshold 0.7

# 创建代码审查工作流
alonechat workflow create my_review --preset code_review

# 执行工作流
alonechat workflow run my_review

# 规划任务
alonechat workflow plan "重构用户认证模块"

# 查看环境状态
alonechat env status

# 创建环境检查点
alonechat env checkpoint --name before_refactor

# 恢复检查点
alonechat env restore before_refactor
```

***

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    AloneChat v0.2.3                              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Data Layer │  │  Env Layer  │  │   Agent Layer           │  │
│  │  数据收集    │  │  行动环境    │  │  Supervisor-Worker      │  │
│  │  质量评估    │  │  反馈闭环    │  │  多智能体协作            │  │
│  │  训练数据输出 │  │  沙箱安全    │  │  自我反思               │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────────┘  │
│         │                │                     │                 │
│         └────────────────┼─────────────────────┘                 │
│                          ▼                                       │
│              ┌─────────────────────┐                             │
│              │   Workflow Engine   │                             │
│              │   工作流编排引擎     │                             │
│              │   顺序/并行/条件/循环 │                             │
│              └──────────┬──────────┘                             │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Interaction Mode System                     │    │
│  │              交互模式系统                                 │    │
│  │   🔍 PLAN  │  🤖 AGENT  │  🚀 YOLO                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Tool System                             │    │
│  │                  工具系统                                 │    │
│  │   Shell │ File (Read/Write/Edit/Delete/Search) │ Git    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│              ┌─────────────────────┐                             │
│              │      CLI Layer      │                             │
│              │  data/workflow/env  │                             │
│              │  --mode /mode       │                             │
│              └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

***

## 技术实现

### agent-framework 层
- `core/types.py` - InteractionMode 枚举 + ModeConfig
- `core/mode_manager.py` - 模式管理器基类
- `core/base_tool.py` - ToolCategory + PermissionLevel
- `tools/builtin/shell.py` - ShellTool
- `tools/builtin/file/` - File工具集
- `tools/builtin/git/` - Git工具集
- `orchestration/` - 工作流引擎
- `storage/` - 会话存储

### alonework-cli 层
- `modes/manager.py` - CLI模式管理器（Rich界面）
- `tools/executor.py` - 工具执行器
- `tools/renderer.py` - Rich渲染器
- `slash/commands/mode.py` - /mode命令
- `commands/data.py` - 数据管理命令
- `commands/workflow.py` - 工作流命令
- `commands/env.py` - 环境命令

### alonechat-desktop 层
- `components/agent/mode-switch.tsx` - 模式切换组件
- `components/agent/tools-panel.tsx` - 工具面板
- `components/agent/tool-approval-card.tsx` - 审批卡片
- `stores/agent-store.ts` - interactionMode状态

***

## 配置文件

### 交互模式配置
`agent-framework/agent_framework/configs/mode_config.yaml`

### 工具配置
`agent-framework/agent_framework/configs/tools.yaml`

### 工作流配置
`agent-framework/agent_framework/configs/workflow_config.yaml`

***

## 下一步计划

- Phase 1.3: 会话管理SQLite迁移
- Phase 1.4: LSP诊断集成
- Phase 1.5: CLI命令增强
- Phase 1.6: 成本追踪增强
- Phase 2: Mavis角色体系（Leader/Worker/Verifier）

***

**GitHub**: <https://github.com/AlonechatWorkspace/AloneWork>

**邮箱**: <aloneworkworkspace@163.com>
