"""
快照模块 / Snapshot Module

工作区快照和回滚功能
Workspace snapshot and rollback functionality
"""

from .engine import SnapshotEngine, SnapshotMeta

__all__ = ["SnapshotEngine", "SnapshotMeta"]
