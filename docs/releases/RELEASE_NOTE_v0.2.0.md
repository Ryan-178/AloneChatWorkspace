# AloneChat Workspace v0.2.0

> **核心功能增强，智能更进一步。**

***

## 发布语

v0.1.3 找到了方向，v0.2.0 夯实了能力。

这个版本我们完成了 **Phase 2 核心功能增强**，让 AloneChat 从"能用"变成"好用"。

**代码库智能索引**：本地 Embedding 支持，无需上传代码到云端。bge-large-zh、text2vec-large-chinese 等中文优化模型开箱即用。索引 10 万行代码，检索响应 < 1 秒。隐私保护，从索引开始。

**自动测试生成**：写完代码，测试自动来。支持 pytest、jest 两大框架。单元测试、集成测试、边缘用例，一键生成。测试覆盖率 > 80%，让每一行代码都有保障。

**错误自动修复**：编译报错、运行时异常，AI 帮你修。语法错误、类型错误、导入错误，智能诊断。修复→测试→验证，循环迭代直到干净。常见错误修复成功率 > 70%。

**多格式文件处理**：7 种文件格式双向转换。PDF、Word、Excel、PPT、图片、代码、文本，通吃。OCR 图片识别，文字提取不再依赖手动输入。

**Skills 技能系统**：5 大内置技能，从文档生成到数据分析，从网络调研到报告编写。支持从 GitHub 和 skills.sh 远程安装社区技能。技能热加载，无需重启。

**DeepSeek V4 深度优化**：请求队列管理，优先级调度。成本控制器，预算不超标。批处理合并请求，效率翻倍。智能重试与降级策略，服务稳定可靠。99.98% 缓存命中率，成本降低 90%+。

**CLI 全面升级**：29 个 Slash 命令，全面对标 Claude Code。会话持久化管理，断点续聊。打印模式与管道输入，脚本集成友好。子代理系统，4 个专业代理随叫随到。权限控制系统，安全可靠。MCP 协议集成，扩展无限可能。

**进阶终端体验**：逐行流式输出，响应生成即可见。OSC 8 可点击文件链接，路径直接打开。Ctrl+O 实时思维块，模型思考过程一目了然。自定义状态栏，打造专属终端提示符。Vim 模式增强，30+ 键绑定。中/日/韩 IME 支持，输入法窗口正确定位。终端通知支持 iTerm2、Kitty、Ghostty，tmux 内也可运行。

**权限与安全升级**：通配符权限规则，`Bash(npm *)` 精细控制。输出重定向感知，`python script.py > out` 正常匹配。沙箱模式正式发布，Linux、macOS、Windows 全平台覆盖。macOS plist 与 Windows 注册表受管设置，企业策略统一下发。OAuth 令牌存储到系统 Keychain，凭据安全有保障。

**CLI 增强基础设施**：Git 工作树隔离启动，不影响主仓库变更。附加目录加载技能、插件、CLAUDE.md。嵌套技能自动发现，.claude/skills/ 目录无需手工注册。条件性规则加载，不同项目类型自动匹配不同规则。CLAUDE.md 支持 @import 文件导入，知识管理更灵活。

**桌面版初登场**：Tauri + Next.js 16 桌面雏形，后端 Rust 性能强劲，前端 React 灵活高效。

还有很多细节：增量索引更新、多语言代码解析、修复历史追踪、Skills 技能市场、自定义 Slash Commands……它们都躺在 `agent-framework` 和 `alonechat-cli` 目录里。

依然在路上，但比 0.1.3 强大了一点。这就是积累的意义。

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

**GitHub**: <https://github.com/Ryan-178/AloneChatWorkspace>

**邮箱**: <alonechatworkspace@163.com>
