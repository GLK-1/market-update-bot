import requests
import json
import time as time_module
import schedule
import pandas as pd
from datetime import datetime
import logging
import random
import os
from io import StringIO
from difflib import SequenceMatcher

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "7702073946:AAFpIPXkjVmg3nnKpPN7m5ylB4fhuHkFik4"
TELEGRAM_CHAT_ID = "-1002501251184"
NEWS_API_KEY = "630a39b344f7414dbc9cb90e8a1823ac"
ALPHA_VANTAGE_API_KEY = "L4NYMVOOPDKX7P3H"

# Load stock names from Nifty 500 list (NSE website)
def build_stock_name_dict():
    url = "https://www1.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www1.nseindia.com"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df = df.dropna(subset=['Symbol', 'Company Name'])
        return dict(zip(df['Symbol'], df['Company Name']))
    except Exception as e:
        logger.error(f"Failed to download or parse Nifty 500 list: {e}")
        return {}

INDIAN_STOCKS = build_stock_name_dict()

# Function to send message to Telegram
def send_telegram_message(message):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(api_url, data=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")

# Function to get stock price from Alpha Vantage or fallback to mock
def get_stock_price(symbol):
    api_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": f"{symbol}:NSE",
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            data = response.json().get("Global Quote", {})
            if data:
                return {
                    "price": data.get("05. price", "N/A"),
                    "change": data.get("09. change", "N/A"),
                    "change_percent": data.get("10. change percent", "N/A")
                }
        # Fallback to mock data
        return generate_mock_stock_price(symbol)
    except Exception as e:
        logger.error(f"Price fetch error for {symbol}: {e}")
        return generate_mock_stock_price(symbol)

# Generate mock price if live data fails
def generate_mock_stock_price(symbol):
    price = random.uniform(200, 3000)
    change_percent = random.uniform(-2, 2)
    change = price * change_percent / 100
    return {
        "price": f"{price:.2f}",
        "change": f"{change:.2f}",
        "change_percent": f"{change_percent:.2f}%",
        "is_mock": True
    }

# Get stock news from NewsAPI
def get_stock_news():
    url = "https://newsapi.org/v2/everything"
    today = datetime.today()
    from_date = (today - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    query = "(India OR Indian) AND (stock OR market OR NSE OR BSE OR shares)"

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "from": from_date,
        "pageSize": 10
    }
    try:
        response = requests.get(url, params=params)
        return response.json().get("articles", [])
    except:
        return []

# Send news update to Telegram
def send_stock_news_update():
    articles = get_stock_news()
    if not articles:
        send_telegram_message("No recent Indian stock market news found.")
        return

    current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
    send_telegram_message(f"<b>📊 Indian Stock Market News - {current_time}</b>")
    time_module.sleep(1)

    for article in articles[:5]:
        title = article.get("title", "")
        desc = article.get("description", "")
        url = article.get("url", "")
        source = article.get("source", {}).get("name", "")

        message = f"<b>📰 {title}</b>\n\n{desc}\n\nSource: {source}\n<a href='{url}'>Read more</a>"
        send_telegram_message(message)
        time_module.sleep(2)

# Send summary of market movers
def send_market_summary():
    current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
    send_telegram_message(f"<b>📈 Market Movers - {current_time}</b>")

    stock_changes = []
    for symbol in list(INDIAN_STOCKS.keys())[:100]:  # Limit to 100 to reduce load
        data = get_stock_price(symbol)
        if data:
            try:
                change_pct = float(data['change_percent'].replace('%', ''))
                stock_changes.append((symbol, data['price'], change_pct, data['change_percent']))
            except:
                continue
        time_module.sleep(0.5)

    gainers = sorted(stock_changes, key=lambda x: x[2], reverse=True)[:5]
    losers = sorted(stock_changes, key=lambda x: x[2])[:5]

    message = "<b>🔼 Top Gainers:</b>\n"
    for symbol, price, _, change_pct_str in gainers:
        message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): ₹{price} 📈 +{change_pct_str}\n"

    message += "\n<b>🔽 Top Losers:</b>\n"
    for symbol, price, _, change_pct_str in losers:
        message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): ₹{price} 📉 {change_pct_str}\n"

    send_telegram_message(message)

# Schedule the tasks
def main():
    schedule.every().monday.at("09:15").do(send_market_summary)
    schedule.every().tuesday.at("09:15").do(send_market_summary)
    schedule.every().wednesday.at("09:15").do(send_market_summary)
    schedule.every().thursday.at("09:15").do(send_market_summary)
    schedule.every().friday.at("09:15").do(send_market_summary)

    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        for t in ['10:30', '13:30', '15:30']:
            getattr(schedule.every(), day).at(t).do(send_stock_news_update)

    logger.info("Bot started. Sending initial message.")
    send_telegram_message("<b>🤖 Stock Bot Started!</b>\nMonitoring Indian stock market news and prices.")
    send_stock_news_update()

    while True:
        schedule.run_pending()
        time_module.sleep(1)

if __name__ == "__main__":
    main()
