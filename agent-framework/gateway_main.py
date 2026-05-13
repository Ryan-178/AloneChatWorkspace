"""
Agent Gateway 启动脚本
🦞 生产级Agent网关 - 像OpenClaw一样冲量！
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_framework.gateway import AgentGateway, GatewayConfig, create_gateway


def main():
    """启动Gateway"""
    print("🦞" * 50)
    print("🦞  Agent Gateway - 生产级Agent运行时网关  🦞")
    print("🦞" * 50)
    
    # 创建配置
    config = GatewayConfig(
        host="0.0.0.0",
        port=18789,
        debug=True,
        default_model="gpt-4o",
    )
    
    # 创建并启动Gateway
    gateway = create_gateway(config=config)
    
    print(f"\n🚀 Starting Agent Gateway on http://{config.host}:{config.port}")
    print(f"📍 WebSocket endpoint: ws://localhost:{config.port}/ws")
    print(f"📍 Health check: http://localhost:{config.port}/health")
    print(f"📍 Status: http://localhost:{config.port}/status")
    print("\nPress Ctrl+C to stop\n")
    
    gateway.run()


if __name__ == "__main__":
    main()
