"""
AloneWork CLI - 国产化、终端原生、深度中文优化的AI编程Agent

AloneWork CLI - AI coding agent with native terminal support and deep Chinese optimization

核心原则 / Core Principles:
- 本地部署优先：所有核心功能本地运行 / Local-first: All core features run locally
- API调用模式：通过API调用外部模型，代码不上传 / API mode: Call external models via API, code stays local
- 隐私保护：用户代码完全本地化，不经过云端 / Privacy: User code stays local, never goes to cloud
- 离线支持：支持本地模型，完全离线可用 / Offline: Support local models, fully offline capable
"""

__version__ = "0.2.0"
__author__ = "AloneWork Team"
__email__ = "aloneworkworkspace@163.com"

from alonework.cli import main

__all__ = ["main"]
