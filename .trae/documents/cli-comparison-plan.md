# AloneChat CLI 对标 Claude Code 改进计划

## 一、现状分析

### 1.1 AloneChat CLI 当前架构

```
alonechat-cli/
├── cli.py                    # 主入口 (Click框架)
├── commands/
│   ├── init.py              # 初始化配置
│   ├── chat.py              # 交互式对话
│   ├── generate.py          # 代码生成
│   ├── test.py              # 自动测试 (开发中)
│   └── commit.py            # 智能提交
└── utils/
    └── interactive.py       # 交互增强 (CommandRegistry, CommandHistory, AutoCompleter)
```

**当前命令列表：**
| 命令 | 功能 |
|------|------|
| `alonechat init` | 初始化配置，创建.alonechatrc |
| `alonechat chat` | 启动交互式对话 |
| `alonechat generate` | 代码生成 |
| `alonechat test` | 自动测试 (开发中) |
| `alonechat commit` | 智能提交 |

### 1.2 Claude Code CLI 特性概览

**CLI命令：**
| 命令 | 功能 |
|------|------|
| `claude` | 启动交互式REPL |
| `claude "query"` | 带初始提示启动 |
| `claude -p "query"` | SDK查询后退出 |
| `cat file \| claude -p "query"` | 管道输入处理 |
| `claude -c` | 继续最近对话 |
| `claude -r "<session-id>" "query"` | 恢复指定会话 |
| `claude update` | 更新版本 |
| `claude mcp` | MCP配置 |

**CLI标志：**
| 标志 | 功能 |
|------|------|
| `--add-dir` | 添加工作目录 |
| `--agents` | 定义子代理 |
| `--allowedTools` | 允许的工具 |
| `--disallowedTools` | 禁用的工具 |
| `--print, -p` | 打印模式 |
| `--system-prompt` | 替换系统提示 |
| `--output-format` | 输出格式 (text/json/stream-json) |
| `--verbose` | 详细日志 |
| `--max-turns` | 限制代理轮数 |
| `--model` | 设置模型 |
| `--permission-mode` | 权限模式 |
| `--resume/--continue` | 会话恢复 |

**Slash Commands (内置)：**
| 命令 | 功能 |
|------|------|
| `/add-dir` | 添加工作目录 |
| `/agents` | 管理子代理 |
| `/bug` | 报告bug |
| `/clear` | 清除对话历史 |
| `/compact` | 压缩对话 |
| `/config` | 打开设置 |
| `/cost` | 显示token使用统计 |
| `/doctor` | 检查安装健康 |
| `/help` | 帮助 |
| `/init` | 初始化项目 |
| `/login` / `/logout` | 账户管理 |
| `/mcp` | MCP管理 |
| `/memory` | 编辑记忆文件 |
| `/model` | 选择模型 |
| `/permissions` | 查看权限 |
| `/pr_comments` | 查看PR评论 |
| `/review` | 代码审查 |
| `/rewind` | 回退对话 |
| `/status` | 显示状态 |
| `/terminal-setup` | 终端设置 |
| `/usage` | 显示使用限制 |
| `/vim` | vim模式 |

**自定义Slash Commands：**
- 项目命令：`.claude/commands/`
- 个人命令：`~/.claude/commands/`
- 支持参数：`$ARGUMENTS`, `$1`, `$2`
- 支持Bash执行：`!`前缀
- 支持文件引用：`@`前缀
- 支持Frontmatter元数据

---

## 二、差距对比分析

### 2.1 功能差距矩阵

| 功能类别 | Claude Code | AloneChat | 差距等级 |
|----------|-------------|-----------|----------|
| **基础命令** | | | |
| 交互式对话 | ✅ | ✅ | 无 |
| 初始化配置 | ✅ | ✅ | 无 |
| 代码生成 | ✅ | ✅ | 无 |
| 智能提交 | ✅ | ✅ | 无 |
| **会话管理** | | | |
| 继续对话 (-c) | ✅ | ❌ | 高 |
| 恢复会话 (-r) | ✅ | ❌ | 高 |
| 会话ID管理 | ✅ | ❌ | 高 |
| **输入输出** | | | |
| 管道输入 | ✅ | ❌ | 高 |
| 打印模式 (-p) | ✅ | ❌ | 高 |
| JSON输出 | ✅ | ❌ | 中 |
| 流式JSON | ✅ | ❌ | 中 |
| **Slash Commands** | | | |
| 内置命令 | 22+ | 0 | 高 |
| 自定义命令 | ✅ | ❌ | 高 |
| 命令参数 | ✅ | 部分 | 中 |
| Frontmatter | ✅ | ❌ | 中 |
| **代理系统** | | | |
| 子代理 | ✅ | ❌ | 高 |
| 代理定义 | ✅ | ❌ | 高 |
| **权限系统** | | | |
| 工具权限 | ✅ | ❌ | 高 |
| 权限模式 | ✅ | ❌ | 高 |
| **MCP集成** | | | |
| MCP命令 | ✅ | ❌ | 高 |
| MCP配置 | ✅ | ❌ | 高 |
| **辅助功能** | | | |
| 对话压缩 | ✅ | ❌ | 中 |
| 成本跟踪 | ✅ | 部分 | 中 |
| 健康检查 | ✅ | ❌ | 低 |
| 代码审查 | ✅ | ❌ | 中 |
| 回退功能 | ✅ | ❌ | 中 |
| Vim模式 | ✅ | ❌ | 低 |
| **系统提示** | | | |
| 替换系统提示 | ✅ | ❌ | 中 |
| 追加系统提示 | ✅ | ❌ | 中 |
| 文件加载提示 | ✅ | ❌ | 中 |

