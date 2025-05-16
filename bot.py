import asyncio
import json
import ssl
import logging
import sys
from datetime import datetime
import os

# Force asyncio to use the event loop that works on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', mode='w')  # 'w' mode to start fresh
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Ensure all handlers are using DEBUG level
for handler in logger.handlers:
    handler.setLevel(logging.DEBUG)

# Now try importing dependencies with error handling
try:
    import upstox_client
    from google.protobuf.json_format import MessageToDict
    import websockets
    from telegram import Bot
    import MarketDataFeed_pb2 as pb
    from config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        UPSTOX_API_KEY,
        UPSTOX_API_SECRET,
        WEBSOCKET_FEED_URL
    )
    logger.info("All required packages imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required package: {str(e)}")
    logger.error("Please install required packages: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error during startup: {str(e)}")
    sys.exit(1)

# Setup Telegram bot
try:
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
except Exception as e:
    logger.error(f"Failed to initialize Telegram bot: {str(e)}")
    telegram_bot = None

def validate_config() -> bool:
    """Validate configuration values"""
    required_configs = {
        "UPSTOX_API_KEY": UPSTOX_API_KEY,
        "UPSTOX_API_SECRET": UPSTOX_API_SECRET,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID
    }
    
    for name, value in required_configs.items():
        if not value:
            logger.error(f"Missing required config: {name}")
            return False
    return True

def load_access_token(filename="access_token.txt"):
    """Load the access token from file"""
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Token file {filename} not found")
        return None

def get_market_data_feed_authorize(api_version, configuration):
    """Get authorization for market data feed."""
    try:
        api_instance = upstox_client.WebsocketApi(
            upstox_client.ApiClient(configuration))
        api_response = api_instance.get_market_data_feed_authorize(api_version)
        logger.info("Market data feed authorization successful")
        return api_response
    except Exception as e:
        logger.error(f"Error getting market data feed authorization: {str(e)}")
        return None

async def process_market_data(data_dict):
    """Process market data and send to Telegram"""
    try:
        if isinstance(data_dict, dict):
            # Extract LTP (Last Traded Price) from the feed
            if 'feeds' in data_dict:
                for feed in data_dict['feeds']:
                    symbol = feed.get('symbol', 'Unknown')
                    ltp = feed.get('ltp')
                    if ltp:
                        message = f"💰 {symbol}: ₹{float(ltp):,.2f}"
                        logger.info(message)
                        
                        # Send to Telegram
                        if telegram_bot:
                            try:
                                await telegram_bot.send_message(
                                    chat_id=TELEGRAM_CHAT_ID,
                                    text=message
                                )
                            except Exception as e:
                                logger.error(f"Error sending Telegram message: {e}")
    except Exception as e:
        logger.error(f"Error processing market data: {str(e)}")

async def fetch_market_data():
    """Fetch market data using WebSocket and process it."""
    try:
        access_token = load_access_token()
        if not access_token:
            logger.error("Access token not found. Please run auth_upstox.py first.")
            return

        configuration = upstox_client.Configuration()
        configuration.access_token = access_token

        # Get market data feed authorization
        response = get_market_data_feed_authorize('2.0', configuration)
        if not response or not hasattr(response, 'data'):
            logger.error("Failed to get market data feed authorization")
            return

        # Use the authorized WebSocket URL from the API response
        ws_url = response.data.authorized_redirect_uri
        logger.info(f"Authorized WebSocket URL: {ws_url}")
        
        # Create headers for WebSocket connection
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Api-Key": UPSTOX_API_KEY
        }

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(f"Connecting to WebSocket...")
        async with websockets.connect(
            ws_url,
            ssl=ssl_context,
            extra_headers=headers,
            subprotocols=['json', 'protobuf'],
            ping_interval=30,
            ping_timeout=10
        ) as websocket:
            logger.info("WebSocket connection established")

            # Generate a unique session ID
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")

            # Send initial handshake message
            handshake_msg = {
                "guid": session_id,
                "method": "handshake",
                "data": {
                    "authToken": access_token,
                    "apiKey": UPSTOX_API_KEY,
                    "source": "WEBSOCKET"
                }
            }
            
            logger.info("Sending handshake message...")
            await websocket.send(json.dumps(handshake_msg))

            # Wait for handshake response
            handshake_response = await websocket.recv()
            logger.info(f"Handshake response: {handshake_response}")

            # Send subscription request
            subscription_msg = {
                "guid": session_id,
                "method": "sub",
                "data": {
                    "mode": "full",
                    "instrumentKeys": ["NSE_EQ|INE002A01018"]
                }
            }

            logger.info("Sending subscription request...")
            await websocket.send(json.dumps(subscription_msg))

            while True:
                try:
                    message = await websocket.recv()
                    logger.debug(f"Raw message received: {message[:200]}...")
                    
                    try:
                        # Try JSON first
                        data = json.loads(message)
                        logger.debug(f"Parsed JSON message: {data}")
                        
                        # Handle different message types
                        if 'method' in data:
                            if data['method'] == 'heartbeat':
                                # Respond to heartbeat
                                heartbeat_response = {
                                    "guid": session_id,
                                    "method": "heartbeat",
                                    "data": {"status": "OK"}
                                }
                                await websocket.send(json.dumps(heartbeat_response))
                                continue
                                
                        await process_market_data(data)
                    except json.JSONDecodeError:
                        # Try protobuf if JSON fails
                        try:
                            feed_response = pb.FeedResponse()
                            feed_response.ParseFromString(message)
                            data_dict = MessageToDict(feed_response)
                            logger.debug(f"Parsed protobuf message: {data_dict}")
                            await process_market_data(data_dict)
                        except Exception as e:
                            logger.error(f"Error decoding protobuf: {str(e)}")
                    
                except websockets.exceptions.ConnectionClosed as e:
                    logger.error(f"WebSocket connection closed: {str(e)}")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    continue

    except Exception as e:
        logger.error(f"Error in fetch_market_data: {str(e)}")
        await asyncio.sleep(5)
        return

async def main():
    """Main function to run the bot"""
    logger.info("\n===== Starting Upstox Market Data Bot =====")
    
    while True:
        try:
            await fetch_market_data()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        
        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

def run_bot():
    """Initialize and run the bot with proper setup"""
    print("Initializing bot...")  # Direct console output
    
    # Initialize asyncio for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Create and set event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the main async function
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
        logger.info("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")  # Direct console output
        logger.error(f"Fatal error: {str(e)}")
        if logger.isEnabledFor(logging.DEBUG):
            import traceback
            logger.debug(traceback.format_exc())
    finally:
        # Clean up
        loop.close()

if __name__ == "__main__":
    try:
        # Test logging
        print("Starting bot initialization...")
        logger.info("Bot initialization started")
        
        # Validate configuration
        if not validate_config():
            logger.error("Invalid configuration. Please check config.py")
            sys.exit(1)
        
        # Run the bot
        run_bot()
    except Exception as e:
        print(f"Startup error: {str(e)}")
        logger.error(f"Startup error: {str(e)}")
        sys.exit(1)