# AloneChat CLI 与 Agent Framework 集成说明

## 架构关系

```
┌─────────────────────────────────────────────────────────┐
│                    AloneChat CLI                        │
│  (用户交互层 - 命令行界面)                               │
│  - 命令解析和路由                                        │
│  - 用户界面展示                                          │
│  - 配置管理                                              │
└─────────────────────────────────────────────────────────┘
                          ↓ 调用
┌─────────────────────────────────────────────────────────┐
│                  Agent Framework                        │
│  (核心功能层 - Agent、RAG、工具等)                       │
│  - 4种Agent类型                                          │
│  - 6个服务模块                                           │
│  - 4类工具系统                                           │
│  - RAG功能                                               │
│  - LLM集成                                               │
└─────────────────────────────────────────────────────────┘
```

## 集成策略

**原则**：CLI只负责用户交互，核心功能调用agent-framework

**优势**：
1. ✅ 避免重复开发
2. ✅ 统一维护核心功能
3. ✅ 灵活扩展CLI接口
4. ✅ 最大化代码复用

---

## Agent Framework 核心功能

### 一、Agent类型（4种）

#### 1. ReActAgent（基础Agent）
**文件**: `agent_framework/agent/react_agent.py`

**入口函数**:
```python
agent = ReActAgent(llm=llm, tool_registry=tools, memory=memory)
result = agent.run(task="任务描述")  # 同步执行
async for event in agent.run_stream(task="任务描述"):  # 流式执行
    print(event)
```

**CLI命令映射**:
```bash
alonechat chat  # 默认使用ReActAgent
```

---

#### 2. MultiAgentTeam（多Agent协作）
**文件**: `agent_framework/agent/multi_agent.py`

**入口函数**:
```python
team = MultiAgentTeam()
team.add_agent("agent1", agent1, role="分析师")
team.add_agent("agent2", agent2, role="开发者")
result = team.sequential_discussion(task="任务")  # 顺序讨论
result = team.vote_aggregation(task="任务")  # 投票聚合
```

**CLI命令映射**:
```bash
alonechat agent multi --mode sequential  # 顺序讨论
alonechat agent multi --mode vote        # 投票聚合
```

---

#### 3. MTCAgent（More Than Coding - 面向非开发用户）
**文件**: `agent_framework/agent/mtc_agent.py`

**入口函数**:
```python
agent = MTCAgent(llm=llm)

# 意图澄清
clarification = agent.clarify_intent("帮我写个文档")
if clarification["needs_clarification"]:
    questions = clarification["questions"]  # 最多3个问题
    # 收集用户回答
    agent.collect_clarification_answers(answers)

# 任务规划
plan = agent.plan_task("复杂任务")
progress = agent.get_task_progress()

# 执行
result = agent.run("任务描述")
```

**CLI命令映射**:
```bash
alonechat chat --mode mtc  # MTC模式
alonechat agent task "分析数据并生成报告"  # 任务规划
```

---

#### 4. CodeAgent（面向开发者用户）
**文件**: `agent_framework/agent/code_agent.py`

**入口函数**:
```python
agent = CodeAgent(llm=llm)

# 代码分析
result = await agent.analyze_code(code)

# 代码生成
code = await agent.generate_code(
    description="实现快速排序",
    language="python",
    context="..."
)

# 调试支持
result = await agent.debug_code(
    error_message="TypeError...",
    code_context="..."
)

# 重构
result = await agent.refactor_code(
    code=code,
    refactor_goal="提高性能"
)

# 代码搜索
results = await agent.search_code("用户认证逻辑")

# 执行计划
plan = await agent.create_execution_plan("重构用户模块")
```

**CLI命令映射**:
```bash
alonechat chat --mode code  # Code模式
alonechat generate --type function --name quick_sort
alonechat agent fix --error "TypeError" --file my_code.py
alonechat agent search "用户认证逻辑"
```

---

### 二、服务模块（6个）

#### 1. TaskPlanner（任务规划器）
**文件**: `agent_framework/services/task_planner/planner.py`

**入口函数**:
```python
from agent_framework.services.task_planner import TaskPlanner

planner = TaskPlanner(llm=llm)

# 拆解任务
task_plan = await planner.decompose_task(
    user_request="分析sales.xlsx并生成季度报告",
    context={"workspace_id": "xxx"}
)

# 执行计划
result = await planner.execute_task_plan(
    task_plan=task_plan,
    workspace_id="xxx",
    progress_callback=callback
)
```

**CLI命令映射**:
```bash
alonechat agent task "分析sales.xlsx并生成季度报告" --execute
```

---

#### 2. TestGenerator（测试生成器）
**文件**: `agent_framework/services/test_generator/generator.py`

