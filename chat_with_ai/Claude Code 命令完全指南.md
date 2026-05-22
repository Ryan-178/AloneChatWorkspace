# Claude Code 命令完全指南

> 截止 2026 年 5 月，Claude Code 命令体系涵盖 **150+ 个命令**，分为 **8 大类**：CLI 启动命令、斜杠命令、键盘快捷键、特殊符号命令、MCP 管理命令、Skills 管理命令、自定义命令、Settings.json 配置规则。本文档覆盖全部命令及用法。

---

## 目录

1. [安装与启动](#1-安装与启动)
2. [CLI 启动命令（15 个）](#2-cli-启动命令15-个)
3. [斜杠命令·交互模式（48 个）](#3-斜杠命令交互模式48-个)
4. [键盘快捷键（15 个）](#4-键盘快捷键15-个)
5. [特殊符号命令（4 个）](#5-特殊符号命令4-个)
6. [MCP 管理命令（6 个）](#6-mcp-管理命令6-个)
7. [Skills / 插件管理命令（9 个）](#7-skills--插件管理命令9-个)
8. [自定义命令（Custom Commands）](#8-自定义命令custom-commands)
9. [Settings.json 配置规则（30+ 条）](#9-settingsjson-配置规则30-条)
10. [Hooks 事件系统（26 个事件）](#10-hooks-事件系统26-个事件)
11. [完整命令速查表](#11-完整命令速查表)

---

## 1. 安装与启动

### 环境要求
- Node.js 18+（仅 npm 安装方式）
- Claude.ai 账号（需完成手机验证）
- 支持 Windows / macOS / Linux（含 WSL）

### 安装方式

#### 方式一：原生安装（官方推荐，零依赖）
```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# 安装最新版
curl -fsSL https://claude.ai/install.sh | bash -s latest

# 安装特定版本
curl -fsSL https://claude.ai/install.sh | bash -s 1.0.58

# macOS Homebrew
brew install --cask claude-code

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

#### 方式二：npm 全局安装
```bash
npm install -g @anthropic-ai/claude-code
```

### 验证安装
```bash
claude --version
```

---

## 2. CLI 启动命令（15 个）

CLI 命令是指在终端中直接调用 Claude Code 时使用的命令和参数。

### 2.1 基础启动

| 命令 | 说明 |
|------|------|
| `claude` | 启动交互模式 |
| `claude "your task"` | 运行一次性任务，执行后退出 |
| `claude -p "query"` | 执行查询后退出（pipe 模式） |
| `claude --help` | 查看所有 CLI 参数帮助 |
| `claude --version` | 查看版本信息 |
| `claude --verbose` | 启用详细日志模式，用于调试诊断 |
| `claude --settings <path>` | 使用指定路径的 settings.json 启动 |

### 2.2 模型参数

| 命令 | 说明 |
|------|------|
| `claude --model sonnet` | 使用 Sonnet 模型（日常开发首选） |
| `claude --model opus` | 使用 Opus 模型（复杂推理） |
| `claude --model haiku` | 使用 Haiku 模型（轻量快速） |
| `claude --model claude-3-5-sonnet` | 指定具体版本 |

**模型选择建议：**
- **Sonnet**：日常开发编码，性价比最佳
- **Opus**：架构决策、复杂推理、规划任务
- **Haiku**：探索性任务、简单查询、低成本快速响应

### 2.3 会话控制

| 命令 | 说明 |
|------|------|
| `claude -c` 或 `claude --continue` | 继续最近一次对话 |
| `claude --resume` | 恢复上次会话（保留上下文） |
| `claude --resume <session-name>` | 按名称恢复特定历史会话 |
| `claude --clear` | 清除对话历史 |
| `claude --output result.md` | 输出结果到指定文件 |

### 2.4 工程化参数

| 命令 | 说明 |
|------|------|
| `claude commit` | 自动分析变更并创建 Git 提交 |
| `claude update` | 手动更新 Claude Code 版本 |
| `claude --worktree feature-xxx` | 在独立 Git Worktree 中启动（并行开发） |
| `claude --add-dir ../shared-lib` | 启动时添加额外工作目录（Monorepo 支持） |
| `cat log \| claude -p "analyze"` | 管道输入日志/文件进行分析 |

---

## 3. 斜杠命令·交互模式（48 个）

斜杠命令是 Claude Code 的核心，在交互模式下直接输入 `/command` 使用。

### 3.1 会话管理类（5 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/clear` | 清除对话历史 | 清除全部对话历史与命令历史，从零开始。**推荐每个新任务前使用** |
| `/compact` | 压缩上下文 | 保留关键决策与模式信息，回收 Token 空间。继续同一任务时使用 |
| `/compact retain <key>` | 带保留指令压缩 | 指定保留的关键内容，如 `/compact retain auth module` |
| `/resume <name>` | 恢复历史会话 | 指定会话名称继续之前的对话 |
| `/exit` | 退出会话 | 退出当前 Claude Code 会话（也可按 Ctrl+C 两次） |
| `/btw <message>` | 侧边提问 | 不打断当前主任务的临时询问，不污染主上下文 |

**使用建议：**
- **继续同一任务** → 用 `/compact`
- **切换到全新任务** → 用 `/clear`
- 建议在上下文用量达 70-80% 时主动压缩，不要等窗口填满

### 3.2 上下文与资源管理类（8 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/context` | 上下文用量查看 | 以彩色网格展示当前上下文使用情况（百分比 + Token 数） |
| `/cost` | 查看 Token 消耗 | 展示本次会话的 Token 用量与预估费用 |
| `/memory` | 编辑记忆文件 | 打开并编辑 CLAUDE.md 记忆文件，更新项目上下文 |
| `/diff` | 差异查看器 | 交互式差异查看器，展示未提交修改及 AI 每轮操作变动 |
| `/diff <file>` | 特定文件差异 | 查看指定文件的改动，如 `/diff src/auth.ts` |
| `/status` | 查看当前状态 | 查看当前模型、版本、API 连接、上下文状态、会话信息 |
| `/history` | 查看命令历史 | 查看当前会话的命令历史记录 |
| `/stats` | 用量统计 | 可视化每日用量与模型偏好统计 |

### 3.3 模型与配置管理类（5 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/model` | 交互式选择模型 | 进入交互式选择器选择模型 |
| `/model <name>` | 切换指定模型 | 在会话中切换模型，无需重启。支持 `sonnet` / `opus` / `haiku` |
| `/config` | 调整配置 | 打开交互式配置面板，修改主题、通知、行为偏好等 |
| `/permissions` | 权限管理 | 查看与更新工具权限（白名单/黑名单） |
| `/fast` | 切换极速模式 | 切换极速模式，优化响应速度 |

**策略建议：**
- Sonnet 起步（日常编码）
- 遇到复杂问题切 Opus（架构决策）
- 琐碎任务用 Haiku（低成本快速）

### 3.4 代码分析与质量类（10 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/review` | 代码审查 | 对当前改动进行 Code Review，检查潜在问题 |
| `/security-review` | 安全审计 | 深度安全审计：注入攻击、认证缺陷、权限问题等 |
| `/simplify` | 代码简化 | 并行启动三个审查 Agent，检查代码复用性、质量与效率后自动修复 |
| `/batch` | 批量改造 | 大规模代码改造的并行编排命令，将任务拆解为 5-30 个独立单元自动发起 PR |
| `/test` | 运行测试 | 自动化测试执行 |
| `/bug` | 修复 Bug | 分析并修复 Bug，定位效率提升 5 倍 |
| `/commit` | 智能提交 | 分析代码改动，自动生成规范的 Conventional Commit 信息并提交 |
| `/autofix-pr` | 自动修复 PR | 持续监听 PR 的云端 Agent，CI 失败时自动推送修复 |
| `/loop <time> "<task>"` | 后台循环任务 | 定时后台执行指定任务，如 `/loop 5m "check status"` |
| `/pr-comments` | PR 评论 | 从 GitHub 拉取 Pull Request 评论并展示 |

### 3.5 项目初始化与诊断类（7 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/init` | 初始化项目 | 扫描代码库自动生成 CLAUDE.md 文件，建立项目上下文 |
| `/doctor` | 健康诊断 | 全面检查安装状况、依赖、API 连接、权限配置 |
| `/debug` | 调试模式 | 开启当前会话调试日志并分析 |
| `/plan <description>` | 计划模式 | 进入计划模式，输出执行方案供确认，不立即修改代码 |
| `/add-dir <path>` | 添加工作目录 | 添加额外工作目录到上下文（支持 Monorepo） |
| `/terminal-setup` | 终端设置 | 为 iTerm2 或 VS Code 设置 Shift+Enter 换行快捷键 |
| `/migrate-installer` | 迁移安装 | 将全局 npm 安装迁移到本地安装 |

### 3.6 工作流增强类（8 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/insights` | 项目分析报告 | 生成项目使用分析报告（交互模式、常见摩擦点等） |
| `/schedule` | 定时任务 | 云端定时任务，支持对话式配置流程 |
| `/fork` | 分支实验 | 分叉当前对话，创建独立分支继续探索 |
| `/rewind` | 回滚 | 回滚到之前的状态（撤销 AI 操作） |
| `/search <query>` | 搜索代码 | 搜索代码库中的特定代码 |
| `/rename <name>` | 重命名会话 | 重命名当前会话 |
| `/export` | 导出对话 | 将当前对话导出到文件或剪贴板 |
| `/help` | 查看帮助 | 列出所有可用斜杠命令和快捷操作 |

### 3.7 高级系统管理类（5 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/agents` | 子代理管理 | 管理用于专门任务的自定义 AI Subagent |
| `/bashes` | Bash 会话管理 | 列出并管理后台运行的 Bash Shell 脚本 |
| `/tasks` | 后台任务管理 | 查看后台运行中的任务（编译、测试等） |
| `/hooks` | 钩子管理 | 管理工具事件的钩子配置 |
| `/vim` | Vim 模式切换 | 在 Vim 编辑模式和普通编辑模式之间切换 |

### 3.8 IDE 与集成类（5 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/ide` | IDE 集成管理 | 管理 IDE 集成并显示状态 |
| `/login` | 切换账户 | 切换 Anthropic 账户 |
| `/logout` | 注销账户 | 从当前 Anthropic 账户登出 |
| `/install-github-app` | 安装 GitHub App | 为仓库设置 Claude GitHub Actions |
| `/release-notes` | 查看发布说明 | 查看 Claude Code 版本发布说明 |

### 3.9 界面与显示类（4 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/statusline` | 状态行设置 | 设置 Claude Code 的状态行用户界面 |
| `/output-style` | 输出样式 | 直接设置输出样式或从选择菜单中设置 |
| `/output-style:new` | 创建自定义样式 | 创建自定义输出样式 |
| `/upgrade` | 升级级别 | 升级至最高级别，获得更高的速率限制和更多功能 |

### 3.10 其他（1 个）

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `/bug` | 反馈 Bug | 报告 Bug，将对话内容发送给 Anthropic |

---

## 4. 键盘快捷键（15 个）

| 快捷键 | 功能 | 详细说明 |
|--------|------|---------|
| `Esc` | 停止执行 | 立即停止当前 AI 工具执行 |
| `Esc + Esc`（快速双击） | 回退/检查点 | 回退对话 / 打开检查点菜单，恢复代码 + 上下文 |
| `Ctrl + C` | 打断执行 | 打断 AI 当前执行 |
| `Ctrl + D` | 安全退出 | 安全退出当前会话 |
| `Ctrl + L` | 清屏刷新 | 清屏刷新终端显示 |
| `Ctrl + R` | 搜索命令历史 | 搜索历史命令 |
| `Ctrl + O` | 切换输出模式 | 切换详细/简洁输出模式 |
| `Ctrl + W` | 删除单词 | 删除前一个单词 |
| `Ctrl + B` | 后台模式 | 将当前任务发送到后台运行（不占用主上下文） |
| `Ctrl + G` | 修改计划 | 在 Plan Mode 下修改当前计划 |
| `Ctrl + T` | 后台任务查看 | 查看后台运行中的任务 |
| `Shift + Tab`（按 1 次） | 切换权限模式 | 在信任模式（Auto-Accept）和确认模式间切换 |
| `Shift + Tab`（按 2 次） | 进入 Plan Mode | 只规划不执行，输出方案供确认 |
| `Shift + Enter` | 多行输入 | 跨平台通用多行输入 |
| `↑ / ↓` | 历史命令导航 | 上下键切换命令历史 |

---

## 5. 特殊符号命令（4 个）

在交互模式下，以下特殊符号可直接使用：

| 符号 | 功能 | 示例 |
|------|------|------|
| `!<command>` | 直接执行 Shell 命令 | `!npm run test`、`!git status` |
| `@<file>` | 精确注入文件上下文 | `@src/components/Button.tsx` |
| `@<dir>` | 精确注入目录上下文 | `@src/components` |
| `#<message>` | 记录到 CLAUDE.md | `# Use async/await for all database queries` |

> **`#` 前缀**：在 Claude Code 中以 `#` 开头输入内容，会自动追加到项目 CLAUDE.md 文件的末尾，实现快速记忆记录。

---

## 6. MCP 管理命令（6 个）

MCP（Model Context Protocol）管理命令用于连接外部工具和数据源：

| 命令 | 功能 |
|------|------|
| `claude mcp add --transport http <name> <url>` | 添加 HTTP MCP 服务器（推荐云端服务） |
| `claude mcp add --transport stdio <name> -- <command>` | 添加 Stdio MCP 服务器（本地进程） |
| `claude mcp add --transport sse <name> <url>` | 添加 SSE MCP 服务器（旧版远程连接） |
| `claude mcp list` | 列出所有已安装 MCP 服务器 |
| `claude mcp get <name>` | 查看指定服务器详细配置 |
| `claude mcp remove <name>` | 移除指定 MCP 服务器 |
| `claude mcp add-from-claude-desktop` | 从 Claude Desktop 一键导入（仅 macOS/WSL） |

### 作用域参数

| 作用域 | 存储位置 | 适用场景 |
|--------|----------|---------|
| `--scope local`（默认） | `~/.claude.json`（与当前目录绑定） | 单项目专属工具 |
| `--scope project` | 项目根目录 `.mcp.json`（可提交 Git） | 团队共享工具 |
| `--scope user` | 全局配置 | 个人所有项目通用 |

### HTTP MCP 带鉴权

```bash
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### Stdio MCP 示例

```bash
# Node.js 服务器
claude mcp add --transport stdio firecrawl -- npx -y firecrawl-mcp

# Python 服务器
claude mcp add --transport stdio python-server -- python3 /path/to/server.py

# Windows 环境
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

> **注意**：`--` 是关键分隔符，之前是 Claude Code 自身参数，之后是 MCP 服务器的启动命令与参数。

---

## 7. Skills / 插件管理命令（9 个）

Skills 是 Claude Code 的模块化能力扩展系统：

### 7.1 内置管理命令

| 命令 | 功能 |
|------|------|
| `/skills` | 列出所有已安装的 Skills 及其描述 |
| `/plugin marketplace add <repo>` | 注册官方 Skills 仓库为插件源 |
| `/plugin install <name>` | 安装指定插件/Skill 包 |
| `/plugin list` | 列出已安装的插件 |
| `/plugin remove <name>` | 移除指定插件 |

### 7.2 命令行安装工具

| 命令 | 功能 |
|------|------|
| `skillhub search <keyword>` | 从 skillhub 搜索技能 |
| `skillhub install <name>` | 一键安装 Skills 到 Claude Code |
| `npx skills add <name> -g -y` | 全局安装 Skills |
| `claude-skills install <name> --client claude-code` | 安装到指定客户端 |

### 安装来源

```bash
# 官方插件市场
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills

# 手动安装（项目级）
mkdir -p .claude/skills/<skill-name>
# 放入 SKILL.md 后即刻生效

# 手动安装（用户级）
mkdir -p ~/.claude/skills/<skill-name>
```

---

## 8. 自定义命令（Custom Commands）

将重复工作流封装为可复用的斜杠命令。

### 8.1 YAML 格式命令

在 `.claude/commands/` 下创建 YAML 文件：

```yaml
# .claude/commands/commit-push-pr.yaml
name: commit-push-pr
description: 一键 commit + push + 创建 PR
user-invocable: true
steps:
  - bash: git add . && git commit -m "{{message}}"
  - bash: git push
  - mcp: github-create-pr
```

### 8.2 Markdown 格式命令

在 `.claude/commands/` 下创建 MD 文件：

```markdown
---
description: 审查代码安全漏洞
---
# Security Review
审查此代码的安全漏洞，包括：
1. SQL 注入风险
2. XSS 漏洞
3. 认证缺陷
4. 敏感信息泄露
```

### 命令目录位置

| 位置 | 作用域 | 说明 |
|------|--------|------|
| `.claude/commands/` | 项目级 | 跟随 Git 版本控制，团队共享 |
| `~/.claude/commands/` | 用户级 | 全局生效，跨项目可用 |

使用时直接输入命令名（不含路径）即可调用，如 `/commit-push-pr`。

---

## 9. Settings.json 配置规则（30+ 条）

settings.json 是 Claude Code 的安全中枢和行为控制器，包含 **权限规则、钩子、沙箱、模型、环境变量** 等配置。

### 9.1 配置文件层级（5 级）

| 优先级 | 文件路径 | 作用范围 |
|--------|----------|---------|
| 最低 | `~/.claude/settings.json` | 用户级全局配置 |
| 中 | `.claude/settings.json` | 项目级团队配置（提交 Git） |
| 中高 | `.claude/settings.local.json` | 项目级本地配置（Git 忽略） |
| 高 | `/etc/claude-code/managed-settings.json` | 企业级管理员配置 |
| 最高 | `--settings <path>` | 命令行临时配置 |

### 9.2 权限规则模式（Tool + Pattern）

规则格式：`Action(Tool(Pattern))`

**Action（行为）：**
| 行为 | 含义 |
|------|------|
| `allow` | 允许执行 |
| `deny` | 禁止执行（优先级最高） |
| `ask` | 每次执行前询问用户 |

**Tool（内置工具名称，10 个）：**
| 工具名 | 功能 |
|--------|------|
| `Bash` | Shell 命令执行 |
| `Read` | 文件读取 |
| `Write` | 文件写入 |
| `Edit` | 文件编辑 |
| `WebFetch` | 网页内容获取 |
| `WebSearch` | 网络搜索 |
| `TodoWrite` | 任务列表写入 |
| `Task` | 子任务派发 |
| `NotebookEdit` | Notebook 编辑 |
| `AskUserQuestion` | 用户提问 |

**Pattern（匹配模式示例）：**
| 模式 | 匹配范围 |
|------|---------|
| `Bash(git:*)` | 所有 git 开头的命令 |
| `Bash(npm run test:*)` | npm run test 及其子命令 |
| `Bash(rm -rf:*)` | 所有 rm -rf 操作 |
| `Read(./src/**)` | src 目录下所有文件 |
| `Read(./.env)` | 仅 .env 文件 |
| `WebFetch(domain:api.github.com)` | 限制访问的域名 |

### 9.3 完整配置项速查

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `permissions.allow` | string[] | 允许的操作规则列表 |
| `permissions.deny` | string[] | 禁止的操作规则列表 |
| `permissions.ask` | string[] | 需确认的操作规则列表 |
| `sandbox.enable` | boolean | 是否启用沙箱隔离 |
| `sandbox.enableWeakerNestedSandbox` | boolean | 容器中启用降级沙箱 |
| `sandbox.denyRead` | string[] | OS 级禁止读取的文件 |
| `sandbox.denyWrite` | string[] | OS 级禁止写入的文件 |
| `sandbox.networkAllowlist` | string[] | 网络访问白名单 |
| `hooks.PostToolUse` | object[] | 工具执行后触发 |
| `hooks.PreToolUse` | object[] | 工具执行前触发 |
| `hooks.SessionStart` | object[] | 会话开始时触发 |
| `hooks.Stop` | object[] | 会话结束时触发 |
| `hooks.UserPromptSubmit` | object[] | 用户提交提示词时触发 |
| `hooks.PermissionRequest` | object[] | 权限请求时触发 |
| `hooks.Notification` | object[] | 通知事件触发 |
| `model` | string | 默认模型名称 |
| `env.ANTHROPIC_BASE_URL` | string | API 端点地址 |
| `env.ANTHROPIC_AUTH_TOKEN` | string | API 认证令牌 |
| `env.ANTHROPIC_API_KEY` | string | API 密钥 |
| `env.ANTHROPIC_MODEL` | string | 指定模型 |
| `env.ANTHROPIC_SMALL_FAST_MODEL` | string | 轻量模型 |
| `env.ANTHROPIC_DEFAULT_OPUS_MODEL` | string | 旗舰模型 |
| `language` | string | 回复语言（如 `chinese`） |
| `autoUpdatesChannel` | string | 更新通道（`stable`/`latest`） |
| `showTurnDuration` | boolean | 显示每次回复耗时 |
| `spinnerTipsEnabled` | boolean | 加载时显示提示 |
| `includeCoAuthoredBy` | boolean | Git 提交中添加 Co-Authored-By |
| `cleanupPeriodDays` | number | 自动清理旧会话天数 |
| `ignorePatterns` | string[] | 忽略的文件模式 |
| `additionalDirectories` | string[] | 额外工作目录 |
| `companyAnnouncements` | string[] | 启动公告 |
| `todoFeatureEnabled` | boolean | 启用任务列表功能 |
| `attribution` | object | Git 归属信息 |
| `statusLine` | object | 自定义状态行 |

### 9.4 最小安全配置模板

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(npm run test:*)",
      "Bash(npm run lint:*)",
      "Bash(npm run build:*)",
      "Read",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push:*)",
      "Bash(git reset --hard:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(sudo:*)",
      "Bash(chmod 777:*)",
      "Bash(npm publish:*)",
      "Read(./.env)",
      "Read(./.env.*)"
    ]
  },
  "sandbox": {
    "enable": true,
    "denyRead": ["./.env", "./secrets/**"],
    "denyWrite": ["./.claude/**"],
    "networkAllowlist": ["api.github.com", "registry.npmjs.org"]
  }
}
```

---

## 10. Hooks 事件系统（26 个事件）

Hooks 是 Claude Code 的确定性约束机制，在 Agent 生命周期的特定节点自动触发。支持 **26 个 Hook 事件**。

### 10.1 常用事件一览

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `SessionStart` | 会话开始时 | 环境初始化、公告展示 |
| `UserPromptSubmit` | 用户提交提示词时 | 提示词预处理、安全检查 |
| `PreToolUse` | 工具执行前 | 权限审查、危险命令拦截 |
| `PostToolUse` | 工具执行后 | 代码格式化、日志记录 |
| `PermissionRequest` | 权限请求时 | 自定义权限决策 |
| `Notification` | 通知事件 | 任务完成桌面提醒 |
| `Stop` | 会话结束时 | 清理操作、发送通知 |
| `PreCompact` | 压缩前 | 压缩前保存关键信息 |
| `TurnStart` | 每次轮次开始时 | 重置计数器 |
| `TurnEnd` | 每次轮次结束时 | 记录消耗统计 |

### 10.2 Hook Exit Code 含义

| Exit Code | 含义 | 效果 |
|-----------|------|------|
| `exit 0` | 成功 | 继续执行 |
| `exit 1` | 错误但不阻止 | 工作流继续，记录错误 |
| `exit 2` | 阻止 | **真正拦住执行**，stderr 发回 Claude 做修正 |

> **只有 exit 2 才是真正的安全门**。很多安全 hook 写错就错在这里。

### 10.3 Hook 配置示例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint -- --fix",
            "timeout": 30000
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/bash-firewall.sh",
            "timeout": 5000
          }
        ]
      }
    ],
    "Notification": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude Code task completed\"'"
      }
    ]
  }
}
```

---

## 11. 完整命令速查表

### CLI 命令速查（15 个）

| 命令 | 说明 |
|------|------|
| `claude` | 启动交互模式 |
| `claude "task"` | 运行一次性任务 |
| `claude -p "query"` | 查询后退出 |
| `claude -c` | 继续最近对话 |
| `claude --resume` | 恢复上次会话 |
| `claude --resume <name>` | 恢复指定会话 |
| `claude --model sonnet` | 指定模型启动 |
| `claude --verbose` | 详细日志模式 |
| `claude --settings <path>` | 指定配置文件 |
| `claude --add-dir <path>` | 添加工作目录 |
| `claude commit` | 自动 Git 提交 |
| `claude update` | 手动更新版本 |
| `claude --help` | 查看帮助 |
| `claude --version` | 查看版本 |
| `claude --worktree <name>` | Worktree 启动 |

### 斜杠命令速查（48 个）

**会话管理（6 个）：**
| 命令 | 说明 |
|------|------|
| `/clear` | 清除对话历史 |
| `/compact` | 压缩上下文 |
| `/compact retain <key>` | 带保留指令压缩 |
| `/resume <name>` | 恢复历史会话 |
| `/exit` | 退出会话 |
| `/btw <message>` | 侧边提问 |

**资源管理（8 个）：**
| 命令 | 说明 |
|------|------|
| `/context` | 查看上下文用量 |
| `/cost` | 查看 Token 消耗 |
| `/memory` | 编辑记忆文件 |
| `/diff` | 差异查看器 |
| `/diff <file>` | 特定文件差异 |
| `/status` | 查看当前状态 |
| `/history` | 查看命令历史 |
| `/stats` | 用量统计 |

**配置管理（5 个）：**
| 命令 | 说明 |
|------|------|
| `/model` | 交互式选模型 |
| `/model <name>` | 切换指定模型 |
| `/config` | 调整配置 |
| `/permissions` | 权限管理 |
| `/fast` | 极速模式 |

**代码质量（10 个）：**
| 命令 | 说明 |
|------|------|
| `/review` | Code Review |
| `/security-review` | 安全审计 |
| `/simplify` | 代码简化重构 |
| `/batch` | 批量代码改造 |
| `/test` | 运行测试 |
| `/bug` | 分析修复 Bug |
| `/commit` | 智能 Git 提交 |
| `/autofix-pr` | 自动修复 PR |
| `/loop <time> "<task>"` | 后台循环任务 |
| `/pr-comments` | PR 评论 |

**诊断与初始化（7 个）：**
| 命令 | 说明 |
|------|------|
| `/init` | 生成 CLAUDE.md |
| `/doctor` | 健康诊断 |
| `/debug` | 调试模式 |
| `/plan` | 进入计划模式 |
| `/add-dir <path>` | 添加工作目录 |
| `/terminal-setup` | 终端设置 |
| `/migrate-installer` | 迁移安装 |

**工作流（8 个）：**
| 命令 | 说明 |
|------|------|
| `/insights` | 项目分析报告 |
| `/schedule` | 定时任务 |
| `/fork` | 分支实验 |
| `/rewind` | 回滚 |
| `/search <query>` | 搜索代码库 |
| `/rename <name>` | 重命名会话 |
| `/export` | 导出对话 |
| `/help` | 查看帮助 |

**高级系统（5 个）：**
| 命令 | 说明 |
|------|------|
| `/agents` | 子代理管理 |
| `/bashes` | Bash 会话管理 |
| `/tasks` | 后台任务管理 |
| `/hooks` | 钩子管理 |
| `/vim` | Vim 模式切换 |

**IDE 与集成（5 个）：**
| 命令 | 说明 |
|------|------|
| `/ide` | IDE 集成管理 |
| `/login` | 切换账户 |
| `/logout` | 注销账户 |
| `/install-github-app` | 安装 GitHub App |
| `/release-notes` | 发布说明 |

**界面显示（4 个）：**
| 命令 | 说明 |
|------|------|
| `/statusline` | 状态行设置 |
| `/output-style` | 输出样式 |
| `/output-style:new` | 创建自定义样式 |
| `/upgrade` | 升级级别 |

### 键盘快捷键速查（15 个）

| 快捷键 | 说明 |
|--------|------|
| `Esc` | 停止执行 |
| `Esc + Esc` | 回退 / 检查点 |
| `Ctrl + C` | 打断执行 |
| `Ctrl + D` | 安全退出 |
| `Ctrl + L` | 清屏 |
| `Ctrl + R` | 搜索历史 |
| `Ctrl + O` | 切换输出模式 |
| `Ctrl + W` | 删除单词 |
| `Ctrl + B` | 后台运行 |
| `Ctrl + G` | 修改计划 |
| `Ctrl + T` | 后台任务 |
| `Shift + Tab`（1次） | 切换权限模式 |
| `Shift + Tab`（2次） | 进入 Plan Mode |
| `Shift + Enter` | 多行输入 |
| `↑ / ↓` | 历史命令 |

### 特殊符号速查（4 个）

| 符号 | 说明 |
|------|------|
| `!<command>` | 直接执行 Shell |
| `@<file>` | 注入文件上下文 |
| `@<dir>` | 注入目录上下文 |
| `#<message>` | 记录到 CLAUDE.md |

### MCP 管理速查（7 个）

| 命令 | 说明 |
|------|------|
| `claude mcp add --transport http` | 添加 HTTP MCP |
| `claude mcp add --transport stdio` | 添加 Stdio MCP |
| `claude mcp add --transport sse` | 添加 SSE MCP |
| `claude mcp list` | 列出 MCP |
| `claude mcp get <name>` | 查看 MCP |
| `claude mcp remove <name>` | 移除 MCP |
| `claude mcp add-from-claude-desktop` | 从 Desktop 导入 |

### Skills / 插件速查（9 个）

| 命令 | 说明 |
|------|------|
| `/skills` | 列出 Skills |
| `/plugin marketplace add <repo>` | 注册插件源 |
| `/plugin install <name>` | 安装插件 |
| `/plugin list` | 列出插件 |
| `/plugin remove <name>` | 移除插件 |
| `skillhub search <keyword>` | 搜索技能 |
| `skillhub install <name>` | 安装技能 |
| `npx skills add <name> -g -y` | 全局安装 |
| `claude-skills install <name>` | 安装到客户端 |

### 内置工具名速查（10 个）

| 工具 | 功能 |
|------|------|
| `Bash` | Shell 命令执行 |
| `Read` | 文件读取 |
| `Write` | 文件写入 |
| `Edit` | 文件编辑 |
| `WebFetch` | 网页获取 |
| `WebSearch` | 网络搜索 |
| `TodoWrite` | 任务写入 |
| `Task` | 子任务派发 |
| `NotebookEdit` | Notebook 编辑 |
| `AskUserQuestion` | 用户提问 |

### Hooks 事件速查（26 个）

| 事件 | 触发时机 |
|------|---------|
| `SessionStart` | 会话开始 |
| `UserPromptSubmit` | 用户提交提示词 |
| `PreToolUse` | 工具执行前 |
| `PostToolUse` | 工具执行后 |
| `PermissionRequest` | 权限请求 |
| `Notification` | 通知 |
| `Stop` | 会话结束 |
| `PreCompact` | 压缩前 |
| `TurnStart` | 轮次开始 |
| `TurnEnd` | 轮次结束 |
| `Resume` | 恢复会话 |
| `Shutdown` | 关闭 |
| `Compact` | 压缩后 |
| `Error` | 错误 |
| 及其他 12 个细分事件 | — |

### Settings.json 配置项速查（30+ 个）

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `permissions.allow` | string[] | 允许规则 |
| `permissions.deny` | string[] | 禁止规则 |
| `permissions.ask` | string[] | 询问规则 |
| `sandbox.enable` | boolean | 沙箱开关 |
| `sandbox.denyRead` | string[] | 禁读文件 |
| `sandbox.denyWrite` | string[] | 禁写文件 |
| `sandbox.networkAllowlist` | string[] | 网络白名单 |
| `hooks` | object | 钩子配置 |
| `model` | string | 默认模型 |
| `language` | string | 回复语言 |
| `autoUpdatesChannel` | string | 更新通道 |
| `showTurnDuration` | boolean | 显示耗时 |
| `cleanupPeriodDays` | number | 清理天数 |
| `ignorePatterns` | string[] | 忽略模式 |
| `additionalDirectories` | string[] | 额外目录 |
| `env.ANTHROPIC_BASE_URL` | string | API 端点 |
| `env.ANTHROPIC_AUTH_TOKEN` | string | 认证令牌 |
| `env.ANTHROPIC_API_KEY` | string | API 密钥 |
| `env.ANTHROPIC_MODEL` | string | 模型名称 |
| `todoFeatureEnabled` | boolean | 任务列表 |
| `companyAnnouncements` | string[] | 启动公告 |
| `includeCoAuthoredBy` | boolean | 提交署名 |
| `spinnerTipsEnabled` | boolean | 提示信息 |
| `statusLine` | object | 状态行 |
| `attribution` | object | 归属信息 |

---

> **统计**：本文档共收录 **CLI 命令 15 个 + 斜杠命令 48 个 + 键盘快捷键 15 个 + 特殊符号 4 个 + MCP 命令 7 个 + Skills 命令 9 个 + 内置工具 10 个 + Hooks 事件 26 个 + Settings 配置项 30+ 条 = 164+ 个命令/配置项**。
>
> **参考资料**：Anthropic 官方文档、Boris Cherny 团队分享、The Pragmatic Engineer 调研、Builder.io 50 Tips、GitHub 社区最佳实践
