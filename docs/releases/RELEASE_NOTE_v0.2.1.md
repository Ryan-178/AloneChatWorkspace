# AloneWork CLI v0.2.1 发布说明 / Release Notes

## 🎉 概述 / Overview

> **核心功能对标，体验全面升级。**

***

### 发布语

v0.2.0 夯实了能力，v0.2.1 对标了标杆。

这个版本我们完成了 **Phase 3 对标 Claude Code 核心功能**，让 AloneWork 从"好用"迈向"专业"。

**项目品牌焕新**：从 AloneChat 到 AloneWork，全新品牌形象，更专业的定位。命令行工具 `alonechat` 升级为 `alonework`，开启新征程。

**Bash 命令历史补全**：`!` 模式下键入部分命令按 Tab 补全，`!!` 执行上一条命令，`!n` 执行第 n 条历史，效率翻倍。

**后台任务管理**：超过阈值自动后台化，Ctrl+B 手动后台化，任务进度实时追踪，后台智能体持续运行。

**任务依赖追踪**：DAG 依赖图管理，循环依赖检测，拓扑排序执行，复杂任务有序推进。

**LSP 工具集成**：跳转到定义、查找引用、悬停文档，多语言智能支持，编程体验大幅提升。

**外部编辑器支持**：Ctrl+G 在系统编辑器中编辑提示词，支持 VS Code、Vim、Notepad++ 等主流编辑器。

**分叉对话功能**：保留原会话创建分支，探索不同方案无需担心影响主线。

**终端界面美化**：Claude 风格欢迎界面、状态栏、输入栏，打造沉浸式开发体验。

**桌面应用初登场**：Tauri + Next.js 16 跨平台桌面应用，Agent 对话、任务管理、Skills 市场一站式体验。

> 📌 **说明 / Note:** 每个功能后标注的版本号（如 v2.1.77）是 **Claude Code 引入该功能的版本**，表示 AloneWork 对标实现了相同功能。

---

## 🔄 项目重命名 / Project Renaming

### 从 AloneChat 到 AloneWork

本版本包含重要的项目重命名变更：

**品牌更新 / Brand Update:**
- 项目名称：`AloneChat` → `AloneWork`
- CLI 命令：`alonechat` → `alonework`
- Python 包：`alonechat` → `alonework`

**目录重命名 / Directory Renaming:**
```
alonechat-cli/           → alonework-cli/
alonechat-cli/src/alonechat/ → alonework-cli/src/alonework/
```

**关键文件更新 / Key Files Updated:**
- `pyproject.toml` - 项目名称、CLI 入口点、作者信息
- `__init__.py` - 包名和版本信息
- `cli.py` - CLI 命令名和帮助文档
- `README.md` / `README_CN.md` - 项目文档
- `.trae/rules/acw.md` - 项目规则文件

**迁移指南 / Migration Guide:**
```bash
# 旧命令 / Old Command
alonechat --name "开发会话"

# 新命令 / New Command
alonework --name "开发会话"

# Python 导入变更 / Python Import Change
# 旧: from alonechat.lsp import go_to_definition
# 新: from alonework.lsp import go_to_definition
```

---

## ✨ 新功能 / New Features

### ⌨️ Bash 命令历史自动补全

**对标 Claude Code v2.1.14** | 在 `!` 模式下键入部分命令按 Tab 补全！

- 支持 `!` 前缀搜索历史命令
- Tab 键自动补全匹配的历史
- `!!` 执行上一条命令
- `!n` 执行第 n 条历史命令
- YAML 文件持久化存储历史

```bash
# 在交互模式中
!git<Tab>      # 补全匹配 git 的历史命令
!!             # 执行上一条命令
!5             # 执行第 5 条历史命令
```

### 🔄 后台 Bash 任务自动后台化

**对标 Claude Code v2.0.19** | 长时间运行的命令自动后台化！

- 超过阈值自动转为后台执行
- 可自定义超时时间（默认 30 秒）
- 后台任务状态追踪
- 任务完成通知

### ⏯️ 后台任务 Ctrl+B

**对标 Claude Code v2.1.0** | 统一将前台任务后台化！

- 按 `Ctrl+B` 将当前输入后台执行
- 后台任务列表管理
- 任务进度追踪
- 结果异步获取

