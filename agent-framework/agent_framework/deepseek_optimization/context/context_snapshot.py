"""
Context Snapshot
上下文快照 - 保存和恢复完整的上下文状态
"""
import json
import gzip
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class SnapshotMetadata:
    snapshot_id: str
    session_id: str
    created_at: datetime
    message_count: int
    token_count: int
    snapshot_type: str  # "full", "incremental"
    parent_snapshot_id: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "message_count": self.message_count,
            "token_count": self.token_count,
            "snapshot_type": self.snapshot_type,
            "parent_snapshot_id": self.parent_snapshot_id,
            "description": self.description,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        return cls(
            snapshot_id=data["snapshot_id"],
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            message_count=data["message_count"],
            token_count=data["token_count"],
            snapshot_type=data["snapshot_type"],
            parent_snapshot_id=data.get("parent_snapshot_id"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class SnapshotData:
    messages: List[Dict[str, Any]]
    managed_messages: List[Dict[str, Any]]
    stats: Dict[str, Any]
    custom_data: Dict[str, Any] = field(default_factory=dict)


class ContextSnapshot:
    """
    上下文快照管理器
    支持完整快照和增量快照
    """
    
    def __init__(
        self,
        storage_root: Path,
        compress: bool = True,
        max_snapshots_per_session: int = 10,
    ):
        self.storage_root = storage_root
        self.compress = compress
        self.max_snapshots_per_session = max_snapshots_per_session
        
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        self._snapshot_index: Dict[str, SnapshotMetadata] = {}
        self._load_index()
    
    def _load_index(self):
        index_file = self.storage_root / "snapshot_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for snap_id, meta_dict in data.items():
                        self._snapshot_index[snap_id] = SnapshotMetadata.from_dict(meta_dict)
            except Exception:
                pass
    
    def _save_index(self):
        index_file = self.storage_root / "snapshot_index.json"
        data = {sid: meta.to_dict() for sid, meta in self._snapshot_index.items()}
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        return self.storage_root / "snapshots" / f"{snapshot_id}.json.gz" if self.compress else f"{snapshot_id}.json"
    
    def create_snapshot(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        managed_messages: Optional[List[Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        token_count: int = 0,
        description: str = "",
        tags: Optional[List[str]] = None,
        parent_snapshot_id: Optional[str] = None,
        snapshot_type: str = "full",
    ) -> SnapshotMetadata:
        snapshot_id = str(uuid.uuid4())
        now = datetime.now()
        
        managed_data = []
        if managed_messages:
            for m in managed_messages:
                if hasattr(m, 'message') and hasattr(m, 'importance'):
                    managed_data.append({
                        "message": m.message,
                        "importance": {
                            "score": m.importance.score,
                            "category": m.importance.category.value,
                            "reasoning": m.importance.reasoning,
                            "topics": m.importance.topics,
                        },
                        "keep_in_context": getattr(m, 'keep_in_context', True),
                    })
        
        snapshot_data = SnapshotData(
            messages=messages,
            managed_messages=managed_data,
            stats=stats or {},
        )
        
        self._write_snapshot(snapshot_id, snapshot_data)
        
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            session_id=session_id,
            created_at=now,
            message_count=len(messages),
            token_count=token_count,
            snapshot_type=snapshot_type,
            parent_snapshot_id=parent_snapshot_id,
            description=description,
            tags=tags or [],
        )
        
        self._snapshot_index[snapshot_id] = metadata
        self._save_index()
        
        self._cleanup_old_snapshots(session_id)
        
        return metadata
    
    def _write_snapshot(self, snapshot_id: str, data: SnapshotData):
        snapshot_path = self._get_snapshot_path(snapshot_id)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        json_data = json.dumps({
            "messages": data.messages,
            "managed_messages": data.managed_messages,
            "stats": data.stats,
            "custom_data": data.custom_data,
        }, ensure_ascii=False)
        
        if self.compress:
            with gzip.open(snapshot_path, "wt", encoding="utf-8") as f:
                f.write(json_data)
        else:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                f.write(json_data)
    
    def load_snapshot(self, snapshot_id: str) -> Optional[SnapshotData]:
        snapshot_path = self._get_snapshot_path(snapshot_id)
        
        if not snapshot_path.exists():
            return None
        
        try:
            if self.compress:
                with gzip.open(snapshot_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with open(snapshot_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            return SnapshotData(
                messages=data["messages"],
                managed_messages=data["managed_messages"],
                stats=data["stats"],
                custom_data=data.get("custom_data", {}),
            )
        except Exception:
            return None
    
    def get_snapshot_metadata(self, snapshot_id: str) -> Optional[SnapshotMetadata]:
        return self._snapshot_index.get(snapshot_id)
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        snapshot_path = self._get_snapshot_path(snapshot_id)
        
        deleted = False
        if snapshot_path.exists():
            snapshot_path.unlink()
            deleted = True
        
        if snapshot_id in self._snapshot_index:
            del self._snapshot_index[snapshot_id]
            self._save_index()
            deleted = True
        
        return deleted
    
    def list_snapshots(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[SnapshotMetadata]:
        snapshots = []
        
        for meta in self._snapshot_index.values():
            if session_id and meta.session_id != session_id:
                continue
            snapshots.append(meta)
        
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        
        return snapshots[:limit]
    
    def get_latest_snapshot(self, session_id: str) -> Optional[SnapshotMetadata]:
        session_snapshots = [
            meta for meta in self._snapshot_index.values()
            if meta.session_id == session_id
        ]
        
        if not session_snapshots:
            return None
        
        return max(session_snapshots, key=lambda s: s.created_at)
    
    def _cleanup_old_snapshots(self, session_id: str):
        session_snapshots = [
            meta for meta in self._snapshot_index.values()
            if meta.session_id == session_id
        ]
        
        if len(session_snapshots) <= self.max_snapshots_per_session:
            return
        
        session_snapshots.sort(key=lambda s: s.created_at, reverse=True)
        
        for meta in session_snapshots[self.max_snapshots_per_session:]:
            self.delete_snapshot(meta.snapshot_id)
    
    def create_incremental_snapshot(
        self,
        session_id: str,
        new_messages: List[Dict[str, Any]],
        parent_snapshot_id: str,
        token_count: int = 0,
        description: str = "",
    ) -> SnapshotMetadata:
        parent_data = self.load_snapshot(parent_snapshot_id)
        if parent_data is None:
            return self.create_snapshot(
                session_id=session_id,
                messages=new_messages,
                token_count=token_count,
                description=description,
                snapshot_type="full",
            )
        
        combined_messages = parent_data.messages + new_messages
        
        return self.create_snapshot(
            session_id=session_id,
            messages=combined_messages,
            token_count=parent_data.stats.get("total_tokens", 0) + token_count,
            description=description,
            parent_snapshot_id=parent_snapshot_id,
            snapshot_type="incremental",
        )
    
    def get_snapshot_chain(self, snapshot_id: str) -> List[SnapshotMetadata]:
        chain = []
        current_id = snapshot_id
        
        while current_id:
            meta = self._snapshot_index.get(current_id)
            if meta is None:
                break
            chain.append(meta)
            current_id = meta.parent_snapshot_id
        
        return chain
    
    def get_storage_stats(self) -> Dict[str, Any]:
        total_snapshots = len(self._snapshot_index)
        total_size = 0
        total_messages = 0
        total_tokens = 0
        
        for meta in self._snapshot_index.values():
            snapshot_path = self._get_snapshot_path(meta.snapshot_id)
            if snapshot_path.exists():
                total_size += snapshot_path.stat().st_size
            total_messages += meta.message_count
            total_tokens += meta.token_count
        
        return {
            "total_snapshots": total_snapshots,
            "total_size_bytes": total_size,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "compression_enabled": self.compress,
        }