**入口函数**:
```python
from agent_framework.services.test_generator import TestGenerator

generator = TestGenerator(llm=llm)

# 生成测试
tests = generator.generate_tests(
    source_file="my_code.py",
    framework="pytest",
    test_types=["unit", "edge"]
)

# 写入测试文件
test_files = generator.write_tests(tests, output_dir="./tests")

# 运行测试
result = generator.run_tests(
    test_path="./tests",
    framework="pytest",
    coverage=True
)

# 生成并运行
tests, result = generator.generate_and_run(
    source_file="my_code.py",
    output_dir="./tests",
    framework="pytest"
)
```

**CLI命令映射**:
```bash
alonechat test --file my_code.py --framework pytest
alonechat test --file my_code.py --run
```

---

#### 3. ErrorFixer（错误修复器）
**文件**: `agent_framework/services/error_fixer/fixer.py`

**入口函数**:
```python
from agent_framework.services.error_fixer import ErrorFixer

fixer = ErrorFixer(llm=llm)

# 修复文件
result = fixer.fix_file(
    file_path="my_code.py",
    run_tests=True  # 修复后运行测试
)

# 修复运行时错误
result = fixer.fix_runtime_error(
    file_path="my_code.py",
    error_output="TypeError: ..."
)

# 分析错误模式
patterns = fixer.analyze_error_patterns()
```

**CLI命令映射**:
```bash
alonechat agent fix --error "TypeError" --file my_code.py
alonechat agent fix --file my_code.py --run-tests
```

---

#### 4. FileProcessors（文件处理器）
**文件**: `agent_framework/services/file_processors/`

**入口函数**:
```python
from agent_framework.services.file_processors import get_processor

# 获取处理器
processor = get_processor('.pdf')  # PDF
processor = get_processor('.docx')  # Word
processor = get_processor('.xlsx')  # Excel
processor = get_processor('.pptx')  # PPT
processor = get_processor('.py')   # Python代码

# 解析文件
text = await processor.to_text('document.pdf')

# 生成文件
result = await processor.from_text(
    content="...",
    output_path='output.docx'
)
```

**支持的格式**:
| 处理器 | 支持格式 |
|--------|----------|
| DocumentProcessor | .docx, .pdf |
| SpreadsheetProcessor | .xlsx, .xls, .csv |
| PresentationProcessor | .pptx |
| CodeProcessor | .py, .js, .ts, .java, .go |
| ImageProcessor | .png, .jpg, .jpeg |
| TextProcessor | .txt, .md |

**CLI命令映射**:
```bash
alonechat agent process document.pdf
alonechat agent process report.docx --output markdown
alonechat agent process data.xlsx --analyze
```

---

#### 5. FileGenerators（文件生成器）
**文件**: `agent_framework/services/file_generators/generator_service.py`

**入口函数**:
```python
from agent_framework.services.file_generators import FileGeneratorService

service = FileGeneratorService(llm=llm)

# 生成PPT
ppt_path = await service.generate_ppt(
    user_request="产品介绍PPT",
    context={"product": "..."},
    output_path="output.pptx"
)

# 生成Excel
excel_path = await service.generate_excel(
    user_request="销售数据报表",
    context={"data": [...]},
    output_path="sales.xlsx"
)

# 生成Word报告
doc_path = await service.generate_word_report(
    user_request="季度报告",
    data={...},
    output_path="report.docx"
)

# 生成代码
code = await service.generate_code(
    user_request="实现用户认证",
    language="python",
    context="..."
)

# 分析数据
analysis = await service.analyze_data(
    data=[...],
    user_request="分析销售趋势"
)
```

**CLI命令映射**:
```bash
alonechat agent generate ppt --request "产品介绍PPT"
alonechat agent generate excel --request "销售数据报表"
alonechat agent generate report --request "季度报告"
alonechat generate --type function --name auth
```

---

#### 6. Skills（技能系统）
**文件**: `agent_framework/services/skills/`

**入口函数**:
```python
from agent_framework.services.skills import SkillsRegistry, SkillsExecutor

registry = SkillsRegistry()
executor = SkillsExecutor()

# 注册技能
registry.register(
    name="document_generation",
    description="生成各类文档",
    tools=["file_writer", "template_engine"],
    dependencies=["python-docx"]
)

# 列出技能
skills = registry.list_skills()

# 执行技能
result = await executor.execute(
    skill_name="document_generation",
    context={...}
)
```

**内置技能**:
| 技能名称 | 功能 |
|----------|------|
| DocumentGenerationSkill | 文档生成 |
| DataAnalysisSkill | 数据分析 |
| WebResearchSkill | 网络调研 |
| PPTGenerationSkill | PPT生成 |
| ReportGenerationSkill | 报告生成 |

**CLI命令映射**:
```bash
alonechat agent skill --list
alonechat agent skill document_generation --run
```

