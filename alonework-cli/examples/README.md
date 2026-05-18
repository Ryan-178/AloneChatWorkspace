# Examples

这个目录包含使用AloneChat CLI的示例代码。

## 示例列表

### 1. basic_usage.py
基础用法示例，展示如何使用SDK进行代码生成和流式输出。

### 2. local_model.py
本地模型示例，展示如何使用Ollama进行完全离线的代码生成。

### 3. multi_turn_chat.py
多轮对话示例，展示如何进行上下文管理和多轮对话。

## 运行示例

```bash
# 确保已安装alonechat
pip install -e ..

# 运行示例
python basic_usage.py
python local_model.py
python multi_turn_chat.py
```

## 注意事项

- 运行前请确保已配置API密钥（运行 `alonechat init`）
- 使用Ollama示例前，请确保Ollama已启动
- 多轮对话示例会消耗较多token，请注意API配额
