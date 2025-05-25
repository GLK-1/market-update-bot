from fyers_api import accessToken, fyersModel
from fyers_api.Websocket import ws
import telegram
from datetime import datetime
import pytz
import logging
import asyncio
import json
import os
import requests
from config import (
      FYERS_CLIENT_ID,
    FYERS_SECRET_KEY,
    FYERS_REDIRECT_URI
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UpstoxLiveFeed:
    def __init__(self):
        """Initialize UpstoxLiveFeed instance"""
        # Initialize Telegram bot
        self.bot = telegram.Bot("AAFpIPXkjVmg3nnKpPN7m5ylB4fhuHkFik4")
        
        # Upstox API credentials
        self.api_key = os.getenv('UPSTOX_API_KEY')
        self.api_secret = os.getenv('UPSTOX_API_SECRET')
        self.redirect_uri = os.getenv('UPSTOX_REDIRECT_URI')
        self.access_token = None
        
        # Initialize data storage
        self.last_prices = {}
        self.subscribed_symbols = []
        
        # Set up logging directory
        if not os.path.exists('logs'):
            os.makedirs('logs')
    
    def authenticate(self):
        """Handle Upstox authentication"""
        try:
            auth_url = f"https://api.upstox.com/login/oauth/authorize?client_id={self.api_key}&response_type=code&redirect_uri={self.redirect_uri}"
            logger.info(f"Login URL: {auth_url}")

            # Wait for auth_code.txt to be created by callback server
            while not os.path.exists('auth_code.txt'):
                logger.info("Waiting for authentication...")
                import time
                time.sleep(2)

            # Read the auth code from file
            with open('auth_code.txt', 'r') as f:
                auth_code = f.read().strip()

            # Delete the file after reading
            os.remove('auth_code.txt')

            token_url = "https://api.upstox.com/login/oauth/token"
            payload = {
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri
            }
            response = requests.post(token_url, data=payload)
            response.raise_for_status()

            self.access_token = response.json().get('access_token')
            logger.info("Authentication successful!")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def get_nifty50_symbols(self):
        """Get NIFTY 50 symbols and format them for Fyers API"""
        try:
            # Get NIFTY 50 constituents from Fyers API
            symbols = [
                "NSE:NIFTY50-INDEX",    # NIFTY 50 Index
                "NSE:BANKNIFTY-INDEX",   # Bank NIFTY Index
                "NSE:RELIANCE-EQ",
                "NSE:TCS-EQ",
                "NSE:HDFCBANK-EQ",
                "NSE:INFY-EQ",
                "NSE:ICICIBANK-EQ",
                "NSE:HINDUNILVR-EQ",
                "NSE:ITC-EQ",
                "NSE:SBIN-EQ",
                # Add more NIFTY 50 stocks as needed
            ]
            
            self.subscribed_symbols = symbols
            logger.info(f"Subscribed to {len(symbols)} symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return []

    def process_message(self, message):
        """Process incoming WebSocket messages"""
        try:
            if not message:
                logger.warning("Received empty message")
                return
                
            data = json.loads(message)
            
            if 'symbol' not in data:
                logger.debug("Message missing symbol field")
                return
                
            symbol = data['symbol']
            ltp = data.get('ltp')
            
            if ltp is None:
                logger.warning(f"No LTP data for symbol {symbol}")
                return
                
            if symbol in self.last_prices:
                old_price = self.last_prices[symbol]
                if old_price > 0:  # Prevent division by zero
                    change = ltp - old_price
                    change_percent = (change / old_price) * 100
                    
                    # Different thresholds for indices and stocks
                    threshold = 0.5 if "INDEX" in symbol else 1.0
                    
                    if abs(change_percent) >= threshold:
                        asyncio.run(self.send_price_alert(symbol, ltp, change, change_percent))
            
            self.last_prices[symbol] = ltp
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)

    async def send_price_alert(self, symbol, ltp, change, change_percent):
        """Send price alert to Telegram"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).strftime('%I:%M %p')
            
            # Emoji based on price movement
            emoji = "🔴" if change < 0 else "🟢"
            
            # Get additional market data
            market_depth = self.get_market_depth(symbol)
            
            message = f"""
{emoji} Live Market Update ({current_time})

{symbol}
Price: ₹{ltp:,.2f}
Change: ₹{change:,.2f} ({change_percent:.2f}%)

Market Depth:
Bid: {market_depth['bid_price']} ({market_depth['bid_qty']})
Ask: {market_depth['ask_price']} ({market_depth['ask_qty']})
Volume: {market_depth['volume']:,}
"""
            await self.bot.send_message(
                chat_id=-1002501251184,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending price alert: {str(e)}", exc_info=True)

    def get_market_depth(self, symbol):
        """Get market depth data for a symbol"""
        try:
            depth = self.fyers.get_market_depth(symbols=symbol)
            data = depth['d'][0]
            
            return {
                'bid_price': data['bids'][0]['price'],
                'bid_qty': data['bids'][0]['qty'],
                'ask_price': data['asks'][0]['price'],
                'ask_qty': data['asks'][0]['qty'],
                'volume': data['tot_qty']
            }
        except Exception as e:
            logger.error(f"Error getting market depth: {str(e)}", exc_info=True)
            return {
                'bid_price': 'N/A',
                'bid_qty': 'N/A',
                'ask_price': 'N/A',
                'ask_qty': 'N/A',
                'volume': 'N/A'
            }

    def start_streaming(self):
        """Start fetching market data"""
        try:
            symbols = ["NSE:NIFTY50", "NSE:BANKNIFTY"]
            self.subscribed_symbols = symbols

            market_data_url = "https://api.upstox.com/marketdata/quotes"
            headers = {'Authorization': f'Bearer {self.access_token}'}

            for symbol in symbols:
                params = {'exchange': 'NSE', 'symbol': symbol}
                response = requests.get(market_data_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Market data for {symbol}: {data}")
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")

    def reconnect(self):
        """Attempt to reconnect WebSocket"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Attempting to reconnect... (Attempt {retry_count + 1}/{max_retries})")
                if hasattr(self, 'ws'):
                    self.ws.close()
                self.start_streaming()
                return
            except Exception as e:
                logger.error(f"Reconnection failed: {str(e)}", exc_info=True)
                retry_count += 1
                import time
                time.sleep(min(5 * retry_count, 30))  # Exponential backoff with 30s cap
        
        logger.error("Max reconnection attempts reached. Please check your connection and restart the application.")

def main():
    """Main entry point of the application"""
    try:
        feed = UpstoxLiveFeed()
        if feed.authenticate():
            feed.start_streaming()
            
            # Keep the main thread running
            import time
            while True:
                time.sleep(1)
        else:
            logger.error("Authentication failed. Please check your credentials and try again.")
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