```bash
# 在输入时按 Ctrl+B
用户输入: 分析这个大文件...
[按 Ctrl+B]
→ 任务已后台化，ID: abc123
```

### 📋 任务管理系统（依赖追踪）

**对标 Claude Code v2.1.16** | 新任务管理，包括依赖追踪！

- DAG 依赖图管理
- 循环依赖检测
- 拓扑排序执行顺序
- 任务状态追踪（pending/running/completed/failed/cancelled）
- 依赖条件满足检查

```python
from agent_framework.services import TaskManager, task_manager

# 创建带依赖的任务
task1 = task_manager.create_task("安装依赖", name="install_deps")
task2 = task_manager.create_task("构建项目", dependencies=[task1.id])
task3 = task_manager.create_task("运行测试", dependencies=[task2.id])

# 获取执行顺序
order = task_manager.get_execution_order()
```

### 🔍 LSP 工具

**对标 Claude Code v2.0.74** | 跳转到定义、查找引用、悬停文档！

- 跳转到定义 (Go to Definition)
- 查找引用 (Find References)
- 悬停文档 (Hover Documentation)
- 多语言支持 (Python/TypeScript/JavaScript/Go/Rust)
- 自动语言检测

```python
from alonework.lsp import go_to_definition, find_references, get_hover

# 跳转到定义
result = go_to_definition("src/main.py", line=10, character=5)

# 查找引用
refs = find_references("src/main.py", line=10, character=5)

# 获取悬停文档
hover = get_hover("src/main.py", line=10, character=5)
```

### 📝 外部编辑器编辑提示词

**对标 Claude Code v2.0.10** | 按 Ctrl+G 在系统编辑器中编辑！

- 自动检测系统编辑器 ($EDITOR / $VISUAL)
- Windows 支持 (VS Code / Notepad++ / Notepad)
- Linux/macOS 支持 (VS Code / Vim / Nano)
- 临时文件自动清理
- 编辑完成后自动读取内容

```bash
# 在输入时按 Ctrl+G
[按 Ctrl+G]
→ 打开外部编辑器编辑当前输入
→ 保存后自动返回
```

### 🤖 后台智能体支持

**对标 Claude Code v2.0.60** | 代理在用户工作时于后台运行！

- 后台聊天任务
- 后台代码生成
- 后台代码审查
- 后台文件处理
- 后台 RAG 查询
- 完成通知机制

```python
from alonework.background import BackgroundAgentRunner

runner = BackgroundAgentRunner()

# 提交后台聊天任务
task = runner.submit_chat("分析这个代码库的结构")

# 提交后台代码生成
task = runner.submit_code_generation("实现一个排序算法", language="python")

# 提交后台代码审查
task = runner.submit_code_review(code_content, file_path="main.py")
```

### ✅ 待办事项列表

**对标 Claude Code v0.2.93** | Claude 使用 Todo 列表保持组织！

- 创建/更新/删除待办事项
- 优先级管理 (LOW/MEDIUM/HIGH/URGENT)
- 状态追踪 (PENDING/IN_PROGRESS/COMPLETED/CANCELLED)
- 标签分类
- 截止日期和过期检测
- 子任务支持
- YAML 持久化

```python
from alonework.todo import TodoManager, TodoPriority

manager = TodoManager()

# 创建待办
todo = manager.create(
    content="实现用户认证功能",
    priority=TodoPriority.HIGH,
    tags=["backend", "security"],
)

# 更新状态
manager.mark_in_progress(todo.id)
manager.mark_completed(todo.id)

# 获取统计
stats = manager.get_stats()
```

---

### 🔄 自动对话压缩

**对标 Claude Code v0.2.47** | 支持无限长度对话！

- 智能压缩对话历史，自动保留关键信息
- AI智能摘要，识别重要决策和任务
- 可配置压缩策略（标准/激进）
- 自动压缩阈值设置

```bash
alonework --auto-compact --compact-threshold 100
/compact --aggressive --summary
```

### 🌳 分叉对话

**对标 Claude Code v2.1.77** | 保留原会话并创建新分支！

- `/fork` - 从当前点创建新分支
- `/branch` - 管理会话分支（列出、切换、删除）
- 支持指定分叉点位置
- 完整的分支历史追踪