### 2.2 关键差距详解

#### 高优先级差距

1. **Slash Commands系统**
   - Claude Code: 22+内置命令 + 自定义命令支持
   - AloneChat: 仅有CommandRegistry框架，无实际slash命令
   - 影响: 用户无法在交互会话中执行快捷操作

2. **会话管理**
   - Claude Code: `-c`继续、`-r`恢复、会话ID管理
   - AloneChat: 无会话持久化和恢复
   - 影响: 无法恢复之前的工作上下文

3. **管道输入/打印模式**
   - Claude Code: `cat file | claude -p "query"`
   - AloneChat: 无管道支持
   - 影响: 无法在脚本中集成使用

4. **子代理系统**
   - Claude Code: `--agents`定义、`/agents`管理
   - AloneChat: 无子代理概念
   - 影响: 无法分配专门任务给专门代理

5. **权限系统**
   - Claude Code: `--allowedTools`、`/permissions`
   - AloneChat: 无权限控制
   - 影响: 安全性和控制力不足

6. **MCP集成**
   - Claude Code: 完整MCP支持
   - AloneChat: 无MCP命令
   - 影响: 无法扩展外部工具

---

## 三、改进实施计划

### 阶段一：核心CLI增强 (优先级: 高)

#### 3.1.1 添加打印模式 (-p/--print)
**文件**: `alonechat-cli/src/alonechat/cli.py`
**实现**:
- 添加 `--print, -p` 标志
- 非交互模式下执行查询后退出
- 支持管道输入读取

#### 3.1.2 添加会话管理
**新文件**: `alonechat-cli/src/alonechat/session/`
**实现**:
- `SessionManager` - 会话管理器
- `--continue, -c` - 继续最近会话
- `--resume, -r <session-id>` - 恢复指定会话
- 会话存储: `~/.alonechat/sessions/`

#### 3.1.3 添加输出格式支持
**文件**: `alonechat-cli/src/alonechat/cli.py`
**实现**:
- `--output-format` 标志 (text/json/stream-json)
- JSON格式化输出
- 流式JSON输出

### 阶段二：Slash Commands系统 (优先级: 高)

#### 3.2.1 创建Slash Commands框架
**新文件**: `alonechat-cli/src/alonechat/slash/`
```
slash/
├── __init__.py
├── registry.py      # 命令注册表
├── parser.py        # 命令解析器
├── executor.py      # 命令执行器
└── commands/        # 内置命令
    ├── __init__.py
    ├── clear.py
    ├── compact.py
    ├── config.py
    ├── cost.py
    ├── doctor.py
    ├── help.py
    ├── model.py
    ├── review.py
    ├── status.py
    └── usage.py
```

#### 3.2.2 实现内置Slash Commands
| 命令 | 实现文件 | 功能 |
|------|----------|------|
| `/clear` | clear.py | 清除对话历史 |
| `/compact` | compact.py | 压缩对话上下文 |
| `/config` | config.py | 打开配置界面 |
| `/cost` | cost.py | 显示token使用统计 |
| `/doctor` | doctor.py | 检查安装健康状态 |
| `/help` | help.py | 显示帮助信息 |
| `/model` | model.py | 切换模型 |
| `/review` | review.py | 请求代码审查 |
| `/status` | status.py | 显示当前状态 |
| `/usage` | usage.py | 显示使用限制 |

#### 3.2.3 支持自定义Slash Commands
**实现**:
- 项目命令目录: `.alonechat/commands/`
- 用户命令目录: `~/.alonechat/commands/`
- 参数解析: `$ARGUMENTS`, `$1`, `$2`
- Frontmatter解析: YAML格式元数据

### 阶段三：代理与权限系统 (优先级: 高)

#### 3.3.1 子代理系统
**新文件**: `alonechat-cli/src/alonechat/agents/`
```
agents/
├── __init__.py
├── manager.py       # 代理管理器
├── definition.py    # 代理定义
└── executor.py      # 代理执行器
```
**CLI支持**:
- `--agents` 标志定义代理
- `/agents` 命令管理代理

#### 3.3.2 权限系统
**新文件**: `alonechat-cli/src/alonechat/permissions/`
```
permissions/
├── __init__.py
├── manager.py       # 权限管理器
├── rules.py         # 权限规则
└── prompts.py       # 权限提示
```
**CLI支持**:
- `--allowedTools` 标志
- `--disallowedTools` 标志
- `--permission-mode` 标志
- `/permissions` 命令

