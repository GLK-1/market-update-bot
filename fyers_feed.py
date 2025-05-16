from fyers_api import accessToken, fyersModel
from fyers_api.Websocket import ws
import telegram
from datetime import datetime
import pytz
import json
import logging
import asyncio
import os
import time
import webbrowser
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    FYERS_CLIENT_ID,
    FYERS_SECRET_KEY
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AuthServer:
    """Simple auth server to handle callback"""
    def __init__(self, port=8000):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import parse_qs, urlparse
                query_components = parse_qs(urlparse(self.path).query)
                
                auth_code = query_components.get("auth_code", [None])[0]
                if auth_code:
                    with open("auth_code.txt", "w") as f:
                        f.write(auth_code)
                    
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"Authentication successful! You can close this window.")
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"No auth code received")
        
        self.httpd = HTTPServer(("localhost", port), CallbackHandler)
    
    def start(self):
        """Start the server in a separate thread"""
        from threading import Thread
        self.server_thread = Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def stop(self):
        """Stop the server"""
        self.httpd.shutdown()
        self.httpd.server_close()

class FyersLiveFeed:
    def __init__(self):
        """Initialize FyersLiveFeed with configurations"""
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.client_id = FYERS_CLIENT_ID
        self.secret_key = FYERS_SECRET_KEY
        self.redirect_uri = "https://your-app-name.onrender.com/callback"  # Replace with your Render URL
        self.auth_server = AuthServer(port=8000)
        self.fyers = None
        self.ws = None
        self.last_prices = {}
        
    def authenticate(self):
        """Handle authentication with improved flow"""
        try:
            print("\nStarting authentication process...")
            
            # Start the auth server
            self.auth_server.start()
            print("Auth server started on port 8000")
            
            # Create session
            session = accessToken.SessionModel(
                client_id=self.client_id,
                secret_key=self.secret_key,
                redirect_uri=self.redirect_uri,
                response_type="code",
                grant_type="authorization_code"
            )
            
            # Generate and open auth URL
            auth_url = session.generate_authcode()
            print("\nOpening login URL in your browser...")
            webbrowser.open(auth_url)
            
            # Wait for auth code
            print("\nWaiting for authentication...\n")
            start_time = time.time()
            while not os.path.exists("auth_code.txt"):
                if time.time() - start_time > 120:  # 2 minutes timeout
                    raise TimeoutError("Authentication timed out")
                time.sleep(1)
            
            # Read auth code
            with open("auth_code.txt", "r") as f:
                auth_code = f.read().strip()
            os.remove("auth_code.txt")
            
            # Stop auth server
            self.auth_server.stop()
            
            # Generate access token
            session.set_token(auth_code)
            self.access_token = session.generate_token()["access_token"]
            
            # Initialize API
            self.fyers = fyersModel.FyersModel(
                client_id=self.client_id,
                token=self.access_token,
                log_path="logs/"
            )
            
            print("\n✅ Authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            if hasattr(self, 'auth_server'):
                self.auth_server.stop()
            return False
    
    def get_symbols(self):
        """Get symbols to monitor"""
        return [
            # Indices
            "NSE:NIFTY50-INDEX",    # NIFTY 50
            "NSE:BANKNIFTY-INDEX",   # Bank NIFTY
            "NSE:FINNIFTY-INDEX",    # Financial Services
            
            # Large Cap Leaders
            "NSE:RELIANCE-EQ",      # Reliance Industries
            "NSE:TCS-EQ",           # Tata Consultancy
            "NSE:HDFCBANK-EQ",      # HDFC Bank
            "NSE:INFY-EQ",          # Infosys
            "NSE:ICICIBANK-EQ",     # ICICI Bank
            
            # Active Mid Caps
            "NSE:TATAMOTORS-EQ",    # Tata Motors
            "NSE:BAJFINANCE-EQ",    # Bajaj Finance
            "NSE:LTIM-EQ",          # L&T Technology
            "NSE:HCLTECH-EQ",       # HCL Technologies
        ]
    
    async def send_market_update(self, data):
        """Send formatted market update to Telegram"""
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%I:%M %p')
        
        symbol = data['symbol'].replace("NSE:", "").replace("-EQ", "")
        ltp = data['ltp']
        change = data['change']
        change_percent = data['change_percent']
        
        # Emoji and color based on movement
        if change > 0:
            emoji = "🟢"
            trend = "⬆️"
        else:
            emoji = "🔴"
            trend = "⬇️"
        
        # Get market depth
        depth = await self.get_market_depth(data['symbol'])
        
        message = f"""
{emoji} *{symbol}* {trend}
🕒 {current_time}

💰 *Price*: ₹{ltp:,.2f}
📊 *Change*: ₹{change:,.2f} ({change_percent:.2f}%)

🔎 *Market Depth*:
• Buy Orders: {depth['total_buy_qty']:,} @ ₹{depth['best_bid']}
• Sell Orders: {depth['total_sell_qty']:,} @ ₹{depth['best_ask']}
• Volume: {depth['volume']:,}
• Day Range: ₹{depth['low']} - ₹{depth['high']}
"""
        await self.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )

    async def get_market_depth(self, symbol):
        """Get market depth with error handling"""
        try:
            quote = await self.fyers.quotes({"symbols": symbol})
            depth = quote[symbol]
            
            return {
                'best_bid': depth['depth']['buy'][0]['price'],
                'best_ask': depth['depth']['sell'][0]['price'],
                'total_buy_qty': sum(level['qty'] for level in depth['depth']['buy']),
                'total_sell_qty': sum(level['qty'] for level in depth['depth']['sell']),
                'volume': depth['tot_qty'],
                'high': depth['high_price'],
                'low': depth['low_price']
            }
        except:
            return {
                'best_bid': 'N/A',
                'best_ask': 'N/A',
                'total_buy_qty': 0,
                'total_sell_qty': 0,
                'volume': 0,
                'high': 'N/A',
                'low': 'N/A'
            }

    def process_tick(self, tick_data):
        """Process incoming market data"""
        try:
            symbol = tick_data['symbol']
            ltp = tick_data['ltp']
            
            if symbol in self.last_prices:
                old_price = self.last_prices[symbol]
                change = ltp - old_price
                change_percent = (change / old_price) * 100
                
                # Threshold for alerts
                threshold = 0.3 if 'INDEX' in symbol else 0.8
                
                if abs(change_percent) >= threshold:
                    asyncio.run(self.send_market_update({
                        'symbol': symbol,
                        'ltp': ltp,
                        'change': change,
                        'change_percent': change_percent
                    }))
            
            self.last_prices[symbol] = ltp
            
        except Exception as e:
            logger.error(f"Error processing tick: {str(e)}")

    def start_streaming(self):
        """Initialize and start WebSocket connection"""
        try:
            symbols = self.get_symbols()
            ws_access_token = f"{self.client_id}:{self.access_token}"
            
            self.ws = ws.FyersSocket(
                access_token=ws_access_token,
                run_background=True,
                log_path="logs/"
            )
            
            self.ws.on_connect = lambda: logger.info("Connected to Fyers WebSocket")
            self.ws.on_message = lambda msg: self.process_tick(json.loads(msg))
            self.ws.on_error = lambda err: logger.error(f"WebSocket error: {err}")
            self.ws.on_close = self.reconnect
            
            # Subscribe to market data
            self.ws.subscribe(symbols=symbols, data_type="symbolData")
            self.ws.keep_running()
            
            print("\n✅ Successfully started market data stream!")
            
        except Exception as e:
            logger.error(f"Error starting stream: {str(e)}")

    def reconnect(self):
        """Handle WebSocket reconnection"""
        logger.info("Reconnecting to WebSocket...")
        try:
            if self.ws:
                self.ws.close()
            time.sleep(5)
            self.start_streaming()
        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            time.sleep(5)
            self.reconnect()

def main():
    feed = FyersLiveFeed()
    
    print("\n🚀 Starting Market Feed Bot")
    print("---------------------------")
    
    if feed.authenticate():
        feed.start_streaming()
        
        print("\n⌛ Bot is running... Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down bot...")
            if feed.ws:
                feed.ws.close()

if __name__ == "__main__":
    main()
