"""
WebSocket测试客户端 - 测试Agent Gateway
"""
import asyncio
import websockets
import json
import sys


async def test_gateway():
    """测试Gateway"""
    uri = "ws://localhost:18789/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🦞 Connected to Agent Gateway!")
            
            # 1. 发送初始化消息
            init_msg = {
                "user_id": "test_user_123",
                "session_key": "test_session_456"
            }
            await websocket.send(json.dumps(init_msg))
            print(f"📤 Sent init: {init_msg}")
            
            # 2. 接收连接确认
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get("type") == "connected":
                session_id = data.get("session_id")
                print(f"✅ Connected! Session ID: {session_id}")
                print(f"🔧 Available tools: {data.get('available_tools')}")
            else:
                print("❌ Unexpected response!")
                return
            
            # 3. 发送测试消息
            print("\n" + "="*60)
            test_messages = [
                "你好！",
                "现在几点了？",
                "计算一下 25 + 36 * 2",
                "搜索一下人工智能",
            ]
            
            for i, msg in enumerate(test_messages, 1):
                print(f"\n{i}. 📤 Sending: {msg}")
                await websocket.send(json.dumps({
                    "type": "message",
                    "body": msg,
                    "user_id": "test_user_123"
                }))
                
                # 接收响应
                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(response)
                        msg_type = data.get("type")
                        
                        if msg_type == "thinking":
                            print(f"   🤔 {data.get('message')}")
                        
                        elif msg_type == "stream":
                            print(f"   💬 {data.get('content')}", end="", flush=True)
                        
                        elif msg_type == "acting":
                            print(f"\n   🔧 {data.get('message')}")
                        
                        elif msg_type == "observation":
                            print(f"   👀 Tool [{data.get('tool')}]: {data.get('result')}")
                        
                        elif msg_type == "final":
                            print(f"\n   ✅ Final Answer: {data.get('content')}")
                            print(f"   📊 Tokens: {data.get('total_tokens')}, Time: {data.get('execution_time_ms'):.0f}ms")
                            break
                        
                        elif msg_type == "error":
                            print(f"   ❌ Error: {data.get('error')}")
                            break
                        
                        elif msg_type == "busy":
                            print(f"   ⏳ {data.get('message')}")
                            break
                    
                    except asyncio.TimeoutError:
                        print("   ⏰ Timeout!")
                        break
            
            print("\n" + "="*60)
            print("✅ All tests completed!")
            
            # 测试重置会话
            print("\nTesting reset...")
            await websocket.send(json.dumps({
                "type": "reset"
            }))
            response = await websocket.recv()
            print(f"📥 Reset response: {json.loads(response)}")
    
    except ConnectionRefusedError:
        print("❌ Connection refused! Is Gateway running?")
        print("   Start it with: python gateway_main.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🦞" * 60)
    print("🦞   Agent Gateway Test Client")
    print("🦞" * 60)
    
    # 检查是否有自定义地址
    if len(sys.argv) > 1:
        uri = sys.argv[1]
        print(f"Using custom URI: {uri}")
    
    asyncio.run(test_gateway())
