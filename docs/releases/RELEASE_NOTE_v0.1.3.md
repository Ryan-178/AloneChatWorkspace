# AloneChat Workspace v0.1.3

> **专注一个模型，做到极致。**

***

## 发布语

v0.1.2 扎下了根基，v0.1.3 找到了方向。

这个版本我们做了一件大事：**专注 DeepSeek V4 Flash，深度优化**。

**移除选择，专注体验**：我们移除了所有模型选择选项，固定使用 DeepSeek V4 Flash。不再让用户纠结选哪个模型，而是把这一个模型用到极致。reasoning\_effort=high 的思考模式默认开启，让每一次对话都有深度推理。

**思考模式支持**：DeepSeek V4 Flash 的思考能力被充分释放。reasoning\_content 返回完整的思考过程，用户可以通过 --show-reasoning 查看模型是如何一步步得出结论的。这是透明，也是信任。

**多轮对话与缓存**：正确实现上下文拼接，支持 DeepSeek 的硬盘缓存机制。缓存命中率可达 99.98%，这意味着后续对话几乎不需要重新计算前文，响应更快，成本更低。

**中文深度优化**：中文 NLP 分词、实体识别、语义分析；命名建议、注释生成、代码风格检查。让中文开发者有原生的体验。

**智能 Git 集成**：自动分析代码变更，生成规范的 commit message。支持 AI 增强建议，让每一次提交都有意义。

还有很多细节：AES-256-GCM 代码加密、100万 Token 上下文、多语言代码生成……它们都躺在 `alonechat-cli` 目录里。

依然不完美，但比 0.1.2 专注了一点。这就是减法的意义。

***

**快速开始**：

```bash
# 进入CLI目录
cd alonechat-cli

# 安装依赖
pip install -e .

# 初始化（只需配置API key）
alonechat init

# 启动对话
alonechat chat

# 显示思考过程
alonechat chat --show-reasoning

# 生成代码
alonechat generate -t function -n my_func

# 智能提交
alonechat commit
```

***

**GitHub**: <https://github.com/Ryan-178/AloneChatWorkspace>

**邮箱**: <alonechatworkspace@163.com>
