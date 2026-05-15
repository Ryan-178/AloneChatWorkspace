"""
表格处理器

处理 Excel、CSV 等表格格式
"""

from pathlib import Path
from typing import Any, Dict, List
from io import StringIO
from .base_processor import BaseFileProcessor


class SpreadsheetProcessor(BaseFileProcessor):
    """Excel/CSV 表格处理器"""
    
    async def to_text(self, file_path: Path) -> str:
        """将表格转换为文本表示"""
        
        try:
            import pandas as pd
        except ImportError:
            return "[错误] 需要安装 pandas: pip install pandas"
        
        ext = file_path.suffix.lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif ext == '.tsv':
                df = pd.read_csv(file_path, sep='\t')
            else:
                raise ValueError(f"不支持的表格格式: {ext}")
        except Exception as e:
            return f"[错误] 读取文件失败: {str(e)}"
        
        # 生成结构化文本表示
        text_parts = [
            f"[表格数据: {file_path.name}]\n\n",
            f"行数: {len(df)}\n",
            f"列数: {len(df.columns)}\n",
            f"列名: {', '.join(str(c) for c in df.columns)}\n\n",
        ]
        
        # 数据类型
        text_parts.append("=== 列数据类型 ===\n")
        for col in df.columns:
            text_parts.append(f"  {col}: {df[col].dtype}\n")
        text_parts.append("\n")
        
        # 数据预览
        text_parts.append("=== 数据预览 (前10行) ===\n")
        try:
            preview = df.head(10).to_markdown(index=False)
            text_parts.append(preview + "\n\n")
        except:
            text_parts.append(df.head(10).to_string() + "\n\n")
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            text_parts.append("=== 数值统计 ===\n")
            try:
                stats = df[numeric_cols].describe().to_markdown()
                text_parts.append(stats + "\n\n")
            except:
                text_parts.append(df[numeric_cols].describe().to_string() + "\n\n")
        
        # 缺失值统计
        missing = df.isnull().sum()
        if missing.any():
            text_parts.append("=== 缺失值统计 ===\n")
            for col, count in missing.items():
                if count > 0:
                    pct = count / len(df) * 100
                    text_parts.append(f"  {col}: {count} ({pct:.1f}%)\n")
            text_parts.append("\n")
        
        # 唯一值统计（对于分类列）
        text_parts.append("=== 分类列唯一值 ===\n")
        for col in df.columns:
            unique_count = df[col].nunique()
            if unique_count < 20 and unique_count > 1:
                text_parts.append(f"\n{col} ({unique_count} 个唯一值):\n")
                value_counts = df[col].value_counts().head(10)
                for val, count in value_counts.items():
                    text_parts.append(f"  - {val}: {count}\n")
        
        return "".join(text_parts)
    
    async def from_text(self, text: str, output_path: Path) -> bool:
        """从文本描述生成 Excel 文件"""
        
        try:
            import pandas as pd
        except ImportError:
            return False
        
        lines = text.strip().split('\n')
        
        # 检测是否为 CSV 格式
        if len(lines) > 0 and ',' in lines[0]:
            try:
                df = pd.read_csv(StringIO(text))
            except:
                df = self._parse_structured_text(text)
        else:
            df = self._parse_structured_text(text)
        
        if df.empty:
            return False
        
        # 保存为 Excel
        ext = output_path.suffix.lower()
        if ext == '.csv':
            df.to_csv(output_path, index=False)
        else:
            df.to_excel(output_path, index=False, engine='openpyxl')
        
        return True
    
    def _parse_structured_text(self, text: str) -> Any:
        """解析结构化文本描述"""
        
        try:
            import pandas as pd
        except ImportError:
            return None
        
        import re
        
        data = []
        
        # 尝试解析键值对格式
        # 例如: "姓名: 张三, 年龄: 25, 城市: 北京"
        kv_pattern = r'(\w+):\s*([^,\n]+)'
        
        for line in text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('='):
                continue
            
            matches = re.findall(kv_pattern, line)
            if matches:
                row = {k.strip(): v.strip() for k, v in matches}
                if row:
                    data.append(row)
        
        if data:
            return pd.DataFrame(data)
        
        # 尝试解析列表格式
        # 例如: "- 项目1\n- 项目2"
        list_pattern = r'^\s*[-*]\s*(.+)$'
        items = re.findall(list_pattern, text, re.MULTILINE)
        
        if items:
            return pd.DataFrame({'项目': items})
        
        return pd.DataFrame()
    
    def get_supported_extensions(self) -> list[str]:
        return ['.xlsx', '.xls', '.csv', '.tsv']
