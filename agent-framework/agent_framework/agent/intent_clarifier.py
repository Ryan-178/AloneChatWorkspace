"""
意图澄清系统 - Intent Clarifier
用于澄清模糊的用户需求
从配置文件加载，替代硬编码
"""
from typing import Any, Dict, List, Optional

from agent_framework.core.base_llm import Message
from agent_framework.configs import get_intent_config


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
    
    def __init__(self, llm, max_questions: int = None):
        self.llm = llm
        self._config = get_intent_config()
        self.max_questions = max_questions or self._config.max_questions
        self.collected_answers: Dict[str, Any] = {}
        self.questions: List[ClarificationQuestion] = []
    
    def should_clarify(self, task: str) -> bool:
        """判断是否需要澄清意图"""
        vague_keywords = self._config.vague_keywords
        specific_indicators = self._config.specific_indicators
        vague_indicators = self._config.vague_indicators
        
        specific_checks = [
            any(char.isdigit() for char in task),
            len(task) > specific_indicators.get("min_length_for_specific", 50),
            any(kw in task.lower() for kw in specific_indicators.get("keywords", [])),
            task.count("的") >= specific_indicators.get("min_de_count", 2),
        ]
        
        vague_checks = [
            len(task) < vague_indicators.get("max_length_for_vague", 20),
            any(keyword in task for keyword in vague_keywords) and len(task.split()) < vague_indicators.get("max_word_count", 8),
            not any(specific for specific in specific_checks),
        ]
        
        return sum(vague_checks) >= 2
    
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
        task_keywords = self._config.task_keywords
        question_templates = self._config.question_templates
        
        document_keywords = task_keywords.get("document", [])
        data_keywords = task_keywords.get("data", [])
        research_keywords = task_keywords.get("research", [])
        
        if any(kw in task for kw in document_keywords):
            for q_template in question_templates.get("document", []):
                self.questions.append(ClarificationQuestion(
                    question_id=q_template.get("id", ""),
                    question_text=q_template.get("question", ""),
                    question_type=q_template.get("type", "text"),
                    options=q_template.get("options", []),
                    required=q_template.get("required", True),
                ))
        
        if any(kw in task for kw in data_keywords):
            for q_template in question_templates.get("data", []):
                self.questions.append(ClarificationQuestion(
                    question_id=q_template.get("id", ""),
                    question_text=q_template.get("question", ""),
                    question_type=q_template.get("type", "text"),
                    options=q_template.get("options", []),
                    required=q_template.get("required", True),
                ))
        
        if any(kw in task for kw in research_keywords):
            for q_template in question_templates.get("research", []):
                self.questions.append(ClarificationQuestion(
                    question_id=q_template.get("id", ""),
                    question_text=q_template.get("question", ""),
                    question_type=q_template.get("type", "text"),
                    options=q_template.get("options", []),
                    required=q_template.get("required", True),
                ))
        
        if len(self.questions) == 0:
            for q_template in question_templates.get("default", []):
                self.questions.append(ClarificationQuestion(
                    question_id=q_template.get("id", ""),
                    question_text=q_template.get("question", ""),
                    question_type=q_template.get("type", "text"),
                    options=q_template.get("options", []),
                    required=q_template.get("required", True),
                ))
        
        for q_template in question_templates.get("common", []):
            self.questions.append(ClarificationQuestion(
                question_id=q_template.get("id", ""),
                question_text=q_template.get("question", ""),
                question_type=q_template.get("type", "text"),
                options=q_template.get("options", []),
                required=q_template.get("required", False),
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


def reload_intent_config():
    """重新加载意图澄清配置"""
    get_intent_config().reload()