---

### 三、工具模块（4类）

#### 1. ToolRegistry（工具注册表）
**文件**: `agent_framework/tools/registry.py`

**入口函数**:
```python
from agent_framework.tools import ToolRegistry

registry = ToolRegistry()

# 注册工具
registry.register(tool)

# 执行工具
result = registry.execute_tool(
    name="code_generator",
    params={"language": "python", "description": "..."}
)

# 列出工具
tools = registry.list_tools()
```

---

#### 2. SkillsRegistry（技能注册表）
**文件**: `agent_framework/tools/skills_registry.py`

**入口函数**:
```python
from agent_framework.tools import SkillsRegistry

registry = SkillsRegistry()

# 注册技能
registry.register(
    name="my_skill",
    description="技能描述",
    tools=["tool1", "tool2"]
)

# 执行技能
result = await registry.execute(
    skill_name="my_skill",
    context={...}
)

# 列出技能
skills = registry.list_skills()
```

---

#### 3. CODE工具集
**文件**: `agent_framework/tools/code/code_tools.py`

**工具列表**:
| 工具名称 | 功能 | CLI命令 |
|----------|------|---------|
| CodeGeneratorTool | 代码生成 | `alonechat generate` |
| CodeExecutionTool | 代码执行 | `alonechat run` |
| DebugAnalyzerTool | 调试分析 | `alonechat agent fix` |
| RefactorTool | 代码重构 | `alonechat agent refactor` |
| TestGeneratorTool | 测试生成 | `alonechat test` |
| LintTool | 代码检查 | `alonechat agent lint` |
| GitTool | Git操作 | `alonechat commit` |
| FileSearchTool | 文件搜索 | `alonechat agent search` |

---

#### 4. MTC工具集
**文件**: `agent_framework/tools/mtc/document_tools.py`

**工具列表**:
| 工具名称 | 功能 | CLI命令 |
|----------|------|---------|
| DocumentGeneratorTool | 文档生成 | `alonechat agent generate doc` |
| DataAnalysisTool | 数据分析 | `alonechat agent analyze` |
| WebSearchTool | 网络搜索 | `alonechat agent search --web` |
| FileReaderTool | 文件读取 | `alonechat agent process` |
| FileWriterTool | 文件写入 | `alonechat agent write` |
| FileListTool | 文件列表 | `alonechat agent list` |
| SummaryGeneratorTool | 摘要生成 | `alonechat agent summarize` |

---

### 四、RAG功能

**文件**: `agent_framework/rag/`

**入口函数**:
```python
from agent_framework.rag import RAGPipeline

pipeline = RAGPipeline(
    embedding_provider="local",  # 本地嵌入
    vector_store="chromadb"      # 本地向量库
)

# 导入文档
count = pipeline.ingest("./src")

# 导入文本
count = pipeline.ingest_text(
    text="...",
    source="file.py"
)

# 检索
results = pipeline.retrieve(
    query="用户认证逻辑",
    k=5
)
```

**核心组件**:
| 模块 | 功能 |
|------|------|
| RAGPipeline | RAG管道主入口 |
| Retriever | 向量检索 |
| EmbeddingProvider | 嵌入向量生成 |
| LocalEmbeddingProvider | 本地嵌入模型 |
| CodeIndexer | 代码索引 |

**CLI命令映射**:
```bash
alonechat agent rag index ./src
alonechat agent rag search "用户认证逻辑"
```

---

### 五、LLM集成

**文件**: `agent_framework/llm/`

**入口函数**:
```python
from agent_framework.llm import LiteLLMProvider

llm = LiteLLMProvider(
    model="deepseek-chat",
    api_key="...",
    base_url="https://api.deepseek.com/v1"
)

# 同步聊天
response = llm.chat(
    messages=[{"role": "user", "content": "..."}],
    config=LLMConfig(temperature=0.7)
)

# 流式聊天
async for chunk in llm.chat_stream(messages, config):
    print(chunk.content)
```

**支持的模型**:
| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| deepseek-chat | ¥0.001/1K | ¥0.002/1K |
| gpt-4o | $0.005/1K | $0.015/1K |
| claude-3-5-sonnet | $0.003/1K | $0.015/1K |

---

### 六、DeepSeek优化系统

**文件**: `agent_framework/deepseek_optimization/`

**核心组件**:
| 模块 | 功能 |
|------|------|
| DeepSeekOptimizer | API调用优化、成本控制 |
| CacheEngine | 语义缓存、向量缓存 |
| MegaContextManager | 百万级上下文管理 |
| ContextCompressor | 上下文压缩 |
| SWEEngine | 软件工程引擎 |
| LicenseManager | 许可证管理 |
| EncryptionManager | 数据加密 |

