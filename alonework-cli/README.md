# AloneChat CLI

国产化、终端原生、深度中文优化的AI编程Agent

## 核心特性

- 🧠 **DeepSeek V4 Flash**：最新一代模型，思考强度最高
- 💾 **上下文缓存**：硬盘缓存命中率高达99.91%，大幅降低成本
- 🔒 **隐私保护**：用户代码完全本地化，不经过云端
- 🚀 **本地优先**：所有核心功能本地运行
- 🇨🇳 **中文优化**：深度中文理解，准确率>92%
- 💰 **成本优势**：无云服务费用，仅API调用成本

## 安装

```bash
pip install alonechat
```

## 快速开始

```bash
# 初始化配置（配置DeepSeek API密钥）
alonechat init

# 启动交互式对话
alonechat chat

# 生成代码
alonechat generate

# 智能提交
alonechat commit

# 自动测试
alonechat test
```

## 模型配置

**固定使用 DeepSeek V4 Flash**

| 参数 | 值 |
|------|-----|
| 模型ID | `deepseek-v4-flash` |
| 思考强度 | `high`（最高） |
| 上下文窗口 | 1,000,000 tokens |
| 缓存命中率 | 99.91% |

### 上下文硬盘缓存

DeepSeek API 上下文硬盘缓存技术对所有用户默认开启，用户无需修改代码即可享用。

**缓存优势**：
- 缓存命中的tokens不计费，大幅降低API成本
- 多轮对话自动复用前缀缓存
- 长文本问答自动识别公共前缀

**缓存命中规则**：
1. **请求结束位置落盘**：每次请求的用户输入结束位置与模型输出结束位置，会产生两个缓存前缀单元
2. **公共前缀检测落盘**：系统检测到多次请求之间存在公共前缀时，自动落盘
3. **固定token间隔落盘**：长输入/输出中按间隔截取缓存前缀单元

### 查看缓存命中情况

API返回的 `usage` 字段包含：
- `prompt_cache_hit_tokens`：缓存命中的tokens数
- `prompt_cache_miss_tokens`：缓存未命中的tokens数

## 配置

配置文件位于 `~/.alonechat/.alonechatrc`

```yaml
version: "2.0"
model:
  provider: deepseek
  name: deepseek-v4-flash
  api_base: https://api.deepseek.com/v1
context:
  max_tokens: 1000000
  compression_enabled: true
privacy:
  code_local: true
  encryption_enabled: true
```

## 数据流设计

```
用户代码 (本地) 
    ↓
Prompt构建 (本地)
    ↓
API调用 (仅发送Prompt，不含代码)
    ↓
代码生成 (本地)
```

**关键点**：
- ✅ 用户代码永远留在本地
- ✅ 只发送Prompt到API
- ✅ 完全隐私保护

## 命令列表

| 命令 | 说明 |
|------|------|
| `alonechat init` | 初始化配置 |
| `alonechat chat` | 交互式对话 |
| `alonechat generate` | 生成代码 |
| `alonechat commit` | 智能提交 |
| `alonechat test` | 自动测试 |
| `alonechat agent` | Agent模式 |

### Agent子命令

| 命令 | 说明 |
|------|------|
| `alonechat agent task` | 执行任务 |
| `alonechat agent process` | 处理文件 |
| `alonechat agent fix` | 修复代码 |
| `alonechat agent skill` | 执行技能 |
| `alonechat agent rag` | RAG检索 |
| `alonechat agent generate` | 生成内容 |
| `alonechat agent analyze` | 分析代码 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/

# 类型检查
mypy src/
```

## 许可证

MIT License
