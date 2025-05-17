from kiteconnect import KiteConnect, KiteTicker
import telegram
from datetime import datetime
import pytz
import json
import logging
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    KITE_API_KEY,
    KITE_API_SECRET
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KiteLiveFeed:
    def __init__(self):
        # Initialize Telegram bot
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Initialize Kite Connect
        self.api_key = KITE_API_KEY
        self.api_secret = KITE_API_SECRET
        self.kite = KiteConnect(api_key=self.api_key)
        self.ticker = None
        
        # Store last prices and subscribed instruments
        self.last_prices = {}
        self.subscribed_instruments = {}
        self.nifty50_stocks = []
        
    def authenticate(self):
        """Generate authentication URL and handle login"""
        try:
            print("Login to Zerodha and authorize the application...")
            print(f"Login URL: {self.kite.login_url()}")
            request_token = input("Enter request token: ")
            
            # Generate access token
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.kite.set_access_token(data["access_token"])
            
            # Initialize ticker with access token
            self.ticker = KiteTicker(self.api_key, data["access_token"])
            
            print("Authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def get_instruments(self):
        """Get instrument tokens for NIFTY 50 stocks and indices"""
        try:
            # Get all NSE instruments
            instruments = self.kite.instruments("NSE")
            
            # Get NIFTY 50 list
            nifty50 = self.kite.instruments("NFO")
            nifty50_symbols = [inst['tradingsymbol'] for inst in nifty50 if 'NIFTY50' in inst['tradingsymbol']]
            
            # Store instrument tokens
            for instrument in instruments:
                if (instrument['tradingsymbol'] in nifty50_symbols or 
                    instrument['tradingsymbol'] in ['NIFTY 50', 'NIFTY BANK']):
                    self.subscribed_instruments[instrument['instrument_token']] = instrument['tradingsymbol']
                    
            logger.info(f"Subscribed to {len(self.subscribed_instruments)} instruments")
            
        except Exception as e:
            logger.error(f"Error getting instruments: {str(e)}")

    def on_ticks(self, ws, ticks):
        """Callback when new ticks arrive"""
        try:
            for tick in ticks:
                instrument_token = tick['instrument_token']
                symbol = self.subscribed_instruments.get(instrument_token)
                
                if not symbol:
                    continue
                
                ltp = tick.get('last_price', 0)
                
                # Calculate price change
                if instrument_token in self.last_prices:
                    old_price = self.last_prices[instrument_token]
                    change = ltp - old_price
                    change_percent = (change / old_price) * 100
                    
                    # Alert on significant moves (>1% for stocks, >0.5% for indices)
                    threshold = 0.5 if symbol in ['NIFTY 50', 'NIFTY BANK'] else 1.0
                    
                    if abs(change_percent) >= threshold:
                        self.send_price_alert(symbol, ltp, change, change_percent)
                
                self.last_prices[instrument_token] = ltp
                
        except Exception as e:
            logger.error(f"Error processing ticks: {str(e)}")

    def on_connect(self, ws, response):
        """Callback on successful connection"""
        logger.info("Successfully connected to Kite WebSocket")
        # Subscribe to instruments
        ws.subscribe(list(self.subscribed_instruments.keys()))
        ws.set_mode(ws.MODE_FULL, list(self.subscribed_instruments.keys()))

    def on_close(self, ws, code, reason):
        """Callback when connection is closed"""
        logger.warning(f"Connection closed: {reason}")
        # Attempt to reconnect
        self.start_streaming()

    def on_error(self, ws, code, reason):
        """Callback when an error occurs"""
        logger.error(f"Error in WebSocket: {reason}")

    async def send_price_alert(self, symbol, ltp, change, change_percent):
        """Send price alert to Telegram"""
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%I:%M %p')
        
        # Emoji based on price movement
        emoji = "🔴" if change < 0 else "🟢"
        
        message = f"""
{emoji} Live Market Update ({current_time})

{symbol}
Price: ₹{ltp:,.2f}
Change: ₹{change:,.2f} ({change_percent:.2f}%)

Volume: {self.get_volume_data(symbol)}
"""
        await self.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )

    def get_volume_data(self, symbol):
        """Get trading volume data for a symbol"""
        try:
            quote = self.kite.quote(f"NSE:{symbol}")
            volume = quote[f"NSE:{symbol}"]["volume"]
            return f"{volume:,}"
        except:
            return "N/A"

    def start_streaming(self):
        """Start WebSocket connection"""
        try:
            # Get instruments first
            self.get_instruments()
            
            # Set callbacks
            self.ticker.on_ticks = self.on_ticks
            self.ticker.on_connect = self.on_connect
            self.ticker.on_close = self.on_close
            self.ticker.on_error = self.on_error
            
            # Start WebSocket connection
            self.ticker.connect(threaded=True)
            
        except Exception as e:
            logger.error(f"Error starting WebSocket: {str(e)}")

def main():
    # Create instance
    kite_feed = KiteLiveFeed()
    
    # Authenticate
    if kite_feed.authenticate():
        # Start streaming
        kite_feed.start_streaming()
        
        # Keep the main thread running
        import time
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()
