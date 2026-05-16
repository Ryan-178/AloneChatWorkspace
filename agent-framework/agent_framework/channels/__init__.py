"""
通道适配器模块 - Channel Adapters
支持多种聊天应用的集成
"""
from .base import BaseChannel, ChannelMessage, ChannelUser
from .chat_app import ChatAppChannel

__all__ = [
    'BaseChannel',
    'ChannelMessage',
    'ChannelUser',
    'ChatAppChannel'
]
