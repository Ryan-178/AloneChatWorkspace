from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryEntry(BaseModel):
    id: Optional[str] = Field(default=None)
    content: str = Field(..., description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    embedding: Optional[List[float]] = Field(default=None)
    score: Optional[float] = Field(default=None, description="Similarity score for query results")


class BaseMemory(ABC):
    @abstractmethod
    def add(self, entry: MemoryEntry) -> None:
        pass

    @abstractmethod
    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
