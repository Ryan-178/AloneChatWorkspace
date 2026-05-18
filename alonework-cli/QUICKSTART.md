# AloneChat CLI 快速开始指南

## 🚀 5分钟快速开始

### 1. 安装

```bash
# 进入项目目录
cd alonechat-cli

# 安装依赖
pip install -e .
```

### 2. 初始化配置

```bash
# 运行初始化命令
alonechat init
```

按照提示：
1. 输入API密钥（支持DeepSeek、Qwen、混元、GLM）
2. 选择默认模型
3. 配置文件将创建在 `.alonechatrc`

### 3. 开始使用

#### 交互式对话

```bash
alonechat chat
```

示例对话：
```
You: 帮我写一个Python函数，计算斐波那契数列

AloneChat: 好的，这是一个计算斐波那契数列的Python函数：

def fibonacci(n: int) -> int:
    """
    计算斐波那契数列的第n项
    
    Args:
        n: 项数（从0开始）
    
    Returns:
        斐波那契数列的第n项
    """
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b
```

#### 代码生成

```bash
# 生成函数
alonechat generate --type function --name my_function

# 生成类
alonechat generate --type class --name MyClass

# 生成模块
alonechat generate --type module --name my_module
```

## 📝 配置示例

### .alonechatrc 配置文件

```toml
version = "1.0"

[model]
default = "deepseek"

[model.providers.deepseek]
api_key = ""  # 通过alonechat init设置
base_url = "https://api.deepseek.com/v1"
model = "deepseek-chat"

[model.providers.qwen]
api_key = ""
base_url = "https://dashscope.aliyuncs.com/api/v1"
model = "qwen-max"

[model.providers.ollama]
base_url = "http://localhost:11434"
model = "deepseek-coder:6.7b"

[context]
max_tokens = 128000
compression_enabled = true

[privacy]
code_local = true
api_prompt_only = true
log_enabled = false
```

### 环境变量配置

```bash
# 在 .env 文件中设置
DEEPSEEK_API_KEY=your_api_key
QWEN_API_KEY=your_api_key
HUNYUAN_API_KEY=your_api_key
GLM_API_KEY=your_api_key
```

## 🔧 高级用法

### 使用不同模型

```bash
# 使用Qwen模型
alonechat chat --model qwen

# 使用本地Ollama模型
alonechat chat --model ollama
```

### 调整上下文窗口

```bash
# 设置上下文窗口为64K
alonechat chat --context 64000
```

### 指定配置文件

```bash
alonechat --config /path/to/config.toml chat
```

## 🌐 离线使用（Ollama）

### 1. 安装Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull deepseek-coder:6.7b
```

### 2. 启动Ollama

```bash
ollama serve
```

### 3. 使用本地模型

```bash
alonechat chat --model ollama
```

## 🔒 隐私保护

AloneChat 采用严格的隐私保护策略：

1. **代码本地化**：所有代码文件都在本地处理，不上传到云端
2. **API调用仅含Prompt**：只发送用户输入的Prompt到API，不发送代码
3. **本地加密存储**：API密钥使用本地加密存储
4. **离线可用**：支持Ollama等本地模型，完全离线运行

## 📚 下一步

- 查看 [完整文档](./README.md)
- 了解 [市场调研报告](../AI_Agent_Market_Research_Report.md)
- 查看 [实施计划](../.trae/documents/AloneChat_AI_Agent_Implementation_Plan.md)

## ❓ 常见问题

### Q: 如何获取API密钥？

**DeepSeek**：访问 https://platform.deepseek.com/ 注册获取

**Qwen**：访问 https://dashscope.aliyun.com/ 注册获取

**混元**：访问 https://cloud.tencent.com/product/hunyuan 注册获取

**GLM**：访问 https://open.bigmodel.cn/ 注册获取

### Q: 支持哪些编程语言？

目前支持：
- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- 更多语言支持开发中

### Q: 如何切换模型？

```bash
# 方法1：命令行参数
alonechat chat --model qwen

# 方法2：修改配置文件
# 编辑 .alonechatrc，修改 model.default
```

### Q: 如何查看详细日志？

```bash
alonechat --verbose chat
```

## 🐛 问题反馈

如果遇到问题，请：
1. 检查配置文件是否正确
2. 确认API密钥是否有效
3. 查看错误信息
4. 提交Issue到GitHub

---

**祝您使用愉快！** 🎉