```bash
/fork "实验性修改"
/fork --at 5 "从第5条消息分支"
/branch list
/branch switch abc123
```

### 🔥 技能自动热重载

**对标 Claude Code v2.1.0** | 修改技能无需重启服务！

- 自动检测技能文件变化
- 支持Python和YAML文件热重载
- 变更事件回调机制
- 强制重载支持

### 🔗 斜杠命令与技能合并

**对标 Claude Code v2.1.3** | 统一的心智模型！

- 技能可作为斜杠命令直接调用
- 斜杠命令可作为技能管理
- 统一的注册、发现和执行接口
- 简化用户学习曲线

### 🎨 输出样式调整

**对标 Claude Code v2.0.32** | 根据社区反馈恢复弃用样式！

- 多主题支持（dark/light/monokai）
- 可配置消息样式和图标
- 经典进度条、简单表格恢复
- 可访问性支持（高对比度、减少动画）

### 🔍 插件商店搜索增强

**对标 Claude Code v2.0.73** | 更强大的搜索能力！

- 按名称搜索（支持精确匹配）
- 按描述搜索
- 按市场过滤（github/skills.sh）
- 多条件组合搜索
- 排序和分页支持

### 📝 --name CLI参数

**对标 Claude Code v2.1.76** | 启动时设置会话显示名称！

```bash
alonework --name "我的开发会话"
alonework --name "Bug修复" --auto-compact
```

### ⚙️ --agent CLI标志

**对标 Claude Code v2.0.59** | 覆盖当前会话的代理设置！

```bash
alonework --agent model=deepseek-v3
alonework --agent model=deepseek-v3,temperature=0.7,max_tokens=4000
```

### 🎨 终端界面美化（Claude风格）

**对标 Claude Code v2.1.126** | 参考Claude Code界面设计风格！

- **欢迎界面组件** - 美观的启动欢迎界面
  - ASCII艺术Logo (▐▛███▜▌)
  - Welcome back! 欢迎文字
  - Tips提示卡片（/init、/help、?快捷键）
  - What's new新功能介绍
  - API密钥遮蔽显示
  - 工作目录显示

- **状态栏组件** - 实时状态显示
  - 快捷键提示 (? for shortcuts)
  - 登录状态显示
  - effort级别 (● high · /effort)
  - Token使用量统计
  - 计时器功能

- **输入栏组件** - 美化的输入提示符
  - 会话名称显示
  - 上下文使用进度条

- **Claude风格配置** - 完整的样式配置
  - 颜色方案（主色调、强调色、成功/警告/错误色）
  - 边框样式（圆角、内边距）
  - 动画效果（思考动画、流式输出动画）
  - 可访问性支持

```
╭─── AloneWork v0.2.1 ───────────────────────────────────────────────╮
│                    Welcome back!                                   │
│                                                                    │
│              ▐▛███▜▌      │ Tips for getting started              │
│             ▝▜█████▛▘     │ ──────────────────────────────        │
│               ▘▘ ▝▝       │ • Run /init to create a CLAUDE.md     │
│                            │ • Run /help to see all commands       │
│                            │ • Press ? for keyboard shortcuts      │
╰────────────────────────────────────────────────────────────────────╯

sk-de2c0...8530 · API Usage Billing  E:\AloneChat-workspace-master

────────────────────────────────────────────────────────────────────────
? for shortcuts                    Logged in                    ● high · /effort
```

---

### 🖥️ AloneChat Desktop 桌面应用

**对标 Claude Cowork & Codex App** | 全新 Tauri + Next.js 跨平台桌面应用！

基于 **Tauri v2 + Next.js 16** 构建的跨平台桌面应用，对标 Claude Cowork 和 OpenAI Codex App，集成现有的 `agent-framework` 后端。

**技术栈 / Tech Stack:**
- **前端**: Next.js 16 + React 19 + TypeScript + Tailwind CSS
- **桌面框架**: Tauri v2 (Rust)
- **状态管理**: Zustand
- **UI 组件**: shadcn/ui + Radix UI
- **实时通信**: WebSocket Gateway

