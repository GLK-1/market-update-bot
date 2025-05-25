import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "7702073946:AAFpIPXkjVmg3nnKpPN7m5ylB4fhuHkFik4")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', "-1002501251184")

# Fyers API Configuration
FYERS_CLIENT_ID = os.getenv('FYERS_CLIENT_ID', "YG04377")  # Your client ID from Fyers API dashboard
FYERS_SECRET_KEY = os.getenv('FYERS_SECRET_KEY', "e1f8b2c4-0d3f-4a5c-9b6d-7c8e1f2a3b4c")  # Your secret key
FYERS_REDIRECT_URI = os.getenv('FYERS_REDIRECT_URI', "https://market-update-bot.onrender.com/callback")

# Print configuration status on load
def validate_config():
    print("Configuration Status:")
    print(f"FYERS_CLIENT_ID: {'Set' if FYERS_CLIENT_ID else 'Not Set'}")
    print(f"FYERS_SECRET_KEY: {'Set' if FYERS_SECRET_KEY else 'Not Set'}")
    print(f"FYERS_REDIRECT_URI: {FYERS_REDIRECT_URI}")
    print(f"TELEGRAM_BOT_TOKEN: {'Set' if TELEGRAM_BOT_TOKEN else 'Not Set'}")
    print(f"TELEGRAM_CHAT_ID: {'Set' if TELEGRAM_CHAT_ID else 'Not Set'}")

validate_config()

# Flask Configuration
FLASK_ENV = "production"
FLASK_APP = "render_server.py"

