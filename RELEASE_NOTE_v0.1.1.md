# AloneChat Workspace v0.1.1

> **从骨架到血肉，这一版开始有了真正的能力。**

---

## 发布语

v0.1.0 搭起了骨架，v0.1.1 开始填充血肉。

这个版本我们做了两件事：一是让 Agent 真正能干活，二是让普通人也能用。

**让 Agent 能干活**：新增多格式文件处理能力，PDF、Word、Excel、PPT、代码文件都能读、能改、能生成。加上 OCR 图片识别，截图里的文字也能提取。配合 Skills 注册系统和任务分解引擎，现在你可以说"帮我分析这个 Excel 并生成报告"，Agent 会自动拆解任务、调用工具、产出结果。

**让普通人也能用**：新增 MTC 模式（More Than Coding）。当用户说"帮我写个文档"，Agent 不再直接瞎写，而是先追问：什么格式？多长？给谁看？通过意图澄清表单收集需求，再执行任务。这是面向非开发用户的设计——不需要懂 Prompt 工程，也能得到满意的结果。

**国际化**：前端支持中英双语切换，基于 next-intl 实现。

还有很多细节：DeepSeek 语义缓存命中率优化、沙箱安全加固、API 文档补全……它们都躺在 commit 记录里。

依然不完美，但比 0.1.0 好了一点。这就是迭代的意义。

---

## 更新内容

### 新增功能

#### 1. 多格式文件处理

支持解析和生成多种文件格式：

| 格式 | 解析 | 生成 | 说明 |
|------|------|------|------|
| PDF | ✅ | ❌ | 基于 PyMuPDF |
| Word (.docx) | ✅ | ✅ | 基于 python-docx |
| Excel (.xlsx) | ✅ | ✅ | 基于 openpyxl |
| PPT (.pptx) | ✅ | ✅ | 基于 python-pptx |
| Code | ✅ | ✅ | 语法高亮 |
| CSV/JSON | ✅ | ✅ | 结构化处理 |

```python
from agent_framework.services.file_processors import get_processor

# 解析任意文件
processor = get_processor('.pdf')
text = await processor.to_text('document.pdf')

# 生成文件
result = await processor.from_text(content, output_path='output.docx')
```

#### 2. OCR 图片识别

支持三种 OCR 引擎：

- **PaddleOCR**（默认）- 中文识别效果最佳
- **Tesseract** - 轻量级，支持多语言
- **EasyOCR** - GPU 加速

```python
processor = get_processor('.png')
text = await processor.to_text('screenshot.png', engine='paddleocr')
```

#### 3. MTC 模式（意图澄清）

面向非开发用户的智能交互模式：

```python
from agent_framework.agent.mtc_agent import MTCAgent

agent = MTCAgent(llm=llm)
clarification = agent.clarify_intent("帮我写个文档")

# 自动生成追问表单
if clarification["needs_clarification"]:
    # {
    #   "questions": [
    #     {"question": "输出格式？", "options": ["Markdown", "Word", "PDF"]},
    #     {"question": "详细程度？", "options": ["简洁", "标准", "详细"]}
    #   ]
    # }
    pass

# 收集用户回答后执行
agent.collect_clarification_answers({"output_format": "Word", "detail_level": "详细"})
result = agent.run("帮我写个文档")
```

#### 4. Skills 注册系统

可扩展的技能注册与执行：

```python
from agent_framework.tools.skills_registry import SkillsRegistry

registry = SkillsRegistry()
registry.register_skill(
    name="document_generation",
    description="生成各类文档",
    tools=["file_writer", "template_engine"],
    workflow="sequential"
)

# 列出所有技能
skills = registry.list_skills()

# 执行技能
result = await registry.execute_skill("document_generation", context)
```

#### 5. 任务分解与执行

自然语言驱动的任务自动分解：

```python
from agent_framework.agent.task_planner import TaskPlanner

planner = TaskPlanner(llm=llm)
plan = planner.decompose("分析 sales.xlsx 并生成季度报告")

# 自动分解为：
# 1. 读取 Excel 文件
# 2. 数据清洗与分析
# 3. 生成图表
# 4. 撰写报告
# 5. 导出为 Word

result = await planner.execute(plan)
```

#### 6. 国际化支持

前端支持中英双语：

- 基于 `next-intl` 实现
- URL 路径带语言前缀（`/zh-CN/chat`、`/en-US/chat`）
- 自动语言检测与切换
- 所有页面文本可翻译

### 改进项

- **DeepSeek 语义缓存**：优化缓存命中率，减少重复 LLM 调用
- **沙箱安全**：增强命令白名单，限制危险操作
- **API 文档**：补全所有端点的 OpenAPI 描述
- **错误处理**：统一错误码和错误消息格式
- **日志系统**：结构化日志，支持链路追踪

### Bug 修复

- 修复 WebSocket 连接断开后会话未清理的问题
- 修复 Multi-Agent 模式下消息路由错误
- 修复 RAG 检索时向量维度不匹配
- 修复文件上传时大文件内存溢出

---

## 与 v0.1.0 对比

| 功能 | v0.1.0 | v0.1.1 |
|------|--------|--------|
| ReAct Agent | ✅ | ✅ |
| Multi-Agent | ✅ | ✅ |
| RAG 检索 | ✅ | ✅ |
| Agent 网关 | ✅ | ✅ |
| DeepSeek 优化 | ✅ | ✅ (改进) |
| MCP 市场 | ✅ | ✅ |
| **多格式文件处理** | ❌ | ✅ |
| **OCR 图片识别** | ❌ | ✅ |
| **MTC 模式** | ❌ | ✅ |
| **Skills 注册** | ❌ | ✅ |
| **任务分解** | ❌ | ✅ |
| **国际化** | ❌ | ✅ |

---

## 升级指南

从 v0.1.0 升级到 v0.1.1：

```bash
git pull origin main
make install  # 安装新依赖
```

新增依赖：
- `paddleocr>=2.7.0` - OCR 引擎
- `python-docx>=0.8.11` - Word 处理
- `openpyxl>=3.1.2` - Excel 处理
- `python-pptx>=0.6.21` - PPT 处理
- `PyMuPDF>=1.23.0` - PDF 处理

---

## 已知问题

- PaddleOCR 首次加载模型较慢（约 10 秒）
- 大文件（>100MB）解析可能超时
- MTC 模式追问次数上限为 3 次（可配置）
- 部分翻译键尚未覆盖

---

## 下一步

v0.2.0 计划：
- 前端 Office 编辑器（Word/Excel/PPT）
- 本地优先文件存储（IndexedDB）
- Agent 对话历史持久化

---

**GitHub**: [https://github.com/xiaodu-duhongrui/AloneChat-workspace.git](https://github.com/xiaodu-duhongrui/AloneChat-workspace.git)
