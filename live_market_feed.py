import asyncio
import json
import websockets
import telegram
from datetime import datetime
import pytz
from config import (
    UPSTOX_API_KEY,
    WEBSOCKET_FEED_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)
from auth_upstox import get_access_token

class LiveMarketFeed:
    def __init__(self):
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.access_token = None
        self.websocket = None
        self.subscribed_symbols = set()
        # Store last prices to calculate % change
        self.last_prices = {}
        
    async def connect(self):
        try:
            # Read access token from file
            with open('access_token.txt', 'r') as f:
                self.access_token = f.read().strip()
            
            headers = {
                "Api-Version": "2.0",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            async with websockets.connect(WEBSOCKET_FEED_URL, extra_headers=headers) as websocket:
                self.websocket = websocket
                print("Connected to Upstox WebSocket")
                
                # Subscribe to market data
                await self.subscribe_market_data()
                
                # Handle incoming messages
                while True:
                    message = await websocket.recv()
                    await self.handle_market_data(message)
                    
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            await self.reconnect()

    async def subscribe_market_data(self):
        # Subscribe to NIFTY 50 and key stocks
        subscription_request = {
            "guid": "someguid",
            "method": "sub",
            "data": {
                "mode": "full",
                "instrumentKeys": [
                    "NSE_INDEX|Nifty 50",
                    "NSE_INDEX|BANKNIFTY",
                    "NSE_EQ|RELIANCE",
                    "NSE_EQ|TCS",
                    "NSE_EQ|HDFCBANK",
                    "NSE_EQ|INFY",
                    # Add more symbols as needed
                ]
            }
        }
        await self.websocket.send(json.dumps(subscription_request))
        print("Subscribed to market data")

    async def handle_market_data(self, message):
        try:
            data = json.loads(message)
            
            if "status" in data and data["status"] == "error":
                print(f"Error in market data: {data}")
                return

            if "data" not in data:
                return

            market_data = data["data"]
            
            # Process each tick
            for tick in market_data:
                symbol = tick.get("symbol", "")
                ltp = tick.get("ltp", 0)
                change = tick.get("change", 0)
                change_percent = tick.get("change_percent", 0)
                
                # Store the last price
                if symbol not in self.last_prices:
                    self.last_prices[symbol] = ltp
                
                # Calculate significant price movement (e.g., > 1%)
                price_change_percent = ((ltp - self.last_prices[symbol]) / self.last_prices[symbol]) * 100
                
                if abs(price_change_percent) >= 1:
                    await self.send_price_alert(symbol, ltp, change, change_percent)
                    self.last_prices[symbol] = ltp

    async def send_price_alert(self, symbol, ltp, change, change_percent):
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%I:%M %p')
        
        message = f"""
🔴 Live Market Update ({current_time})

{symbol}
Price: ₹{ltp:,.2f}
Change: ₹{change:,.2f} ({change_percent:.2f}%)
"""
        await self.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )

    async def reconnect(self):
        print("Attempting to reconnect...")
        await asyncio.sleep(5)  # Wait before reconnecting
        await self.connect()

async def main():
    market_feed = LiveMarketFeed()
    await market_feed.connect()

if __name__ == "__main__":
    asyncio.run(main())
