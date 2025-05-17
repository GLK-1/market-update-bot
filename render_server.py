from flask import Flask, request, jsonify
import os
import telegram
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FYERS_CLIENT_ID = os.getenv('FYERS_CLIENT_ID')
FYERS_SECRET_KEY = os.getenv('FYERS_SECRET_KEY')
FYERS_REDIRECT_URI = os.getenv('FYERS_REDIRECT_URI')

app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'Market Data Server is Running!'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'telegram_bot': bool(TELEGRAM_BOT_TOKEN),
        'fyers_config': bool(FYERS_CLIENT_ID and FYERS_SECRET_KEY)
    })

@app.route('/callback')
def callback():
    """Handle the callback from Fyers authentication"""
    try:
        # Get the auth code from URL parameters
        auth_code = request.args.get('auth_code')
        if auth_code:
            # Save the auth code to a file
            with open('auth_code.txt', 'w') as f:
                f.write(auth_code)
            
            # Send the auth code to your Telegram bot
            message = f"Auth Code Received: {auth_code}"
            asyncio.run(bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            ))
            return "Authentication successful! The auth code has been sent to your Telegram bot. You can close this window."
        else:
            return "No auth code received", 400
    except Exception as e:
        return f"Error processing callback: {str(e)}", 500

@app.route('/start')
def start_feed():
    """Start the market data feed"""
    try:
        from fyers_live_feed import FyersLiveFeed
        feed = FyersLiveFeed()
        if feed.authenticate():
            feed.start_streaming()
            return jsonify({
                'status': 'success',
                'message': 'Market data feed started successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Authentication failed'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
