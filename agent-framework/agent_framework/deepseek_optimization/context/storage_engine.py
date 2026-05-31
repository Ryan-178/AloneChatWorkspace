"""
Storage Engine
结构化本地存储引擎 - 智能归档与检索
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

from .message_ranker import MessageImportance, ImportanceCategory


@dataclass
class StoredMessage:
    """存储的消息条目"""
    id: str
    original_message: Dict[str, Any]
    importance: MessageImportance
    storage_path: Path
    storage_topic: str
    archived_at: datetime
    retrieval_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "original_message": self.original_message,
            "importance": {
                "score": self.importance.score,
                "category": self.importance.category.value,
                "reasoning": self.importance.reasoning,
                "topics": self.importance.topics
            },
            "storage_path": str(self.storage_path),
            "storage_topic": self.storage_topic,
            "archived_at": self.archived_at.isoformat(),
            "retrieval_key": self.retrieval_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredMessage":
        """从字典创建"""
        return cls(
            id=data["id"],
            original_message=data["original_message"],
            importance=MessageImportance(
                score=data["importance"]["score"],
                category=ImportanceCategory(data["importance"]["category"]),
                reasoning=data["importance"]["reasoning"],
                topics=data["importance"]["topics"],
                timestamp=datetime.now()
            ),
            storage_path=Path(data["storage_path"]),
            storage_topic=data["storage_topic"],
            archived_at=datetime.fromisoformat(data["archived_at"]),
            retrieval_key=data["retrieval_key"]
        )


@dataclass
class StorageStats:
    """存储统计"""
    total_archived: int = 0
    total_topics: int = 0
    total_size_bytes: int = 0
    first_archived_at: Optional[datetime] = None
    last_archived_at: Optional[datetime] = None
    topic_counts: Dict[str, int] = field(default_factory=dict)


class StructuredStorageEngine:
    """
    结构化本地存储引擎
    按主题、时间、重要性分类存储消息
    """
    
    def __init__(
        self,
        storage_root: Path,
        max_file_size_mb: float = 10.0
    ):
        self.storage_root = storage_root
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        
        # 确保目录存在
        self._init_directories()
        
        # 索引和缓存
        self._message_index: Dict[str, StoredMessage] = {}
        self._topic_index: Dict[str, List[str]] = {}
        self._stats = StorageStats()
        
        # 加载现有索引
        self._load_index()
    
    def _init_directories(self):
        """初始化目录结构"""
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # 主题目录会在需要时创建
        # 按日期归档结构
        today_dir = self.storage_root / datetime.now().strftime("%Y-%m-%d")
        today_dir.mkdir(exist_ok=True)
    
    def archive_message(
        self,
        message: Dict[str, Any],
        importance: MessageImportance
    ) -> StoredMessage:
        """
        归档单条消息
        
        Args:
            message: 原始消息
            importance: 重要性评估
            
        Returns:
            StoredMessage: 存储的消息条目
        """
        # 生成ID和检索键
        message_id = str(uuid.uuid4())
        retrieval_key = self._generate_retrieval_key(message, importance)
        
        # 确定存储主题 - 使用最重要的主题
        storage_topic = importance.topics[0] if importance.topics else "general"
        
        # 确定存储文件路径
        storage_path = self._get_storage_path(storage_topic)
        
        # 创建存储条目
        stored = StoredMessage(
            id=message_id,
            original_message=message,
            importance=importance,
            storage_path=storage_path,
            storage_topic=storage_topic,
            archived_at=datetime.now(),
            retrieval_key=retrieval_key
        )
        
        # 写入文件
        self._append_to_file(stored)
        
        # 更新索引
        self._update_index(stored)
        
        # 更新统计
        self._update_stats(stored)
        
        return stored
    
    def _generate_retrieval_key(
        self,
        message: Dict[str, Any],
        importance: MessageImportance
    ) -> str:
        """生成检索键"""
        content = message.get("content", "")
        # 简单摘要 - 取前50个字符
        summary = content[:50].replace("\n", " ").strip()
        return f"{importance.category.value}:{summary}"
    
    def _get_storage_path(self, topic: str) -> Path:
        """获取存储文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        topic_dir = self.storage_root / date_str
        topic_dir.mkdir(exist_ok=True)
        
        filename = f"topic_{topic}.jsonl"
        return topic_dir / filename
    
    def _append_to_file(self, stored: StoredMessage):
        """追加到文件"""
        # 检查文件大小，如果太大创建新文件
        file_path = stored.storage_path
        if file_path.exists():
            size = file_path.stat().st_size
            if size > self.max_file_size_bytes:
                # 文件太大，创建分号文件
                counter = 1
                while True:
                    new_path = file_path.parent / f"{file_path.stem}_{counter}{file_path.suffix}"
                    if not new_path.exists():
                        stored.storage_path = new_path
                        break
                    counter += 1
        
        # 追加写入
        with open(stored.storage_path, "a", encoding="utf-8") as f:
            json_line = json.dumps(stored.to_dict(), ensure_ascii=False)
            f.write(json_line + "\n")
    
    def _update_index(self, stored: StoredMessage):
        """更新索引"""
        self._message_index[stored.id] = stored
        
        if stored.storage_topic not in self._topic_index:
            self._topic_index[stored.storage_topic] = []
        self._topic_index[stored.storage_topic].append(stored.id)
    
    def _update_stats(self, stored: StoredMessage):
        """更新统计"""
        self._stats.total_archived += 1
        
        topic = stored.storage_topic
        self._stats.topic_counts[topic] = self._stats.topic_counts.get(topic, 0) + 1
        
        self._stats.total_topics = len(self._stats.topic_counts)
        
        if not self._stats.first_archived_at or stored.archived_at < self._stats.first_archived_at:
            self._stats.first_archived_at = stored.archived_at
        
        self._stats.last_archived_at = stored.archived_at
    
    def retrieve_by_id(self, message_id: str) -> Optional[StoredMessage]:
        """按ID检索"""
        return self._message_index.get(message_id)
    
    def retrieve_by_topic(self, topic: str, limit: int = 100) -> List[StoredMessage]:
        """按主题检索"""
        if topic not in self._topic_index:
            return []
        
        message_ids = self._topic_index[topic][:limit]
        return [self._message_index[id] for id in message_ids if id in self._message_index]
    
    def search_messages(
        self,
        keyword: str,
        limit: int = 50
    ) -> List[StoredMessage]:
        """搜索消息"""
        results = []
        keyword_lower = keyword.lower()
        
        for stored in self._message_index.values():
            content = stored.original_message.get("content", "").lower()
            if keyword_lower in content:
                results.append(stored)
                if len(results) >= limit:
                    break
        
        return results
    
    def _load_index(self):
        """加载现有索引"""
        # 简单实现 - 生产环境可以优化
        # 扫描目录加载最近的文件
        for day_dir in sorted(self.storage_root.glob("*"), reverse=True):
            if day_dir.is_dir():
                for jsonl_file in day_dir.glob("*.jsonl"):
                    try:
                        with open(jsonl_file, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        stored = StoredMessage.from_dict(data)
                                        self._update_index(stored)
                                        self._stats.total_archived += 1
                                    except:
                                        continue
                    except:
                        continue
            # 只加载最近3天的
            if len(self._message_index) > 1000:
                break
    
    def get_stats(self) -> StorageStats:
        """获取存储统计"""
        return self._stats
    
    def get_file_list(self) -> List[Path]:
        """获取所有存储文件列表"""
        files = []
        for item in self.storage_root.rglob("*.jsonl"):
            if item.is_file():
                files.append(item)
        return sorted(files, reverse=True)