**核心功能 / Core Features:**
- 🤖 **Agent 对话** - MTC/CODE 双模式切换，思考过程可视化，工具调用展示
- 📋 **任务管理** - 后台任务追踪，进度实时更新
- 🔧 **Skills 市场** - Skills 浏览、搜索、执行
- 📁 **工作区管理** - 文件系统访问，目录浏览
- ⚙️ **MCP 管理** - MCP 服务器配置，工具浏览
- 🎨 **主题支持** - 明/暗模式切换

**Tauri Rust 后端 / Tauri Rust Backend:**
- 文件操作: `read_file`, `write_file`, `list_directory`, `delete_path`, `file_exists`, `create_directory`, `get_file_info`
- Shell 命令执行: `execute_command`
- 权限管理: `PermissionManager` (路径/命令权限控制)

**前端组件 / Frontend Components:**
- `AgentChat` - 主对话界面
- `MessageBubble` - 消息气泡
- `ThinkingBlock` - 思考过程展示 (可折叠)
- `ToolCallCard` - 工具调用卡片 (状态可视化)
- `ModeSwitch` - MTC/CODE 模式切换
- `SessionList` - 会话列表管理
- `CommandPalette` - 命令面板 (Ctrl+K)

**API 集成 / API Integration:**
- 完整对接 `agent-framework` REST API (认证、会话、任务、Skills、MCP)
- WebSocket Gateway 连接，支持订阅频道和实时推送
- 消息类型: `task_progress`, `agent_thinking`, `artifact_update`, `mode_switch`, `skill_execution`

```bash
# 开发模式
cd alonechat-desktop
pnpm tauri:dev

# 构建生产版本
pnpm tauri:build

# 仅构建前端
pnpm build
```

**项目结构 / Project Structure:**
```
alonechat-desktop/
├── src-tauri/           # Tauri Rust 后端
│   └── src/
│       ├── commands/    # 文件操作、Shell 命令
│       └── plugins/     # 权限管理
├── src/
│   ├── app/             # Next.js App Router 页面
│   ├── components/      # React 组件
│   │   ├── ui/          # shadcn/ui 组件
│   │   ├── agent/       # Agent 对话组件
│   │   └── layout/      # 布局组件
│   ├── lib/             # 工具库
│   │   ├── api/         # HTTP API 客户端
│   │   ├── websocket/   # WebSocket 客户端
│   │   └── tauri/       # Tauri API 封装
│   ├── stores/          # Zustand 状态管理
│   └── types/           # TypeScript 类型定义
└── package.json
```

---

## 📋 完整命令行参数 / CLI Parameters

```bash
alonework [OPTIONS] [QUERY]

新增选项 / New Options:
  --name NAME                设置会话显示名称
  --agent CONFIG             覆盖代理设置 (格式: key1=value1,key2=value2)
  --auto-compact             启用自动对话压缩
  --compact-threshold N      自动压缩阈值（默认100）
```

---

## ⌨️ 快捷键 / Keyboard Shortcuts

| 快捷键 | 功能 | 描述 |
|--------|------|------|
| `Ctrl+B` | 后台化 | 将当前输入转为后台任务执行 |
| `Ctrl+G` | 外部编辑器 | 在系统编辑器中编辑当前输入 |
| `Ctrl+C` | 中断 | 中断当前操作 |
| `Tab` | 补全 | 命令/历史补全 |
| `!` | 历史搜索 | 进入历史命令搜索模式 |

---

## 🔧 斜杠命令更新 / Slash Commands

| 命令 | 别名 | 描述 |
|------|------|------|
| `/fork` | - | 分叉当前会话 ✨ |
| `/branch` | branches | 管理会话分支 ✨ |
| `/compact` | - | 压缩对话上下文（增强） |
| `/todos` | todo | 列出当前待办事项 ✨ |

---

## 📁 文件变更 / File Changes

### 目录重命名 / Directory Renaming

```
alonechat-cli/                     → alonework-cli/
alonechat-cli/src/alonechat/       → alonework-cli/src/alonework/
```

### 新增文件 / New Files

