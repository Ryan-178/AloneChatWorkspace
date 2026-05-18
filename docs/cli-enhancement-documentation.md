# AloneChat CLI 增强功能文档 / CLI Enhancement Documentation

## 概述 / Overview

本文档记录了 AloneChat CLI 对标 Claude Code 的功能增强 / This document records AloneChat CLI enhancements aligned with Claude Code

---

## 功能列表 / Feature List

### 1. 自动对话压缩 / Auto Conversation Compression

**版本 / Version:** `0.2.47`

**功能描述 / Description:**
- 支持无限长度对话 / Support unlimited length conversation
- 智能压缩对话历史 / Smart compress conversation history
- AI智能摘要 / AI smart summarization
- 可配置压缩策略 / Configurable compression strategy

**使用方法 / Usage:**

```bash
# 启用自动压缩 / Enable auto compact
alonechat --auto-compact

# 设置压缩阈值 / Set compact threshold
alonechat --auto-compact --compact-threshold 50

# 手动压缩 / Manual compact
/compact                    # 智能压缩 / Smart compact
/compact --aggressive       # 激进压缩 / Aggressive compact
/compact --summary          # 显示压缩摘要 / Show compression summary
/compact --auto             # 启用自动压缩 / Enable auto compact
/compact "保留关键决策"      # 带指令压缩 / Compact with instructions
```

**相关文件 / Related Files:**
- [alonechat/slash/commands/compact.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/compact.py)
- [agent_framework/deepseek_optimization/context/context_compressor.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/deepseek_optimization/context/context_compressor.py)

---

### 2. 分叉对话 / Fork Conversation

**版本 / Version:** `2.1.77`

**功能描述 / Description:**
- `/fork` 从当前点创建新分支 / Create new branch from current point
- `/branch` 管理会话分支 / Manage session branches
- 保留原会话历史 / Preserve original session history
- 支持指定分叉点 / Support specifying branch point

**使用方法 / Usage:**

```bash
# 斜杠命令 / Slash commands
/fork                       # 创建分支，自动命名 / Create branch with auto name
/fork "实验性修改"           # 创建分支并命名 / Create named branch
/fork --at 5                # 从第5条消息处创建分支 / Create branch from message 5

/branch                     # 列出所有分支 / List all branches
/branch new "修复方案A"     # 创建新分支 / Create new branch
/branch switch abc123       # 切换到分支 / Switch to branch
/branch delete abc123       # 删除分支 / Delete branch
```

**相关文件 / Related Files:**
- [alonechat/slash/commands/fork.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/commands/fork.py)
- [alonechat/session/storage.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/storage.py) - Session.fork() 方法
- [alonechat/session/manager.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/session/manager.py) - fork_session() 方法

---

### 3. 技能自动热重载 / Skills Hot Reload

**版本 / Version:** `2.1.0`

**功能描述 / Description:**
- 自动检测技能文件变化 / Auto detect skill file changes
- 无需重启服务 / No service restart needed
- 支持Python和YAML文件 / Support Python and YAML files
- 变更事件回调 / Change event callbacks

**使用方法 / Usage:**

```python
from agent_framework.tools.skills_hot_reload import SkillsHotReloader

# 创建热重载器 / Create hot reloader
reloader = SkillsHotReloader(skills_registry, skills_dir)

# 注册回调 / Register callback
reloader.on_reload(lambda event: print(f"Skill {event.skill_name} reloaded"))

# 开始监视 / Start watching
reloader.start()

# 强制重载 / Force reload
reloader.force_reload("my_skill")

# 停止监视 / Stop watching
reloader.stop()
```

**相关文件 / Related Files:**
- [agent_framework/tools/skills_hot_reload.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_hot_reload.py)

---

### 4. 斜杠命令与技能合并 / Slash Commands & Skills Merge

**版本 / Version:** `2.1.3`

**功能描述 / Description:**
- 技能可作为斜杠命令调用 / Skills can be invoked as slash commands
- 斜杠命令可作为技能管理 / Slash commands can be managed as skills
- 统一的注册和发现 / Unified registration and discovery
- 简化心智模型 / Simplified mental model

**使用方法 / Usage:**

