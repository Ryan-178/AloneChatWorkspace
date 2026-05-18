"""
AloneChat CLI - 国产化、终端原生、深度中文优化的AI编程Agent

核心原则：
- 本地部署优先：所有核心功能本地运行
- API调用模式：通过API调用外部模型，代码不上传
- 隐私保护：用户代码完全本地化，不经过云端
- 离线支持：支持本地模型，完全离线可用
"""

__version__ = "0.2.0"
__author__ = "AloneChat Team"
__email__ = "alonechatworkspace@163.com"

from alonechat.cli import main

__all__ = ["main"]
