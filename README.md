# Market Price Bot

## Setup Instructions

1. **Environment Setup**

Create a `.env` file with these variables:
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Fyers API Configuration
FYERS_CLIENT_ID=your_fyers_client_id
FYERS_SECRET_KEY=your_fyers_secret_key
FYERS_REDIRECT_URI=https://market-update-bot.onrender.com/callback
```

2. **Fyers API Setup**
- Go to [Fyers API Dashboard](https://myapi.fyers.in/)
- Create a new API application
- Set Redirect URL to: `https://market-update-bot.onrender.com/callback`
- Copy Client ID and Secret Key to your `.env` file

3. **Telegram Bot Setup**
- Create a new bot with [BotFather](https://t.me/botfather)
- Copy the bot token to `TELEGRAM_BOT_TOKEN`
- Get your chat ID by:
  - Send a message to your bot
  - Visit: `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
  - Copy the `chat_id` to `TELEGRAM_CHAT_ID`

4. **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python render_server.py

# In another terminal, run the bot
python fyers_live_feed.py
```

5. **Render.com Deployment**
- Fork/Clone this repository
- Create new Web Service on Render
- Use these settings:
  - Build Command: `pip install -r requirements-render.txt`
  - Start Command: `gunicorn render_server:app --config gunicorn_config.py`
- Add all environment variables from `.env`

## Files Overview

- `fyers_live_feed.py`: Main bot logic for market data streaming
- `render_server.py`: Web server for Fyers authentication
- `config.py`: Environment variables and configuration
- `requirements.txt`: Python dependencies for local development
- `requirements-render.txt`: Dependencies for Render deployment
- `gunicorn_config.py`: Gunicorn server configuration
- `render.yaml`: Render deployment configuration

A real-time market data streaming bot that sends price alerts to Telegram. Supports multiple Indian stock market data providers including Fyers, Upstox, and Zerodha.

## Features

- Real-time market data streaming
- Configurable price alerts
- Telegram notifications
- Market depth information
- Support for indices and stocks
- Automatic reconnection
- Cloud-ready with Render.com support

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API credentials:
- Copy `config.py.example` to `config.py`
- Add your API credentials and Telegram bot details

3. Start the bot:
```bash
python fyers_feed.py
```

## Cloud Deployment

The bot includes a ready-to-deploy setup for Render.com with:
- Flask server for authentication
- Gunicorn configuration
- Environment variable support

## Configuration

Edit `config.py` to configure:
- API credentials
- Telegram bot settings
- Trading pairs to monitor
- Alert thresholds

## Data Providers

Supports multiple Indian market data providers:
- Fyers API
- Upstox API
- Zerodha Kite Connect

## License

MIT License
