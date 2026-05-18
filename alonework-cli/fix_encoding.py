#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码修复脚本 / Encoding Fix Script

修复 Python 文件的编码问题，将乱码的中文字符修复为正确的 UTF-8 编码
Fix encoding issues in Python files, converting garbled Chinese characters to correct UTF-8 encoding
"""

import os
import chardet
from pathlib import Path
from typing import Optional, Tuple

# 需要修复的文件列表 / Files to fix
FILES_TO_FIX = [
    "src/alonework/utils/__init__.py",
    "src/alonework/utils/progress.py",
    "src/alonework/utils/streaming.py",
    "src/alonework/utils/thinking_block.py",
    "src/alonework/utils/logger.py",
    "src/alonework/utils/interactive.py",
    "src/alonework/commands/chat.py",
    "src/alonework/commands/generate.py",
    "src/alonework/commands/commit.py",
    "src/alonework/commands/test.py",
    "src/alonework/commands/agent.py",
    "src/alonework/deepseek/__init__.py",
    "src/alonework/deepseek/context_manager.py",
    "src/alonework/deepseek/prompt_engineer.py",
    "src/alonework/lsp/__init__.py",
    "src/alonework/lsp/client.py",
    "src/alonework/mcp/cli.py",
    "src/alonework/mcp/config.py",
    "src/alonework/input/__init__.py",
    "src/alonework/input/session.py",
    "src/alonework/input/history.py",
    "src/alonework/input/key_bindings.py",
    "src/alonework/input/external_editor.py",
    "src/alonework/background/__init__.py",
    "src/alonework/background/manager.py",
    "src/alonework/background/task.py",
    "src/alonework/background/agent_runner.py",
    "src/alonework/agents/__init__.py",
    "src/alonework/agents/definition.py",
    "src/alonework/agents/executor.py",
    "src/alonework/agents/manager.py",
    "src/alonework/chinese/__init__.py",
    "src/alonework/chinese/nlp.py",
    "src/alonework/chinese/code_style.py",
    "src/alonework/code/generator.py",
    "src/alonework/git/__init__.py",
    "src/alonework/git/git_manager.py",
    "src/alonework/git/smart_commit.py",
    "src/alonework/permissions/__init__.py",
    "src/alonework/permissions/manager.py",
    "src/alonework/permissions/prompts.py",
    "src/alonework/permissions/rules.py",
    "src/alonework/planning/__init__.py",
    "src/alonework/execution/__init__.py",
    "src/alonework/slash/__init__.py",
    "src/alonework/slash/executor.py",
    "src/alonework/slash/parser.py",
    "src/alonework/slash/registry.py",
    "src/alonework/slash/custom_loader.py",
    "src/alonework/slash/command_skill_bridge.py",
    "src/alonework/configs/config_loader.py",
    "src/alonework/configs/style_loader.py",
]

# 已知正确编码的文件（不需要修复）/ Files with correct encoding (no need to fix)
SKIP_FILES = [
    "src/alonework/context/__init__.py",
    "src/alonework/session/__init__.py",
    "src/alonework/session/manager.py",
    "src/alonework/session/storage.py",
    "src/alonework/models/__init__.py",
    "src/alonework/config/__init__.py",
    "src/alonework/commands/init.py",
    "src/alonework/cli.py",
    "src/alonework/__init__.py",
]

def detect_encoding(file_path: Path) -> Tuple[str, float]:
    """
    检测文件编码 / Detect file encoding
    
    Args:
        file_path: 文件路径 / File path
        
    Returns:
        (编码名称, 置信度) / (encoding name, confidence)
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    result = chardet.detect(raw_data)
    return result['encoding'], result['confidence']

def try_read_with_encoding(file_path: Path, encoding: str) -> Optional[str]:
    """
    尝试用指定编码读取文件 / Try to read file with specified encoding
    
    Args:
        file_path: 文件路径 / File path
        encoding: 编码名称 / Encoding name
        
    Returns:
        文件内容或 None / File content or None
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='strict') as f:
            return f.read()
    except (UnicodeDecodeError, LookupError):
        return None

def has_garbled_chinese(content: str) -> bool:
    """
    检查内容是否有乱码中文字符 / Check if content has garbled Chinese characters
    
    Args:
        content: 文件内容 / File content
        
    Returns:
        是否有乱码 / Whether has garbled characters
    """
    garbled_patterns = [
        'å', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï',
        'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', 'ø', 'ù', 'ú',
        'û', 'ü', 'ý', 'þ', 'ÿ',
        '鏃', 'ュ', '織', '绯', '荤', '粺', '妯', '″', '潡',
        '宸', 'ュ', '叿', '妯', '″', '潡',
        '鍖', '呭', '惈', '锛',
    ]
    
    for pattern in garbled_patterns:
        if pattern in content:
            return True
    
    return False

def fix_file_encoding(file_path: Path, base_dir: Path) -> bool:
    """
    修复单个文件的编码 / Fix encoding of a single file
    
    Args:
        file_path: 文件路径 / File path
        base_dir: 基础目录 / Base directory
        
    Returns:
        是否成功修复 / Whether successfully fixed
    """
    full_path = base_dir / file_path
    
    if not full_path.exists():
        print(f"  [跳过] 文件不存在: {file_path}")
        return False
    
    print(f"  [检查] {file_path}")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not has_garbled_chinese(content):
            print(f"  [正常] UTF-8 编码正确，无需修复")
            return True
        
        print(f"  [问题] 发现乱码，尝试修复...")
        
    except UnicodeDecode