```
# 输入系统 (Group A)
alonework-cli/src/alonework/input/__init__.py
alonework-cli/src/alonework/input/session.py           # EnhancedInputSession
alonework-cli/src/alonework/input/history.py           # 命令历史管理
alonework-cli/src/alonework/input/key_bindings.py      # 快捷键绑定
alonework-cli/src/alonework/input/external_editor.py   # 外部编辑器

# 后台执行系统 (Group B)
alonework-cli/src/alonework/background/__init__.py
alonework-cli/src/alonework/background/manager.py      # 后台任务管理器
alonework-cli/src/alonework/background/task.py         # 后台任务模型
alonework-cli/src/alonework/background/agent_runner.py # 后台智能体运行器

# 待办事项 (Group C)
alonework-cli/src/alonework/todo/__init__.py
alonework-cli/src/alonework/todo/item.py               # 待办项模型
alonework-cli/src/alonework/todo/manager.py            # 待办管理器

# LSP 工具 (Group D)
alonework-cli/src/alonework/lsp/__init__.py
alonework-cli/src/alonework/lsp/client.py              # LSP 客户端
alonework-cli/src/alonework/lsp/features.py            # LSP 功能实现

# 任务管理 (agent-framework)
agent-framework/agent_framework/services/task_manager/__init__.py  # 任务管理器 + 依赖图

# 配置文件
alonework-cli/src/alonework/configs/cli_enhanced.yaml  # CLI 增强配置

# 终端界面美化 (Claude风格)
alonework-cli/src/alonework/utils/welcome_screen.py    # 欢迎界面组件
alonework-cli/src/alonework/utils/status_bar.py        # 状态栏组件

# 其他
alonework-cli/src/alonework/slash/commands/fork.py
alonework-cli/src/alonework/slash/command_skill_bridge.py
alonework-cli/src/alonework/configs/output_style.yaml  # 输出样式配置（已更新Claude风格）
alonework-cli/src/alonework/configs/style_loader.py
agent-framework/agent_framework/tools/skills_hot_reload.py

# AloneChat Desktop 桌面应用 (Tauri + Next.js)
alonechat-desktop/                                     # 桌面应用根目录
alonechat-desktop/src-tauri/                           # Tauri Rust 后端
alonechat-desktop/src-tauri/src/main.rs               # Tauri 主入口
alonechat-desktop/src-tauri/src/lib.rs                # Tauri 库入口
alonechat-desktop/src-tauri/src/commands/mod.rs       # 命令模块
alonechat-desktop/src-tauri/src/commands/file_ops.rs  # 文件操作命令
alonechat-desktop/src-tauri/src/commands/shell.rs     # Shell 命令执行
alonechat-desktop/src-tauri/src/plugins/mod.rs        # 插件模块
alonechat-desktop/src-tauri/src/plugins/permissions.rs # 权限管理插件
alonechat-desktop/src-tauri/tauri.conf.json           # Tauri 配置
alonechat-desktop/src-tauri/Cargo.toml                # Rust 依赖
alonechat-desktop/src/app/layout.tsx                  # Next.js 根布局
alonechat-desktop/src/app/globals.css                 # 全局样式
alonechat-desktop/src/app/(main)/layout.tsx           # 主应用布局
alonechat-desktop/src/app/(main)/page.tsx             # 首页
alonechat-desktop/src/app/(main)/agent/page.tsx       # Agent 对话页
alonechat-desktop/src/app/(main)/tasks/page.tsx       # 任务管理页
alonechat-desktop/src/app/(main)/skills/page.tsx      # Skills 市场页
alonechat-desktop/src/app/(main)/workspace/page.tsx   # 工作区页
alonechat-desktop/src/app/(main)/settings/page.tsx    # 设置页
alonechat-desktop/src/components/ui/*.tsx             # shadcn/ui 组件
alonechat-desktop/src/components/agent/*.tsx          # Agent 对话组件
alonechat-desktop/src/components/layout/*.tsx         # 布局组件
alonechat-desktop/src/lib/api/*.ts                    # HTTP API 客户端
alonechat-desktop/src/lib/websocket/*.ts              # WebSocket 客户端
alonechat-desktop/src/lib/tauri/*.ts                  # Tauri API 封装
alonechat-desktop/src/stores/*.ts                     # Zustand 状态管理
alonechat-desktop/src/types/*.ts                      # TypeScript 类型定义
alonechat-desktop/package.json                        # 前端依赖
alonechat-desktop/next.config.ts                      # Next.js 配置
alonechat-desktop/tsconfig.json                       # TypeScript 配置
```

### 修改文件 / Modified Files

