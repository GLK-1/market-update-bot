from flask import Flask, request
import os
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import telegram
import asyncio

app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

@app.route('/')
def home():
    return 'Market Data Server is Running!'

@app.route('/callback')
def callback():
    """Handle the callback from Fyers authentication"""
    try:
        # Get the auth code from URL parameters
        auth_code = request.args.get('auth_code')
        if auth_code:
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
