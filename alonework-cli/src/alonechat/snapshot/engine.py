"""
工作区快照引擎 / Workspace Snapshot Engine

基于side-git的快照/回滚机制
Side-git based snapshot/rollback mechanism
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SnapshotMeta:
    """
    快照元数据 / Snapshot Metadata
    """
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    workspace_path: str = ""
    branch_name: str = ""
    commit_hash: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "workspace_path": self.workspace_path,
            "branch_name": self.branch_name,
            "commit_hash": self.commit_hash,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMeta":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            workspace_path=data.get("workspace_path", ""),
            branch_name=data.get("branch_name", ""),
            commit_hash=data.get("commit_hash", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


class SnapshotEngine:
    """
    工作区快照引擎 / Workspace Snapshot Engine

    功能：
    - 创建工作区快照（基于git stash或独立分支）
    - 列出/搜索快照
    - 回滚到指定快照
    - 对比快照差异
    - 自动清理过期快照

    Features:
    - Create workspace snapshots (based on git stash or independent branch)
    - List/search snapshots
    - Rollback to specified snapshot
    - Compare snapshot differences
    - Auto cleanup expired snapshots
    """

    SNAPSHOTS_DIR = ".alonechat_snapshots"
    METADATA_FILE = "metadata.json"
    SIDE_GIT_BRANCH_PREFIX = "alonechat-snap-"

    def __init__(
        self,
        workspace_path: str,
        max_snapshots: int = 50,
        auto_cleanup: bool = True,
        retention_days: int = 30,
    ):
        self.workspace_path = Path(workspace_path).resolve()
        self.max_snapshots = max_snapshots
        self.auto_cleanup = auto_cleanup
        self.retention_days = retention_days

        self._snapshots_dir = self.workspace_path / self.SNAPSHOTS_DIR
        self._metadata_path = self._snapshots_dir / self.METADATA_FILE
        self._snapshots: Dict[str, SnapshotMeta] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """
        初始化快照引擎 / Initialize snapshot engine
        """
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

        if self._metadata_path.exists():
            try:
                with open(self._metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for snap_data in data.get("snapshots", []):
                        meta = SnapshotMeta.from_dict(snap_data)
                        self._snapshots[meta.id] = meta
            except Exception as e:
                logger.warning(f"Failed to load snapshot metadata: {e}")

        self._initialized = True
        logger.info(f"Snapshot engine initialized with {len(self._snapshots)} snapshots")

    async def _save_metadata(self) -> None:
        """
        保存元数据 / Save metadata
        """
        data = {
            "snapshots": [s.to_dict() for s in self._snapshots.values()],
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _run_git_command(self, *args: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """
        运行git命令 / Run git command
        """
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=cwd or self.workspace_path,
            capture_output=True,
            text=True,
        )

    def _is_git_repo(self) -> bool:
        """
        检查是否是git仓库 / Check if is git repository
        """
        result = self._run_git_command("rev-parse", "--is-inside-work-tree")
        return result.returncode == 0 and result.stdout.strip() == "true"

    async def create_snapshot(
        self,
        name: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        include_untracked: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SnapshotMeta:
        """
        创建快照 / Create snapshot

        Args:
            name: 快照名称
            description: 描述
            tags: 标签列表
            include_untracked: 是否包含未跟踪文件
            metadata: 额外元数据

        Returns:
            快照元数据
        """
        if not self._initialized:
            await self.initialize()

        snapshot_id = str(uuid.uuid4())[:8]
        branch_name = f"{self.SIDE_GIT_BRANCH_PREFIX}{snapshot_id}"
        commit_hash = ""

        if self._is_git_repo():
            result = self._run_git_command("stash", "push", "-m", f"snapshot-{snapshot_id}")
            if result.returncode != 0:
                logger.warning(f"Git stash failed: {result.stderr}")

            result = self._run_git_command("rev-parse", "HEAD")
            if result.returncode == 0:
                commit_hash = result.stdout.strip()

            result = self._run_git_command("branch", branch_name)
            if result.returncode != 0:
                logger.warning(f"Git branch creation failed: {result.stderr}")

        snapshot = SnapshotMeta(
            id=snapshot_id,
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            workspace_path=str(self.workspace_path),
            branch_name=branch_name,
            commit_hash=commit_hash,
            tags=tags or [],
            metadata=metadata or {},
        )

        self._snapshots[snapshot_id] = snapshot
        await self._save_metadata()

        logger.info(f"Created snapshot: {snapshot_id} - {name}")
        return snapshot

    async def list_snapshots(
        self,
        tag: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SnapshotMeta]:
        """
        列出快照 / List snapshots

        Args:
            tag: 按标签筛选
            limit: 最大数量
            offset: 偏移量

        Returns:
            快照列表
        """
        if not self._initialized:
            await self.initialize()

        snapshots = list(self._snapshots.values())

        if tag:
            snapshots = [s for s in snapshots if tag in s.tags]

        snapshots.sort(key=lambda s: s.created_at, reverse=True)

        return snapshots[offset:offset + limit]

    async def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotMeta]:
        """
        获取快照 / Get snapshot
        """
        if not self._initialized:
            await self.initialize()
        return self._snapshots.get(snapshot_id)

    async def rollback(
        self,
        snapshot_id: str,
        confirm: bool = False,
    ) -> bool:
        """
        回滚到快照 / Rollback to snapshot

        Args:
            snapshot_id: 快照ID
            confirm: 是否已确认（安全检查）

        Returns:
            是否成功
        """
        if not self._initialized:
            await self.initialize()

        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False

        if not confirm:
            logger.warning("Rollback requires confirmation")
            return False

        if self._is_git_repo():
            if snapshot.branch_name:
                result = self._run_git_command("checkout", snapshot.branch_name)
                if result.returncode != 0:
                    logger.error(f"Git checkout failed: {result.stderr}")
                    return False

            if snapshot.commit_hash:
                result = self._run_git_command("reset", "--hard", snapshot.commit_hash)
                if result.returncode != 0:
                    logger.error(f"Git reset failed: {result.stderr}")
                    return False

        logger.info(f"Rolled back to snapshot: {snapshot_id}")
        return True

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        删除快照 / Delete snapshot
        """
        if not self._initialized:
            await self.initialize()

        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        if self._is_git_repo() and snapshot.branch_name:
            result = self._run_git_command("branch", "-D", snapshot.branch_name)
            if result.returncode != 0:
                logger.warning(f"Failed to delete branch: {result.stderr}")

        del self._snapshots[snapshot_id]
        await self._save_metadata()

        logger.info(f"Deleted snapshot: {snapshot_id}")
        return True

    async def compare_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str,
    ) -> Dict[str, Any]:
        """
        对比两个快照 / Compare two snapshots
        """
        snap1 = self._snapshots.get(snapshot_id1)
        snap2 = self._snapshots.get(snapshot_id2)

        if not snap1 or not snap2:
            return {"error": "Snapshot not found"}

        if self._is_git_repo() and snap1.commit_hash and snap2.commit_hash:
            result = self._run_git_command(
                "diff", snap1.commit_hash, snap2.commit_hash, "--stat"
            )
            if result.returncode == 0:
                return {
                    "snapshot1": snapshot_id1,
                    "snapshot2": snapshot_id2,
                    "diff": result.stdout,
                }

        return {
            "snapshot1": snapshot_id1,
            "snapshot2": snapshot_id2,
            "diff": "Unable to compute diff",
        }

    async def cleanup_expired(self) -> int:
        """
        清理过期快照 / Cleanup expired snapshots
        """
        if not self._initialized:
            await self.initialize()

        cutoff = datetime.utcnow().timestamp() - (self.retention_days * 86400)
        removed = 0

        to_remove = []
        for snapshot_id, snapshot in self._snapshots.items():
            if snapshot.created_at.timestamp() < cutoff:
                to_remove.append(snapshot_id)

        for snapshot_id in to_remove:
            if await self.delete_snapshot(snapshot_id):
                removed += 1

        while len(self._snapshots) > self.max_snapshots:
            oldest = min(self._snapshots.values(), key=lambda s: s.created_at)
            if await self.delete_snapshot(oldest.id):
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired snapshots")

        return removed

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息 / Get statistics
        """
        return {
            "total_snapshots": len(self._snapshots),
            "max_snapshots": self.max_snapshots,
            "retention_days": self.retention_days,
            "workspace_path": str(self.workspace_path),
        }
