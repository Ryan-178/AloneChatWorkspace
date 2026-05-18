# 集成测试示例

本目录包含AloneChat CLI与agent-framework集成的测试示例。

## 文件说明

### integration_test.py
完整的集成测试，演示所有主要功能：

- 任务规划 (TaskPlanner)
- 文件处理 (FileProcessors)
- 测试生成 (TestGenerator)
- 错误修复 (ErrorFixer)
- 技能管理 (SkillsRegistry)
- RAG检索 (RAGPipeline)
- 文件生成 (FileGenerators)

## 运行测试

```bash
# 确保已安装依赖
pip install -e ..
pip install -e ../../agent-framework

# 运行集成测试
python integration_test.py
```

## CLI命令示例

### 1. 任务规划

```bash
# 拆解任务
alonechat agent task "分析sales.xlsx并生成季度报告"

# 拆解并执行
alonechat agent task "重构用户认证模块" --execute
```

### 2. 文件处理

```bash
# 处理PDF
alonechat agent process document.pdf

# 处理Word文档
alonechat agent process report.docx --output markdown

# 处理Excel
alonechat agent process data.xlsx --save output.txt
```

### 3. 错误修复

```bash
# 修复运行时错误
alonechat agent fix --error "TypeError: ..." --file my_code.py

# 修复并运行测试
alonechat agent fix --file my_code.py --run-tests
```

### 4. 技能管理

```bash
# 列出所有技能
alonechat agent skill --list

# 运行技能
alonechat agent skill document_generation --run

# 带参数运行
alonechat agent skill data_analysis --run --params '{"data": [...]}'
```

### 5. RAG检索

```bash
# 索引代码库
alonechat agent rag index ./src

# 搜索代码
alonechat agent rag search "用户认证逻辑"

# 指定结果数量
alonechat agent rag search "查询内容" --k 10
```

### 6. 文件生成

```bash
# 生成PPT
alonechat agent generate ppt --request "产品介绍PPT" --output product.pptx

# 生成Excel
alonechat agent generate excel --request "销售数据报表" --output sales.xlsx

# 生成报告
alonechat agent generate report --request "季度报告" --output report.docx
```

### 7. 测试生成

```bash
# 生成测试
alonechat test --file my_code.py

# 生成并运行测试
alonechat test --file my_code.py --run

# 带覆盖率
alonechat test --file my_code.py --coverage

# 指定框架
alonechat test --file app.js --framework jest
```

### 8. 数据分析

```bash
# 分析数据文件
alonechat agent analyze data.xlsx

# 输出为Markdown
alonechat agent analyze sales.csv --output markdown
```

## 预期输出

运行集成测试后，应该看到类似以下输出：

```
============================================================
AloneChat CLI + Agent Framework 集成测试
============================================================

=== 测试任务规划 ===
任务拆解结果: 5 个子任务
  1. 读取Excel文件
  2. 数据清洗和分析
  3. 生成图表
  4. 撰写报告
  5. 导出为Word

=== 测试文件处理 ===
  ✓ .py -> CodeProcessor
  ✓ .xlsx -> SpreadsheetProcessor
  ✓ .docx -> DocumentProcessor
  ✓ .pptx -> PresentationProcessor

=== 测试测试生成 ===
生成了 3 个测试用例
  • test_quick_sort: unit
  • test_edge_cases: edge
  • test_empty_input: edge

=== 测试错误修复 ===
支持 5 种错误类型修复
  • SyntaxError
  • TypeError
  • NameError
  • ImportError
  • AttributeError

=== 测试技能注册表 ===
注册了 5 个技能
  • document_generation: 生成各类文档
  • data_analysis: 数据分析和可视化
  • web_research: 网络调研
  • ppt_generation: PPT演示文稿生成
  • report_generation: 报告生成

=== 测试RAG功能 ===
索引了 10 个文档
找到 5 个相关结果
  1. auth.py (相似度: 0.8923)
  2. user.py (相似度: 0.8456)
  3. login.py (相似度: 0.8234)
  4. session.py (相似度: 0.7892)
  5. middleware.py (相似度: 0.7543)

=== 测试文件生成 ===
支持的生成类型:
  • PPT演示文稿
  • Excel数据报表
  • Word报告文档
  • 代码文件

============================================================
✓ 所有测试通过！
============================================================
```

## 注意事项

1. 确保agent-framework已正确安装
2. 确保配置文件(.alonechatrc)已初始化
3. 确保API密钥已配置
4. 某些功能需要网络连接

## 故障排除

### 问题1: ImportError: agent-framework未安装

**解决方案**:
```bash
cd ../../agent-framework
pip install -e .
```

### 问题2: 无法初始化LLM

**解决方案**:
```bash
alonechat init
# 按提示配置API密钥
```

### 问题3: 测试失败

**解决方案**:
- 检查配置文件
- 检查API密钥是否有效
- 查看错误日志
