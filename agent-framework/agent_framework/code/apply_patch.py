"""
ApplyPatchTool - 文件补丁应用工具
File patch application tool.

Based on Codex's apply-patch crate:
- Parse unified diff patches
- Apply add/delete/update file changes
- Validate patches before applying
- Support relative and absolute paths
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class FileChangeType(str, Enum):
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"
    RENAME = "rename"


@dataclass
class FileChange:
    change_type: FileChangeType
    path: str
    content: str = ""
    old_content: str = ""
    new_content: str = ""
    unified_diff: str = ""
    move_path: Optional[str] = None


@dataclass
class PatchHunk:
    source_start: int = 0
    source_count: int = 0
    target_start: int = 0
    target_count: int = 0
    lines: List[str] = field(default_factory=list)


@dataclass
class PatchResult:
    success: bool = False
    applied_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    changes: List[FileChange] = field(default_factory=list)
    details: str = ""


PATCH_HEADER_PATTERN = re.compile(
    r'^--- (.+?)\s.*$|^\+\+\+ (.+?)\s.*$', re.MULTILINE
)
HUNK_HEADER_PATTERN = re.compile(
    r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
)


def parse_patch(patch_text: str, workdir: str = ".") -> List[FileChange]:
    """解析统一 diff 格式的补丁"""
    changes = []
    sections = re.split(r'(?=^--- )', patch_text, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if not section:
            continue
        old_match = re.search(r'^--- (.+?)(?:\s.*)?$', section, re.MULTILINE)
        new_match = re.search(r'^\+\+\+ (.+?)(?:\s.*)?$', section, re.MULTILINE)
        if old_match and new_match:
            old_path = old_match.group(1).strip()
            new_path = new_match.group(1).strip()
            if old_path == '/dev/null':
                content_lines = []
                for line in section.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        content_lines.append(line[1:])
                changes.append(FileChange(
                    change_type=FileChangeType.ADD,
                    path=_resolve_path(new_path, workdir),
                    content='\n'.join(content_lines),
                    new_content='\n'.join(content_lines),
                ))
            elif new_path == '/dev/null':
                changes.append(FileChange(
                    change_type=FileChangeType.DELETE,
                    path=_resolve_path(old_path, workdir),
                    unified_diff=section,
                ))
            elif old_path != new_path:
                changes.append(FileChange(
                    change_type=FileChangeType.RENAME,
                    path=_resolve_path(old_path, workdir),
                    move_path=_resolve_path(new_path, workdir),
                    unified_diff=section,
                ))
            else:
                changes.append(FileChange(
                    change_type=FileChangeType.UPDATE,
                    path=_resolve_path(old_path, workdir),
                    unified_diff=section,
                ))
    return changes


def _resolve_path(path_str: str, workdir: str) -> str:
    if path_str.startswith('a/') or path_str.startswith('b/'):
        path_str = path_str[2:]
    path = Path(path_str)
    if not path.is_absolute():
        path = Path(workdir) / path
    return str(path.resolve())


def _parse_hunks(diff_text: str) -> List[PatchHunk]:
    hunks = []
    current_hunk = None
    for line in diff_text.split('\n'):
        match = HUNK_HEADER_PATTERN.match(line)
        if match:
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = PatchHunk(
                source_start=int(match.group(1)),
                source_count=int(match.group(2) or '1'),
                target_start=int(match.group(3)),
                target_count=int(match.group(4) or '1'),
            )
        elif current_hunk is not None:
            current_hunk.lines.append(line)
    if current_hunk:
        hunks.append(current_hunk)
    return hunks


def _apply_hunks_to_content(content: str, hunks: List[PatchHunk]) -> str:
    lines = content.split('\n')
    result = []
    source_line = 1
    for hunk in hunks:
        while source_line < hunk.source_start and source_line <= len(lines):
            result.append(lines[source_line - 1])
            source_line += 1
        for hunk_line in hunk.lines:
            if hunk_line.startswith('-'):
                if source_line <= len(lines):
                    source_line += 1
            elif hunk_line.startswith('+'):
                result.append(hunk_line[1:])
            elif hunk_line.startswith(' '):
                if source_line <= len(lines):
                    result.append(lines[source_line - 1])
                    source_line += 1
            elif hunk_line.startswith('\\'):
                pass
    while source_line <= len(lines):
        result.append(lines[source_line - 1])
        source_line += 1
    return '\n'.join(result)


class ApplyPatchTool:
    """文件补丁应用工具"""

    def __init__(self, workdir: str = ".", dry_run: bool = False):
        self.workdir = os.path.abspath(workdir)
        self.dry_run = dry_run
        self._applied_patches: List[PatchResult] = []

    def validate_patch(self, patch_text: str) -> Tuple[bool, List[str]]:
        """验证补丁格式"""
        errors = []
        changes = parse_patch(patch_text, self.workdir)
        if not changes:
            errors.append("No valid file changes found in patch")
            return False, errors
        for change in changes:
            path = Path(change.path)
            if change.change_type == FileChangeType.ADD:
                if path.exists():
                    errors.append(f"File already exists: {change.path}")
            elif change.change_type == FileChangeType.DELETE:
                if not path.exists():
                    errors.append(f"File does not exist: {change.path}")
            elif change.change_type == FileChangeType.UPDATE:
                if not path.exists():
                    errors.append(f"File does not exist for update: {change.path}")
                elif not change.unified_diff:
                    errors.append(f"No diff provided for update: {change.path}")
        return len(errors) == 0, errors

    def apply(self, patch_text: str) -> PatchResult:
        """应用补丁"""
        result = PatchResult()
        is_valid, errors = self.validate_patch(patch_text)
        if not is_valid:
            result.errors = errors
            result.details = f"Patch validation failed: {'; '.join(errors)}"
            return result
        changes = parse_patch(patch_text, self.workdir)
        for change in changes:
            try:
                if self.dry_run:
                    result.applied_files.append(change.path)
                    result.changes.append(change)
                    continue
                if change.change_type == FileChangeType.ADD:
                    self._apply_add(change)
                elif change.change_type == FileChangeType.DELETE:
                    self._apply_delete(change)
                elif change.change_type == FileChangeType.UPDATE:
                    self._apply_update(change)
                elif change.change_type == FileChangeType.RENAME:
                    self._apply_rename(change)
                result.applied_files.append(change.path)
                result.changes.append(change)
            except Exception as e:
                result.errors.append(f"Error applying {change.path}: {e}")
        result.success = len(result.errors) == 0
        result.details = (
            f"Applied {len(result.applied_files)} changes"
            + (f", {len(result.errors)} errors" if result.errors else "")
        )
        self._applied_patches.append(result)
        return result

    def _apply_add(self, change: FileChange) -> None:
        path = Path(change.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change.content, encoding='utf-8')

    def _apply_delete(self, change: FileChange) -> None:
        path = Path(change.path)
        if path.exists():
            path.unlink()

    def _apply_update(self, change: FileChange) -> None:
        path = Path(change.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {change.path}")
        current_content = path.read_text(encoding='utf-8')
        hunks = _parse_hunks(change.unified_diff)
        if hunks:
            new_content = _apply_hunks_to_content(current_content, hunks)
        else:
            new_content = change.new_content or current_content
        path.write_text(new_content, encoding='utf-8')
        change.new_content = new_content

    def _apply_rename(self, change: FileChange) -> None:
        src = Path(change.path)
        dst = Path(change.move_path)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)

    def get_history(self) -> List[PatchResult]:
        return self._applied_patches.copy()

    def preview(self, patch_text: str) -> Dict[str, Any]:
        """预览补丁效果，不实际应用"""
        changes = parse_patch(patch_text, self.workdir)
        preview_data = []
        for change in changes:
            entry = {
                "type": change.change_type.value,
                "path": change.path,
            }
            if change.change_type == FileChangeType.UPDATE:
                path = Path(change.path)
                if path.exists():
                    current = path.read_text(encoding='utf-8')
                    hunks = _parse_hunks(change.unified_diff)
                    if hunks:
                        entry["new_content"] = _apply_hunks_to_content(current, hunks)
            elif change.change_type == FileChangeType.ADD:
                entry["content"] = change.content
            preview_data.append(entry)
        return {
            "file_count": len(changes),
            "changes": preview_data,
        }
