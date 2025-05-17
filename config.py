import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Fyers API Configuration
FYERS_CLIENT_ID = os.getenv('FYERS_CLIENT_ID')
# TODO: Replace with actual secret key once obtained from Fyers API Portal
FYERS_SECRET_KEY = os.getenv('FYERS_SECRET_KEY', 'demo_secret_key')  # Temporary placeholder
# Construct the redirect URI using the app's domain
FYERS_REDIRECT_URI = os.getenv('FYERS_REDIRECT_URI', 'https://market-update-bot.onrender.com/callback')

# Validate configuration
if not all([FYERS_CLIENT_ID, FYERS_SECRET_KEY, FYERS_REDIRECT_URI]):
    print("Warning: Missing Fyers API configuration!")
