"""
Gateway 测试脚本
验证基本功能是否正常
"""
import asyncio
import websockets
import json
import httpx


async def test_health_check():
    """测试健康检查端点"""
    print("\n🧪 Testing Health Check...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:18789/health")
            print(f"✅ Health Check Status: {response.status_code}")
            print(f"📊 Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Check failed: {e}")
        return False


async def test_websocket():
    """测试WebSocket通信"""
    print("\n🧪 Testing WebSocket...")
    try:
        uri = "ws://localhost:18789/ws"
        
        async with websockets.connect(uri) as websocket:
            # 1. 发送初始化消息
            init_msg = {
                "user_id": "test_user_123",
                "session_key": "test_session_456"
            }
            await websocket.send(json.dumps(init_msg))
            print("📤 Sent init message")
            
            # 2. 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("type") == "connected":
                session_id = data.get("session_id")
                print(f"✅ Connected! Session ID: {session_id}")
            else:
                print("❌ Unexpected response")
                return False
            
            # 3. 发送测试消息
            test_msg = {
                "type": "message",
                "body": "你好，Agent Gateway！🦞",
                "user_id": "test_user_123"
            }
            await websocket.send(json.dumps(test_msg))
            print(f"\n📤 Sent test message: {test_msg['body']}")
            
            # 4. 接收流式响应
            print("\n📥 Receiving stream responses...")
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "thinking":
                        print(f"🤔 {data.get('message')}")
                    elif data.get("type") == "stream":
                        print(f"💬 Stream: {data.get('content')}")
                    elif data.get("type") == "final":
                        print(f"✅ Final: {data.get('content')}")
                        print(f"🔍 Trace ID: {data.get('trace_id')}")
                        break
                    elif data.get("type") == "error":
                        print(f"❌ Error: {data.get('error')}")
                        return False
                except asyncio.TimeoutError:
                    print("⏱️ Timeout waiting for response")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stats():
    """测试统计信息端点"""
    print("\n🧪 Testing Stats...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:18789/stats")
            print(f"✅ Stats Status: {response.status_code}")
            stats = response.json()
            print(f"📊 Gateway Stats:")
            print(f"  - Uptime: {stats['gateway']['uptime_seconds']:.1f}s")
            print(f"  - Active Sessions: {stats['gateway']['active_sessions']}")
            print(f"  - Messages Processed: {stats['gateway']['total_messages_processed']}")
            print(f"  - Session Stats: {stats['sessions']}")
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False


async def main():
    """运行所有测试"""
    print("🦞" * 60)
    print("🦞       Agent Gateway 测试套件       🦞")
    print("🦞" * 60)
    
    results = []
    
    # 测试1: 健康检查
    results.append(("Health Check", await test_health_check()))
    
    # 等待一下确保服务稳定
    await asyncio.sleep(0.5)
    
    # 测试2: WebSocket
    results.append(("WebSocket", await test_websocket()))
    
    # 测试3: 统计
    results.append(("Stats", await test_stats()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！Gateway运行正常！")
    else:
        print("⚠️  部分测试失败，请检查")
    print("=" * 60)


if __name__ == "__main__":
    print("\n⚠️  请确保先启动Gateway: python gateway_main.py")
    print("   然后在另一个终端运行此测试脚本\n")
    input("按Enter继续...")
    
    asyncio.run(main())