```python
from alonechat.slash.command_skill_bridge import create_bridge

# 创建桥接器 / Create bridge
bridge = create_bridge(skills_registry, slash_registry)

# 统一调用 / Unified execution
bridge.execute("compact", args=["--auto"])
bridge.execute("data_analysis", args=["--type", "summary"])

# 搜索命令 / Search commands
results = bridge.search("data")

# 获取补全 / Get completions
completions = bridge.get_completions("/com")
```

**相关文件 / Related Files:**
- [alonechat/slash/command_skill_bridge.py](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/slash/command_skill_bridge.py)

---

### 5. 输出样式调整 / Output Style Adjustment

**版本 / Version:** `2.0.32`

**功能描述 / Description:**
- 根据社区反馈恢复弃用样式 / Restore deprecated styles based on community feedback
- 多主题支持 / Multiple theme support
- 可配置输出格式 / Configurable output format
- 可访问性支持 / Accessibility support

**配置文件 / Config File:**
- [alonechat/configs/output_style.yaml](file:///e:/AloneChat-workspace-master/alonechat-cli/src/alonechat/configs/output_style.yaml)

**使用方法 / Usage:**

```python
from alonechat.configs.style_loader import get_style_config, format_message_prefix

# 获取样式配置 / Get style config
config = get_style_config()

# 获取消息前缀 / Get message prefix
prefix = format_message_prefix("user")  # 👤
prefix = format_message_prefix("assistant")  # 🤖

# 获取主题配置 / Get theme config
theme = config.theme
```

**恢复的弃用样式 / Restored Deprecated Styles:**
- `classic_progress`: 经典进度条 / Classic progress bar
- `simple_table`: 简单表格 / Simple table
- `plain_text`: 纯文本输出 / Plain text output
- `no_icon_message`: 无图标消息 / Message without icons

---

### 6. 插件商店搜索增强 / Plugin Store Search Enhancement

**版本 / Version:** `2.0.73`

**功能描述 / Description:**
- 按名称搜索 / Search by name
- 按描述搜索 / Search by description
- 按市场过滤 / Filter by marketplace
- 多条件组合搜索 / Multi-condition combined search
- 排序和分页 / Sorting and pagination

**使用方法 / Usage:**

```python
from agent_framework.tools.skills_marketplace import SkillsMarketplace, SearchFilter, SortBy

marketplace = SkillsMarketplace(registry)

# 按名称搜索 / Search by name
results = marketplace.search_by_name("data")

# 按描述搜索 / Search by description
results = marketplace.search_by_description("analysis")

# 按市场搜索 / Search by marketplace
results = marketplace.search_by_marketplace("github")

# 高级搜索 / Advanced search
results = marketplace.advanced_search(
    filter=SearchFilter(
        name="data",
        category="analysis",
        min_rating=4.0,
    ),
    sort_by=SortBy.RATING,
    limit=20,
)

# 组合搜索 / Combined search
results = marketplace.search_combined("react", search_in=["name", "description", "tags"])
```

**相关文件 / Related Files:**
- [agent_framework/tools/skills_marketplace.py](file:///e:/AloneChat-workspace-master/agent-framework/agent_framework/tools/skills_marketplace.py)

---

### 7. --name CLI参数 / --name CLI Parameter

**版本 / Version:** `2.1.76`

**功能描述 / Description:**
- 启动时设置会话显示名称 / Set session display name at startup
- 便于识别和管理会话 / Easy session identification and management

**使用方法 / Usage:**

```bash
# 设置会话名称 / Set session name
alonechat --name "我的开发会话"

# 结合其他参数使用 / Use with other parameters
alonechat --name "Bug修复" --auto-compact
```

---

### 8. --agent CLI标志 / --agent CLI Flag

**版本 / Version:** `2.0.59`

**功能描述 / Description:**
- 覆盖当前会话的代理设置 / Override agent settings for current session
- 支持多个配置项 / Support multiple config items

**使用方法 / Usage:**

```bash
# 覆盖模型设置 / Override model setting
alonechat --agent model=deepseek-v3

# 多个配置项 / Multiple config items
alonechat --agent model=deepseek-v3,temperature=0.7,max_tokens=4000

# 结合会话名称 / With session name
alonechat --name "测试会话" --agent model=deepseek-v3
```

---

## 完整命令行参数列表 / Complete CLI Parameters

```bash
alonechat [OPTIONS] [QUERY]

选项 / Options:
  --config PATH              配置文件路径 / Config file path
  -v, --verbose              详细输出 / Verbose output
  -p, --print                打印模式（非交互）/ Print mode (non-interactive)
  -C, --continue             继续最近的会话 / Continue latest session
  -r, --resume ID            恢复指定会话 / Resume specific session
  --output-format FORMAT     输出格式 (text/json/stream-json) / Output format
  -m, --model NAME           指定模型 / Specify model
  --system-prompt TEXT       替换系统提示 / Replace system prompt
  --append-system-prompt TEXT 追加系统提示 / Append system prompt
  --name NAME                设置会话显示名称 (v2.1.76) / Set session display name
  --agent CONFIG             覆盖代理设置 (v2.0.59) / Override agent settings
  --auto-compact             启用自动对话压缩 (v0.2.47) / Enable auto compact
  --compact-threshold N      自动压缩阈值（默认100）/ Auto compact threshold

子命令 / Subcommands:
  init                       初始化项目配置 / Initialize project config
  chat                       启动交互式对话 / Start interactive chat
  generate                   代码生成 / Code generation
  test                       自动测试 / Auto testing
  commit                     智能提交 / Smart commit
  mcp                        MCP服务器管理 / MCP server management
  agent                      Agent管理 / Agent management
```

---

## 斜杠命令列表 / Slash Commands List

| 命令 | 别名 | 版本 | 描述 |
|------|------|------|------|
| `/fork` | - | 2.1.77 | 分叉当前会话 |
| `/branch` | branches | 2.1.77 | 管理会话分支 |
| `/compact` | - | 0.2.47 | 压缩对话上下文 |
| `/clear` | cls | - | 清除对话历史 |
| `/rewind` | rw | - | 回退对话 |
| `/agents` | agent | - | 管理子代理 |
| `/config` | cfg | - | 打开配置界面 |
| `/model` | m | - | 切换模型 |
| `/permissions` | perm | - | 管理权限 |
| `/mcp` | - | - | 管理MCP服务器 |
| `/init` | - | - | 初始化项目 |
| `/review` | r | - | 请求代码审查 |
| `/status` | st | - | 显示当前状态 |
| `/cost` | - | - | 显示token使用统计 |
| `/usage` | - | - | 显示使用限制 |
| `/doctor` | - | - | 检查安装健康状态 |
| `/help` | h, ? | - | 显示帮助信息 |
| `/vim` | - | - | Vim模式 |

---

## 文件变更摘要 / File Changes Summary

### 新增文件 / New Files

1. `alonechat-cli/src/alonechat/slash/commands/fork.py` - 分叉对话命令
2. `alonechat-cli/src/alonechat/slash/command_skill_bridge.py` - 命令技能桥接器
3. `alonechat-cli/src/alonechat/configs/output_style.yaml` - 输出样式配置
4. `alonechat-cli/src/alonechat/configs/style_loader.py` - 样式配置加载器
5. `agent-framework/agent_framework/tools/skills_hot_reload.py` - 技能热重载

### 修改文件 / Modified Files

1. `alonechat-cli/src/alonechat/cli.py` - 添加新CLI参数
2. `alonechat-cli/src/alonechat/session/storage.py` - Session增强
3. `alonechat-cli/src/alonechat/session/manager.py` - 会话管理器增强
4. `alonechat-cli/src/alonechat/slash/commands/__init__.py` - 导出新命令
5. `alonechat-cli/src/alonechat/slash/commands/compact.py` - 压缩功能增强
6. `alonechat-cli/src/alonechat/slash/executor.py` - 注册新命令
7. `alonechat-cli/src/alonechat/commands/chat.py` - 集成新功能
8. `agent-framework/agent_framework/tools/skills_marketplace.py` - 搜索功能增强

---

## 版本兼容性 / Version Compatibility

| 功能 | 最低版本 | 推荐版本 |
|------|----------|----------|
| 自动对话压缩 | 0.2.47 | 0.2.47+ |
| 分叉对话 | 2.1.77 | 2.1.77+ |
| 技能热重载 | 2.1.0 | 2.1.0+ |
| 斜杠命令与技能合并 | 2.1.3 | 2.1.3+ |
| 输出样式调整 | 2.0.32 | 2.0.32+ |
| 插件商店搜索 | 2.0.73 | 2.0.73+ |
| --name参数 | 2.1.76 | 2.1.76+ |
| --agent标志 | 2.0.59 | 2.0.59+ |
