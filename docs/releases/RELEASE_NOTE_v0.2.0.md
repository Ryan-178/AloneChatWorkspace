# AloneChat Workspace v0.2.0

> **核心功能增强，智能更进一步。**

***

## 发布语

v0.1.3 找到了方向，v0.2.0 夯实了能力。

这个版本我们完成了 **Phase 2 核心功能增强**，让 AloneChat 从"能用"变成"好用"。

**代码库智能索引**：本地 Embedding 支持，无需上传代码到云端。bge-large-zh、text2vec-large-chinese 等中文优化模型开箱即用。索引 10 万行代码，检索响应 < 1 秒。隐私保护，从索引开始。

**自动测试生成**：写完代码，测试自动来。支持 pytest、jest、junit 三大框架。单元测试、集成测试、边缘用例，一键生成。测试覆盖率 > 80%，让每一行代码都有保障。

**错误自动修复**：编译报错、运行时异常，AI 帮你修。语法错误、类型错误、导入错误，智能诊断。修复→测试→验证，循环迭代直到干净。常见错误修复成功率 > 70%。

**DeepSeek V4 深度优化**：请求队列管理，优先级调度。成本控制器，预算不超标。批处理合并请求，效率翻倍。智能重试与降级策略，服务稳定可靠。99.98% 缓存命中率，成本降低 90%+。

**CLI 全面升级（对标 Claude Code）**：全新 Slash Commands 系统，15+ 内置命令。会话持久化管理，断点续聊。打印模式与管道输入，脚本集成友好。子代理系统，任务分工更精细。权限控制系统，安全可靠。MCP 协议集成，扩展无限可能。

**本地优先，隐私至上**：所有核心功能本地运行。代码不离开你的机器，加密上传保护隐私。这是我们的承诺，也是你的权利。

还有很多细节：增量索引更新、多语言代码解析、修复历史追踪、成本使用报告、自定义 Slash Commands……它们都躺在 `agent-framework` 和 `alonechat-cli` 目录里。

依然在路上，但比 0.1.3 强大了一点。这就是积累的意义。

***

## CLI 新特性详解

### Slash Commands 系统

交互会话中的快捷命令，对标 Claude Code 体验：

| 命令 | 别名 | 功能 |
|------|------|------|
| `/help` | `/h`, `/?` | 显示帮助信息 |
| `/clear` | `/cls` | 清除对话历史 |
| `/compact` | - | 压缩对话上下文 |
| `/config` | `/cfg` | 打开配置界面 |
| `/cost` | - | 显示 token 使用统计 |
| `/doctor` | - | 检查安装健康状态 |
| `/model` | `/m` | 切换模型 |
| `/status` | `/st` | 显示当前状态 |
| `/usage` | - | 显示使用限制 |
| `/agents` | `/agent` | 管理子代理 |
| `/permissions` | `/perm` | 管理权限 |
| `/mcp` | - | 管理 MCP 服务器 |
| `/review` | `/r` | 请求代码审查 |
| `/rewind` | `/rw` | 回退对话 |
| `/vim` | - | Vim 模式 |
| `/init` | - | 初始化项目 |

### 自定义 Slash Commands

支持项目级和用户级自定义命令：

```
# 项目命令目录
.alonechat/commands/

# 用户命令目录
~/.alonechat/commands/
```

支持参数替换（`$ARGUMENTS`, `$1`, `$2`）、Frontmatter 元数据、Bash 执行（`!`前缀）、文件引用（`@`前缀）。

### 会话管理

```bash
# 继续最近的会话
alonechat -C

# 恢复指定会话
alonechat -r <session-id>

# 打印模式（非交互）
alonechat -p "解释这个函数"

# 管道输入
cat file.py | alonechat -p "审查代码"

# JSON 输出格式
alonechat -p "查询" --output-format json
```

### 子代理系统

内置 4 个专业代理：

| 代理 | 功能 |
|------|------|
| `code-reviewer` | 代码审查专家，主动审查代码变更 |
| `debugger` | 调试专家，分析错误和测试失败 |
| `test-writer` | 测试编写专家，编写单元测试和集成测试 |
| `doc-writer` | 文档编写专家，编写技术文档和注释 |

### 权限控制系统

工具级别的权限管理：

```bash
# 查看权限状态
/permissions

# 允许工具
/permissions allow Write

# 拒绝工具
/permissions deny Bash

# 设置模式
/permissions mode accept  # 自动接受所有
```

### MCP 协议集成

Model Context Protocol 服务器管理：

```bash
# 列出 MCP 服务器
alonechat mcp list

# 添加服务器
alonechat mcp add github npx -a @anthropic/mcp-server-github

# 启用/禁用服务器
alonechat mcp enable github
alonechat mcp disable github
```

***

## 快速开始

```bash
# 进入CLI目录
cd alonechat-cli

# 安装依赖
pip install -e .

# 初始化（只需配置API key）
alonechat init

# 启动对话
alonechat chat

# 带初始查询启动
alonechat "解释这个项目"

# 打印模式
alonechat -p "分析这段代码"

# 继续上次会话
alonechat -C

# 索引代码库
alonechat index ./my-project

# 生成测试
alonechat test generate ./my_module.py

# 修复错误
alonechat fix ./broken_code.py

# 查看成本统计
alonechat cost

# MCP 服务器管理
alonechat mcp list
```

***

## Phase 2 功能清单

| 功能 | 说明 | 状态 |
|------|------|------|
| 本地 Embedding | bge-large-zh 等中文模型 | ✅ |
| 代码库索引 | 10万+行，<1秒检索 | ✅ |
| 自动测试生成 | pytest/jest/junit | ✅ |
| 错误自动修复 | 诊断→修复→验证 | ✅ |
| DeepSeek 优化 | 队列/成本/批处理 | ✅ |
| Slash Commands | 15+ 内置命令 | ✅ |
| 会话管理 | 持久化/恢复/继续 | ✅ |
| 打印模式 | -p/--print，管道输入 | ✅ |
| 子代理系统 | 4 个专业代理 | ✅ |
| 权限控制 | 工具级别权限管理 | ✅ |
| MCP 集成 | 服务器配置管理 | ✅ |
| 自定义命令 | 项目/用户级扩展 | ✅ |

***

## 架构变更

### 新增模块

```
alonechat-cli/src/alonechat/
├── session/          # 会话管理
│   ├── storage.py    # 持久化存储
│   └── manager.py    # 会话管理器
├── slash/            # Slash Commands
│   ├── registry.py   # 命令注册表
│   ├── parser.py     # 命令解析器
│   ├── executor.py   # 命令执行器
│   ├── custom_loader.py  # 自定义命令加载
│   └── commands/     # 15+ 内置命令
├── agents/           # 子代理系统
│   ├── definition.py # 代理定义
│   ├── manager.py    # 代理管理器
│   └── executor.py   # 代理执行器
├── permissions/      # 权限系统
│   ├── rules.py      # 权限规则
│   ├── manager.py    # 权限管理器
│   └── prompts.py    # 权限提示
└── mcp/              # MCP 集成
    ├── config.py     # 配置管理
    └── cli.py        # CLI 命令
```

***

**GitHub**: <https://github.com/Ryan-178/AloneChatWorkspace>

**邮箱**: <alonechatworkspace@163.com>