```
alonework-cli/pyproject.toml                           # 项目重命名 + 添加 prompt_toolkit 依赖
alonework-cli/src/alonework/__init__.py                # 包名更新
alonework-cli/src/alonework/cli.py                     # CLI 命令名更新
alonework-cli/src/alonework/session/storage.py
alonework-cli/src/alonework/session/manager.py
alonework-cli/src/alonework/slash/commands/__init__.py
alonework-cli/src/alonework/slash/commands/compact.py
alonework-cli/src/alonework/slash/executor.py
alonework-cli/src/alonework/commands/chat.py          # 集成增强输入系统 + Claude风格欢迎界面
alonework-cli/src/alonework/cli.py                     # CLI 命令名更新 + 欢迎界面导入
agent-framework/agent_framework/tools/skills_marketplace.py
agent-framework/agent_framework/services/__init__.py  # 导出 TaskManager
README.md / README_CN.md                               # 项目文档更新
.trae/rules/acw.md                                     # 项目规则更新
```

---

## 🚀 快速开始 / Quick Start

```bash
# 基础使用
alonework --name "开发会话"

# 启用自动压缩
alonework --auto-compact --compact-threshold 50

# 覆盖代理设置
alonework --agent model=deepseek-v3,temperature=0.7

# 组合使用
alonework --name "Bug修复" --auto-compact --agent model=deepseek-v3

# 在对话中使用新命令
/fork "尝试新方案"
/branch list
/compact --summary
/todos

# 使用快捷键
# Ctrl+B - 后台化当前任务
# Ctrl+G - 打开外部编辑器
# !git<Tab> - 搜索历史命令

# 启动桌面应用
cd alonechat-desktop
pnpm tauri:dev
```

---

## 📊 Claude Code 功能对标 / Feature Alignment

> 以下版本号为 Claude Code 引入该功能的版本 / Version numbers indicate when Claude Code introduced the feature

| 功能 | Claude Code 版本 | AloneWork 状态 |
|------|-----------------|---------------|
| Bash 命令历史自动补全 | 2.1.14 | ✅ 已实现 |
| 后台 Bash 任务自动后台化 | 2.0.19 | ✅ 已实现 |
| 后台任务 Ctrl+B | 2.1.0 | ✅ 已实现 |
| 任务管理系统（依赖追踪） | 2.1.16 | ✅ 已实现 |
| LSP 工具 | 2.0.74 | ✅ 已实现 |
| 外部编辑器编辑提示词 | 2.0.10 | ✅ 已实现 |
| 后台智能体支持 | 2.0.60 | ✅ 已实现 |
| 待办事项列表 | 0.2.93 | ✅ 已实现 |
| 自动对话压缩 | 0.2.47 | ✅ 已实现 |
| 分叉对话 | 2.1.77 | ✅ 已实现 |
| 技能热重载 | 2.1.0 | ✅ 已实现 |
| 斜杠命令与技能合并 | 2.1.3 | ✅ 已实现 |
| 输出样式调整 | 2.0.32 | ✅ 已实现 |
| 插件商店搜索 | 2.0.73 | ✅ 已实现 |
| --name参数 | 2.1.76 | ✅ 已实现 |
| --agent标志 | 2.0.59 | ✅ 已实现 |
| **终端界面美化（Claude风格）** | 2.1.126 | ✅ 已实现 |
| **项目重命名** | - | ✅ AloneChat → AloneWork |
| **桌面应用 (Tauri + Next.js)** | Cowork/Codex | ✅ 已实现 |

---

## 🙏 致谢 / Acknowledgments

感谢社区反馈，帮助我们将弃用的输出样式恢复，并持续改进产品体验。

Thanks to the community for feedback that helped us restore deprecated output styles and continuously improve the product experience.

---

## 📖 完整文档 / Full Documentation

详细功能文档请参阅: [cli-enhancement-documentation.md](./cli-enhancement-documentation.md)

---

**发布日期 / Release Date:** 2026-05-17

**下一版本计划 / Next Release Plans:**
- 更多斜杠命令增强
- 性能优化
- 国际化支持扩展
- LSP 异步通信完善
- alonechat-desktop 重命名为 alonework-desktop
- 桌面应用 MCP 服务器集成完善
- 桌面应用文件编辑器组件