**入口函数**:
```python
from agent_framework.deepseek_optimization import DeepSeekOptimizer

optimizer = DeepSeekOptimizer(
    api_key="...",
    enable_cache=True,
    max_context_tokens=1000000  # 100万Token
)

# 优化调用
result = await optimizer.optimize_call(
    messages=[...],
    use_cache=True,
    compress_context=True
)
```

---

## CLI命令完整映射表

| CLI命令 | Agent Framework模块 | 入口函数 |
|---------|-------------------|----------|
| `alonechat init` | ConfigManager | 配置初始化 |
| `alonechat chat` | ReActAgent | `run()` |
| `alonechat chat --mode mtc` | MTCAgent | `run()` |
| `alonechat chat --mode code` | CodeAgent | `run()` |
| `alonechat chat --mode multi` | MultiAgentTeam | `sequential_discussion()` |
| `alonechat generate` | FileGenerators | `generate_code()` |
| `alonechat test` | TestGenerator | `generate_tests()` |
| `alonechat commit` | GitTool | 智能提交 |
| `alonechat agent task` | TaskPlanner | `decompose_task()` |
| `alonechat agent fix` | ErrorFixer | `fix_file()` |
| `alonechat agent process` | FileProcessors | `to_text()` |
| `alonechat agent generate` | FileGenerators | `generate_ppt/excel/report()` |
| `alonechat agent skill` | SkillsRegistry | `execute()` |
| `alonechat agent rag` | RAGPipeline | `ingest/retrieve()` |
| `alonechat agent search` | CodeAgent | `search_code()` |
| `alonechat agent refactor` | RefactorTool | 重构代码 |
| `alonechat agent lint` | LintTool | 代码检查 |

---

## 依赖关系

```toml
[project.dependencies]
# CLI核心依赖
click = ">=8.1.0"
rich = ">=13.0.0"

# Agent Framework（本地依赖）
agent-framework = { path = "../agent-framework", develop = true }
```

---

## 使用示例

### 示例1：使用ReActAgent

```bash
# CLI命令
alonechat chat

# 内部调用
# ReActAgent.run() → 思考-行动-观察循环
```

### 示例2：使用MTCAgent

```bash
# CLI命令
alonechat chat --mode mtc

# 内部调用
# MTCAgent.clarify_intent() → 意图澄清
# MTCAgent.plan_task() → 任务规划
# MTCAgent.run() → 执行任务
```

### 示例3：使用任务规划

```bash
# CLI命令
alonechat agent task "分析data.xlsx并生成报告" --execute

# 内部调用
# TaskPlanner.decompose_task() → 任务拆解
# TaskPlanner.execute_task_plan() → 执行计划
```

### 示例4：使用文件处理

```bash
# CLI命令
alonechat agent process report.docx --output pdf

# 内部调用
# get_processor('.docx') → 获取处理器
# processor.to_text() → 解析文件
# processor.from_text() → 生成文件
```

### 示例5：使用测试生成

```bash
# CLI命令
alonechat test --file my_code.py --run

# 内部调用
# TestGenerator.generate_tests() → 生成测试
# TestGenerator.run_tests() → 运行测试
```

---

## 开发指南

### 添加新的CLI命令

1. 在 `alonechat/commands/` 创建命令文件
2. 调用 agent-framework 的对应模块
3. 在 `cli.py` 中注册命令

示例：
```python
# alonechat/commands/my_command.py
import click
from rich.console import Console

console = Console()

@click.command()
@click.pass_obj
def my_command(obj: dict):
    """我的命令"""
    from agent_framework.services.my_service import MyService
    
    service = MyService()
    result = service.do_something()
    
    console.print(result)
```

### 调用Agent Framework

```python
# 直接导入使用
from agent_framework.agent import ReActAgent
from agent_framework.services import TaskPlanner
from agent_framework.tools import ToolRegistry

# 创建实例
agent = ReActAgent(llm=llm, tool_registry=tools)
result = agent.run("任务")
```

---

## 总结

通过集成agent-framework，AloneChat CLI获得了：

1. ✅ **4种Agent类型**：ReAct、Multi、MTC、Code
2. ✅ **6个服务模块**：规划、测试、修复、文件处理、生成、技能
3. ✅ **4类工具系统**：工具注册、技能注册、CODE工具、MTC工具
4. ✅ **完整的RAG功能**：检索、嵌入、索引
5. ✅ **多模型支持**：DeepSeek、GPT、Claude等
6. ✅ **DeepSeek深度优化**：缓存、上下文管理、成本控制

**核心优势**：
- 避免重复开发
- 统一维护核心功能
- 灵活扩展CLI接口
- 最大化代码复用

---

**文档版本**: v1.0  
**更新时间**: 2026-05-16
