"""
通道适配器示例
展示如何使用BaseChannel和ChatAppChannel
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework.observability.logger import get_logger, LogLevel
from agent_framework.channels.base import ChannelMessage, ChannelUser, MessageType
from agent_framework.channels.chat_app import ChatAppChannel


# 初始化日志
logger = get_logger("channel_example", level=LogLevel.INFO)


async def example_chat_app_channel():
    """聊天应用通道示例"""
    logger.info("=" * 50)
    logger.info("Example: Chat App Channel")
    logger.info("=" * 50)
    
    # 创建通道
    channel = ChatAppChannel("chat_app_1")
    
    # 添加消息处理器
    async def handle_message(msg: ChannelMessage):
        logger.info(f"Received message from {msg.user.display_name}: {msg.content}")
        
        # 发送回复
        reply_id = await channel.send_reply(
            msg.message_id,
            f"Received your message: '{msg.content}'",
            metadata={"original_id": msg.message_id}
        )
        logger.info(f"Sent reply with ID: {reply_id}")
    
    channel.add_message_handler(handle_message)
    
    # 连接通道
    await channel.connect()
    logger.info("Channel connected")
    
    # 模拟从聊天应用接收消息
    logger.info("\nSimulating incoming messages...")
    
    # 用户1发送消息
    msg1_id = await channel.receive_from_chat_app(
        user_id="user_1",
        content="Hello, can you help me?",
        metadata={"priority": "high"}
    )
    logger.info(f"Message received with ID: {msg1_id}")
    
    # 用户2发送消息
    msg2_id = await channel.receive_from_chat_app(
        user_id="user_2",
        content="I have a question about the API.",
        attachments=[{"type": "link", "url": "https://example.com"}]
    )
    logger.info(f"Message received with ID: {msg2_id}")
    
    # 直接发送消息
    logger.info("\nSending direct messages...")
    direct_msg_id = await channel.send_message(
        content="This is a broadcast message to all users.",
        message_type=MessageType.SYSTEM
    )
    logger.info(f"Direct message sent with ID: {direct_msg_id}")
    
    # 获取消息历史
    logger.info("\nMessage history:")
    history = channel.get_message_history()
    for msg in history:
        logger.info(f"  [{msg.timestamp}] {msg.user.display_name}: {msg.content}")
    
    # 等待一下让处理完成
    await asyncio.sleep(0.1)
    
    # 断开连接
    await channel.disconnect()
    logger.info("Channel disconnected")


async def example_multi_channel():
    """多通道示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example: Multi Channel")
    logger.info("=" * 50)
    
    # 创建多个通道
    channels = []
    for i in range(3):
        channel = ChatAppChannel(f"channel_{i}")
        channels.append(channel)
        
        # 连接
        await channel.connect()
        logger.info(f"Channel {i} connected")
    
    # 发送消息到所有通道
    for i, channel in enumerate(channels):
        msg_id = await channel.send_message(
            f"Hello from channel {i}!",
            metadata={"channel_index": i}
        )
        logger.info(f"Channel {i} sent message: {msg_id}")
    
    # 断开所有通道
    for i, channel in enumerate(channels):
        await channel.disconnect()
        logger.info(f"Channel {i} disconnected")


async def main():
    """主函数"""
    logger.info("📡 Channel Adapter Examples")
    
    try:
        await example_chat_app_channel()
        await example_multi_channel()
        
        logger.info("\n✅ All examples completed!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
