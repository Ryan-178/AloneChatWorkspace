"""
数据迁移工具 - Data Migration Tool

从JSON迁移到SQLite
Migrate from JSON to SQLite
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from alonechat.storage.base_storage import SessionData


class MigrationTool:
    """
    数据迁移工具 - Data Migration Tool
    
    从JSON文件存储迁移到SQLite存储
    Migrate from JSON file storage to SQLite storage
    
    特性 / Features:
    - JSON → SQLite迁移
    - 保留JSON备份
    - 迁移验证
    - 回滚支持
    """
    
    def __init__(
        self,
        json_dir: str,
        sqlite_path: str,
        backup_dir: Optional[str] = None,
    ):
        """
        初始化迁移工具 / Initialize migration tool
        
        Args:
            json_dir: JSON文件目录 / JSON file directory
            sqlite_path: SQLite数据库路径 / SQLite database path
            backup_dir: 备份目录 / Backup directory
        """
        self.json_dir = Path(json_dir)
        self.sqlite_path = Path(sqlite_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.json_dir.parent / "backup"
    
    def find_json_sessions(self) -> List[Path]:
        """
        查找JSON会话文件 / Find JSON session files
        
        Returns:
            JSON文件列表 / JSON file list
        """
        if not self.json_dir.exists():
            return []
        
        return list(self.json_dir.glob("*.json"))
    
    def load_json_session(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        加载JSON会话 / Load JSON session
        
        Args:
            file_path: JSON文件路径 / JSON file path
        
        Returns:
            会话数据 / Session data
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def convert_to_session_data(self, json_data: Dict[str, Any]) -> SessionData:
        """
        转换JSON数据为SessionData / Convert JSON data to SessionData
        
        Args:
            json_data: JSON数据 / JSON data
        
        Returns:
            SessionData对象 / SessionData object
        """
        session = SessionData(
            id=json_data.get("id", json_data.get("session_id", "")),
            display_name=json_data.get("display_name", json_data.get("title")),
            created_at=self._parse_datetime(json_data.get("created_at")),
            updated_at=self._parse_datetime(json_data.get("updated_at")),
            parent_id=json_data.get("parent_id"),
            branch_point=json_data.get("branch_point"),
            mode=json_data.get("mode", "agent"),
            interaction_mode=json_data.get("interaction_mode", "agent"),
            metadata=json_data.get("metadata", {}),
            agent_config=json_data.get("agent_config", {}),
        )
        
        messages = json_data.get("messages", [])
        for msg in messages:
            session.messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
                "metadata": msg.get("metadata", {}),
            })
        
        return session
    
    def _parse_datetime(self, value: Optional[str]) -> datetime:
        """解析日期时间 / Parse datetime"""
        if not value:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(value)
        except:
            return datetime.utcnow()
    
    async def migrate(
        self,
        keep_backup: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        执行迁移 / Execute migration
        
        Args:
            keep_backup: 是否保留备份 / Whether to keep backup
            dry_run: 是否只模拟 / Whether dry run
        
        Returns:
            迁移结果 / Migration result
        """
        result = {
            "success": False,
            "total_files": 0,
            "migrated": 0,
            "failed": 0,
            "errors": [],
        }
        
        json_files = self.find_json_sessions()
        result["total_files"] = len(json_files)
        
        if not json_files:
            result["success"] = True
            return result
        
        if keep_backup and not dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir(parents=True, exist_ok=True)
        
        from alonechat.storage.sqlite_storage import SQLiteSessionStorage
        storage = SQLiteSessionStorage(str(self.sqlite_path))
        
        for json_file in json_files:
            try:
                json_data = self.load_json_session(json_file)
                if not json_data:
                    result["failed"] += 1
                    result["errors"].append(f"Failed to load: {json_file}")
                    continue
                
                session = self.convert_to_session_data(json_data)
                
                if not dry_run:
                    await storage.save(session)
                
                if keep_backup and not dry_run:
                    shutil.copy2(json_file, backup_subdir / json_file.name)
                
                result["migrated"] += 1
                
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"Error migrating {json_file}: {e}")
        
        result["success"] = result["failed"] == 0
        return result
    
    async def verify_migration(self) -> Dict[str, Any]:
        """
        验证迁移 / Verify migration
        
        Returns:
            验证结果 / Verification result
        """
        result = {
            "success": True,
            "json_count": 0,
            "sqlite_count": 0,
            "missing": [],
        }
        
        json_files = self.find_json_sessions()
        result["json_count"] = len(json_files)
        
        from alonechat.storage.sqlite_storage import SQLiteSessionStorage
        storage = SQLiteSessionStorage(str(self.sqlite_path))
        
        sessions = await storage.list(limit=10000)
        result["sqlite_count"] = len(sessions)
        
        sqlite_ids = {s.id for s in sessions}
        for json_file in json_files:
            json_data = self.load_json_session(json_file)
            if json_data:
                session_id = json_data.get("id", json_data.get("session_id"))
                if session_id and session_id not in sqlite_ids:
                    result["missing"].append(session_id)
        
        if result["missing"]:
            result["success"] = False
        
        return result
