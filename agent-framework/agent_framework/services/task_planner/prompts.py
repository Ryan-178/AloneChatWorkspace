"""
任务规划 Prompt 模板
"""

TASK_DECOMPOSITION_PROMPT = """你是一个任务规划专家。请将用户的自然语言需求拆解为可执行的子任务。

用户需求：{user_request}

请按照以下 JSON 格式输出任务分解：

```json
{
  "main_task": "主任务描述",
  "subtasks": [
    {
      "id": "task_1",
      "name": "子任务名称",
      "description": "详细描述",
      "skill": "使用的技能",
      "tools": ["需要的工具"],
      "dependencies": ["依赖的任务ID"],
      "estimated_steps": 3,
      "output_type": "输出类型"
    }
  ],
  "execution_order": ["task_1", "task_2", ...],
  "final_output": "最终交付物描述"
}
```

可用的技能：
- web_reading: 网页读取和信息提取
- data_analysis: 数据分析和可视化
- document_generation: 文档生成
- presentation_generation: PPT生成
- spreadsheet_generation: Excel生成
- file_conversion: 文件格式转换
- research: 信息调研
- code_generation: 代码生成
- ocr_processing: OCR文字识别

可用的工具：
- file_reader: 读取文件
- file_writer: 写入文件
- web_search: 网络搜索
- data_processor: 数据处理
- chart_generator: 图表生成
- api_caller: API调用
- ocr: OCR识别

请确保：
1. 任务拆解合理，每个子任务目标明确
2. 依赖关系清晰，执行顺序正确
3. 技能和工具选择恰当
4. 最终能产出用户需要的交付物
"""

TASK_EXECUTION_PROMPT = """请执行以下任务：

任务名称：{task_name}
任务描述：{task_description}
使用的技能：{skill}
需要的工具：{tools}

上下文信息（之前任务的结果）：
{context}

请提供执行结果。
"""
