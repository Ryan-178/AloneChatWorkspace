"""
路径安全验证器 - Path Security Validator

提供统一的路径遍历防护机制
Provides unified path traversal protection
"""
import os
import re
from pathlib import Path
from typing import Optional, Set


class PathValidator:
    """
    路径安全验证器 - Path Security Validator

    防止路径遍历攻击，确保文件操作仅限于安全目录内
    Prevents path traversal attacks, ensuring file operations are limited to safe directories

    用法 / Usage:
        validator = PathValidator(allowed_base="/path/to/project")
        if validator.is_safe_path("/path/to/project/file.txt"):
            # 安全执行 / Safe to proceed
    """

    def __init__(
        self,
        allowed_base: Optional[str] = None,
        blocked_paths: Optional[Set[str]] = None,
    ):
        self.allowed_base = Path(allowed_base).resolve() if allowed_base else None
        self.blocked_paths = blocked_paths or {
            "/etc", "/sys", "/proc", "/dev",
            "C:\\Windows\\System32", "C:\\Windows", "C:\\Program Files",
        }

    def is_safe_path(self, path: str, check_traversal: bool = True) -> bool:
        """
        检查路径是否安全 - Check if path is safe

        Args:
            path: 要检查的路径 / Path to check
            check_traversal: 是否检查路径遍历 / Whether to check path traversal

        Returns:
            是否安全 / Whether safe
        """
        try:
            resolved = Path(path).resolve()

            if check_traversal:
                for block in self.blocked_paths:
                    if str(resolved).lower().startswith(block.lower()):
                        return False

            if self.allowed_base:
                try:
                    resolved.relative_to(self.allowed_base)
                    return True
                except ValueError:
                    return False

            return True
        except (OSError, ValueError, RuntimeError):
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        净化文件名，移除危险字符 - Sanitize filename, remove dangerous characters

        Args:
            filename: 原始文件名 / Original filename

        Returns:
            净化后的文件名 / Sanitized filename
        """
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        sanitized = sanitized.strip('.')
        sanitized = sanitized.strip()
        return sanitized or "unnamed"

    def sanitize_session_id(self, session_id: str) -> str:
        """
        净化会话ID，防止路径遍历 - Sanitize session ID, prevent path traversal

        Args:
            session_id: 原始会话ID / Original session ID

        Returns:
            净化后的会话ID / Sanitized session ID
        """
        sanitized = re.sub(r'[^\w\-\.]', '', session_id)
        sanitized = sanitized.strip('.')
        return sanitized or "invalid"

    def sanitize_skill_name(self, name: str) -> str:
        """
        净化Skill名称，防止路径遍历 - Sanitize skill name, prevent path traversal

        Args:
            name: 原始Skill名称 / Original skill name

        Returns:
            净化后的Skill名称 / Sanitized skill name
        """
        sanitized = re.sub(r'[^\w\-\.]', '', name)
        sanitized = sanitized.strip('.')
        return sanitized or "unknown-skill"

    @staticmethod
    def resolve_safe_path(path: str, allowed_base: str) -> Optional[Path]:
        """
        安全解析路径，确保在允许的基目录内 - Safely resolve path within allowed base directory

        参考 / Reference: agent_framework/rag/loader.py _resolve_safe_path

        Args:
            path: 要解析的路径 / Path to resolve
            allowed_base: 允许的基目录 / Allowed base directory

        Returns:
            安全解析后的Path对象，如果不安全则返回None / Safely resolved Path, or None if unsafe
        """
        try:
            resolved = Path(path).resolve()
            base = Path(allowed_base).resolve()

            resolved.relative_to(base)

            if not resolved.exists():
                return resolved

            if resolved.is_symlink():
                link_target = resolved.resolve()
                try:
                    link_target.relative_to(base)
                except ValueError:
                    return None

            return resolved
        except (ValueError, OSError, RuntimeError):
            return None


def validate_file_path(path: str, allowed_base: Optional[str] = None) -> Optional[Path]:
    """
    便捷函数：验证文件路径是否安全 - Convenience function: validate file path safety

    Args:
        path: 文件路径 / File path
        allowed_base: 允许的基目录（可选）/ Allowed base directory (optional)

    Returns:
        安全的Path对象，不安全则返回None / Safe Path object, or None if unsafe
    """
    return PathValidator.resolve_safe_path(path, allowed_base) if allowed_base else None