### 阶段四：MCP集成 (优先级: 中)

#### 3.4.1 MCP CLI命令
**新文件**: `alonechat-cli/src/alonechat/mcp/`
```
mcp/
├── __init__.py
├── cli.py           # MCP CLI命令
├── config.py        # MCP配置
└── commands.py      # MCP slash命令
```
**CLI支持**:
- `alonechat mcp` 命令
- `/mcp` slash命令

### 阶段五：辅助功能 (优先级: 中/低)

#### 3.5.1 系统提示定制
- `--system-prompt` 替换系统提示
- `--system-prompt-file` 从文件加载
- `--append-system-prompt` 追加提示

#### 3.5.2 其他功能
- `/rewind` 回退功能
- `/vim` vim模式
- `/terminal-setup` 终端设置
- `/bug` bug报告

---

## 四、实施步骤

### Step 1: 打印模式与会话管理
1. 修改 `cli.py` 添加 `-p/--print` 标志
2. 创建 `session/` 模块
3. 实现会话持久化存储
4. 添加 `-c/--continue` 和 `-r/--resume` 标志

### Step 2: Slash Commands框架
1. 创建 `slash/` 模块结构
2. 实现命令注册、解析、执行
3. 实现10个核心内置命令
4. 集成到 `chat.py` 交互会话

### Step 3: 自定义命令支持
1. 实现项目/用户命令目录扫描
2. 实现参数替换 (`$ARGUMENTS`, `$1`)
3. 实现Frontmatter解析
4. 实现Bash执行 (`!`前缀)

### Step 4: 代理系统
1. 创建 `agents/` 模块
2. 实现代理定义和执行
3. 添加 `--agents` 标志
4. 实现 `/agents` 命令

### Step 5: 权限系统
1. 创建 `permissions/` 模块
2. 实现工具权限控制
3. 添加权限相关CLI标志
4. 实现 `/permissions` 命令

### Step 6: MCP集成
1. 创建 `mcp/` CLI模块
2. 实现 `alonechat mcp` 命令
3. 实现 `/mcp` slash命令
4. 集成现有MCP框架

### Step 7: 辅助功能
1. 实现系统提示定制标志
2. 实现 `/rewind` 回退
3. 实现 `/vim` 模式
4. 实现其他辅助命令

---

## 五、文件变更清单

### 新增文件
```
alonechat-cli/src/alonechat/
├── session/
│   ├── __init__.py
│   ├── manager.py
│   └── storage.py
├── slash/
│   ├── __init__.py
│   ├── registry.py
│   ├── parser.py
│   ├── executor.py
│   └── commands/
│       ├── __init__.py
│       ├── clear.py
│       ├── compact.py
│       ├── config.py
│       ├── cost.py
│       ├── doctor.py
│       ├── help.py
│       ├── model.py
│       ├── review.py
│       ├── status.py
│       └── usage.py
├── agents/
│   ├── __init__.py
│   ├── manager.py
│   ├── definition.py
│   └── executor.py
├── permissions/
│   ├── __init__.py
│   ├── manager.py
│   ├── rules.py
│   └── prompts.py
└── mcp/
    ├── __init__.py
    ├── cli.py
    └── commands.py
```

### 修改文件
```
alonechat-cli/src/alonechat/
├── cli.py              # 添加新标志和命令
└── commands/
    └── chat.py         # 集成slash commands
```

---

## 六、验收标准

### 功能验收
- [ ] `alonechat -p "query"` 正确执行并退出
- [ ] `cat file | alonechat -p "query"` 正确处理管道输入
- [ ] `alonechat -c` 正确继续最近会话
- [ ] `alonechat -r "session-id"` 正确恢复指定会话
- [ ] `/clear` 正确清除对话历史
- [ ] `/compact` 正确压缩对话
- [ ] `/cost` 正确显示token统计
- [ ] `/doctor` 正确检查健康状态
- [ ] `/help` 正确显示帮助
- [ ] `/model` 正确切换模型
- [ ] `/status` 正确显示状态
- [ ] 自定义命令正确加载和执行
- [ ] `--agents` 正确定义子代理
- [ ] `--allowedTools` 正确控制权限
- [ ] `--output-format json` 正确输出JSON

### 质量验收
- [ ] 所有新代码有对应测试
- [ ] 代码覆盖率 > 80%
- [ ] 无安全漏洞
- [ ] 文档完整

---

## 七、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Click框架限制 | 中 | 评估是否需要迁移到其他框架 |
| 会话存储性能 | 低 | 使用增量存储、压缩 |
| 权限系统复杂度 | 中 | 分阶段实现，先基础后高级 |
| MCP兼容性 | 中 | 复用现有agent-framework的MCP实现 |

---

## 八、时间估算

| 阶段 | 预估工作量 |
|------|------------|
| 阶段一：核心CLI增强 | 中 |
| 阶段二：Slash Commands | 高 |
| 阶段三：代理与权限 | 高 |
| 阶段四：MCP集成 | 中 |
| 阶段五：辅助功能 | 低 |
| **总计** | 高 |
