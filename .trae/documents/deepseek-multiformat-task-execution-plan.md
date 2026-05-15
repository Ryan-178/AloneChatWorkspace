# DeepSeek 多格式文件处理与智能任务执行实现计划

## 项目目标

让纯文本 DeepSeek 模型实现两大核心能力：
1. **多格式文件理解与生成** - 处理 JSON、Python、PPTX、CSV、Word、PDF 等格式
2. **智能任务拆解与执行** - 自然语言驱动的自动化任务执行

---

## 核心设计理念

DeepSeek 是纯文本模型，无法直接处理二进制文件。解决方案：
- **理解文件**：将文件转换为文本表示（文本化）
- **生成文件**：生成文本描述/代码，由工具转换为实际文件

---

## Phase 1: 文件文本化系统

### 1.1 文件解析器架构

```
backend/app/services/file_processors/
├── __init__.py
├── base_processor.py          # 基类
├── text_processor.py          # TXT/MD/JSON/XML
├── code_processor.py          # Python/JS/Java/Go
├── document_processor.py      # Word/PDF/RTF
├── spreadsheet_processor.py   # Excel/CSV/TSV
├── presentation_processor.py  # PPTX/Keynote
├── image_processor.py         # 图片 OCR + 描述
└── universal_processor.py     # 统一入口
```

### 1.2 文件转文本实现

```python
# backend/app/services/file_processors/base_processor.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

class BaseFileProcessor(ABC):
    """文件处理器基类"""
    
    @abstractmethod
    async def to_text(self, file_path: Path) -&gt; str:
        """将文件转换为 DeepSeek 可理解的文本表示"""
        pass
    
    @abstractmethod
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从文本描述生成实际文件"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -&gt; list[str]:
        """返回支持的文件扩展名"""
        pass
    
    def get_file_metadata(self, file_path: Path) -&gt; Dict[str, Any]:
        """获取文件元数据"""
        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size": file_path.stat().st_size,
        }
```

### 1.3 各格式处理器实现

#### 1.3.1 文档处理器 (Word/PDF)

```python
# backend/app/services/file_processors/document_processor.py
import pdfplumber
from docx import Document
from pathlib import Path
from .base_processor import BaseFileProcessor

class DocumentProcessor(BaseFileProcessor):
    """Word/PDF 文档处理器"""
    
    async def to_text(self, file_path: Path) -&gt; str:
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return await self._pdf_to_text(file_path)
        elif ext in ['.docx', '.doc']:
            return await self._word_to_text(file_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")
    
    async def _pdf_to_text(self, file_path: Path) -&gt; str:
        """PDF 转文本表示"""
        text_parts = ["[PDF文档结构]\n"]
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text_parts.append(f"\n=== 第 {i} 页 ===\n")
                text_parts.append(page.extract_text() or "")
                
                # 提取表格
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables, 1):
                        text_parts.append(f"\n[表格 {j}]\n")
                        text_parts.append(self._table_to_markdown(table))
        
        return "".join(text_parts)
    
    async def _word_to_text(self, file_path: Path) -&gt; str:
        """Word 转文本表示"""
        doc = Document(file_path)
        text_parts = ["[Word文档结构]\n"]
        
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                level = para.style.name[-1] if para.style.name[-1].isdigit() else '1'
                text_parts.append(f"\n{'#' * int(level)} {para.text}\n")
            else:
                text_parts.append(f"{para.text}\n")
        
        # 处理表格
        for i, table in enumerate(doc.tables, 1):
            text_parts.append(f"\n[表格 {i}]\n")
            table_data = [[cell.text for cell in row.cells] for row in table.rows]
            text_parts.append(self._table_to_markdown(table_data))
        
        return "".join(text_parts)
    
    def _table_to_markdown(self, table: list) -&gt; str:
        """表格转 Markdown 格式"""
        if not table:
            return ""
        
        lines = []
        # 表头
        lines.append("| " + " | ".join(str(cell) for cell in table[0]) + " |")
        lines.append("| " + " | ".join("---" for _ in table[0]) + " |")
        # 数据行
        for row in table[1:]:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        
        return "\n".join(lines) + "\n"
    
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从文本描述生成 Word 文档"""
        doc = Document()
        
        # 解析文本结构
        lines = text.split('\n')
        for line in lines:
            if line.startswith('# '):
                doc.add_heading(line[2:], level=1)
            elif line.startswith('## '):
                doc.add_heading(line[3:], level=2)
            elif line.startswith('### '):
                doc.add_heading(line[4:], level=3)
            else:
                doc.add_paragraph(line)
        
        doc.save(output_path)
        return True
    
    def get_supported_extensions(self) -&gt; list[str]:
        return ['.pdf', '.docx', '.doc', '.rtf']
```

#### 1.3.2 表格处理器 (Excel/CSV)

