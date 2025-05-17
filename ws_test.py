import asyncio
import websockets
import ssl
import json
import sys
from datetime import datetime

async def test_connection():
    print("Starting WebSocket test...")  # Basic console output
    
    # Load access token
    with open('access_token.txt', 'r') as f:
        access_token = f.read().strip()
    
    # Connection details
    ws_url = "wss://feed.upstox.com/v2/feed"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Api-Key": "8421b9e7-b350-428c-a0bd-c48a570b1c32"
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(
            ws_url,
            ssl=ssl_context,
            extra_headers=headers,
            ping_interval=30,
            ping_timeout=10
        ) as ws:
            print("Connected! Sending subscription message...")
            
            # Send subscription
            sub_message = {
                "guid": datetime.now().strftime("%Y%m%d%H%M%S"),
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": ["NSE_EQ|INE002A01018"]
                }
            }
            
            await ws.send(json.dumps(sub_message))
            print("Subscription sent, waiting for messages...")
            
            while True:
                try:
                    msg = await ws.recv()
                    print(f"Received: {msg[:200]}...")  # Print first 200 chars
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    print("Starting test script...")
    asyncio.run(test_connection())