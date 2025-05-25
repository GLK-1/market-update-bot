from flask import Flask, request, jsonify
import os
import telegram
import asyncio
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Get configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
UPSTOX_API_KEY = os.getenv('UPSTOX_API_KEY')
UPSTOX_API_SECRET = os.getenv('UPSTOX_API_SECRET')
UPSTOX_REDIRECT_URI = os.getenv('UPSTOX_REDIRECT_URI')

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
        'upstox_config': bool(UPSTOX_API_KEY and UPSTOX_API_SECRET)
    })

@app.route('/callback')
def callback():
    """Handle the callback from Upstox authentication"""
    try:
        app.logger.info("Callback endpoint hit")
        app.logger.info(f"Request args: {dict(request.args)}")

        # Get the auth code from the request
        auth_code = request.args.get('code')
        if not auth_code:
            return "No auth code received", 400

        # Exchange auth code for access token
        token_url = "https://api.upstox.com/login/oauth/token"
        payload = {
            'client_id': UPSTOX_API_KEY,
            'client_secret': UPSTOX_API_SECRET,
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': UPSTOX_REDIRECT_URI
        }
        response = requests.post(token_url, data=payload)
        if response.status_code != 200:
            return f"Error fetching access token: {response.text}", 500

        access_token = response.json().get('access_token')
        if not access_token:
            return "Access token not found in response", 500

        # Save the access token to a file
        with open('access_token.txt', 'w') as f:
            f.write(access_token)

        # Send the access token to your Telegram bot
        message = f"Access Token Received: {access_token[:4]}****"
        asyncio.run(bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        ))
        return "Authentication successful! The access token has been sent to your Telegram bot. You can close this window."
    except Exception as e:
        return f"Error processing callback: {str(e)}", 500

@app.route('/start')
def start_feed():
    """Start the market data feed using Upstox"""
    try:
        with open('access_token.txt', 'r') as f:
            access_token = f.read().strip()

        # Fetch market data (example: NIFTY 50 index)
        market_data_url = "https://api.upstox.com/marketdata/quotes"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        params = {
            'exchange': 'NSE',
            'symbol': 'NIFTY 50'
        }
        response = requests.get(market_data_url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Error fetching market data: {response.text}", 500

        market_data = response.json()
        return jsonify({
            'status': 'success',
            'market_data': market_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test-redirect')
def test_redirect():
    """Test endpoint to verify redirect URL configuration"""
    # Get all environment variables for debugging
    env_vars = {
        'UPSTOX_REDIRECT_URI': UPSTOX_REDIRECT_URI,
        'UPSTOX_API_KEY': UPSTOX_API_KEY[:4] + '****' if UPSTOX_API_KEY else None,
        'HAS_API_SECRET': bool(UPSTOX_API_SECRET),
        'HAS_TELEGRAM_TOKEN': bool(TELEGRAM_BOT_TOKEN),
        'HAS_TELEGRAM_CHAT': bool(TELEGRAM_CHAT_ID)
    }
    
    # Construct the expected callback URL
    expected_callback = "https://market-update-bot.onrender.com/callback"
    
    return jsonify({
        'status': 'ok',
        'message': 'Redirect URL is accessible',
        'environment': env_vars,
        'suggested_redirect_uri': expected_callback,
        'request_info': {
            'scheme': request.scheme,
            'host': request.host,
            'path': request.path,
            'url': request.url,
            'base_url': request.base_url,
            'headers': dict(request.headers)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