```python
# backend/app/services/file_processors/spreadsheet_processor.py
import pandas as pd
import openpyxl
from pathlib import Path
from .base_processor import BaseFileProcessor

class SpreadsheetProcessor(BaseFileProcessor):
    """Excel/CSV 表格处理器"""
    
    async def to_text(self, file_path: Path) -&gt; str:
        ext = file_path.suffix.lower()
        
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported format: {ext}")
        
        # 生成结构化文本表示
        text_parts = [
            f"[表格数据]\n",
            f"行数: {len(df)}\n",
            f"列数: {len(df.columns)}\n",
            f"列名: {', '.join(df.columns)}\n\n",
            f"[数据预览 - 前10行]\n",
            df.head(10).to_markdown(index=False),
            "\n\n[数据统计]\n",
        ]
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) &gt; 0:
            text_parts.append("\n数值列统计:\n")
            text_parts.append(df[numeric_cols].describe().to_markdown())
        
        # 缺失值统计
        missing = df.isnull().sum()
        if missing.any():
            text_parts.append("\n缺失值统计:\n")
            for col, count in missing.items():
                if count &gt; 0:
                    text_parts.append(f"  {col}: {count} 个缺失值\n")
        
        return "".join(text_parts)
    
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从文本描述生成 Excel 文件"""
        # DeepSeek 会生成 CSV 格式的文本
        # 或结构化的数据描述
        
        lines = text.strip().split('\n')
        
        # 检测是否为 CSV 格式
        if ',' in lines[0]:
            df = pd.read_csv(pd.StringIO(text))
        else:
            # 解析结构化描述
            df = self._parse_structured_text(text)
        
        # 保存为 Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        return True
    
    def _parse_structured_text(self, text: str) -&gt; pd.DataFrame:
        """解析结构化文本描述"""
        # 实现解析逻辑
        # 例如: "姓名: 张三, 年龄: 25, 城市: 北京"
        import re
        
        data = []
        pattern = r'(\w+):\s*([^,]+)'
        
        for line in text.split('\n'):
            if ':' in line:
                row = dict(re.findall(pattern, line))
                if row:
                    data.append(row)
        
        return pd.DataFrame(data)
    
    def get_supported_extensions(self) -&gt; list[str]:
        return ['.xlsx', '.xls', '.csv', '.tsv']
```

#### 1.3.3 演示文稿处理器 (PPTX)

```python
# backend/app/services/file_processors/presentation_processor.py
from pptx import Presentation
from pptx.util import Inches, Pt
from pathlib import Path
from .base_processor import BaseFileProcessor

class PresentationProcessor(BaseFileProcessor):
    """PPTX 演示文稿处理器"""
    
    async def to_text(self, file_path: Path) -&gt; str:
        prs = Presentation(file_path)
        text_parts = ["[演示文稿结构]\n"]
        text_parts.append(f"幻灯片数量: {len(prs.slides)}\n\n")
        
        for i, slide in enumerate(prs.slides, 1):
            text_parts.append(f"\n{'='*50}\n")
            text_parts.append(f"幻灯片 {i}\n")
            text_parts.append(f"{'='*50}\n")
            
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            # 检测标题样式
                            if para.level == 0 and shape == slide.shapes[0]:
                                text_parts.append(f"\n## {text}\n")
                            else:
                                indent = "  " * para.level
                                text_parts.append(f"{indent}• {text}\n")
                
                # 处理表格
                if shape.has_table:
                    table = shape.table
                    text_parts.append("\n[表格]\n")
                    for row in table.rows:
                        cells = [cell.text for cell in row.cells]
                        text_parts.append("| " + " | ".join(cells) + " |\n")
        
        return "".join(text_parts)
    
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从文本描述生成 PPTX"""
        prs = Presentation()
        
        # 解析幻灯片结构
        slides_content = self._parse_slides(text)
        
        for slide_content in slides_content:
            # 使用标题和内容布局
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            
            # 设置标题
            if slide_content.get('title'):
                title = slide.shapes.title
                title.text = slide_content['title']
            
            # 设置内容
            if slide_content.get('content'):
                body = slide.placeholders[1]
                tf = body.text_frame
                for i, item in enumerate(slide_content['content']):
                    if i == 0:
                        tf.text = item
                    else:
                        p = tf.add_paragraph()
                        p.text = item
        
        prs.save(output_path)
        return True
    
    def _parse_slides(self, text: str) -&gt; list[dict]:
        """解析幻灯片文本描述"""
        slides = []
        current_slide = None
        
        for line in text.split('\n'):
            if line.startswith('## '):
                if current_slide:
                    slides.append(current_slide)
                current_slide = {'title': line[3:], 'content': []}
            elif current_slide and line.strip():
                current_slide['content'].append(line.strip())
        
        if current_slide:
            slides.append(current_slide)
        
        return slides
    
    def get_supported_extensions(self) -&gt; list[str]:
        return ['.pptx', '.ppt']
```

#### 1.3.4 代码处理器

```python
# backend/app/services/file_processors/code_processor.py
from pathlib import Path
from .base_processor import BaseFileProcessor

class CodeProcessor(BaseFileProcessor):
    """代码文件处理器"""
    
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.c': 'C',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
    }
    
    async def to_text(self, file_path: Path) -&gt; str:
        ext = file_path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, 'Unknown')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 生成带语言标记的代码块
        text_parts = [
            f"[代码文件: {file_path.name}]\n",
            f"语言: {language}\n",
            f"行数: {len(code.splitlines())}\n\n",
            f"```{language.lower()}\n",
            code,
            "\n```\n"
        ]
        
        return "".join(text_parts)
    
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从代码文本生成文件"""
        # 提取代码块内容
        import re
        
        # 匹配代码块
        code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            code = matches[0]
        else:
            code = text
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return True
    
    def get_supported_extensions(self) -&gt; list[str]:
        return list(self.LANGUAGE_MAP.keys())
```

---

## Phase 2: 文件生成系统

### 2.1 DeepSeek 文件生成 Prompt 设计

```python
# backend/app/services/file_generators/prompts.py

FILE_GENERATION_PROMPTS = {
    "ppt": """你是一个专业的演示文稿设计专家。请根据用户需求，生成结构化的幻灯片内容。

