"""
Audit Logger
审计日志 - 合规性记录
"""
import json
import time
import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    action: str
    resource: str
    success: bool
    metadata: Dict[str, Any]
    duration_ms: Optional[float] = None


class AuditLogger:
    """
    审计日志记录器
    用于记录系统操作，满足合规性要求
    提供日志完整性保护（HMAC 签名）
    """

    def __init__(self, log_dir: Optional[str] = None, secret_key: Optional[str] = None):
        self.log_dir = Path(log_dir) if log_dir else Path("./logs/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._logs: List[AuditLogEntry] = []

        # 使用提供的密钥或生成一个随机密钥
        # 生产环境应该从安全存储（如环境变量、KMS）获取
        if secret_key:
            self._secret_key = secret_key.encode("utf-8")
        else:
            # 尝试从环境变量获取，否则生成随机密钥（每次重启会变化，仅用于开发）
            import os
            env_key = os.environ.get("AUDIT_LOG_SECRET_KEY")
            if env_key:
                self._secret_key = env_key.encode("utf-8")
            else:
                self._secret_key = secrets.token_bytes(32)

        # 用于哈希链的上一条日志哈希
        self._previous_hash: Optional[str] = None

    def _compute_hmac(self, log_data: Dict[str, Any]) -> str:
        """计算日志条目的 HMAC 签名"""
        # 将日志数据按固定顺序序列化
        canonical = json.dumps(log_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hmac.new(
            self._secret_key,
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _compute_hash_chain(self, log_data: Dict[str, Any]) -> str:
        """计算哈希链值"""
        canonical = json.dumps(log_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if self._previous_hash:
            canonical = self._previous_hash + canonical
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def log_access(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ):
        """记录访问事件"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            event_type="ACCESS",
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            metadata=metadata or {},
            duration_ms=duration_ms,
        )
        self._logs.append(entry)
        self._write_log(entry)

    def log_modification(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录修改事件"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            event_type="MODIFICATION",
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            metadata=metadata or {},
        )
        self._logs.append(entry)
        self._write_log(entry)

    def log_error(
        self,
        user_id: Optional[str],
        error_type: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录错误事件"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            event_type="ERROR",
            user_id=user_id,
            action=error_type,
            resource="SYSTEM",
            success=False,
            metadata={
                "error_message": error_message,
                **(metadata or {}),
            },
        )
        self._logs.append(entry)
        self._write_log(entry)

    def _write_log(self, entry: AuditLogEntry):
        """写入日志文件 - 带 HMAC 签名和哈希链"""
        log_file = self.log_dir / f"audit_{entry.timestamp.strftime('%Y%m%d')}.jsonl"

        log_data = {
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "user_id": entry.user_id,
            "action": entry.action,
            "resource": entry.resource,
            "success": entry.success,
            "duration_ms": entry.duration_ms,
            "metadata": entry.metadata,
        }

        # 计算 HMAC 签名
        hmac_signature = self._compute_hmac(log_data)

        # 计算哈希链
        hash_chain = self._compute_hash_chain(log_data)

        # 构建带完整性保护的日志记录
        protected_log = {
            "data": log_data,
            "integrity": {
                "hmac": hmac_signature,
                "hash_chain": hash_chain,
                "previous_hash": self._previous_hash,
            }
        }

        # 更新上一条哈希
        self._previous_hash = hash_chain

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(protected_log, ensure_ascii=False) + "\n")

    def verify_log_file(self, date_str: Optional[str] = None) -> bool:
        """
        验证日志文件的完整性
        返回 True 如果所有记录验证通过，否则返回 False
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')

        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        if not log_file.exists():
            return True  # 文件不存在，视为验证通过

        previous_hash = None
        with open(log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    return False

                data = record.get("data", {})
                integrity = record.get("integrity", {})
                stored_hmac = integrity.get("hmac")
                stored_hash_chain = integrity.get("hash_chain")
                stored_previous_hash = integrity.get("previous_hash")

                # 验证 HMAC
                computed_hmac = self._compute_hmac(data)
                if not hmac.compare_digest(computed_hmac, stored_hmac):
                    return False

                # 验证哈希链连续性
                if stored_previous_hash != previous_hash:
                    return False

                # 验证哈希链值
                canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                if previous_hash:
                    canonical = previous_hash + canonical
                computed_hash_chain = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if not hmac.compare_digest(computed_hash_chain, stored_hash_chain):
                    return False

                previous_hash = stored_hash_chain

        return True

    def get_logs(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """获取审计日志"""
        filtered = self._logs

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]

        return filtered[-limit:]
