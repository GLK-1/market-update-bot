# Market Price Bot

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