输出格式要求：
## 标题
- 要点1
- 要点2
- 要点3

## 下一页标题
- 内容...

请确保：
1. 每页有明确的主题
2. 内容简洁有力
3. 逻辑清晰连贯

用户需求：{user_request}
上下文信息：{context}
""",

    "excel": """你是一个数据分析专家。请根据用户需求，生成结构化的表格数据。

输出格式要求（CSV格式）：
列1,列2,列3,列4
数据1,数据2,数据3,数据4
...

请确保：
1. 数据准确完整
2. 格式规范统一
3. 包含必要的统计信息

用户需求：{user_request}
上下文信息：{context}
""",

    "word": """你是一个文档撰写专家。请根据用户需求，生成专业的文档内容。

输出格式要求：
# 一级标题

正文内容...

## 二级标题

- 要点1
- 要点2

### 三级标题

详细说明...

请确保：
1. 结构层次清晰
2. 内容详实准确
3. 语言专业规范

用户需求：{user_request}
上下文信息：{context}
""",

    "report": """你是一个报告撰写专家。请根据提供的数据和分析，生成专业的复盘报告。

报告结构：
# 报告标题

## 一、项目概述
项目背景、目标、范围

## 二、执行情况
- 完成情况
- 关键里程碑
- 数据指标

## 三、成果与亮点
- 主要成果
- 创新亮点

## 四、问题与挑战
- 遇到的问题
- 解决方案

## 五、经验总结
- 成功经验
- 改进建议

## 六、下一步计划
- 后续工作
- 资源需求

用户需求：{user_request}
数据信息：{context}
"""
}
```

### 2.2 文件生成服务

```python
# backend/app/services/file_generators/generator_service.py
from typing import Optional, Dict, Any
from pathlib import Path
from ..deepseek_service import deepseek_service
from .prompts import FILE_GENERATION_PROMPTS
from ..file_processors import get_processor

class FileGeneratorService:
    """文件生成服务"""
    
    async def generate_ppt(
        self,
        user_request: str,
        context: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -&gt; str:
        """生成 PPT 演示文稿"""
        
        # 1. 让 DeepSeek 生成幻灯片内容
        prompt = FILE_GENERATION_PROMPTS["ppt"].format(
            user_request=user_request,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": "你是演示文稿设计专家，擅长创建结构清晰、内容专业的PPT。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await deepseek_service.chat_completion(messages)
        slide_content = response["choices"][0]["message"]["content"]
        
        # 2. 将文本转换为 PPTX 文件
        if output_path:
            processor = get_processor('.pptx')
            await processor.from_text(slide_content, output_path)
        
        return slide_content
    
    async def generate_excel(
        self,
        user_request: str,
        context: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -&gt; str:
        """生成 Excel 数据报表"""
        
        prompt = FILE_GENERATION_PROMPTS["excel"].format(
            user_request=user_request,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": "你是数据分析专家，擅长创建结构化的数据报表。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await deepseek_service.chat_completion(messages)
        data_content = response["choices"][0]["message"]["content"]
        
        if output_path:
            processor = get_processor('.xlsx')
            await processor.from_text(data_content, output_path)
        
        return data_content
    
    async def generate_word_report(
        self,
        user_request: str,
        data: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None
    ) -&gt; str:
        """生成 Word 复盘报告"""
        
        # 将数据转换为文本上下文
        context = self._format_data_context(data) if data else None
        
        prompt = FILE_GENERATION_PROMPTS["report"].format(
            user_request=user_request,
            context=context or "无数据信息"
        )
        
        messages = [
            {"role": "system", "content": "你是报告撰写专家，擅长撰写专业、全面的复盘报告。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await deepseek_service.chat_completion(messages, max_tokens=4000)
        report_content = response["choices"][0]["message"]["content"]
        
        if output_path:
            processor = get_processor('.docx')
            await processor.from_text(report_content, output_path)
        
        return report_content
    
    def _format_data_context(self, data: Dict[str, Any]) -&gt; str:
        """格式化数据上下文"""
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)

file_generator = FileGeneratorService()
```

---

## Phase 3: 智能任务拆解系统

### 3.1 任务拆解 Prompt 设计

```python
# backend/app/services/task_planner/prompts.py

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

可用的工具：
- file_reader: 读取文件
- file_writer: 写入文件
- web_search: 网络搜索
- data_processor: 数据处理
- chart_generator: 图表生成
- api_caller: API调用

请确保：
1. 任务拆解合理，每个子任务目标明确
2. 依赖关系清晰，执行顺序正确
3. 技能和工具选择恰当
4. 最终能产出用户需要的交付物
"""
```

### 3.2 任务规划器实现

```python
# backend/app/services/task_planner/planner.py
import json
from typing import Dict, Any, List, Optional
from ..deepseek_service import deepseek_service
from .prompts import TASK_DECOMPOSITION_PROMPT

