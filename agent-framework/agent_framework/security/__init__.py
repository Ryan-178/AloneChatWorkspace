"""
安全模块 - Security Module

提供统一的安全工具集，包括路径安全验证和动态安全扫描
Provides unified security toolset including path security validation and dynamic security scanning

模块组成 / Module Components:
- path_validator: 路径遍历防护 / Path traversal protection
- scanner: 动态安全扫描器 / Dynamic security scanner
"""

from .path_validator import PathValidator, validate_file_path
from .scanner import SecurityScanner, SecurityFinding, ScanReport, scan_project

__all__ = [
    "PathValidator",
    "validate_file_path",
    "SecurityScanner",
    "SecurityFinding",
    "ScanReport",
    "scan_project",
]