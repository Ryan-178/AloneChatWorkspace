"""
意图澄清系统 - Intent Clarifier
用于澄清模糊的用户需求
"""
from typing import Any, Dict, List, Optional

from agent_framework.core.base_llm import Message


class ClarificationQuestion:
    """澄清问题"""
    
    def __init__(
        self,
        question_id: str,
        question_text: str,
        question_type: str = "text",
        options: Optional[List[str]] = None,
        required: bool = True,
        default: Optional[str] = None,
    ):
        self.id = question_id
        self.text = question_text
        self.type = question_type
        self.options = options or []
        self.required = required
        self.default = default
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.text,
            "type": self.type,
            "options": self.options,
            "required": self.required,
            "default": self.default,
        }


class IntentClarifier:
    """意图澄清系统"""
    
    def __init__(self, llm, max_questions: int = 3):
        self.llm = llm
        self.max_questions = max_questions
        self.collected_answers: Dict[str, Any] = {}
        self.questions: List[ClarificationQuestion] = []
    
    def should_clarify(self, task: str) -> bool:
        """判断是否需要澄清意图"""
        vague_keywords = [
            "帮我", "弄一下", "处理", "做个", "写个",
            "分析", "整理", "优化", "改进", "修改",
            "看看", "检查", "弄好",
        ]
        
        specific_indicators = [
            any(char.isdigit() for char in task),
            len(task) > 50,
            any(kw in task.lower() for kw in ["具体", "详细", "格式", "要求"]),
            task.count("的") >= 2,
        ]
        
        vague_indicators = [
            len(task) < 20,
            any(keyword in task for keyword in vague_keywords) and len(task.split()) < 8,
            not any(specific for specific in specific_indicators),
        ]
        
        return sum(vague_indicators) >= 2
    
    def analyze(self, task: str) -> Dict[str, Any]:
        """分析用户请求意图"""
        return {
            "original_task": task,
            "needs_clarification": self.should_clarify(task),
            "task_length": len(task),
            "has_numbers": any(char.isdigit() for char in task),
            "word_count": len(task.split()),
            "has_specific_requirements": "具体" in task or "要求" in task,
        }
    
    def generate_questions(self, task: str) -> List[ClarificationQuestion]:
        """生成追问表单（最多N个问题）"""
        self.questions = []
        
        if not self.should_clarify(task):
            return self.questions
        
        task_lower = task.lower()
        
        if "文档" in task or "报告" in task or "写" in task:
            self.questions.append(ClarificationQuestion(
                question_id="output_format",
                question_text="您希望输出什么格式的文档？",
                question_type="choice",
                options=["Markdown", "Word文档", "PDF", "Excel表格", "PPT演示文稿"],
                required=True,
            ))
            
            self.questions.append(ClarificationQuestion(
                question_id="detail_level",
                question_text="您需要多详细的内容？",
                question_type="choice",
                options=["简要概述（1-2页）", "标准详细（3-5页）", "非常详细（5页以上）"],
                required=True,
            ))
        
        if "数据" in task or "分析" in task:
            self.questions.append(ClarificationQuestion(
                question_id="data_source",
                question_text="数据来源是什么？",
                question_type="text",
                required=True,
            ))
            
            self.questions.append(ClarificationQuestion(
                question_id="analysis_type",
                question_text="您需要什么类型的分析？",
                question_type="choice",
                options=["描述性统计", "趋势分析", "对比分析", "相关性分析"],
                required=True,
            ))
        
        if "调研" in task or "搜索" in task:
            self.questions.append(ClarificationQuestion(
                question_id="research_scope",
                question_text="调研范围是什么？",
                question_type="text",
                required=True,
            ))
            
            self.questions.append(ClarificationQuestion(
                question_id="output_requirements",
                question_text="调研报告需要包含哪些内容？",
                question_type="choice",
                options=["基本信息", "详细分析", "对比评估", "建议方案"],
                required=True,
            ))
        
        if len(self.questions) == 0:
            self.questions.append(ClarificationQuestion(
                question_id="goal",
                question_text="您希望达到什么目标？",
                question_type="text",
                required=True,
            ))
            
            self.questions.append(ClarificationQuestion(
                question_id="constraints",
                question_text="有什么特殊要求或限制吗？",
                question_type="text",
                required=False,
            ))
        
        self.questions.append(ClarificationQuestion(
            question_id="target_audience",
            question_text="这份产出的目标读者是谁？（可选）",
            question_type="text",
            required=False,
        ))
        
        return self.questions[:self.max_questions]
    
    def collect_answers(self, answers: Dict[str, Any]) -> None:
        """收集用户回答"""
        self.collected_answers.update(answers)
    
    def integrate(self, original_task: str) -> str:
        """整合回答为完整需求"""
        if not self.collected_answers:
            return original_task
        
        integrated_parts = [f"原始需求：{original_task}"]
        integrated_parts.append("\n澄清信息：")
        
        for question in self.questions:
            if question.id in self.collected_answers:
                answer = self.collected_answers[question.id]
                integrated_parts.append(f"- {question.text} {answer}")
        
        return "\n".join(integrated_parts)
    
    def get_missing_required_answers(self) -> List[str]:
        """获取缺失的必填问题ID"""
        missing = []
        for question in self.questions:
            if question.required and question.id not in self.collected_answers:
                missing.append(question.id)
        return missing
    
    def is_complete(self) -> bool:
        """检查是否所有必填问题都已回答"""
        return len(self.get_missing_required_answers()) == 0
    
    def reset(self) -> None:
        """重置澄清状态"""
        self.collected_answers = {}
        self.questions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "questions": [q.to_dict() for q in self.questions],
            "collected_answers": self.collected_answers,
            "is_complete": self.is_complete(),
        }