class TaskPlanner:
    """智能任务规划器"""
    
    async def decompose_task(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -&gt; Dict[str, Any]:
        """拆解用户任务"""
        
        # 构建完整的需求描述
        full_request = user_request
        if context:
            full_request += f"\n\n上下文信息：{json.dumps(context, ensure_ascii=False)}"
        
        messages = [
            {
                "role": "system",
                "content": "你是任务规划专家，擅长将复杂需求拆解为可执行的子任务。"
            },
            {
                "role": "user",
                "content": TASK_DECOMPOSITION_PROMPT.format(user_request=full_request)
            }
        ]
        
        response = await deepseek_service.chat_completion(messages, temperature=0.3)
        content = response["choices"][0]["message"]["content"]
        
        # 解析 JSON
        task_plan = self._extract_json(content)
        
        return task_plan
    
    async def execute_task_plan(
        self,
        task_plan: Dict[str, Any],
        workspace_id: str,
        progress_callback: Optional[callable] = None
    ) -&gt; Dict[str, Any]:
        """执行任务计划"""
        
        results = {}
        subtasks = task_plan["subtasks"]
        execution_order = task_plan["execution_order"]
        
        for task_id in execution_order:
            task = next(t for t in subtasks if t["id"] == task_id)
            
            # 检查依赖是否完成
            deps_satisfied = all(
                dep in results for dep in task.get("dependencies", [])
            )
            
            if not deps_satisfied:
                raise ValueError(f"Task {task_id} dependencies not satisfied")
            
            # 执行子任务
            if progress_callback:
                await progress_callback(task_id, "started", task)
            
            try:
                result = await self._execute_subtask(
                    task,
                    results,
                    workspace_id
                )
                results[task_id] = result
                
                if progress_callback:
                    await progress_callback(task_id, "completed", result)
                    
            except Exception as e:
                if progress_callback:
                    await progress_callback(task_id, "failed", str(e))
                raise
        
        return {
            "main_task": task_plan["main_task"],
            "results": results,
            "final_output": task_plan["final_output"]
        }
    
    async def _execute_subtask(
        self,
        task: Dict[str, Any],
        previous_results: Dict[str, Any],
        workspace_id: str
    ) -&gt; Any:
        """执行单个子任务"""
        
        skill = task["skill"]
        tools = task.get("tools", [])
        
        # 根据技能调用对应的服务
        if skill == "document_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_word_report(
                task["description"],
                context=previous_results
            )
        
        elif skill == "presentation_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_ppt(
                task["description"],
                context=str(previous_results)
            )
        
        elif skill == "spreadsheet_generation":
            from ..file_generators import file_generator
            return await file_generator.generate_excel(
                task["description"],
                context=str(previous_results)
            )
        
        elif skill == "data_analysis":
            return await self._execute_data_analysis(task, previous_results)
        
        elif skill == "web_reading":
            return await self._execute_web_reading(task, previous_results)
        
        else:
            # 通用技能执行
            return await self._execute_generic_skill(task, previous_results)
    
    async def _execute_data_analysis(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -&gt; Dict[str, Any]:
        """执行数据分析任务"""
        
        prompt = f"""请执行以下数据分析任务：

任务描述：{task['description']}

上下文数据：{json.dumps(context, ensure_ascii=False, indent=2)}

请提供：
1. 分析过程
2. 关键发现
3. 数据洞察
4. 可视化建议
"""
        
        messages = [
            {"role": "system", "content": "你是数据分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await deepseek_service.chat_completion(messages, max_tokens=3000)
        return {
            "analysis": response["choices"][0]["message"]["content"],
            "task_id": task["id"]
        }
    
    def _extract_json(self, text: str) -&gt; Dict[str, Any]:
        """从文本中提取 JSON"""
        import re
        
        # 查找 JSON 代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # 尝试直接解析
            json_str = text
        
        return json.loads(json_str)

task_planner = TaskPlanner()
```

---

## Phase 4: Skills 注册与执行系统

### 4.1 Skills 定义

```python
# backend/app/services/skills/registry.py
from typing import Dict, Any, Callable, Optional
from pydantic import BaseModel

class SkillDefinition(BaseModel):
    """技能定义"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    input_types: list[str]
    output_types: list[str]
    required_tools: list[str]
    executor: Optional[Callable] = None

class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._register_builtin_skills()
    
    def _register_builtin_skills(self):
        """注册内置技能"""
        
        self.register(SkillDefinition(
            id="web_reading",
            name="网页读取",
            description="读取网页内容，提取关键信息",
            icon="Globe",
            category="information",
            input_types=["url", "text"],
            output_types=["text", "json"],
            required_tools=["web_search", "file_reader"]
        ))
        
        self.register(SkillDefinition(
            id="research_analysis",
            name="调研分析",
            description="深度调研分析，生成专业报告",
            icon="Search",
            category="analysis",
            input_types=["text", "data"],
            output_types=["document", "report"],
            required_tools=["web_search", "data_processor"]
        ))
        
        self.register(SkillDefinition(
            id="data_mining",
            name="数据挖掘",
            description="数据挖掘与分析，发现数据洞察",
            icon="BarChart",
            category="analysis",
            input_types=["file", "data"],
            output_types=["report", "chart", "spreadsheet"],
            required_tools=["data_processor", "chart_generator"]
        ))
        
        self.register(SkillDefinition(
            id="file_management",
            name="文件管理",
            description="文件处理、格式转换、内容编辑",
            icon="FileText",
            category="productivity",
            input_types=["file"],
            output_types=["file"],
            required_tools=["file_reader", "file_writer"]
        ))
        
        self.register(SkillDefinition(
            id="presentation_generation",
            name="PPT生成",
            description="自动生成专业演示文稿",
            icon="Presentation",
            category="generation",
            input_types=["text", "data"],
            output_types=["pptx"],
            required_tools=["file_writer"]
        ))
        
        self.register(SkillDefinition(
            id="spreadsheet_generation",
            name="Excel生成",
            description="自动生成数据报表",
            icon="Table",
            category="generation",
            input_types=["data", "text"],
            output_types=["xlsx"],
            required_tools=["file_writer", "data_processor"]
        ))
        
        self.register(SkillDefinition(
            id="document_generation",
            name="文档生成",
            description="自动生成专业文档报告",
            icon="FileText",
            category="generation",
            input_types=["text", "data"],
            output_types=["docx", "pdf"],
            required_tools=["file_writer"]
        ))
    
    def register(self, skill: SkillDefinition):
        """注册技能"""
        self._skills[skill.id] = skill
    
    def get(self, skill_id: str) -&gt; Optional[SkillDefinition]:
        """获取技能"""
        return self._skills.get(skill_id)
    
    def list_all(self) -&gt; list[SkillDefinition]:
        """列出所有技能"""
        return list(self._skills.values())
    
    def get_by_category(self, category: str) -&gt; list[SkillDefinition]:
        """按类别获取技能"""
        return [s for s in self._skills.values() if s.category == category]

skill_registry = SkillRegistry()
```

### 4.2 Skill 执行器

```python
# backend/app/services/skills/executor.py
from typing import Dict, Any, Optional
from ..deepseek_service import deepseek_service
from ..file_generators import file_generator
from ..file_processors import get_processor
from .registry import skill_registry

class SkillExecutor:
    """技能执行器"""
    
    async def execute(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -&gt; Dict[str, Any]:
        """执行技能"""
        
        skill = skill_registry.get(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        # 根据技能类型执行
        if skill_id == "web_reading":
            return await self._execute_web_reading(input_data, context)
        
        elif skill_id == "research_analysis":
            return await self._execute_research(input_data, context)
        
        elif skill_id == "data_mining":
            return await self._execute_data_mining(input_data, context)
        
        elif skill_id == "presentation_generation":
            return await self._execute_ppt_generation(input_data, context)
        
        elif skill_id == "spreadsheet_generation":
            return await self._execute_excel_generation(input_data, context)
        
        elif skill_id == "document_generation":
            return await self._execute_doc_generation(input_data, context)
        
        else:
            return await self._execute_generic(skill, input_data, context)
    
    async def _execute_web_reading(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -&gt; Dict[str, Any]:
        """执行网页读取"""
        
        url = input_data.get("url")
        query = input_data.get("query", "")
        
        # 让 DeepSeek 分析网页内容
        prompt = f"""请分析以下网页内容：

URL: {url}
用户查询: {query}

请提供：
1. 网页主题
2. 关键信息提取
3. 内容摘要
4. 相关数据点
"""
        
        messages = [
            {"role": "system", "content": "你是网页内容分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await deepseek_service.chat_completion(messages)
        
        return {
            "skill": "web_reading",
            "result": response["choices"][0]["message"]["content"],
            "url": url
        }
    
    async def _execute_ppt_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -&gt; Dict[str, Any]:
        """执行 PPT 生成"""
        
        request = input_data.get("request", "")
        context_str = str(context) if context else None
        
        content = await file_generator.generate_ppt(
            user_request=request,
            context=context_str
        )
        
        return {
            "skill": "presentation_generation",
            "content": content,
            "format": "pptx"
        }
    
    async def _execute_excel_generation(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -&gt; Dict[str, Any]:
        """执行 Excel 生成"""
        
        request = input_data.get("request", "")
        data = input_data.get("data")
        
        content = await file_generator.generate_excel(
            user_request=request,
            context=str(data) if data else str(context)
        )
        
        return {
            "skill": "spreadsheet_generation",
            "content": content,
            "format": "xlsx"
        }

skill_executor = SkillExecutor()
```

---

## Phase 5: API 端点实现

### 5.1 文件处理 API

```python
# backend/app/api/v1/files.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from ...services.file_processors import get_processor

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    """解析文件为文本表示"""
    
    # 保存临时文件
    temp_path = Path(f"/tmp/{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # 获取处理器
    processor = get_processor(temp_path.suffix)
    if not processor:
        raise HTTPException(400, f"Unsupported file type: {temp_path.suffix}")
    
    # 转换为文本
    text = await processor.to_text(temp_path)
    
    return {
        "filename": file.filename,
        "text_representation": text,
        "metadata": processor.get_file_metadata(temp_path)
    }

@router.post("/generate/{file_type}")
async def generate_file(
    file_type: str,
    request: FileGenerationRequest
):
    """生成文件"""
    
    from ...services.file_generators import file_generator
    
    if file_type == "ppt":
        content = await file_generator.generate_ppt(
            request.user_request,
            request.context
        )
    elif file_type == "excel":
        content = await file_generator.generate_excel(
            request.user_request,
            request.context
        )
    elif file_type == "word":
        content = await file_generator.generate_word_report(
            request.user_request,
            request.data
        )
    else:
        raise HTTPException(400, f"Unsupported file type: {file_type}")
    
    return {
        "file_type": file_type,
        "content": content
    }
```

### 5.2 任务执行 API

```python
# backend/app/api/v1/tasks.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...services.task_planner import task_planner

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/decompose")
async def decompose_task(request: TaskDecomposeRequest):
    """拆解任务"""
    
    task_plan = await task_planner.decompose_task(
        request.user_request,
        request.context
    )
    
    return task_plan

@router.post("/execute")
async def execute_task(request: TaskExecuteRequest):
    """执行任务计划"""
    
    result = await task_planner.execute_task_plan(
        request.task_plan,
        request.workspace_id
    )
    
    return result

@router.websocket("/ws/execute/{workspace_id}")
async def websocket_execute_task(
    websocket: WebSocket,
    workspace_id: str
):
    """WebSocket 实时任务执行"""
    
    await websocket.accept()
    
    async def progress_callback(task_id, status, data):
        await websocket.send_json({
            "type": "progress",
            "task_id": task_id,
            "status": status,
            "data": data
        })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "execute":
                task_plan = data["task_plan"]
                
                result = await task_planner.execute_task_plan(
                    task_plan,
                    workspace_id,
                    progress_callback
                )
                
                await websocket.send_json({
                    "type": "complete",
                    "result": result
                })
                
    except WebSocketDisconnect:
        pass
```

### 5.3 Skills API

```python
# backend/app/api/v1/skills.py
from fastapi import APIRouter
from ...services.skills import skill_registry, skill_executor

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/")
async def list_skills():
    """列出所有技能"""
    return skill_registry.list_all()

@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    """获取技能详情"""
    skill = skill_registry.get(skill_id)
    if not skill:
        raise HTTPException(404, "Skill not found")
    return skill

@router.post("/{skill_id}/execute")
async def execute_skill(skill_id: str, request: SkillExecuteRequest):
    """执行技能"""
    
    result = await skill_executor.execute(
        skill_id,
        request.input_data,
        request.context
    )
    
    return result
```

---

## Phase 6: 前端集成

### 6.1 文件上传与处理组件

```tsx
// frontend/src/components/files/FileUploader.tsx
"use client";

import { useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";

export function FileUploader({ onParsed }: { onParsed: (result: any) =&gt; void }) {
  const [uploading, setUploading] = useState(false);
  const [parsedText, setParsedText] = useState("");

  const handleUpload = async (file: File) =&gt; {
    setUploading(true);
    
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch("/api/v1/files/parse", {
      method: "POST",
      body: formData
    });
    
    const result = await response.json();
    setParsedText(result.text_representation);
    onParsed(result);
    setUploading(false);
  };

  return (
    &lt;div className="border-2 border-dashed rounded-lg p-8"&gt;
      &lt;input
        type="file"
        onChange={(e) =&gt; e.target.files?.[0] &amp;&amp; handleUpload(e.target.files[0])}
        className="hidden"
        id="file-upload"
      /&gt;
      
      &lt;label htmlFor="file-upload" className="cursor-pointer"&gt;
        {uploading ? (
          &lt;Loader2 className="w-8 h-8 animate-spin mx-auto" /&gt;
        ) : (
          &lt;Upload className="w-8 h-8 mx-auto text-gray-400" /&gt;
        )}
        &lt;p className="mt-2 text-sm text-gray-500"&gt;
          上传文件 (支持 PDF, Word, Excel, PPT, 代码等)
        &lt;/p&gt;
      &lt;/label&gt;
      
      {parsedText &amp;&amp; (
        &lt;div className="mt-4 p-4 bg-gray-50 rounded max-h-60 overflow-auto"&gt;
          &lt;pre className="text-xs whitespace-pre-wrap"&gt;{parsedText}&lt;/pre&gt;
        &lt;/div&gt;
      )}
    &lt;/div&gt;
  );
}
```

### 6.2 任务执行界面

```tsx
// frontend/src/components/tasks/TaskExecutor.tsx
"use client";

import { useState } from "react";
import { Play, CheckCircle, Loader2 } from "lucide-react";

export function TaskExecutor() {
  const [userRequest, setUserRequest] = useState("");
  const [taskPlan, setTaskPlan] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [results, setResults] = useState({});

  const handleDecompose = async () =&gt; {
    const response = await fetch("/api/v1/tasks/decompose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_request: userRequest })
    });
    
    const plan = await response.json();
    setTaskPlan(plan);
  };

  const handleExecute = async () =&gt; {
    setExecuting(true);
    
    const response = await fetch("/api/v1/tasks/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        task_plan: taskPlan,
        workspace_id: "default"
      })
    });
    
    const result = await response.json();
    setResults(result.results);
    setExecuting(false);
  };

  return (
    &lt;div className="space-y-4"&gt;
      &lt;textarea
        value={userRequest}
        onChange={(e) =&gt; setUserRequest(e.target.value)}
        placeholder="用自然语言描述你的需求..."
        className="w-full h-32 p-4 border rounded-lg"
      /&gt;
      
      &lt;button onClick={handleDecompose} className="btn-primary"&gt;
        拆解任务
      &lt;/button&gt;
      
      {taskPlan &amp;&amp; (
        &lt;div className="border rounded-lg p-4"&gt;
          &lt;h3 className="font-bold mb-2"&gt;任务计划&lt;/h3&gt;
          {taskPlan.subtasks.map((task: any) =&gt; (
            &lt;div key={task.id} className="flex items-center gap-2 p-2"&gt;
              {results[task.id] ? (
                &lt;CheckCircle className="w-4 h-4 text-green-500" /&gt;
              ) : executing ? (
                &lt;Loader2 className="w-4 h-4 animate-spin" /&gt;
              ) : (
                &lt;div className="w-4 h-4 rounded-full border" /&gt;
              )}
              &lt;span&gt;{task.name}&lt;/span&gt;
            &lt;/div&gt;
          ))}
          
          &lt;button 
            onClick={handleExecute} 
            disabled={executing}
            className="btn-primary mt-4"
          &gt;
            {executing ? "执行中..." : "执行任务"}
          &lt;/button&gt;
        &lt;/div&gt;
      )}
    &lt;/div&gt;
  );
}
```

---

## Phase 7: 实施步骤

### Step 1: 文件处理系统
- [ ] 实现各格式文件处理器
- [ ] 创建文件转文本转换逻辑
- [ ] 实现文本转文件生成逻辑
- [ ] 添加文件元数据提取

### Step 2: 文件生成系统
- [ ] 设计 DeepSeek 生成 Prompt
- [ ] 实现 PPT 生成服务
- [ ] 实现 Excel 生成服务
- [ ] 实现 Word 文档生成服务

### Step 3: 任务拆解系统
- [ ] 设计任务拆解 Prompt
- [ ] 实现任务规划器
- [ ] 实现依赖关系解析
- [ ] 实现执行顺序优化

### Step 4: Skills 系统
- [ ] 注册所有技能
- [ ] 实现技能执行器
- [ ] 创建技能组合机制
- [ ] 添加技能参数验证

### Step 5: API 集成
- [ ] 实现文件处理 API
- [ ] 实现任务执行 API
- [ ] 实现 WebSocket 实时通信
- [ ] 添加错误处理和重试

### Step 6: 前端界面
- [ ] 文件上传组件
- [ ] 任务执行界面
- [ ] 进度展示组件
- [ ] 结果预览组件

---

## 验收标准

1. **文件理解**
   - [ ] 能正确解析 PDF、Word、Excel、PPT、代码文件
   - [ ] 转换后的文本保留完整信息
   - [ ] 表格、图表正确转换

2. **文件生成**
   - [ ] 能生成专业级 PPT
   - [ ] 能生成格式规范的 Excel
   - [ ] 能生成结构清晰的 Word 文档

3. **任务拆解**
   - [ ] 自然语言正确理解
   - [ ] 任务拆解合理完整
   - [ ] 依赖关系正确
   - [ ] 执行顺序正确

4. **任务执行**
   - [ ] 子任务正确执行
   - [ ] 结果正确传递
   - [ ] 最终交付物符合预期

---

## Phase 8: OCR 图片识别系统

### 8.1 OCR 库选择与配置

支持多种 OCR 引擎：
- **PaddleOCR** (推荐) - 百度开源，中文识别优秀
- **Tesseract** - 开源经典，多语言支持
- **EasyOCR** - 深度学习，多语言支持

### 8.2 图片处理器实现

```python
# backend/app/services/file_processors/image_processor.py
from pathlib import Path
from typing import Dict, Any, Optional, List
import base64
from .base_processor import BaseFileProcessor

class ImageProcessor(BaseFileProcessor):
    """图片处理器 - 支持 OCR 文字识别"""
    
    def __init__(self, ocr_engine: str = "paddle"):
        self.ocr_engine = ocr_engine
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化 OCR 引擎"""
        if self.ocr_engine == "paddle":
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False
            )
        elif self.ocr_engine == "tesseract":
            import pytesseract
            self.ocr = pytesseract
        elif self.ocr_engine == "easy":
            import easyocr
            self.ocr = easyocr.Reader(['ch_sim', 'en'])
    
    async def to_text(self, file_path: Path) -&gt; str:
        """图片转文本 - OCR 识别"""
        
        text_parts = [
            f"[图片文件: {file_path.name}]\n",
            f"格式: {file_path.suffix}\n\n"
        ]
        
        # 获取图片基本信息
        try:
            from PIL import Image
            img = Image.open(file_path)
            text_parts.append(f"尺寸: {img.size[0]} x {img.size[1]}\n")
            text_parts.append(f"模式: {img.mode}\n\n")
        except:
            pass
        
        # OCR 文字识别
        text_parts.append("=== OCR 识别结果 ===\n")
        
        if self.ocr_engine == "paddle":
            ocr_result = self.ocr.ocr(str(file_path), cls=True)
            text_content = self._format_paddle_result(ocr_result)
        elif self.ocr_engine == "tesseract":
            text_content = self._tesseract_ocr(file_path)
        elif self.ocr_engine == "easy":
            ocr_result = self.ocr.readtext(str(file_path))
            text_content = self._format_easy_result(ocr_result)
        
        text_parts.append(text_content)
        
        # 图片描述生成（可选，通过 DeepSeek）
        text_parts.append("\n=== 图片内容描述 ===\n")
        text_parts.append("可通过 DeepSeek 分析 OCR 文本，生成图片内容描述\n")
        
        return "".join(text_parts)
    
    def _format_paddle_result(self, result: List) -&gt; str:
        """格式化 PaddleOCR 结果"""
        lines = []
        
        if result and result[0]:
            for item in result[0]:
                if item:
                    # item = [[[x1,y1], [x2,y2], ...], (text, confidence)]
                    box = item[0]
                    text, confidence = item[1]
                    lines.append(f"{text} (置信度: {confidence:.2f})")
        
        return "\n".join(lines) if lines else "未识别到文字"
    
    def _tesseract_ocr(self, file_path: Path) -&gt; str:
        """Tesseract OCR"""
        from PIL import Image
        
        img = Image.open(file_path)
        text = self.ocr.image_to_string(img, lang='chi_sim+eng')
        
        return text if text.strip() else "未识别到文字"
    
    def _format_easy_result(self, result: List) -&gt; str:
        """格式化 EasyOCR 结果"""
        lines = []
        
        for item in result:
            # item = ([[x1,y1], ...], text, confidence)
            box, text, confidence = item
            lines.append(f"{text} (置信度: {confidence:.2f})")
        
        return "\n".join(lines) if lines else "未识别到文字"
    
    async def from_text(self, text: str, output_path: Path) -&gt; bool:
        """从文本生成图片（通过 DeepSeek 描述生成）"""
        # 这个功能通常不使用，图片生成需要专门的图像生成模型
        # 这里可以保存文本描述作为元数据
        return False
    
    def get_supported_extensions(self) -&gt; list[str]:
        return ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    
    async def batch_ocr(self, file_paths: List[Path]) -&gt; Dict[str, str]:
        """批量 OCR 处理"""
        results = {}
        
        for file_path in file_paths:
            try:
                text = await self.to_text(file_path)
                results[str(file_path)] = text
            except Exception as e:
                results[str(file_path)] = f"OCR 失败: {str(e)}"
        
        return results
    
    async def ocr_with_structure(self, file_path: Path) -&gt; Dict[str, Any]:
        """带结构信息的 OCR 识别"""
        
        if self.ocr_engine != "paddle":
            text = await self.to_text(file_path)
            return {"text": text, "structure": None}
        
        # PaddleOCR 带位置信息
        ocr_result = self.ocr.ocr(str(file_path), cls=True)
        
        structured_result = {
            "text_blocks": [],
            "full_text": "",
            "layout": []
        }
        
        if ocr_result and ocr_result[0]:
            for item in ocr_result[0]:
                if item:
                    box, (text, confidence) = item
                    
                    # 计算文本块位置
                    x_coords = [p[0] for p in box]
                    y_coords = [p[1] for p in box]
                    
                    text_block = {
                        "text": text,
                        "confidence": float(confidence),
                        "position": {
                            "x_min": min(x_coords),
                            "x_max": max(x_coords),
                            "y_min": min(y_coords),
                            "y_max": max(y_coords)
                        },
                        "box": box
                    }
                    
                    structured_result["text_blocks"].append(text_block)
                    structured_result["full_text"] += text + "\n"
        
        return structured_result
```

### 8.3 PDF 图片 OCR 增强

```python
# 扩展 PDF 处理器，支持图片页 OCR
async def _pdf_to_text_with_ocr(self, file_path: Path) -&gt; str:
    """PDF 转文本，图片页使用 OCR"""
    
    import pdfplumber
    from PIL import Image
    import io
    
    text_parts = ["[PDF文档结构 - 增强版]\n"]
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text_parts.append(f"\n=== 第 {i} 页 ===\n")
            
            # 尝试提取文本
            text = page.extract_text()
            
            if text and text.strip():
                # 有文本内容
                text_parts.append(text)
            else:
                # 可能是图片页，使用 OCR
                text_parts.append("[图片页 - 使用 OCR 识别]\n")
                
                # 将页面转为图片
                im = page.to_image(resolution=300)
                img_bytes = io.BytesIO()
                im.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # OCR 识别
                img = Image.open(img_bytes)
                ocr_result = self.ocr.ocr(img, cls=True)
                
                if ocr_result and ocr_result[0]:
                    for item in ocr_result[0]:
                        if item:
                            text_parts.append(item[1][0] + "\n")
            
            # 提取表格
            tables = page.extract_tables()
            if tables:
                for j, table in enumerate(tables, 1):
                    text_parts.append(f"\n[表格 {j}]\n")
                    text_parts.append(self._table_to_markdown(table))
    
    return "".join(text_parts)
```

---

## 技术依赖

```txt
# requirements.txt 新增

# 文档处理
pdfplumber>=0.9.0
python-docx>=0.8.11
openpyxl>=3.1.2
python-pptx>=0.6.21
pandas>=2.0.0
tabulate>=0.9.0

# OCR 识别 (选择其一或全部)
paddleocr>=2.7.0          # 推荐，中文识别优秀
paddlepaddle>=2.5.0       # PaddleOCR 依赖
pytesseract>=0.3.10       # Tesseract OCR
easyocr>=1.7.0            # EasyOCR

# 图片处理
Pillow>=10.0.0
opencv-python>=4.8.0      # 图片预处理

# PDF 图片处理
pdf2image>=1.16.3         # PDF 转图片
```

